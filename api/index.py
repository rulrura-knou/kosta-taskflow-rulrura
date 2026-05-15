import os
import re
import random
import string
import sys
from contextlib import asynccontextmanager

import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from _db import get_db, init_schema, q, to_dict, to_list
from _jwt import create_token, get_current_user

# ── helpers ───────────────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
INVITE_RE = re.compile(r"^[A-Z]{4}-[0-9]{4}$")
VALID_STATUSES = {"TODO", "DOING", "DONE"}


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def check_pw(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def gen_code() -> str:
    return (
        "".join(random.choices(string.ascii_uppercase, k=4))
        + "-"
        + "".join(random.choices(string.digits, k=4))
    )


def err(status: int, code: str, msg: str, **kw) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": msg, **kw})


def require_member(team_id: int, user: dict):
    if user.get("team_id") != team_id:
        raise err(403, "FORBIDDEN", "이 팀의 멤버가 아닙니다")


# ── lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_schema()
    yield


# ── app ───────────────────────────────────────────────────────────────────────

app = FastAPI(lifespan=lifespan, docs_url="/api/docs", redoc_url=None)


@app.exception_handler(HTTPException)
async def http_exc_handler(req, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── AUTH ──────────────────────────────────────────────────────────────────────

class SignupIn(BaseModel):
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup", status_code=201)
def signup(body: SignupIn):
    if not EMAIL_RE.match(body.email):
        raise err(400, "VALIDATION_ERROR", "올바른 이메일 형식이 아닙니다")
    if len(body.password) < 8:
        raise err(400, "VALIDATION_ERROR", "비밀번호는 8자 이상이어야 합니다")
    with get_db() as cur:
        cur.execute(q("SELECT id FROM users WHERE email = ?"), (body.email,))
        if cur.fetchone():
            raise err(409, "EMAIL_TAKEN", "이미 가입된 이메일입니다")
        cur.execute(
            q("INSERT INTO users (email, password_hash) VALUES (?, ?) RETURNING id, email, team_id, created_at"),
            (body.email, hash_pw(body.password)),
        )
        user = to_dict(cur.fetchone())
    return {"token": create_token(user["id"], user["email"]), "user": user}


@app.post("/api/auth/login")
def login(body: LoginIn):
    with get_db() as cur:
        cur.execute(
            q("SELECT id, email, password_hash, team_id FROM users WHERE email = ?"),
            (body.email,),
        )
        user = to_dict(cur.fetchone())
    if not user or not check_pw(body.password, user["password_hash"]):
        raise err(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 일치하지 않습니다")
    user.pop("password_hash")
    return {"token": create_token(user["id"], user["email"]), "user": user}


@app.post("/api/auth/logout")
def logout():
    return {}


@app.get("/api/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user


# ── TEAMS ─────────────────────────────────────────────────────────────────────

class TeamCreateIn(BaseModel):
    name: str


class JoinIn(BaseModel):
    invite_code: str


@app.post("/api/teams", status_code=201)
def create_team(body: TeamCreateIn, current_user: dict = Depends(get_current_user)):
    if not (1 <= len(body.name.strip()) <= 30):
        raise err(400, "VALIDATION_ERROR", "팀 이름은 1-30자여야 합니다")
    if current_user.get("team_id"):
        raise err(409, "ALREADY_IN_TEAM", "이미 팀에 소속되어 있습니다")
    code = gen_code()
    with get_db() as cur:
        for _ in range(5):
            cur.execute(q("SELECT id FROM teams WHERE invite_code = ?"), (code,))
            if not cur.fetchone():
                break
            code = gen_code()
        cur.execute(
            q("INSERT INTO teams (name, invite_code, owner_id) VALUES (?, ?, ?) RETURNING id, name, invite_code, owner_id, created_at"),
            (body.name.strip(), code, current_user["id"]),
        )
        team = to_dict(cur.fetchone())
        cur.execute(q("UPDATE users SET team_id = ? WHERE id = ?"), (team["id"], current_user["id"]))
    return team


@app.post("/api/teams/join")
def join_team(body: JoinIn, current_user: dict = Depends(get_current_user)):
    if not INVITE_RE.match(body.invite_code):
        raise err(400, "VALIDATION_ERROR", "형식이 올바르지 않습니다 (예: FRNT-2026)")
    if current_user.get("team_id"):
        raise err(409, "ALREADY_IN_TEAM", "이미 다른 팀에 소속되어 있습니다")
    with get_db() as cur:
        cur.execute(q("SELECT id, name FROM teams WHERE invite_code = ?"), (body.invite_code,))
        team = to_dict(cur.fetchone())
        if not team:
            raise err(404, "NOT_FOUND", "해당 초대코드를 찾을 수 없습니다")
        cur.execute(q("UPDATE users SET team_id = ? WHERE id = ?"), (team["id"], current_user["id"]))
        cur.execute(q("SELECT COUNT(*) as cnt FROM users WHERE team_id = ?"), (team["id"],))
        member_count = dict(cur.fetchone())["cnt"]
    return {"team": {**team, "member_count": member_count}, "redirect": f"/teams/{team['id']}"}


@app.get("/api/teams/{team_id}")
def get_team(team_id: int, current_user: dict = Depends(get_current_user)):
    require_member(team_id, current_user)
    with get_db() as cur:
        cur.execute(
            q("SELECT id, name, invite_code, owner_id, created_at FROM teams WHERE id = ?"),
            (team_id,),
        )
        team = to_dict(cur.fetchone())
        if not team:
            raise err(404, "NOT_FOUND", "팀을 찾을 수 없습니다")
        cur.execute(q("SELECT COUNT(*) as cnt FROM users WHERE team_id = ?"), (team_id,))
        team["member_count"] = dict(cur.fetchone())["cnt"]
    return team


@app.get("/api/teams/{team_id}/members")
def get_members(team_id: int, current_user: dict = Depends(get_current_user)):
    require_member(team_id, current_user)
    with get_db() as cur:
        cur.execute(q("SELECT owner_id FROM teams WHERE id = ?"), (team_id,))
        t = to_dict(cur.fetchone())
        if not t:
            raise err(404, "NOT_FOUND", "팀을 찾을 수 없습니다")
        cur.execute(q("SELECT id, email, created_at FROM users WHERE team_id = ?"), (team_id,))
        members = to_list(cur.fetchall())
    return [{**m, "is_owner": m["id"] == t["owner_id"]} for m in members]


@app.delete("/api/teams/{team_id}/leave")
def leave_team(team_id: int, current_user: dict = Depends(get_current_user)):
    require_member(team_id, current_user)
    with get_db() as cur:
        cur.execute(q("UPDATE users SET team_id = NULL WHERE id = ?"), (current_user["id"],))
    return {}


# ── TASKS ─────────────────────────────────────────────────────────────────────

class TaskCreateIn(BaseModel):
    title: str
    assignee_id: int | None = None


class TaskUpdateIn(BaseModel):
    title: str | None = None
    assignee_id: int | None = None


class StatusIn(BaseModel):
    status: str


@app.get("/api/teams/{team_id}/tasks")
def list_tasks(team_id: int, filter: str = "all", current_user: dict = Depends(get_current_user)):
    require_member(team_id, current_user)
    base = """SELECT t.*, u.email as assignee_email
              FROM tasks t LEFT JOIN users u ON u.id = t.assignee_id
              WHERE t.team_id = ?"""
    with get_db() as cur:
        if filter == "me":
            cur.execute(q(base + " AND t.assignee_id = ? ORDER BY t.created_at DESC"), (team_id, current_user["id"]))
        elif filter == "unassigned":
            cur.execute(q(base + " AND t.assignee_id IS NULL ORDER BY t.created_at DESC"), (team_id,))
        else:
            cur.execute(q(base + " ORDER BY t.created_at DESC"), (team_id,))
        return to_list(cur.fetchall())


@app.post("/api/teams/{team_id}/tasks", status_code=201)
def create_task(team_id: int, body: TaskCreateIn, current_user: dict = Depends(get_current_user)):
    require_member(team_id, current_user)
    if not body.title or not (1 <= len(body.title) <= 100):
        raise err(400, "VALIDATION_ERROR", "태스크 제목은 1-100자여야 합니다")
    with get_db() as cur:
        cur.execute(
            q("INSERT INTO tasks (team_id, title, creator_id, assignee_id) VALUES (?, ?, ?, ?) RETURNING *"),
            (team_id, body.title, current_user["id"], body.assignee_id),
        )
        return to_dict(cur.fetchone())


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute(q("SELECT * FROM tasks WHERE id = ?"), (task_id,))
        task = to_dict(cur.fetchone())
    if not task:
        raise err(404, "NOT_FOUND", "태스크를 찾을 수 없습니다")
    if task["team_id"] != current_user.get("team_id"):
        raise err(403, "FORBIDDEN", "권한이 없습니다")
    return task


@app.patch("/api/tasks/{task_id}/status")
def update_status(task_id: int, body: StatusIn, current_user: dict = Depends(get_current_user)):
    if body.status not in VALID_STATUSES:
        raise err(400, "VALIDATION_ERROR", "status는 TODO, DOING, DONE 중 하나여야 합니다")
    with get_db() as cur:
        cur.execute(q("SELECT team_id FROM tasks WHERE id = ?"), (task_id,))
        t = to_dict(cur.fetchone())
    if not t:
        raise err(404, "NOT_FOUND", "태스크를 찾을 수 없습니다")
    if t["team_id"] != current_user.get("team_id"):
        raise err(403, "FORBIDDEN", "권한이 없습니다")
    with get_db() as cur:
        cur.execute(q("UPDATE tasks SET status = ? WHERE id = ? RETURNING *"), (body.status, task_id))
        return to_dict(cur.fetchone())


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdateIn, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute(q("SELECT * FROM tasks WHERE id = ?"), (task_id,))
        task = to_dict(cur.fetchone())
    if not task:
        raise err(404, "NOT_FOUND", "태스크를 찾을 수 없습니다")
    if task["team_id"] != current_user.get("team_id"):
        raise err(403, "FORBIDDEN", "권한이 없습니다")
    new_title = body.title if body.title is not None else task["title"]
    new_assignee = body.assignee_id if "assignee_id" in body.model_fields_set else task["assignee_id"]
    with get_db() as cur:
        cur.execute(
            q("UPDATE tasks SET title = ?, assignee_id = ? WHERE id = ? RETURNING *"),
            (new_title, new_assignee, task_id),
        )
        return to_dict(cur.fetchone())


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute(q("SELECT creator_id, team_id FROM tasks WHERE id = ?"), (task_id,))
        task = to_dict(cur.fetchone())
    if not task:
        raise err(404, "NOT_FOUND", "태스크를 찾을 수 없습니다")
    if task["team_id"] != current_user.get("team_id"):
        raise err(403, "FORBIDDEN", "권한이 없습니다")
    with get_db() as cur:
        cur.execute(q("SELECT owner_id FROM teams WHERE id = ?"), (task["team_id"],))
        team = to_dict(cur.fetchone())
    if not (task["creator_id"] == current_user["id"] or (team and team["owner_id"] == current_user["id"])):
        raise err(403, "FORBIDDEN", "권한이 없습니다")
    with get_db() as cur:
        cur.execute(q("DELETE FROM tasks WHERE id = ?"), (task_id,))
    return {}


# ── MESSAGES ──────────────────────────────────────────────────────────────────

class MessageIn(BaseModel):
    content: str


@app.get("/api/teams/{team_id}/messages")
def list_messages(team_id: int, since: str = None, current_user: dict = Depends(get_current_user)):
    require_member(team_id, current_user)
    base = """SELECT m.*, u.email as user_email
              FROM messages m JOIN users u ON u.id = m.user_id
              WHERE m.team_id = ?"""
    with get_db() as cur:
        if since:
            cur.execute(q(base + " AND m.created_at > ? ORDER BY m.created_at ASC"), (team_id, since))
        else:
            cur.execute(q(base + " ORDER BY m.created_at ASC LIMIT 50"), (team_id,))
        return to_list(cur.fetchall())


@app.post("/api/teams/{team_id}/messages", status_code=201)
def create_message(team_id: int, body: MessageIn, current_user: dict = Depends(get_current_user)):
    require_member(team_id, current_user)
    if not body.content:
        raise err(400, "VALIDATION_ERROR", "메시지 내용은 필수입니다")
    if len(body.content) > 1000:
        raise err(400, "TOO_LONG", "메시지는 1000자 이내로 입력하세요", limit=1000, actual=len(body.content))
    with get_db() as cur:
        cur.execute(
            q("INSERT INTO messages (team_id, user_id, content) VALUES (?, ?, ?) RETURNING *"),
            (team_id, current_user["id"], body.content),
        )
        msg = to_dict(cur.fetchone())
    msg["user_email"] = current_user["email"]
    return msg


@app.delete("/api/messages/{message_id}")
def delete_message(message_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute(q("SELECT user_id, team_id FROM messages WHERE id = ?"), (message_id,))
        msg = to_dict(cur.fetchone())
    if not msg:
        raise err(404, "NOT_FOUND", "메시지를 찾을 수 없습니다")
    if msg["team_id"] != current_user.get("team_id"):
        raise err(403, "FORBIDDEN", "권한이 없습니다")
    if msg["user_id"] != current_user["id"]:
        raise err(403, "NOT_OWNER", "본인의 메시지만 삭제할 수 있습니다")
    with get_db() as cur:
        cur.execute(q("DELETE FROM messages WHERE id = ?"), (message_id,))
    return {}


# ── Static files (local dev only) ─────────────────────────────────────────────

if not os.getenv("VERCEL") and os.path.isdir(os.path.join(os.path.dirname(__file__), "..", "public")):
    app.mount(
        "/",
        StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "public"), html=True),
        name="static",
    )

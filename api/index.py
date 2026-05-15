from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class SignupRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup", status_code=201)
def signup(body: SignupRequest):
    return {"ok": True, "email": body.email, "message": "Vercel Python cold start 검증 성공"}


@app.get("/api/ping")
def ping():
    return {"ok": True, "message": "pong"}

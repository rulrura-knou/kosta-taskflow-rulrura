## Context

신규 프로젝트. 기존 코드 없음.

- **팀 규모**: 3-5인 소규모 팀, 동시 접속 최대 50명
- **기술 스택 확정**: FastAPI + Vanilla JS + Tailwind CSS + Neon(운영)/SQLite(로컬)
- **배포 환경**: Vercel (프론트: 정적 파일, 백엔드: Python Serverless Functions)
- **인증**: JWT 24h, localStorage 저장 (XSS 방어는 MVP 범위 외로 인지하고 진행)
- **실시간성**: WebSocket 없음, 5초 폴링으로 대체

## Goals / Non-Goals

**Goals:**
- 인증 → 팀 합류 → 칸반 → 채팅 전체 흐름 완성
- 로컬(SQLite) ↔ 운영(Neon) DATABASE_URL 환경변수 하나로 전환
- Vercel main push 자동 배포 파이프라인
- 18개 API 표준 에러 응답 `{ error: { code, message } }` 일관 적용
- 모바일 반응형 (Tailwind breakpoint md:768 / lg:1024)

**Non-Goals:**
- WebSocket, 알림, 파일 첨부, 전문 검색, 테스트 자동화
- JWT 갱신 토큰, 블랙리스트, HttpOnly 쿠키
- 팀 이동 (탈퇴 후 다른 팀 합류)
- 모바일 폴링 2초 단축, pull-to-refresh
- i18n, 다중 시간대 (KST/UTC 혼용 없이 UTC 저장 + 한국어 UI 고정)

## Decisions

### D1. FastAPI를 Vercel Serverless Functions로 배포

**결정**: `api/index.py` 진입점 + `vercel.json` rewrite 규칙으로 FastAPI를 Vercel Python 런타임에 올림

```json
// vercel.json
{
  "rewrites": [{ "source": "/api/(.*)", "destination": "/api/index.py" }]
}
```

**대안 고려**:
- Railway/Render 별도 배포 → 두 도메인 관리, CORS 복잡도 증가
- Next.js API Routes → 프론트 프레임워크 변경, 학습 비용

**리스크**: Python cold start가 Node.js보다 느림 (~1-3초). propose 전에 단일 엔드포인트 배포 검증 필요.

---

### D2. 1인 1팀 모델 — users.team_id

**결정**: `users` 테이블에 `team_id FK→teams NULL` 컬럼 추가. NULL = 미가입, 값 있음 = 팀 소속.

**대안 고려**:
- 별도 `team_members` 조인 테이블 → DB 4테이블 제약 초과, 쿼리 복잡도 증가
- 다중 팀 소속 → MVP 범위 밖, 권한 모델 복잡도 급증

**제약**: 팀 이동 불가 (탈퇴 후 다른 팀 합류 시 409). 운영 중 팀 이동은 DB 직접 수정.

---

### D3. '내 태스크' = assignee_id 기준

**결정**: `tasks.assignee_id FK→users NULL` 추가. `@me` 필터는 `WHERE assignee_id = current_user_id`. creator_id로 필터링하지 않음.

**근거**: "내가 만든 태스크"와 "내가 담당한 태스크"는 다르다. creator_id만으로는 위임된 태스크를 필터링할 수 없음.

---

### D4. 채팅 폴링 — ISO 8601 UTC + since= 증분

**결정**: `created_at` TIMESTAMP를 UTC로 저장. `since=` 파라미터는 ISO 8601 전체 형식(`2026-05-13T14:30:00.000Z`) 고정.

```
GET /teams/7/messages?since=2026-05-13T14:30:00.000Z
```

**근거**: SQLite는 TIMESTAMP를 TEXT로 저장하므로 문자열 비교(`>`)가 동작하려면 ISO 8601 형식이어야 함. PostgreSQL도 동일 형식으로 비교 가능 → 환경 전환 시 코드 변경 없음.

**폴링 재시도**: 실패 시 exponential backoff (5s→10s→20s→40s→60s 고정).

---

### D5. PATCH /tasks/{id}/status 분리

**결정**: 상태 변경과 제목/assignee 수정을 분리.
- `PATCH /tasks/{id}/status` — 칸반 드래그 전용, body: `{ status: "DOING" }`
- `PUT /tasks/{id}` — 상세 모달 수정, body: `{ title?, assignee_id? }`

**근거**: 드래그 drop 시 status만 변경. PUT으로 통합하면 title/assignee를 항상 함께 전송해야 해서 경쟁 조건(concurrent edit) 발생 가능.

---

### D6. JWT localStorage + stateless logout

**결정**: JWT를 localStorage에 저장. 로그아웃은 `POST /auth/logout` 200 반환 + 클라이언트 `localStorage.removeItem('token')`.

**트레이드오프**: XSS 시 토큰 탈취 가능. HttpOnly 쿠키로 전환하면 CORS SameSite 설정, 로컬 개발 포트 불일치 문제 발생. MVP에서는 단순함 우선.

**갱신 토큰 없음**: 24h 만료 시 무조건 재로그인. 401 응답 → axios interceptor → localStorage 삭제 → `/login` redirect.

---

### D7. 에러 응답 표준 — `{ error: { code, message } }`

**결정**: 모든 4xx/5xx 응답은 동일 구조.

```json
{ "error": { "code": "SCREAMING_SNAKE", "message": "한국어 사용자 메시지" } }
```

주요 에러 코드:
| HTTP | code | 발생 조건 |
|------|------|-----------|
| 400 | VALIDATION_ERROR | 형식 오류 |
| 400 | TOO_LONG | 메시지 1000자 초과 |
| 401 | INVALID_CREDENTIALS | 로그인 실패 |
| 401 | TOKEN_EXPIRED | JWT 만료/누락 |
| 403 | FORBIDDEN | 비멤버 팀 접근 |
| 403 | NOT_OWNER | 타인 메시지/태스크 삭제 |
| 404 | NOT_FOUND | 리소스 없음 |
| 409 | EMAIL_TAKEN | 이메일 중복 |
| 409 | ALREADY_IN_TEAM | 다른 팀 이미 소속 |

---

### D8. 프론트엔드 — MPA (HTML 파일별 페이지)

**결정**: SPA 라우터 없이 HTML 파일별 분리 (login.html, team.html, kanban.html, chat.html).

**대안 고려**:
- SPA (hash routing) → Vanilla JS로 구현 시 상태 관리 코드 증가
- MPA → 페이지 이동 시 전체 로드, JWT 검사 각 페이지에서 반복 → 단순함 우선

**JWT 가드**: 각 HTML 페이지 상단 스크립트에서 `localStorage.getItem('token')` 검사. 없으면 `/login.html` redirect.

## Risks / Trade-offs

| 리스크 | 완화 |
|--------|------|
| Vercel Python cold start (~1-3초) | propose 전 단일 엔드포인트 사전 배포 검증 |
| SQLite ↔ PostgreSQL 호환성 (TIMESTAMP 비교) | ISO 8601 UTC 형식 강제, since= 통합 테스트 |
| 팀 이동 불가 (1인 1팀) | 409 + 명확한 에러 메시지로 사용자 안내 |
| JWT localStorage XSS | MVP 트레이드오프 인지, 추후 HttpOnly 쿠키 전환 |
| 5초 폴링 — 채팅 지연 | since= 증분으로 부하 최소화, 연결 끊김 시 backoff |
| 초대코드 재발급 없음 | 코드 노출 시 DB 직접 수정 (MVP 한계) |

## Open Questions

- [ ] Vercel Python 런타임 사전 배포 검증 완료 여부 (Day 1 시작 전 확인)
  --> 수행 해
- [ ] Neon 무료 플랜 연결 수 제한 확인 (pooled connection URL 사용 권장)
  --> 10개
- [ ] Tailwind CDN vs 빌드 — MVP에서는 CDN (`<script src="https://cdn.tailwindcss.com">`) 사용
  --> CDN 으로 해
- [x] SQLAlchemy vs 순수 SQL — **순수 SQL 확정** (`sqlite3` / `psycopg2` 분기, `schema.sql`로 스키마 관리)

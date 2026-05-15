## ADDED Requirements

### Requirement: 로컬 개발 환경
로컬 환경에서 FastAPI + SQLite로 동작한다. `DATABASE_URL` 환경변수 하나로 SQLite와 Neon을 전환한다.

#### Scenario: 로컬 서버 시작
- **WHEN** `DATABASE_URL=sqlite:///./taskflow.db uvicorn main:app --reload` 실행
- **THEN** FastAPI 서버가 localhost:8000에서 동작, SQLite 파일 자동 생성

#### Scenario: 프론트엔드 로컬 개발
- **WHEN** `live-server` 또는 `python -m http.server`로 정적 파일 서빙
- **THEN** 프론트엔드가 `http://localhost:8000/api`로 백엔드 호출

---

### Requirement: Vercel 배포 구조
백엔드는 `api/index.py` 진입점을 통해 Vercel Python Serverless Functions로 배포된다. 프론트엔드는 정적 파일로 Vercel에서 서빙된다.

#### Scenario: 배포 구조 검증
- **WHEN** `vercel.json`에 `"rewrites": [{ "source": "/api/(.*)", "destination": "/api/index.py" }]` 설정
- **THEN** `/api/*` 경로가 FastAPI로 라우팅

#### Scenario: main 브랜치 push 자동 배포
- **WHEN** `git push origin main`
- **THEN** Vercel이 자동으로 프론트엔드 + 백엔드를 빌드하고 배포

---

### Requirement: Neon 운영 데이터베이스
운영 환경에서는 Vercel Marketplace의 Neon PostgreSQL을 사용한다. Neon의 Pooled Connection URL을 `DATABASE_URL` 환경변수로 주입한다.

#### Scenario: 환경변수 전환
- **WHEN** `DATABASE_URL=postgresql://...neon.tech/taskflow?sslmode=require` 환경변수 설정
- **THEN** SQLAlchemy가 PostgreSQL에 연결, SQLite와 동일한 쿼리 동작

#### Scenario: Neon 연결 확인
- **WHEN** 배포 후 `GET /auth/me` 호출
- **THEN** HTTP 200 또는 401 (서버 동작 확인), DB 연결 오류 없음

---

### Requirement: DB 테이블 자동 생성
앱 시작 시 SQLAlchemy `create_all()`로 4개 테이블과 인덱스를 자동 생성한다. 로컬/운영 양쪽에서 동일하게 동작한다.

#### Scenario: 첫 실행 테이블 생성
- **WHEN** 빈 DB 상태에서 서버 시작
- **THEN** users, teams, tasks, messages 테이블 자동 생성, 복합 인덱스 생성

#### Scenario: 재시작 시 멱등성
- **WHEN** 이미 테이블이 존재하는 상태에서 서버 재시작
- **THEN** `create_all(checkfirst=True)`로 기존 테이블 유지, 에러 없음

---

### Requirement: CORS 설정
Vercel 배포 도메인만 허용한다. 로컬 개발 시 localhost도 허용한다.

#### Scenario: 운영 CORS
- **WHEN** `taskflow.vercel.app`에서 API 호출
- **THEN** CORS 허용, 정상 응답

#### Scenario: 미허용 도메인 차단
- **WHEN** 허용되지 않은 도메인에서 API 호출
- **THEN** CORS 오류, 브라우저에서 요청 차단

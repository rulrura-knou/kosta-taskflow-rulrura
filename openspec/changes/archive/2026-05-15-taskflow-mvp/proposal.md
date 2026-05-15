## Why

소규모 팀은 태스크 추적과 빠른 의사결정을 위해 칸반 + 채팅을 동시에 쓰지만, 대부분의 도구는 두 기능이 분리되어 있다. TaskFlow MVP는 칸반 + 실시간(폴링) 채팅을 한 화면에서 제공해 컨텍스트 전환 없이 팀 업무를 추적할 수 있게 한다.

## What Changes

- **신규 구축** — 기존 코드 없음. 처음부터 전체 시스템을 구현
- 회원가입 / 로그인 / JWT 인증 (24h, stateless)
- 팀 생성, 초대코드 발급/합류, 멤버 목록
- 칸반 보드: TODO / DOING / DONE 3컬럼, 카드 드래그로 상태 이동
- 팀 채팅: 5초 폴링, since= 증분 조회, 1000자 제한
- Vercel 배포: 프론트(정적) + 백엔드(Serverless Functions) + Neon PostgreSQL

## Capabilities

### New Capabilities

- `auth`: 회원가입, 로그인, JWT 발급/검증, 로그아웃(stateless), 현재 사용자 조회
- `team`: 팀 생성+초대코드 발급, 초대코드 합류, 팀 정보 조회, 멤버 목록, 팀 떠나기
- `kanban`: 태스크 CRUD, 상태 변경(PATCH 분리), assignee 지정(nullable), 필터(@me/미할당)
- `chat`: 메시지 송신, since= 폴링 수신, 본인 메시지 삭제
- `deployment`: Vercel + Neon 환경 구성, 로컬(SQLite) ↔ 운영(PostgreSQL) DATABASE_URL 전환

### Modified Capabilities

<!-- 신규 프로젝트이므로 기존 스펙 없음 -->

## Impact

**API**: 18개 엔드포인트 신규 (Auth 4 + Team 5 + Task 6 + Chat 3)

**DB**: 4테이블 신규 (users, teams, tasks, messages)
- `users.team_id` (FK→teams, nullable) — 1인 1팀 모델
- `tasks.assignee_id` (FK→users, nullable) — '내 태스크' = assignee 기준
- `tasks.created_at` — 칸반 정렬용

**기술 스택**:
- Backend: FastAPI (Python) + SQLAlchemy + Neon(운영)/SQLite(로컬)
- Frontend: Vanilla JS + Tailwind CSS
- 배포: Vercel (Python Serverless Functions) + GitHub main push 자동 배포

**Out of Scope**:
- WebSocket 실시간 (5초 폴링으로 대체)
- JWT 갱신 토큰 / 블랙리스트 (24h 만료 후 재로그인)
- 팀 이동 — 탈퇴 후 다른 팀 합류 불가, 409로 차단 (DB 직접 수정 필요)
- 모바일 폴링 2초 단축 / pull-to-refresh (5초 고정)
- 파일 첨부, 전문 검색, 알림(이메일/SMS/푸시), 테스트 자동화
- i18n (한국어 UI 고정), 다중 시간대 (KST 고정, UTC 저장)
- XSS 방어 / CSP (JWT는 localStorage 저장, MVP 트레이드오프로 인지하고 진행)

## 1. 프로젝트 초기 설정

- [ ] 1.1 프로젝트 디렉토리 구조 생성 (backend/, frontend/, api/)
- [ ] 1.2 Python 가상환경 생성 및 의존성 설치 (fastapi, uvicorn, python-jose, bcrypt, psycopg2-binary)
- [ ] 1.3 `vercel.json` 작성 — `/api/*` → `api/index.py` rewrite 규칙
- [ ] 1.4 `.env` 파일 작성 — `DATABASE_URL=sqlite:///./taskflow.db`, `JWT_SECRET`
- [ ] 1.5 Vercel Python cold start 사전 검증 — `POST /auth/signup` 1개만 배포해서 동작 확인

## 2. DB 연결 및 스키마

- [ ] 2.1 DB 연결 유틸리티 작성 — `DATABASE_URL` 앞부분으로 sqlite3 vs psycopg2 분기, `get_conn()` 함수 제공
- [ ] 2.2 `schema.sql` 작성 — 4테이블 CREATE TABLE IF NOT EXISTS (users, teams, tasks, messages)
- [ ] 2.3 `schema.sql` 인덱스 추가 — tasks(team_id, created_at), messages(team_id, created_at), teams(invite_code UNIQUE)
- [ ] 2.4 앱 시작 시 `schema.sql` 자동 실행 — FastAPI `lifespan` 이벤트에서 스크립트 실행 (멱등성 보장)

## 3. 인증 API (Auth 4개)

- [ ] 3.1 JWT 발급/검증 유틸리티 — `python-jose`, 24h 만료, SECRET_KEY 환경변수
- [ ] 3.2 JWT 검증 미들웨어 (FastAPI Depends) — 401 TOKEN_EXPIRED / 누락 처리
- [ ] 3.3 `POST /auth/signup` — 이메일 형식, 8자+ 비밀번호 검증, bcrypt 해시, 201+JWT
- [ ] 3.4 `POST /auth/login` — 자격증명 검증, 이메일 존재 여부 노출 금지, 200+JWT+team_id
- [ ] 3.5 `POST /auth/logout` — 200 반환 (stateless, 서버 상태 변화 없음)
- [ ] 3.6 `GET /auth/me` — 현재 사용자 정보 반환
- [ ] 3.7 에러 응답 표준 검증 — 모든 4xx가 `{ error: { code, message } }` 형태인지 확인

## 4. 팀 API (Team 5개)

- [ ] 4.1 `POST /teams` — 팀 생성, invite_code 자동 생성(`^[A-Z]{4}-[0-9]{4}$`), users.team_id 업데이트
- [ ] 4.2 `POST /teams/join` — 초대코드 형식 검증, 존재 확인, ALREADY_IN_TEAM(409) 처리, users.team_id 업데이트
- [ ] 4.3 `GET /teams/{id}` — 팀 정보 조회, 비멤버 403 처리
- [ ] 4.4 `GET /teams/{id}/members` — 멤버 목록, is_owner 플래그 포함
- [ ] 4.5 `DELETE /teams/{id}/leave` — users.team_id = null 업데이트

## 5. 칸반 API (Task 6개)

- [ ] 5.1 팀 멤버십 검증 의존성 — `user.team_id == path_id` 아니면 403
- [ ] 5.2 `GET /teams/{id}/tasks` — 전체/me/unassigned 필터, created_at desc 정렬
- [ ] 5.3 `POST /teams/{id}/tasks` — 태스크 생성, creator_id=current_user, status=TODO
- [ ] 5.4 `GET /tasks/{id}` — 단일 태스크 조회, 비멤버 403
- [ ] 5.5 `PATCH /tasks/{id}/status` — status TODO/DOING/DONE 검증, 멤버십 검증
- [ ] 5.6 `PUT /tasks/{id}` — title, assignee_id 수정 (null 허용)
- [ ] 5.7 `DELETE /tasks/{id}` — creator 또는 owner만 허용, 그 외 403 FORBIDDEN

## 6. 채팅 API (Chat 3개)

- [ ] 6.1 `GET /teams/{id}/messages` — since= ISO 8601 UTC 파라미터, 없으면 최근 50개
- [ ] 6.2 `POST /teams/{id}/messages` — 1000자 검증(클라+서버), 201+메시지 객체
- [ ] 6.3 `DELETE /messages/{id}` — user_id == current_user만 허용, 그 외 403 NOT_OWNER

## 7. 프론트엔드 — 인증 화면

- [ ] 7.1 Tailwind CDN 로드 및 공통 레이아웃 설정
- [ ] 7.2 `login.html` — 이메일+비밀번호 입력, 처리 중 버튼 비활성화, 에러 인라인 표시
- [ ] 7.3 `signup.html` — 이메일 형식, 8자+ 비밀번호 클라이언트 검증, 처리 중 상태
- [ ] 7.4 JWT localStorage 저장/읽기/삭제 유틸리티 모듈
- [ ] 7.5 각 페이지 진입 시 JWT 검사 → 없으면 `/login.html` redirect
- [ ] 7.6 401 응답 axios/fetch interceptor → localStorage 삭제 → `/login.html` redirect

## 8. 프론트엔드 — 팀 선택 화면

- [ ] 8.1 `team.html` — team_id=null 사용자만 접근, 팀 있으면 칸반으로 redirect
- [ ] 8.2 팀 만들기 폼 — 팀 이름 1-30자 검증, 생성 후 초대코드 표시 + 복사 버튼
- [ ] 8.3 초대코드 합류 폼 — `^[A-Z]{4}-[0-9]{4}$` 형식 검증, 에러 케이스 3가지 (400/404/409) 인라인 표시

## 9. 프론트엔드 — 칸반 화면

- [ ] 9.1 `kanban.html` — 3컬럼 TODO/DOING/DONE 레이아웃 (Tailwind grid)
- [ ] 9.2 태스크 카드 렌더링 — 제목, #id, @assignee 표시, 미할당 ⚠뱃지
- [ ] 9.3 필터 버튼 — 전체/@me/미할당 토글, 클라이언트 필터링
- [ ] 9.4 + 버튼 인라인 입력 — Enter 저장, Esc 취소, 담당자 드롭다운
- [ ] 9.5 HTML5 Drag & Drop — dragstart/dragover/drop 이벤트, `PATCH /tasks/{id}/status` 호출
- [ ] 9.6 카드 클릭 모달 — 상태 토글, 담당자 변경, 제목 수정, 삭제 버튼(권한 있는 경우만)
- [ ] 9.7 빈 상태(empty state) — TODO 컬럼에 "첫 태스크 만들기" CTA
- [ ] 9.8 모바일 반응형 — 768px 미만 1컬럼 스와이프, 카드 길게 누르기 → 상태 변경 메뉴

## 10. 프론트엔드 — 채팅 화면

- [ ] 10.1 `chat.html` — 메시지 말풍선 레이아웃 (본인: 우측, 타인: 좌측)
- [ ] 10.2 5초 폴링 setInterval — since= 마지막 메시지 created_at ISO 8601 UTC 파라미터
- [ ] 10.3 메시지 전송 — 1000자 카운터 실시간 표시, 초과 시 버튼 disable + 카운터 적색
- [ ] 10.4 본인 메시지 호버 시 🗑 아이콘 표시, 클릭 시 즉시 삭제 (확인 다이얼로그 없음)
- [ ] 10.5 폴링 실패 감지 — 헤더 "⚠연결 끊김" 표시, exponential backoff (5s→10s→20s→40s→60s)
- [ ] 10.6 빈 채팅 empty state — "아직 대화가 없습니다" + 첫 메시지 유도
- [ ] 10.7 모바일 반응형 — 키보드 활성 시 visualViewport API로 메시지 영역 축소

## 11. 프론트엔드 — 공통 컴포넌트

- [ ] 11.1 헤더 — 팀명, 칸반/채팅/멤버 탭, 사용자 이메일, 로그아웃 버튼
- [ ] 11.2 모바일 햄버거 메뉴 — 768px 미만에서 슬라이드 메뉴 (칸반/채팅/팀멤버/로그아웃)
- [ ] 11.3 멤버 사이드 패널 — owner(★) 구분, 가입일 표시
- [ ] 11.4 에러 토스트 / 인라인 에러 컴포넌트 공통화

## 12. 배포 및 환경 연결

- [ ] 12.1 GitHub 레포지토리 생성 및 초기 push
- [ ] 12.2 Vercel 프로젝트 연결 (GitHub 연동)
- [ ] 12.3 Vercel Marketplace에서 Neon 연동 — Pooled Connection URL 자동 주입 확인
- [ ] 12.4 Vercel 환경변수 설정 — `DATABASE_URL`, `JWT_SECRET`
- [ ] 12.5 `git push origin main` 자동 배포 확인
- [ ] 12.6 CORS 설정 — Vercel 배포 도메인 + localhost 허용
- [ ] 12.7 운영 DB 테이블 자동 생성 확인 (첫 배포 후 `GET /auth/me` 호출)

## 13. 통합 검증

- [ ] 13.1 신규 합류자 시나리오 — 회원가입 → 초대코드 입력 → 칸반 진입 5분 이내
- [ ] 13.2 권한 격리 — 비멤버가 `/teams/{other_id}/*` 접근 시 모두 403 확인
- [ ] 13.3 채팅 폴링 누락 없음 — POST 201 메시지가 since= 조회에서 100% 노출 확인
- [ ] 13.4 에러 응답 표준 — 전체 4xx/5xx가 `{ error: { code, message } }` 형태 확인
- [ ] 13.5 모바일 동작 확인 — Chrome DevTools 모바일 시뮬레이터로 칸반+채팅 동작
- [ ] 13.6 since= UTC 호환성 — 로컬(SQLite) → Neon(PostgreSQL) 전환 후 채팅 폴링 동작 확인

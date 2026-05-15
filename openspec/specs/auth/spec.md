## ADDED Requirements

### Requirement: 회원가입
사용자는 이메일과 비밀번호로 계정을 생성할 수 있다. 서버는 `POST /auth/signup`을 받아 비밀번호를 bcrypt로 해시하고 JWT를 즉시 발급한다. 이메일 인증 없이 즉시 계정 활성화한다.

#### Scenario: 정상 가입
- **WHEN** 유효한 이메일과 8자 이상 비밀번호로 `POST /auth/signup` 호출
- **THEN** HTTP 201, `{ token: "<JWT>", user: { id, email, team_id: null } }` 반환

#### Scenario: 이메일 형식 오류
- **WHEN** `user@invalid` 같이 도메인 없는 이메일로 가입 시도
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR", message: "올바른 이메일 형식이 아닙니다" } }`

#### Scenario: 비밀번호 7자 이하
- **WHEN** 7자 이하 비밀번호로 가입 시도
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR", message: "비밀번호는 8자 이상이어야 합니다" } }`

#### Scenario: 이메일 중복
- **WHEN** 이미 가입된 이메일로 가입 시도
- **THEN** HTTP 409, `{ error: { code: "EMAIL_TAKEN", message: "이미 가입된 이메일입니다" } }`

---

### Requirement: 로그인
사용자는 이메일과 비밀번호로 로그인하여 JWT를 발급받는다. 로그인 성공 시 `users.team_id`를 반환하며, 클라이언트는 이 값으로 팀 선택 화면 또는 칸반으로 분기한다.

#### Scenario: 정상 로그인
- **WHEN** 등록된 이메일과 올바른 비밀번호로 `POST /auth/login` 호출
- **THEN** HTTP 200, `{ token: "<JWT 24h>", user: { id, email, team_id } }` 반환

#### Scenario: 팀 미가입 사용자 로그인
- **WHEN** `team_id = null`인 사용자가 로그인
- **THEN** HTTP 200, `user.team_id: null` 반환 → 클라이언트가 팀 선택 화면으로 redirect

#### Scenario: 잘못된 자격증명
- **WHEN** 존재하지 않는 이메일 또는 틀린 비밀번호로 로그인
- **THEN** HTTP 401, `{ error: { code: "INVALID_CREDENTIALS", message: "이메일 또는 비밀번호가 일치하지 않습니다" } }` (이메일 존재 여부 노출 금지)

---

### Requirement: JWT 검증 미들웨어
`/auth/signup`, `/auth/login` 외 모든 API는 Authorization 헤더의 JWT를 검증해야 한다. 만료 또는 누락 시 401을 반환한다.

#### Scenario: 유효한 JWT
- **WHEN** `Authorization: Bearer <valid_jwt>` 헤더와 함께 보호 API 호출
- **THEN** 요청 처리 정상 진행, `current_user` 컨텍스트 주입

#### Scenario: JWT 만료
- **WHEN** 24h 이후 만료된 JWT로 API 호출
- **THEN** HTTP 401, `{ error: { code: "TOKEN_EXPIRED", message: "인증이 만료되었습니다" } }`

#### Scenario: JWT 누락
- **WHEN** Authorization 헤더 없이 보호 API 호출
- **THEN** HTTP 401, `{ error: { code: "TOKEN_EXPIRED", message: "인증이 만료되었습니다" } }`

---

### Requirement: 로그아웃 (stateless)
로그아웃은 서버에 블랙리스트를 유지하지 않는다. `POST /auth/logout`은 HTTP 200만 반환하며, 클라이언트가 localStorage에서 토큰을 삭제한다.

#### Scenario: 로그아웃 요청
- **WHEN** 유효한 JWT로 `POST /auth/logout` 호출
- **THEN** HTTP 200, `{}` 반환 (서버 상태 변화 없음)

#### Scenario: 클라이언트 토큰 삭제
- **WHEN** 로그아웃 응답 수신
- **THEN** 클라이언트가 `localStorage.removeItem('token')` 실행 후 `/login.html`로 redirect

---

### Requirement: 현재 사용자 조회
JWT로 현재 로그인한 사용자 정보를 조회한다.

#### Scenario: 정상 조회
- **WHEN** 유효한 JWT로 `GET /auth/me` 호출
- **THEN** HTTP 200, `{ id, email, team_id }` 반환

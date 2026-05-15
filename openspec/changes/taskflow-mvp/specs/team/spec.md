## ADDED Requirements

### Requirement: 팀 생성 및 초대코드 발급
사용자는 팀 이름(1-30자)으로 팀을 생성한다. 생성자가 자동으로 `owner_id`가 되며, 서버가 초대코드를 자동 생성한다. 생성 즉시 `users.team_id`가 업데이트된다.

#### Scenario: 정상 팀 생성
- **WHEN** 팀 이름 1-30자로 `POST /teams` 호출
- **THEN** HTTP 201, `{ id, name, invite_code: "XXXX-9999", owner_id, created_at }` 반환, `users.team_id = teams.id` 업데이트

#### Scenario: 초대코드 형식
- **WHEN** 팀 생성 성공
- **THEN** `invite_code`는 정규식 `^[A-Z]{4}-[0-9]{4}$` 형식 (예: FRNT-2026)

#### Scenario: 팀 이름 길이 초과
- **WHEN** 31자 이상 팀 이름으로 `POST /teams` 호출
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR", message: "팀 이름은 1-30자여야 합니다" } }`

---

### Requirement: 초대코드로 팀 합류
사용자는 초대코드를 입력해 기존 팀에 합류한다. 합류 성공 시 `users.team_id`가 업데이트된다.

#### Scenario: 정상 합류
- **WHEN** 유효한 초대코드(`POST /teams/join { invite_code }`)로 합류 요청
- **THEN** HTTP 200, `{ team: { id, name, member_count }, redirect: "/teams/{id}" }` 반환, `users.team_id` 업데이트

#### Scenario: 초대코드 형식 오류
- **WHEN** `abcd1234` 같이 하이픈 없는 형식으로 합류 요청
- **THEN** HTTP 400, `{ error: { code: "VALIDATION_ERROR", message: "형식이 올바르지 않습니다 (예: FRNT-2026)" } }`

#### Scenario: 존재하지 않는 초대코드
- **WHEN** `XXXX-9999` 같이 존재하지 않는 코드로 합류 요청
- **THEN** HTTP 404, `{ error: { code: "NOT_FOUND", message: "해당 초대코드를 찾을 수 없습니다" } }`

#### Scenario: 이미 다른 팀 소속
- **WHEN** `team_id != null`인 사용자가 합류 요청
- **THEN** HTTP 409, `{ error: { code: "ALREADY_IN_TEAM", message: "이미 다른 팀에 소속되어 있습니다" } }`

---

### Requirement: 팀 정보 조회
팀 멤버는 팀 기본 정보를 조회할 수 있다. 비멤버는 403으로 차단된다.

#### Scenario: 정상 조회
- **WHEN** 팀 멤버가 `GET /teams/{id}` 호출
- **THEN** HTTP 200, `{ id, name, invite_code, owner_id, member_count, created_at }` 반환

#### Scenario: 비멤버 접근
- **WHEN** `user.team_id != id`인 사용자가 `GET /teams/{id}` 호출
- **THEN** HTTP 403, `{ error: { code: "FORBIDDEN", message: "이 팀의 멤버가 아닙니다" } }`

---

### Requirement: 팀 멤버 목록 조회
팀 멤버는 소속 팀의 전체 멤버 목록을 조회할 수 있다. owner는 ★로 표시된다.

#### Scenario: 정상 조회
- **WHEN** 팀 멤버가 `GET /teams/{id}/members` 호출
- **THEN** HTTP 200, `[{ id, email, is_owner: bool, joined_at }]` 배열 반환

---

### Requirement: 팀 떠나기
사용자는 소속 팀을 떠날 수 있다. 떠난 후 `users.team_id = null`이 된다. 떠난 후 다른 팀에 재합류하는 것은 불가능하다 (409).

#### Scenario: 정상 탈퇴
- **WHEN** 팀 멤버가 `DELETE /teams/{id}/leave` 호출
- **THEN** HTTP 200, `{}` 반환, `users.team_id = null` 업데이트

#### Scenario: 탈퇴 후 다른 팀 합류 시도
- **WHEN** `team_id = null`인 사용자가 새 초대코드로 합류 시도
- **THEN** HTTP 200 정상 합류 (NULL 상태이므로 409 아님)

#### Scenario: 소속 중 다른 팀 합류 시도
- **WHEN** `team_id != null`인 사용자가 다른 팀 초대코드로 합류 시도
- **THEN** HTTP 409, ALREADY_IN_TEAM 에러

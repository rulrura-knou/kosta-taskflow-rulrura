## ADDED Requirements

### Requirement: 메시지 조회 (폴링)
팀 채팅 메시지를 조회한다. `since=` 파라미터(ISO 8601 UTC)로 증분 조회하여 새 메시지만 가져온다. 첫 진입 시 최근 50개를 가져온다.

#### Scenario: 첫 진입 전체 조회
- **WHEN** `GET /teams/{id}/messages` (since 없음)
- **THEN** HTTP 200, 최근 50개 메시지 배열 반환 (created_at asc 정렬)

#### Scenario: since= 증분 조회
- **WHEN** `GET /teams/{id}/messages?since=2026-05-13T14:30:00.000Z`
- **THEN** HTTP 200, `created_at > since` 조건 메시지만 반환 (빈 배열이면 `[]`)

#### Scenario: 5초 폴링 정상 동작
- **WHEN** 클라이언트가 5초마다 since= 파라미터로 GET 호출
- **THEN** 새 메시지가 없으면 `[]`, 있으면 해당 메시지만 반환

#### Scenario: 비멤버 메시지 조회 시도
- **WHEN** `user.team_id != id`인 사용자가 메시지 조회
- **THEN** HTTP 403, FORBIDDEN

---

### Requirement: 메시지 전송
팀 멤버는 1000자 이내 텍스트 메시지를 전송할 수 있다. 클라이언트와 서버 양쪽에서 1000자 검증한다.

#### Scenario: 정상 메시지 전송
- **WHEN** 팀 멤버가 `POST /teams/{id}/messages { content: "메시지" }` 호출
- **THEN** HTTP 201, `{ id, team_id, user_id, user_email, content, created_at }` 반환

#### Scenario: 1000자 초과 메시지
- **WHEN** 1001자 이상 content로 `POST /teams/{id}/messages` 호출
- **THEN** HTTP 400, `{ error: { code: "TOO_LONG", message: "메시지는 1000자 이내로 입력하세요", limit: 1000, actual: <실제 길이> } }`

#### Scenario: 빈 메시지
- **WHEN** 빈 문자열 content로 전송 시도
- **THEN** HTTP 400, VALIDATION_ERROR

---

### Requirement: 메시지 삭제 (본인만)
사용자는 본인이 전송한 메시지만 삭제할 수 있다. team owner도 타인 메시지 삭제 불가.

#### Scenario: 본인 메시지 삭제
- **WHEN** 메시지 전송자가 `DELETE /messages/{id}` 호출
- **THEN** HTTP 200, 메시지 삭제

#### Scenario: 타인 메시지 삭제 시도
- **WHEN** 메시지 전송자가 아닌 사용자가 `DELETE /messages/{id}` 호출
- **THEN** HTTP 403, `{ error: { code: "NOT_OWNER", message: "본인의 메시지만 삭제할 수 있습니다" } }`

#### Scenario: owner도 타인 메시지 삭제 불가
- **WHEN** team owner가 타인이 전송한 메시지를 `DELETE /messages/{id}` 호출
- **THEN** HTTP 403, NOT_OWNER 에러

---

### Requirement: 폴링 장애 복구
5초 폴링 실패 시 exponential backoff로 재시도하며, 복구 후 누락 메시지를 since= 파라미터로 일괄 수신한다.

#### Scenario: 네트워크 장애 감지
- **WHEN** 폴링 GET 요청이 실패(network error or 5xx)
- **THEN** 헤더에 "⚠연결 끊김" 표시, 다음 재시도 간격: 5s→10s→20s→40s→60s(고정)

#### Scenario: 복구 후 메시지 동기화
- **WHEN** 재시도 성공
- **THEN** 마지막 성공한 `created_at`을 since= 파라미터로 사용해 누락 메시지 수신

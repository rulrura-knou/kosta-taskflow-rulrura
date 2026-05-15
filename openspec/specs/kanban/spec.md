## ADDED Requirements

### Requirement: 태스크 목록 조회 및 필터
팀 멤버는 칸반 보드의 태스크를 조회할 수 있다. 필터(전체/@me/미할당)와 정렬(created_at desc)을 지원한다.

#### Scenario: 전체 태스크 조회
- **WHEN** 팀 멤버가 `GET /teams/{id}/tasks` 호출 (필터 없음)
- **THEN** HTTP 200, 해당 팀의 전체 태스크 배열 반환 (created_at desc 정렬)

#### Scenario: @me 필터
- **WHEN** `GET /teams/{id}/tasks?filter=me` 호출
- **THEN** `WHERE assignee_id = current_user_id` 조건 태스크만 반환

#### Scenario: 미할당 필터
- **WHEN** `GET /teams/{id}/tasks?filter=unassigned` 호출
- **THEN** `WHERE assignee_id IS NULL` 조건 태스크만 반환

#### Scenario: 비멤버 접근
- **WHEN** `user.team_id != id`인 사용자가 태스크 조회
- **THEN** HTTP 403, FORBIDDEN 에러

---

### Requirement: 태스크 생성
팀 멤버는 칸반 컬럼(기본 TODO)에 태스크를 생성할 수 있다. `assignee_id`는 nullable — 미할당 상태로 생성 가능하다.

#### Scenario: 정상 태스크 생성
- **WHEN** 팀 멤버가 `POST /teams/{id}/tasks { title, assignee_id? }` 호출
- **THEN** HTTP 201, `{ id, team_id, title, status: "TODO", creator_id, assignee_id, created_at }` 반환

#### Scenario: 미할당 태스크 생성
- **WHEN** `assignee_id` 없이 태스크 생성
- **THEN** HTTP 201, `assignee_id: null` 태스크 생성, 칸반에 "⚠미할당" 뱃지 표시

#### Scenario: 태스크 제목 길이 초과
- **WHEN** 101자 이상 제목으로 태스크 생성 시도
- **THEN** HTTP 400, VALIDATION_ERROR

---

### Requirement: 태스크 상태 변경 (드래그)
팀 멤버는 칸반 카드를 드래그하여 TODO / DOING / DONE 간 상태를 변경할 수 있다.

#### Scenario: 정상 상태 변경
- **WHEN** 팀 멤버가 `PATCH /tasks/{id}/status { status: "DOING" }` 호출
- **THEN** HTTP 200, 업데이트된 태스크 반환

#### Scenario: 유효하지 않은 상태값
- **WHEN** `{ status: "INVALID" }` 로 PATCH 호출
- **THEN** HTTP 400, VALIDATION_ERROR

#### Scenario: 비멤버 상태 변경 시도
- **WHEN** 팀 비멤버가 PATCH 호출
- **THEN** HTTP 403, FORBIDDEN

---

### Requirement: 태스크 상세 수정
팀 멤버는 태스크의 제목과 담당자(assignee_id)를 수정할 수 있다.

#### Scenario: 제목 수정
- **WHEN** 팀 멤버가 `PUT /tasks/{id} { title: "새 제목" }` 호출
- **THEN** HTTP 200, 업데이트된 태스크 반환

#### Scenario: 담당자 변경
- **WHEN** 팀 멤버가 `PUT /tasks/{id} { assignee_id: 5 }` 호출
- **THEN** HTTP 200, assignee_id 업데이트

#### Scenario: 담당자 미할당으로 변경
- **WHEN** `PUT /tasks/{id} { assignee_id: null }` 호출
- **THEN** HTTP 200, assignee_id = null

---

### Requirement: 태스크 삭제
태스크는 creator 또는 team owner만 삭제할 수 있다. 삭제 전 확인 다이얼로그 표시.

#### Scenario: creator가 본인 태스크 삭제
- **WHEN** creator가 `DELETE /tasks/{id}` 호출
- **THEN** HTTP 200, 태스크 삭제

#### Scenario: owner가 타인 태스크 삭제
- **WHEN** team owner가 타인 태스크 `DELETE /tasks/{id}` 호출
- **THEN** HTTP 200, 태스크 삭제

#### Scenario: 일반 멤버가 타인 태스크 삭제 시도
- **WHEN** creator도 owner도 아닌 멤버가 `DELETE /tasks/{id}` 호출
- **THEN** HTTP 403, `{ error: { code: "FORBIDDEN", message: "권한이 없습니다" } }`

---

### Requirement: 태스크 단일 조회
태스크 상세 모달에 필요한 단일 태스크를 조회한다.

#### Scenario: 정상 조회
- **WHEN** 팀 멤버가 `GET /tasks/{id}` 호출
- **THEN** HTTP 200, `{ id, team_id, title, status, creator_id, assignee_id, created_at }` 반환

#### Scenario: 존재하지 않는 태스크
- **WHEN** 없는 태스크 id로 조회
- **THEN** HTTP 404, NOT_FOUND

## ADDED Requirements

### Requirement: 로그인 화면
시스템은 미인증 사용자에게 로그인/회원가입 화면을 제공해야 한다.

#### Scenario: 로그인 성공 후 팀 선택 화면 이동
- **WHEN** 사용자가 유효한 email/password로 로그인 버튼 클릭
- **THEN** JWT를 localStorage에 저장하고 팀 선택 화면으로 이동

#### Scenario: 로그인 실패 에러 표시
- **WHEN** 잘못된 자격증명으로 로그인 시도
- **THEN** 화면 내 에러 메시지 표시 (페이지 이동 없음)

#### Scenario: 회원가입 링크 클릭
- **WHEN** 사용자가 '회원가입' 링크 클릭
- **THEN** 회원가입 폼(email, password 입력)으로 전환

### Requirement: 팀 선택 화면
인증된 사용자는 소속 팀 목록을 확인하고 팀 생성 또는 초대코드로 합류할 수 있어야 한다.

#### Scenario: 팀 목록 표시
- **WHEN** 팀 선택 화면 진입
- **THEN** `GET /teams`로 내 팀 목록 조회 후 카드 형태로 표시

#### Scenario: 팀 클릭 시 칸반 화면 이동
- **WHEN** 팀 카드 클릭
- **THEN** 해당 팀의 칸반 화면으로 이동

#### Scenario: 초대코드 입력 후 합류
- **WHEN** 초대코드(XXXX-XXXX) 입력 후 '합류' 버튼 클릭
- **THEN** `POST /teams/join` 호출, 성공 시 팀 목록 갱신

### Requirement: 칸반 화면
팀 멤버는 TODO/DOING/DONE 3컬럼 칸반 보드에서 태스크를 관리할 수 있어야 한다.

#### Scenario: 태스크 드래그로 상태 변경
- **WHEN** 태스크 카드를 다른 컬럼으로 드래그앤드롭 (50ms 이내 반응)
- **THEN** `PUT /tasks/{id}` 호출하여 상태 업데이트, 카드가 해당 컬럼으로 이동

#### Scenario: 새 태스크 추가
- **WHEN** 컬럼 상단 '+' 버튼 클릭 후 제목 입력 및 확인
- **THEN** `POST /teams/{id}/tasks` 호출, 해당 컬럼(TODO)에 카드 추가

#### Scenario: 태스크 삭제
- **WHEN** 태스크 카드의 삭제 버튼 클릭
- **THEN** `DELETE /tasks/{id}` 호출, 카드 제거

### Requirement: 채팅 화면
팀 멤버는 팀 채팅 화면에서 메시지를 송수신할 수 있어야 한다. 5초마다 자동으로 신규 메시지를 조회한다.

#### Scenario: 5초 자동 폴링
- **WHEN** 채팅 화면 진입 후 5초 경과
- **THEN** `GET /teams/{id}/messages?since=<마지막_메시지_시각>` 호출, 신규 메시지 하단에 추가

#### Scenario: 메시지 전송
- **WHEN** 입력창에 텍스트 입력 후 전송 버튼 클릭 또는 Enter
- **THEN** `POST /teams/{id}/messages` 호출, 전송 성공 시 입력창 초기화, 메시지 목록에 추가

#### Scenario: 발신자 + 시각 표시
- **WHEN** 메시지 목록 렌더링
- **THEN** 각 메시지에 발신자 email + `created_at` ISO 시각 표시

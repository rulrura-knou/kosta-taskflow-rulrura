## MODIFIED Requirements

### Requirement: 헤더 공통 UI
헤더에 라이트/다크 토글 버튼을 추가한다. 로그아웃 버튼 왼쪽에 위치한다.

#### Scenario: 헤더 토글 버튼 표시
- **WHEN** kanban, chat, members, team 화면 진입
- **THEN** 헤더 우측에 🌙(라이트) 또는 ☀️(다크) 아이콘 버튼 노출

#### Scenario: 로그인/가입 화면 토글 버튼
- **WHEN** login, signup 화면 진입
- **THEN** 우측 상단 플로팅 위치에 토글 버튼 노출

---

### Requirement: 화면 배경 및 카드 색상
모든 앱 화면의 배경, 카드, 텍스트, 입력창, 구분선이 테마 CSS 변수를 따른다.

#### Scenario: 다크모드 배경
- **WHEN** 다크모드 활성화
- **THEN** 페이지 배경 `--bg(#0f172a)`, 카드/패널 `--surface(#1e293b)`, 텍스트 `--text(#f1f5f9)`

#### Scenario: 입력창 다크모드
- **WHEN** 다크모드에서 입력창 포커스
- **THEN** 배경 `--surface2`, 테두리 `--border`, 텍스트 `--text` 적용

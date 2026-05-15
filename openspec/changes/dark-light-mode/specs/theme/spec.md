## ADDED Requirements

### Requirement: 테마 전환
사용자는 라이트/다크 모드를 전환할 수 있다. 선택은 `localStorage`에 저장되어 새로고침 후에도 유지된다.

#### Scenario: 다크모드로 전환
- **WHEN** 토글 버튼 클릭
- **THEN** `<html data-theme="dark">` 설정, 화면이 다크 테마 색상으로 전환, 버튼 아이콘 ☀️로 변경

#### Scenario: 라이트모드로 전환
- **WHEN** 다크모드 상태에서 토글 버튼 클릭
- **THEN** `<html data-theme="light">` 설정, 화면이 라이트 테마로 전환, 버튼 아이콘 🌙으로 변경

#### Scenario: 페이지 새로고침 후 테마 유지
- **WHEN** 다크모드 선택 후 페이지 새로고침
- **THEN** `localStorage('theme')` 값을 읽어 다크모드 유지

#### Scenario: 시스템 기본값 적용
- **WHEN** `localStorage`에 저장된 테마가 없는 첫 방문
- **THEN** `prefers-color-scheme: dark` 이면 다크모드, 아니면 라이트모드로 초기화

---

### Requirement: 테마 CSS 변수
라이트/다크 테마는 CSS 커스텀 프로퍼티(`--bg`, `--surface`, `--text` 등)로 정의된다.

#### Scenario: 라이트 테마 색상
- **WHEN** `data-theme="light"` 또는 기본값
- **THEN** `--bg:#f8fafc`, `--surface:#ffffff`, `--text:#1e293b`, `--border:#e2e8f0`, `--primary:#0d9488`

#### Scenario: 다크 테마 색상
- **WHEN** `data-theme="dark"`
- **THEN** `--bg:#0f172a`, `--surface:#1e293b`, `--text:#f1f5f9`, `--border:#334155`, `--primary:#14b8a6`

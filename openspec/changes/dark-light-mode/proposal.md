## Why

장시간 작업하는 팀원들이 밝은 화면으로 인한 눈 피로를 호소하고 있다. 다크모드를 추가해 사용자가 선호하는 화면 밝기를 선택할 수 있게 한다.

## What Changes

- 모든 HTML 페이지(login, signup, team, kanban, chat, members) 에 다크모드 CSS 변수 추가
- 헤더에 라이트/다크 전환 토글 버튼 추가
- 선택한 테마를 `localStorage`에 저장해 페이지 새로고침 후에도 유지
- 시스템 기본 테마(`prefers-color-scheme`) 를 초기값으로 사용
- 와이어프레임 갤러리(`public/wireframes/*.html`)는 제외 — 스토리보드 원본 디자인 유지

## Capabilities

### New Capabilities

- `theme`: 라이트/다크 모드 전환 — 토글 버튼, localStorage 저장, 시스템 기본값 반영

### Modified Capabilities

- `frontend`: 모든 화면에 다크모드 색상 적용 — CSS 변수 기반 색상 체계로 전환

## Impact

- **수정 파일**: `public/app.js`, `public/login.html`, `public/signup.html`, `public/team.html`, `public/kanban.html`, `public/chat.html`, `public/members.html`
- **신규**: CSS 변수(custom properties) 기반 테마 시스템 (`--bg`, `--surface`, `--text`, `--border`, `--primary` 등)
- **API 변경 없음** — 순수 프론트엔드 변경
- **Tailwind**: CDN 사용 중이므로 `dark:` prefix 대신 CSS 변수 방식 사용 (Tailwind dark mode는 빌드 단계 필요)

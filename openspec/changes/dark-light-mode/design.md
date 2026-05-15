## Context

현재 모든 HTML 페이지는 Tailwind CDN을 사용하는 하드코딩된 라이트 테마다. Tailwind의 `dark:` prefix는 PostCSS 빌드 단계가 필요해 CDN 환경에서 동작하지 않는다.

## Goals / Non-Goals

**Goals:**
- 모든 앱 화면(6개 HTML)에 다크/라이트 모드 전환
- 시스템 기본값(`prefers-color-scheme`) 자동 감지
- `localStorage('theme')` 으로 선택값 유지
- 헤더 토글 버튼 — 🌙 / ☀️ 아이콘

**Non-Goals:**
- Tailwind `dark:` prefix 빌드 파이프라인 도입
- 와이어프레임 갤러리 페이지 다크모드
- 서버 사이드 테마 저장

## Decisions

### D1. CSS 변수(custom properties) 방식

Tailwind CDN 환경에서 `dark:` prefix가 동작하지 않으므로, `data-theme` 속성 + CSS 변수로 구현한다.

```css
:root, [data-theme="light"] {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface2: #f1f5f9;
  --text: #1e293b;
  --text2: #64748b;
  --border: #e2e8f0;
  --primary: #0d9488;
  --primary-text: #ffffff;
}
[data-theme="dark"] {
  --bg: #0f172a;
  --surface: #1e293b;
  --surface2: #334155;
  --text: #f1f5f9;
  --text2: #94a3b8;
  --border: #334155;
  --primary: #14b8a6;
  --primary-text: #ffffff;
}
```

`<html data-theme="dark">` 로 전환. Tailwind 클래스는 유지하되, 색상이 필요한 곳은 `style="background:var(--surface)"` 또는 인라인 CSS 변수를 사용.

**대안 고려**: Tailwind `dark:` 클래스 → CDN에서는 빌드 없이 동작 안 함.

### D2. 테마 적용 범위 — 공통 CSS 블록

각 HTML의 `<style>` 태그에 공통 CSS 변수 블록을 삽입하고, `body`, 카드, 헤더, 입력창 등 주요 요소에 CSS 변수를 적용한다. Tailwind 유틸리티 클래스는 레이아웃/간격에만 유지하고, 색상은 CSS 변수로 override.

### D3. 토글 버튼 위치 — 헤더 우측

스토리보드 헤더 구조를 유지하면서 로그아웃 버튼 왼쪽에 🌙/☀️ 아이콘 버튼 추가. `app.js`에 공통 `initTheme()` / `toggleTheme()` 함수 추가.

### D4. 로그인/가입 화면 — 헤더 없음

login.html, signup.html은 헤더가 없으므로 우측 상단 플로팅 버튼으로 토글 제공.

## Risks / Trade-offs

| 리스크 | 완화 |
|--------|------|
| Tailwind 유틸리티 색상 클래스(`bg-white`, `text-slate-800` 등)가 CSS 변수를 override | 주요 컨테이너에 `style` 속성으로 변수 직접 적용 |
| 6개 파일 수동 수정 → 누락 가능성 | 공통 CSS 블록을 복사·붙여넣기로 일관성 유지 |
| 시스템 테마 변경 감지 미지원 | MVP 범위 외 — `localStorage` 고정값 우선 |

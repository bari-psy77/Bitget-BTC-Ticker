---
description: Codex Agent Rules and Guidelines
---

# Codex Agent 규칙 및 가이드라인

이 문서는 저장소에서 Codex가 작업할 때 따라야 할 프로젝트 전용 규칙입니다.

## 1. 언어 및 커뮤니케이션
- 모든 설명, 문서, 커밋 요약, 인수인계는 **한글**로 작성합니다.
- 사용자에게 보고할 때 변경 파일/영향/리스크를 간결하게 전달합니다.

## 2. Skills 활용 우선순위
업무 시작 전에 사용 가능한 Skills를 확인하고 아래 우선순위를 따릅니다.
1. `.agent/skills` (존재 시 최우선)
2. `~/.codex/skills`
3. `~/.gemini/antigravity/skills`

현재 저장소는 `.agent/skills`가 없으므로 기본적으로 `~/.codex/skills`를 사용합니다.

## 3. Codex Orchestrator 사용 규칙
- 오케스트레이션 문서: `.agents/workflows/codex-only-sub-agent.md` 또는 `.agents/workflows/multi-sub-agent.md`
- 하위 에이전트는 **Codex CLI만 사용**합니다.
- 기본 실행 옵션:
  - `codex exec --full-auto`
- 병렬 처리 원칙:
  - 파일 수정 작업은 `git worktree`를 분리하여 충돌을 방지합니다.
  - SQLite 쓰기 작업은 병렬 금지, 순차 실행합니다.
- 위험 옵션(`--dangerously-bypass-approvals-and-sandbox`)은 사용자가 명시적으로 요청한 경우에만 사용합니다.

## 4. Context7 사용 규칙 (필수)
다음 라이브러리/프레임워크 작업 시 최신 문서를 반드시 Context7으로 확인합니다.
- Next.js (App Router, Route Handler)
- Prisma
- Playwright
- Tailwind CSS
- Gemini/OpenAI SDK 등 AI SDK

절차:
1. `mcp__context7__resolve-library-id`로 라이브러리 ID 확인
2. `mcp__context7__query-docs`로 필요한 주제 조회
3. 조회 결과 기준으로 구현/수정

금지:
- 기억에 의존한 API 추측 사용
- deprecated 패턴 혼용 (예: App Router 작업에 Pages Router 방식 적용)

## 5. 백엔드 작업 시 권장 Skills
- `backend-dev-guidelines`
- `nodejs-backend-patterns`
- `prisma-expert`
- `api-design-principles`
- `security-review`

백엔드 체크포인트:
- API 응답 형식 일관성 유지: `{ success, data?, error? }`
- `src/lib/db/index.ts` Prisma 싱글톤 사용
- 예외 처리와 HTTP 상태코드 명시
- 입력 검증 및 환경변수 하드코딩 금지

## 6. 프론트엔드 작업 시 권장 Skills
- `frontend-dev-guidelines`
- `frontend-design`
- `react-patterns`
- `tailwind-patterns`
- `web-design-guidelines`

프론트 체크포인트:
- 기존 UI 패턴/토큰과 일관성 유지
- 로딩/에러/빈 상태 처리
- 반응형(모바일/데스크톱) 동작 확인
- 접근성(레이블, 포커스, 대비) 기본 준수

## 7. 완료 및 인수인계
- 작업 완료 시 `plans/인수인계.md`에 변경 사항, 현재 상태, 다음 작업 포인트를 기록합니다.
- `plans/인수인계.md`의 **최신 수정 사항은 항상 문서 상단(가장 위)**에 작성합니다.
- 새 인수인계를 작성하기 전에 **직전 인수인계의 TODO/미해결 항목을 먼저 확인**합니다.
- 이번 작업에서 처리하지 않은 이전 TODO가 있으면, 새 인수인계에 **미처리 항목/유지되는 TODO**로 다시 적어 다음 작업자가 바로 참고할 수 있게 합니다.
- 진행 중인 Task/Implementation/Work 관련 문서는 해당 작업 폴더의 `plans`에 복사해 연속 작업이 가능하도록 유지합니다.

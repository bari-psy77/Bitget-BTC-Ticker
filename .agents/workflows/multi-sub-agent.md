---
description: multi-sub-agent
---

# Multi-Agent Orchestrator Workflow (MCP-Enabled)

## 👑 Role Definition
당신은 프로젝트의 리더이자 수석 아키텍트입니다.
당신의 임무는 사용자 요구사항을 바탕으로 최적의 아키텍처를 설계하고, 시스템 터미널(VS Code 내장 터미널 등)을 통해 하위 에이전트(Codex CLI, Claude Code CLI)를 지휘하여 완벽한 바이브 코딩 파이프라인을 구동하는 것입니다.

## 📋 Core Workflow

### Step 1: 아키텍처 설계 및 사용자 검토
1. 사용자의 요구사항을 분석하여 시스템 구조, 데이터 흐름, 컴포넌트 설계를 작성합니다.
2. 작성된 설계안을 사용자에게 제시하고 명시적인 승인을 요청합니다. (승인 전까지 하위 에이전트 호출 대기)

### Step 2: 하위 에이전트 작업 지시 (Delegation)
승인된 설계를 바탕으로 터미널을 통해 전문 CLI 에이전트를 호출합니다.
*(주의: 모든 하위 에이전트는 이미 MCP를 통해 `context7` 룰을 내재화하고 있으므로, 룰에 대한 언급 없이 순수 작업 지시만 명확히 전달합니다.)*

* **[백엔드/로직 구현이 필요한 경우] 👉 Codex CLI 호출**
    * 주요 옵션: 비대화형 자동 승인을 위해 `--full-auto` 옵션을 기본값으로 사용합니다.
    * 터미널 실행 예시:
      * `codex exec --full-auto "다음 아키텍처 설계에 따라 로직을 구현해: [설계 요약 내용]"`
      * 멀티라인 프롬프트 예시:
        ```bash
        codex exec --full-auto "$(cat <<'EOF'
        너는 이 저장소의 CI 실패를 고치는 엔지니어다.
        1) 테스트 실행
        2) 실패 케이스 수정
        3) 테스트 재실행
        4) 변경 파일/원인/리스크를 한국어로 요약
        EOF
        )"
        ```
    * 병렬 작업 원칙: 충돌 방지를 위해 기능별 `git worktree`를 분리하고 각 worktree에서 개별 `codex exec`를 백그라운드 실행합니다.
    * **[목록 처리] xargs 병렬 실행**
        ```bash
        # 최대 4개 동시 실행 (stdin 리다이렉션 필수)
        ls src/api/ | xargs -P 4 -I{} \
          bash -c 'codex exec --full-auto \
            "src/api/{} 엔드포인트 보안 검토 및 문서화" < /dev/null > {}.log'
        ```
    * 금지 및 주의 원칙:
        - `--dangerously-bypass-approvals-and-sandbox` 옵션은 사용자가 명시적으로 요청하거나, 기본 샌드박스가 환경 제약으로 동작하지 않을 때만 제한적으로 사용합니다.
        - SQLite DB 쓰기가 포함된 작업은 병렬 실행을 금지합니다.
* **[디자인/UI/프론트엔드 구현이 필요한 경우] 👉 Claude Code CLI 호출**

    #### [싱글 인스턴스] 단일 작업 실행 원칙
    * 기본 실행 (대화형): `claude "프롬프트"`
    * 비대화형 출력 후 종료: `claude -p "프롬프트"`
    * 완전 자동 승인 (모든 도구 허용): `claude -p --dangerously-skip-permissions "프롬프트"`
    * 특정 도구만 자동 승인 (권장): `claude -p --allowedTools "Read,Write,Edit,Glob,Grep" "프롬프트"`
    * 금지 원칙: `--dangerously-skip-permissions`는 사용자가 명시적으로 요청한 경우에만 사용합니다.
    * 싱글 실행 예시:
      ```bash
      # 읽기 전용 분석
      claude -p --allowedTools "Read,Glob,Grep" "현재 UI 컴포넌트 구조 분석해줘"

      # 파일 수정 및 시스템 작업 포함 (Bash 필수)
      claude -p --allowedTools "Read,Write,Edit,Glob,Grep,Bash" \
        "다음 요구사항에 맞춰 UI 컴포넌트와 디자인을 구현해: [설계 요약 내용]"

      # 멀티라인 프롬프트
      claude -p --dangerously-skip-permissions "$(cat <<'EOF'
      너는 이 저장소의 프론트엔드 엔지니어다.
      1) 기존 컴포넌트 파악
      2) 디자인 시스템에 맞춰 UI 구현
      3) 변경 파일과 구현 내용을 한국어로 요약
      EOF
      )"
      ```

    #### [멀티 인스턴스] 병렬 작업 실행 원칙
    * 파일 충돌 방지를 위해 반드시 `git worktree`를 분리하여 실행합니다.
    * DB(SQLite) 쓰기가 포함된 작업은 동시 실행을 금지하고 순차 실행합니다.
    * 읽기 전용 분석 작업은 worktree 없이 단순 `&` 병렬 실행으로 충분합니다.
    * 멀티 실행 예시:
      ```bash
      # [읽기 전용] 단순 병렬 분석
      claude -p --allowedTools "Read,Glob,Grep" "컴포넌트 A 분석" < /dev/null > taskA.log &
      claude -p --allowedTools "Read,Glob,Grep" "컴포넌트 B 분석" < /dev/null > taskB.log &
      wait && cat taskA.log taskB.log

      # [파일 수정] worktree 분리 후 병렬 실행
      git worktree add /tmp/worker1 HEAD
      git worktree add /tmp/worker2 HEAD

      claude -p --dangerously-skip-permissions \
        --cwd /tmp/worker1 "feature A UI 구현해줘" < /dev/null > w1.log &
      claude -p --dangerously-skip-permissions \
        --cwd /tmp/worker2 "feature B UI 구현해줘" < /dev/null > w2.log &
      wait

      git worktree remove /tmp/worker1
      git worktree remove /tmp/worker2

      # [목록 처리] xargs 병렬 실행 (최대 4개 동시, Bash 권한 및 stdin 리다이렉션 필수)
      ls src/components/ | xargs -P 4 -I{} \
        bash -c 'claude -p --allowedTools "Read,Write,Edit,Glob,Grep,Bash" \
          "src/components/{} 리팩토링 및 개선 가이드 작성" < /dev/null > {}.log'
      ```

    | 작업 유형          | 권장 옵션                                         |
    | ------------------ | ------------------------------------------------- |
    | 읽기 전용 분석     | `--allowedTools "Read,Glob,Grep"`                 |
    | 파일 수정 및 이동  | `--allowedTools "Read,Write,Edit,Glob,Grep,Bash"` |
    | 전체 자동화 (주의) | `--dangerously-skip-permissions`                  |
    | DB 쓰기 포함       | 병렬 금지 → 싱글 순차 실행                        |

### Step 3: 실시간 모니터링 로직

1. 하위 에이전트(Codex CLI / Claude Code CLI)가 출력하는 터미널 로그를 실시간으로 분석합니다.
2. Codex CLI를 `codex exec --full-auto`로 실행한 경우에는 백그라운드 자동 실행으로 승인 프롬프트가 발생하지 않으므로, 로그/결과 검증 중심으로 모니터링합니다.
3. 대화형 모드 또는 타 CLI에서 중간 확인(예: Continue? [Y/n], 실행 권한 요청 등)이 발생하면, 해당 단계의 동작이 초기 설계 방향과 일치할 때만 승인하여 작업을 멈춤 없이 진행시킵니다.
4. 결과물이나 진행 방향이 설계와 명백히 어긋나는 경우에만 개입하여, 터미널을 통해 수정 지시를 내립니다.

### Step 4: 형상 관리 및 완료 보고 (Vibe Coding Completion)
1. 하위 에이전트들의 모든 작업이 성공적으로 종료되면, 전체 변경 사항을 간략히 요약합니다.
2. 터미널을 통해 현재 연결된 **Private Git Repository**에 작업 내역을 자동으로 커밋하고 푸시합니다.
   * 실행 명령어: `git add .` -> `git commit -m "feat: [오케스트레이터 요약 내용] 자동화 작업 완료"` -> `git push`
3. 사용자에게 Git 푸시 완료 소식과 함께 최종 작업 보고를 수행합니다.
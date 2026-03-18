# Bitget BTC Ticker — 아키텍처 설계 문서

**작성일:** 2026-03-18
**버전:** v1.0
**대상 플랫폼:** Windows 10/11

---

## 1. 시스템 개요

Windows 시스템 트레이에 상주하며 Bitget 거래소의 BTC/USDT 현재가를 화면 하단에 반투명 오버레이로 표시하는 경량 데스크톱 위젯.

### 핵심 기능 요약

| 기능 | 설명 |
|------|------|
| 가격 오버레이 | 화면 하단 반투명 플로팅 창, 드래그 이동 가능 |
| 투명도 조절 | 설정 UI에서 슬라이더로 실시간 조절 |
| 가격 알람 | 최대 4개 가격 레벨 지정, 도달 시 팝업 + 비프음 |
| 갱신 주기 | 5 / 10 / 15 / 20 / 30분 선택 |
| 트레이 아이콘 | 우클릭 컨텍스트 메뉴로 설정 진입 및 종료 |

---

## 2. 기술 스택

| 역할 | 라이브러리 | 비고 |
|------|-----------|------|
| UI (오버레이 + 설정창) | `tkinter` | Python 내장, 별도 설치 불필요 |
| 시스템 트레이 | `pystray` | pip 설치 필요 |
| 트레이 아이콘 이미지 생성 | `Pillow (PIL)` | pip 설치 필요 |
| Bitget API 호출 | `requests` | pip 설치 필요 |
| 알람 사운드 | `winsound` | Python 내장, Windows 전용 |
| 백그라운드 스레드 | `threading` | Python 내장 |
| 설정 파일 저장 | `json` | Python 내장, `~/.bitget_ticker_config.json` |

> **선택 이유 — tkinter vs PyQt5**
> tkinter는 Python 내장으로 배포가 쉽고 이 규모의 UI에 충분함.
> PyQt5는 더 세련된 스타일링이 가능하지만 바이너리 크기가 크고 라이선스 이슈 존재.
> → **tkinter 채택**

> **선택 이유 — Polling vs WebSocket**
> 알람 정확도보다 갱신 주기(5~30분)가 우선 요구사항임.
> WebSocket은 연결 유지 복잡도를 높이고 리소스를 더 소비함.
> → **Polling 채택**

---

## 3. 컴포넌트 구조

```
BitgetBTCTicker (Main Class)
├── OverlayWindow          # 화면 하단 반투명 가격 표시 창
├── TrayIcon               # pystray 기반 시스템 트레이 아이콘
├── SettingsDialog         # 탭 구성 설정 UI (알람 / 갱신주기 / 화면)
├── PriceFetcher           # Bitget REST API 호출 (별도 스레드)
├── AlarmEngine            # 가격 레벨 모니터링 및 알람 트리거
└── ConfigManager          # JSON 파일 기반 설정 저장/불러오기
```

### 3-1. OverlayWindow

- `tk.Tk()` with `overrideredirect(True)` → 타이틀바 없는 순수 창
- `-topmost True` → 항상 최상위
- `-alpha` → 투명도 (0.2 ~ 1.0)
- 마우스 드래그로 위치 이동 (`<Button-1>` + `<B1-Motion>`)
- 우클릭 → 컨텍스트 메뉴 (설정 / 종료)
- 표시 요소: **₿ 아이콘** | **$가격** | **▲▼ 방향 화살표**

### 3-2. TrayIcon

- `pystray.Icon` 으로 트레이 등록
- 아이콘 이미지: PIL로 런타임 생성 (오렌지 원 + B 문자)
- 메뉴: `설정` / `종료`
- 별도 데몬 스레드에서 실행 (`tray.run()`)

### 3-3. SettingsDialog

`tk.Toplevel` 기반, `ttk.Notebook`으로 3개 탭 구성

| 탭 | 내용 |
|----|------|
| 가격 알람 | 4개 Entry 입력 (USDT), 저장 시 정렬 |
| 갱신 주기 | Radiobutton 5종 (5/10/15/20/30분) |
| 화면 설정 | 투명도 Scale 슬라이더 (실시간 미리보기) |

### 3-4. PriceFetcher

```
Bitget Public API (인증 불필요)
GET https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT

응답 경로: data[0].lastPr  → float 형변환
```

- timeout=10초
- 실패 시 레이블에 "Error" 표시 후 다음 주기 재시도
- 메인 스레드 UI 업데이트는 반드시 `root.after(0, callback)` 사용

### 3-5. AlarmEngine

**알람 트리거 로직 (Cross-detection 방식)**

```
최초 가격 수신 시:
  각 alarm_price에 대해 alarm_states[key] = 'above' or 'below' 초기화

이후 매 갱신 시:
  curr_side = 'above' if price >= alarm_price else 'below'
  if alarm_states[key] != curr_side:
      → 알람 트리거 (팝업 + 비프음)
      → alarm_states[key] = curr_side (재트리거 방지)

설정 저장 시:
  alarm_states = {} 초기화 (새 알람 레벨 반영)
```

> 단순 임계값 비교 방식 대비 장점: 위 → 아래, 아래 → 위 양방향 감지, 중복 알람 방지

### 3-6. ConfigManager

저장 위치: `C:\Users\{username}\.bitget_ticker_config.json`

```json
{
  "interval": 5,
  "alarms": [85000.0, 90000.0, 95000.0, 100000.0],
  "opacity": 0.85
}
```

- 앱 시작 시 자동 로드 (파일 없으면 기본값 사용)
- 설정 저장 시 즉시 기록

---

## 4. 데이터 흐름

```
[앱 시작]
    │
    ▼
ConfigManager.load()
    │
    ▼
OverlayWindow 생성 (화면 하단 중앙 배치)
    │
    ├──▶ TrayIcon 생성 (별도 스레드)
    │
    ▼
PriceFetcher.fetch() ← 즉시 1회 실행
    │
    ▼
OverlayWindow.update_display(price)
    │
    ├──▶ AlarmEngine.check(price)
    │         │
    │         └──▶ (교차 감지 시) 팝업 + winsound.Beep()
    │
    ▼
[대기: interval × 60초]
    │
    └──▶ PriceFetcher.fetch() (반복)
```

---

## 5. 스레드 구성

| 스레드 | 역할 | 종류 |
|--------|------|------|
| Main Thread | tkinter 메인 루프, UI 업데이트 | — |
| tray_thread | pystray.Icon.run() | daemon |
| update_thread | 주기적 가격 폴링 루프 | daemon |
| (일시적) fetch_thread | API 호출 (블로킹 방지) | daemon |
| (일시적) alarm_thread | winsound.Beep() (UI 블로킹 방지) | daemon |

> **중요:** tkinter는 메인 스레드에서만 UI 조작 가능.
> 모든 UI 업데이트는 `root.after(0, fn)` 으로 메인 스레드에 위임.

---

## 6. 트레이드오프 정리

| 항목 | 선택 | 포기한 것 | 이유 |
|------|------|-----------|------|
| UI 프레임워크 | tkinter | PyQt5의 세련된 스타일 | 내장 라이브러리, 배포 단순 |
| 가격 수신 방식 | REST Polling | WebSocket 실시간성 | 요구사항이 5분+ 간격, 복잡도 최소화 |
| 알람 방식 | Cross-detection | 단순 크기 비교 | 중복 알람 방지, 양방향 감지 |
| 사운드 | winsound | pygame 다양한 사운드 | Windows 내장, 의존성 최소 |
| 설정 저장 | JSON 파일 | Windows Registry | 이식성, 디버깅 용이 |
| 실행 방식 | Python 스크립트 | EXE 패키징 (PyInstaller) | 개발 단계 우선, 추후 패키징 가능 |

---

## 7. 향후 확장 가능 항목 (Optional)

- 다중 코인 지원 (ETH, SOL 등) — 탭 또는 드롭다운으로 선택
- PyInstaller로 단일 EXE 패키징 — 배포 편의
- 가격 변동률 표시 — 24h 등락 추가
- 알람 이력 로그 — 텍스트 파일 또는 토스트 알림
- 자동 시작 — 레지스트리 등록 (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)

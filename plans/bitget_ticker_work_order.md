# Bitget BTC Ticker — 작업 지시서 (Work Order)

**작성일:** 2026-03-18
**버전:** v1.0
**예상 총 작업 시간:** 4~6시간

---

## 사전 준비

### 환경 설정

```bash
# Python 3.10 이상 확인
python --version

# 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install pystray Pillow requests
```

### requirements.txt

```
pystray==0.19.5
Pillow>=10.0.0
requests>=2.31.0
```

### 파일 구조

```
bitget_ticker/
├── main.py               ← 진입점
├── ticker.py             ← BitgetBTCTicker 메인 클래스
├── components/
│   ├── overlay.py        ← OverlayWindow
│   ├── tray.py           ← TrayIcon
│   ├── settings.py       ← SettingsDialog
│   ├── alarm.py          ← AlarmEngine
│   └── config.py         ← ConfigManager
├── requirements.txt
└── run.bat               ← Windows 실행 스크립트
```

> 단일 파일(`ticker.py`)로 모두 작성해도 무방. 클래스별로 분리하면 유지보수 용이.

---

## 작업 목록

### TASK-01 · ConfigManager 구현
**예상 시간:** 20분
**파일:** `components/config.py`

- [ ] 기본값 딕셔너리 정의: `interval=5`, `alarms=[]`, `opacity=0.85`
- [ ] `load()` 메서드: `~/.bitget_ticker_config.json` 읽기, 없으면 기본값
- [ ] `save()` 메서드: 설정 딕셔너리를 JSON으로 저장
- [ ] `alarm_states` 는 저장 대상 제외 (런타임 전용)

**검증:** 저장 후 파일 열어 내용 확인, 재시작 후 값 유지 확인

---

### TASK-02 · PriceFetcher 구현
**예상 시간:** 30분
**파일:** `components/fetcher.py` 또는 `ticker.py` 내 메서드

- [ ] `get_btc_price()` 함수 구현
  ```python
  url = 'https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT'
  # 응답: data[0]['lastPr'] → float
  ```
- [ ] timeout=10 설정
- [ ] 예외 처리: 네트워크 오류, JSON 파싱 오류, `code != '00000'`
- [ ] 실패 시 `None` 반환, 호출부에서 처리

**검증:** 스크립트에서 단독 실행하여 현재 BTC 가격 출력 확인

```python
# 단독 테스트
if __name__ == '__main__':
    price = get_btc_price()
    print(f'BTC: ${price:,.2f}')
```

---

### TASK-03 · AlarmEngine 구현
**예상 시간:** 30분
**파일:** `components/alarm.py`

- [ ] `alarm_states` 딕셔너리 초기화 (key: str(alarm_price))
- [ ] `check(price, alarms)` 메서드:
  - 최초 가격 수신 시: 각 알람의 현재 side(above/below) 초기화 후 return
  - 이후: side 변경 감지 시 → 콜백 호출
- [ ] 트리거 콜백: `on_alarm(alarm_price, current_price)` 주입 방식
- [ ] `reset()` 메서드: 설정 변경 시 `alarm_states` 초기화
- [ ] `winsound.Beep(1200, 400)` 3회 반복 — 별도 스레드에서 실행

**검증:** 가격을 직접 변경하며 alarm_states 전환 로직 단위 테스트

```python
engine = AlarmEngine()
engine.check(90000, [95000])  # 초기화: below
engine.check(96000, [95000])  # → 트리거
engine.check(94000, [95000])  # → 트리거 (하락 방향)
```

---

### TASK-04 · OverlayWindow 구현
**예상 시간:** 60분
**파일:** `components/overlay.py`

#### 창 기본 설정
- [ ] `tk.Tk()` 생성
- [ ] `overrideredirect(True)` — 타이틀바 제거
- [ ] `attributes('-topmost', True)` — 최상위 유지
- [ ] `attributes('-alpha', opacity)` — 투명도 적용
- [ ] `configure(bg='#0d1117')` — 배경색

#### 초기 위치
```python
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
width, height = 260, 38
x = (screen_w - width) // 2
y = screen_h - height - 60
root.geometry(f'{width}x{height}+{x}+{y}')
```

#### 레이아웃 (좌 → 우)
| 요소 | 텍스트 | fg 색상 | 폰트 |
|------|--------|---------|------|
| 코인 아이콘 | `₿` | `#f7931a` | Segoe UI 14 bold |
| 가격 | `$98,500` | `#00d4aa` (상승) / `#ff6b6b` (하락) | Consolas 13 bold |
| 방향 화살표 | `▲` / `▼` / `─` | 가격과 동일 | Segoe UI 11 |

#### 드래그 이동
```python
def start_drag(event): self._dx, self._dy = event.x, event.y
def do_drag(event):
    x = root.winfo_x() + event.x - self._dx
    y = root.winfo_y() + event.y - self._dy
    root.geometry(f'+{x}+{y}')
```
- [ ] 모든 자식 위젯에 `<Button-1>`, `<B1-Motion>` 바인딩

#### 우클릭 컨텍스트 메뉴
- [ ] `<Button-3>` 바인딩
- [ ] 메뉴 항목: `설정`, `종료`

#### update_display(price, prev_price)
- [ ] 방향 판정 → 화살표 및 색상 업데이트
- [ ] `prev_price` 비교 후 label config 갱신
- [ ] AlarmEngine.check() 호출

**검증:** 창이 화면 하단에 표시되고, 드래그로 이동되는지 확인

---

### TASK-05 · TrayIcon 구현
**예상 시간:** 30분
**파일:** `components/tray.py`

#### 아이콘 이미지 생성 (PIL)
```python
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.ellipse([2, 2, 62, 62], fill=(247, 147, 26, 255))  # 오렌지 원
# 중앙에 'B' 텍스트 또는 선으로 ₿ 모양 표현
```

#### 메뉴 구성
```python
menu = pystray.Menu(
    pystray.MenuItem('설정', lambda icon, item: root.after(0, open_settings)),
    pystray.MenuItem('종료', lambda icon, item: root.after(0, quit_app)),
)
```

- [ ] `pystray.Icon` 생성
- [ ] 별도 daemon 스레드에서 `tray.run()` 실행
- [ ] 콜백은 반드시 `root.after(0, ...)` 로 메인 스레드에 위임

**검증:** 트레이 아이콘 표시 확인, 우클릭 메뉴 동작 확인

---

### TASK-06 · SettingsDialog 구현
**예상 시간:** 60분
**파일:** `components/settings.py`

#### 창 기본 설정
```python
win = tk.Toplevel(root)
win.title('설정 - Bitget BTC Ticker')
win.geometry('380x460')
win.resizable(False, False)
win.attributes('-topmost', True)
```

#### Tab 1 — 가격 알람
- [ ] `ttk.Notebook` + `ttk.Frame` 3개
- [ ] Entry × 4개, StringVar로 현재 알람 값 프리필
- [ ] 입력값 유효성 검사: 숫자인지, 빈 값 허용

#### Tab 2 — 갱신 주기
- [ ] `tk.Radiobutton` × 5개 (5/10/15/20/30분)
- [ ] `IntVar`로 현재 설정값 반영

#### Tab 3 — 화면 설정
- [ ] `tk.Scale(from_=20, to=100)` 슬라이더
- [ ] 슬라이더 이동 시 오버레이 투명도 실시간 미리보기
  ```python
  command=lambda v: root.attributes('-alpha', int(v)/100)
  ```
- [ ] 퍼센트 레이블 실시간 업데이트

#### 저장 버튼
- [ ] 알람 값 파싱 (float 변환, 오류 시 messagebox)
- [ ] config 업데이트
- [ ] `ConfigManager.save()` 호출
- [ ] `AlarmEngine.reset()` 호출
- [ ] 창 닫기

**검증:** 저장 후 앱 재시작 시 설정값 유지 확인

---

### TASK-07 · 메인 클래스 & 업데이트 루프 조립
**예상 시간:** 45분
**파일:** `ticker.py`

#### 초기화 순서
```python
1. ConfigManager.load()
2. OverlayWindow 생성
3. AlarmEngine 생성 (콜백 주입)
4. TrayIcon 생성 (별도 스레드)
5. root.after(100, first_price_fetch)   ← 즉시 1회 조회
6. update_thread 시작
7. root.mainloop()
```

#### 업데이트 루프 (별도 스레드)
```python
def price_update_loop():
    time.sleep(5)  # 초기 fetch 대기
    while running:
        wait_seconds = config['interval'] * 60
        for _ in range(wait_seconds):
            if not running: return
            time.sleep(1)
        price = get_btc_price()
        if price:
            root.after(0, lambda p=price: update_display(p))
```

- [ ] `running` 플래그로 종료 제어
- [ ] 종료 시 tray.stop() → root.quit() → sys.exit(0)

---

### TASK-08 · 실행 스크립트 작성
**예상 시간:** 10분

#### `run.bat`
```bat
@echo off
cd /d %~dp0
call venv\Scripts\activate
pythonw main.py
```

> `pythonw` 사용 시 콘솔 창 없이 백그라운드 실행

#### `main.py`
```python
from ticker import BitgetBTCTicker

if __name__ == '__main__':
    app = BitgetBTCTicker()
    app.run()
```

---

### TASK-09 · 통합 테스트
**예상 시간:** 30분

| 테스트 항목 | 확인 방법 |
|------------|----------|
| 앱 시작 시 가격 표시 | 화면 하단 오버레이 등장, BTC 가격 표시 |
| 드래그 이동 | 오버레이를 드래그해 위치 변경 |
| 우클릭 메뉴 | 오버레이 우클릭 → 메뉴 팝업 |
| 트레이 아이콘 | 시스템 트레이 아이콘 확인, 우클릭 메뉴 동작 |
| 설정 저장/로드 | 알람 가격 입력 → 저장 → 재시작 → 값 유지 |
| 투명도 조절 | 슬라이더 이동 → 오버레이 투명도 실시간 변경 |
| 알람 트리거 | 알람 가격을 현재 가격 근처로 설정 → 갱신 후 팝업/비프 확인 |
| API 오류 처리 | 인터넷 끊고 실행 → "Error" 표시 후 재시도 확인 |
| 종료 | 메뉴에서 종료 → 트레이 아이콘 + 오버레이 모두 사라짐 |

---

## 주의사항 & 팁

1. **tkinter 멀티스레드 규칙**: UI 변경은 무조건 `root.after(0, fn)`. 다른 스레드에서 직접 label.config() 호출하면 크래시.

2. **pystray 콜백**: `MenuItem` 콜백은 별도 스레드에서 실행됨. 여기서도 `root.after(0, ...)` 필수.

3. **투명도와 클릭**: `alpha` 값이 너무 낮으면 (0.1 이하) Windows에서 클릭이 통과될 수 있음. 최솟값은 0.2 이상 권장.

4. **알람 초기화 타이밍**: 설정 저장 후 `alarm_states` 리셋 필수. 그렇지 않으면 이전 상태 기준으로 즉시 오알람 발생 가능.

5. **`pythonw` vs `python`**: `run.bat`에서 `python` 사용 시 콘솔 창이 함께 열림. `pythonw`로 실행하면 백그라운드 전용.

6. **EXE 패키징 (선택)**: 배포 시 PyInstaller 사용 가능
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --windowed --icon=btc.ico main.py
   ```

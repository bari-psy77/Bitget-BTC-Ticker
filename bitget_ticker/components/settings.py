from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from bitget_ticker.components.config import ConfigManager


class SettingsDialog:
    """Tabbed settings dialog for alarms, interval, and opacity."""

    POSITION_LABELS = {
        "top-left": "왼쪽 상단",
        "top-right": "오른쪽 상단",
        "bottom-left": "왼쪽 하단",
        "bottom-right": "오른쪽 하단 (기본)",
        "center": "가운데",
        "custom": "사용자 지정 (드래그 위치)",
    }

    def __init__(
        self,
        root: tk.Tk,
        config_manager: ConfigManager,
        config_getter: Callable[[], dict[str, Any]],
        on_save: Callable[[dict[str, Any]], None],
    ) -> None:
        self.root = root
        self.config_manager = config_manager
        self.config_getter = config_getter
        self.on_save = on_save
        self.window: tk.Toplevel | None = None
        self.alarm_vars: list[tk.StringVar] = []
        self.interval_var: tk.IntVar | None = None
        self.interval_label_var: tk.StringVar | None = None
        self.opacity_var: tk.IntVar | None = None
        self.opacity_label_var: tk.StringVar | None = None
        self.position_var: tk.StringVar | None = None
        self._current_custom_position: dict[str, int] | None = None
        self._initial_opacity = 85

    def show(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        config = self.config_getter()
        self._initial_opacity = int(float(config["opacity"]) * 100)
        custom_position = config.get("custom_position")
        self._current_custom_position = (
            dict(custom_position) if isinstance(custom_position, dict) else None
        )

        self.window = tk.Toplevel(self.root)
        self.window.title("설정 - Bitget BTC Ticker")
        self.window.geometry("420x540")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close)

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        alarm_tab = ttk.Frame(notebook)
        interval_tab = ttk.Frame(notebook)
        display_tab = ttk.Frame(notebook)
        notebook.add(alarm_tab, text="가격 알람")
        notebook.add(interval_tab, text="갱신 주기")
        notebook.add(display_tab, text="화면 설정")

        self._build_alarm_tab(alarm_tab, config)
        self._build_interval_tab(interval_tab, config)
        self._build_display_tab(display_tab, config)

        actions = tk.Frame(self.window, pady=10)
        actions.pack(fill="x")
        tk.Button(actions, text="저장", width=12, command=self._save).pack(side="right", padx=12)
        tk.Button(actions, text="취소", width=12, command=self._handle_close).pack(side="right")

    def _build_alarm_tab(self, parent: ttk.Frame, config: dict[str, Any]) -> None:
        alarms = [str(alarm) for alarm in config.get("alarms", [])][:4]
        while len(alarms) < 4:
            alarms.append("")

        container = tk.Frame(parent, padx=18, pady=18)
        container.pack(fill="both", expand=True)

        self.alarm_vars = []
        for index, value in enumerate(alarms, start=1):
            var = tk.StringVar(value=value)
            self.alarm_vars.append(var)
            tk.Label(container, text=f"알람 {index} (USDT)").grid(
                row=index - 1,
                column=0,
                sticky="w",
                pady=8,
            )
            tk.Entry(container, textvariable=var, width=24).grid(
                row=index - 1,
                column=1,
                sticky="ew",
                padx=(12, 0),
                pady=8,
            )

        container.grid_columnconfigure(1, weight=1)

    def _build_interval_tab(self, parent: ttk.Frame, config: dict[str, Any]) -> None:
        container = tk.Frame(parent, padx=18, pady=18)
        container.pack(fill="both", expand=True)

        interval_seconds = int(config.get("interval_seconds", 300))
        self.interval_var = tk.IntVar(value=interval_seconds)
        self.interval_label_var = tk.StringVar(value=self._format_interval_label(interval_seconds))

        tk.Label(container, text="갱신 주기").pack(anchor="w")
        tk.Scale(
            container,
            from_=30,
            to=1800,
            resolution=30,
            orient="horizontal",
            variable=self.interval_var,
            command=self._on_interval_change,
            length=320,
            showvalue=False,
        ).pack(anchor="w", pady=(12, 0))
        tk.Label(container, textvariable=self.interval_label_var, font=("Segoe UI", 10, "bold")).pack(
            anchor="w",
            pady=(10, 0),
        )
        tk.Label(
            container,
            text="30초부터 30분까지 30초 단위로 조절됩니다.",
            fg="#666666",
        ).pack(anchor="w", pady=(12, 0))

    def _build_display_tab(self, parent: ttk.Frame, config: dict[str, Any]) -> None:
        container = tk.Frame(parent, padx=18, pady=18)
        container.pack(fill="both", expand=True)

        self.position_var = tk.StringVar(value=str(config.get("position", "bottom-right")))

        tk.Label(container, text="오버레이 위치").pack(anchor="w")
        positions_frame = tk.Frame(container)
        positions_frame.pack(fill="x", pady=(8, 16))
        for row, (value, label) in enumerate(self.POSITION_LABELS.items()):
            tk.Radiobutton(
                positions_frame,
                text=label,
                variable=self.position_var,
                value=value,
                anchor="w",
            ).grid(row=row // 2, column=row % 2, sticky="w", padx=(0, 20), pady=6)
        tk.Label(
            container,
            text="마우스로 드래그하면 사용자 지정 위치로 저장됩니다.",
            fg="#666666",
        ).pack(anchor="w", pady=(0, 20))

        opacity_value = int(float(config.get("opacity", 0.85)) * 100)
        self.opacity_var = tk.IntVar(value=opacity_value)
        self.opacity_label_var = tk.StringVar(value=f"{opacity_value}%")

        tk.Label(container, text="오버레이 투명도").pack(anchor="w", pady=(0, 8))
        tk.Scale(
            container,
            from_=20,
            to=100,
            orient="horizontal",
            variable=self.opacity_var,
            command=self._on_opacity_change,
            length=280,
        ).pack(anchor="w")
        tk.Label(container, textvariable=self.opacity_label_var).pack(anchor="w", pady=(8, 0))

    def _on_interval_change(self, value: str) -> None:
        if self.interval_label_var is None:
            return
        self.interval_label_var.set(self._format_interval_label(int(float(value))))

    def _on_opacity_change(self, value: str) -> None:
        percent = int(float(value))
        if self.opacity_label_var is not None:
            self.opacity_label_var.set(f"{percent}%")
        self.root.attributes("-alpha", percent / 100)

    def _save(self) -> None:
        try:
            alarms = self._parse_alarm_values()
        except ValueError as exc:
            messagebox.showerror("입력 오류", str(exc), parent=self.window)
            return

        if self.interval_var is None or self.opacity_var is None or self.position_var is None:
            return

        config = {
            "interval_seconds": int(self.interval_var.get()),
            "alarms": alarms,
            "opacity": round(int(self.opacity_var.get()) / 100, 2),
            "position": self.position_var.get(),
            "custom_position": (
                dict(self._current_custom_position)
                if self._current_custom_position is not None
                else None
            ),
        }

        try:
            saved_config = self.config_manager.save(config)
        except OSError as exc:
            messagebox.showerror("저장 실패", str(exc), parent=self.window)
            return

        self.on_save(saved_config)
        self._destroy_window()

    def _parse_alarm_values(self) -> list[float]:
        alarms: list[float] = []
        for var in self.alarm_vars:
            value = var.get().strip()
            if not value:
                continue
            try:
                alarms.append(float(value))
            except ValueError as exc:
                raise ValueError("알람 값은 숫자만 입력할 수 있습니다.") from exc
        return sorted(alarms)

    def _handle_close(self) -> None:
        self.root.attributes("-alpha", self._initial_opacity / 100)
        self._destroy_window()

    def _destroy_window(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        self.window = None

    @staticmethod
    def _format_interval_label(seconds: int) -> str:
        minutes, remain_seconds = divmod(seconds, 60)
        if minutes and remain_seconds:
            return f"{minutes}분 {remain_seconds}초"
        if minutes:
            return f"{minutes}분"
        return f"{remain_seconds}초"

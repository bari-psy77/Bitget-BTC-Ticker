from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from bitget_ticker.components.config import ConfigManager


class SettingsDialog:
    """Tabbed settings dialog for alarms, interval, and opacity."""

    WINDOW_TITLE = "Settings - Bitget BTC Ticker"
    ALERTS_TAB_TITLE = "Price Alerts"
    INTERVAL_TAB_TITLE = "Refresh Interval"
    DISPLAY_TAB_TITLE = "Display"
    SAVE_BUTTON_LABEL = "Save"
    CANCEL_BUTTON_LABEL = "Cancel"
    DRAG_GUIDE_TEXT = "Drag the overlay with the mouse to save its position."
    POPUP_MODE_LABEL = "Popup"
    NOTIFICATION_MODE_LABEL = "Notification"

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
        self.alarm_enabled_vars: list[tk.BooleanVar] = []
        self.alert_mode_var: tk.StringVar | None = None
        self.interval_var: tk.IntVar | None = None
        self.interval_label_var: tk.StringVar | None = None
        self.opacity_var: tk.IntVar | None = None
        self.opacity_label_var: tk.StringVar | None = None
        self._initial_opacity = 85

    def show(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        config = self.config_getter()
        self._initial_opacity = int(float(config["opacity"]) * 100)

        self.window = tk.Toplevel(self.root)
        self.window.title(self.WINDOW_TITLE)
        self.window.geometry("420x580")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close)

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        alarm_tab = ttk.Frame(notebook)
        interval_tab = ttk.Frame(notebook)
        display_tab = ttk.Frame(notebook)
        notebook.add(alarm_tab, text=self.ALERTS_TAB_TITLE)
        notebook.add(interval_tab, text=self.INTERVAL_TAB_TITLE)
        notebook.add(display_tab, text=self.DISPLAY_TAB_TITLE)

        self._build_alarm_tab(alarm_tab, config)
        self._build_interval_tab(interval_tab, config)
        self._build_display_tab(display_tab, config)

        actions = tk.Frame(self.window, pady=10)
        actions.pack(fill="x")
        tk.Button(actions, text=self.SAVE_BUTTON_LABEL, width=12, command=self._save).pack(
            side="right",
            padx=12,
        )
        tk.Button(actions, text=self.CANCEL_BUTTON_LABEL, width=12, command=self._handle_close).pack(
            side="right",
        )

    def _build_alarm_tab(self, parent: ttk.Frame, config: dict[str, Any]) -> None:
        alarms = list(config.get("alarms", []))[:4]
        while len(alarms) < 4:
            alarms.append({"price": "", "enabled": True})

        container = tk.Frame(parent, padx=18, pady=18)
        container.pack(fill="both", expand=True)

        self.alarm_vars = []
        self.alarm_enabled_vars = []
        for index, alarm in enumerate(alarms, start=1):
            price_value = ""
            enabled_value = True
            if isinstance(alarm, dict):
                price_value = self._format_alarm_value(alarm.get("price", ""))
                enabled_value = bool(alarm.get("enabled", True))
            else:
                price_value = self._format_alarm_value(alarm)

            var = tk.StringVar(value=price_value)
            enabled_var = tk.BooleanVar(value=enabled_value)
            self.alarm_vars.append(var)
            self.alarm_enabled_vars.append(enabled_var)
            tk.Label(container, text=f"Alert {index} (USDT)").grid(
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
            tk.Checkbutton(
                container,
                text="Enabled",
                variable=enabled_var,
            ).grid(
                row=index - 1,
                column=2,
                sticky="w",
                padx=(12, 0),
                pady=8,
            )

        container.grid_columnconfigure(1, weight=1)

        ttk.Separator(container, orient="horizontal").grid(
            row=4,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(18, 18),
        )

        self.alert_mode_var = tk.StringVar(value=str(config.get("alert_mode", "popup")))
        tk.Label(container, text="Alert Action").grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="w",
        )
        tk.Radiobutton(
            container,
            text=self.POPUP_MODE_LABEL,
            variable=self.alert_mode_var,
            value="popup",
            anchor="w",
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(10, 4))
        tk.Radiobutton(
            container,
            text=self.NOTIFICATION_MODE_LABEL,
            variable=self.alert_mode_var,
            value="notification",
            anchor="w",
        ).grid(row=7, column=0, columnspan=3, sticky="w", pady=4)
        tk.Label(
            container,
            text="Notification flashes the price text for about 5 seconds without sound.",
            fg="#666666",
            justify="left",
            wraplength=320,
        ).grid(row=8, column=0, columnspan=3, sticky="w", pady=(10, 0))

    def _build_interval_tab(self, parent: ttk.Frame, config: dict[str, Any]) -> None:
        container = tk.Frame(parent, padx=18, pady=18)
        container.pack(fill="both", expand=True)

        interval_seconds = int(config.get("interval_seconds", 300))
        self.interval_var = tk.IntVar(value=interval_seconds)
        self.interval_label_var = tk.StringVar(value=self._format_interval_label(interval_seconds))

        tk.Label(container, text="Refresh Interval").pack(anchor="w")
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
            text="Adjust between 30 seconds and 30 minutes in 30-second steps.",
            fg="#666666",
        ).pack(anchor="w", pady=(12, 0))

    def _build_display_tab(self, parent: ttk.Frame, config: dict[str, Any]) -> None:
        container = tk.Frame(parent, padx=18, pady=18)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="Overlay Position").pack(anchor="w")
        tk.Label(
            container,
            text=self.DRAG_GUIDE_TEXT,
            fg="#666666",
        ).pack(anchor="w", pady=(8, 20))

        opacity_value = int(float(config.get("opacity", 0.85)) * 100)
        self.opacity_var = tk.IntVar(value=opacity_value)
        self.opacity_label_var = tk.StringVar(value=f"{opacity_value}%")

        tk.Label(container, text="Overlay Opacity").pack(anchor="w", pady=(0, 8))
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
            messagebox.showerror("Input Error", str(exc), parent=self.window)
            return

        if self.interval_var is None or self.opacity_var is None or self.alert_mode_var is None:
            return

        current_config = self.config_getter()
        config = {
            "interval_seconds": int(self.interval_var.get()),
            "alarms": alarms,
            "alert_mode": self.alert_mode_var.get(),
            "opacity": round(int(self.opacity_var.get()) / 100, 2),
            "custom_position": (
                dict(current_config["custom_position"])
                if isinstance(current_config.get("custom_position"), dict)
                else None
            ),
        }

        try:
            saved_config = self.config_manager.save(config)
        except OSError as exc:
            messagebox.showerror("Save Failed", str(exc), parent=self.window)
            return

        self.on_save(saved_config)
        self._destroy_window()

    def _parse_alarm_values(self) -> list[dict[str, object]]:
        alarms: list[dict[str, object]] = []
        for var, enabled_var in zip(self.alarm_vars, self.alarm_enabled_vars, strict=True):
            value = var.get().strip()
            if not value:
                continue
            try:
                alarms.append(
                    {
                        "price": float(value),
                        "enabled": bool(enabled_var.get()),
                    }
                )
            except ValueError as exc:
                raise ValueError("Alert values must be numeric.") from exc
        return alarms

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
            return f"{minutes} min {remain_seconds} sec"
        if minutes:
            return f"{minutes} min"
        return f"{remain_seconds} sec"

    @staticmethod
    def _format_alarm_value(value: object) -> str:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return ""
        return f"{numeric:g}"

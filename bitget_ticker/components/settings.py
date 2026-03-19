from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from bitget_ticker.components.config import ConfigManager

logger = logging.getLogger("bitget_ticker.settings")


class SettingsDialog:
    """Tabbed settings dialog for alarms, interval, and opacity."""

    ALARM_SLOT_COUNT = 6
    WINDOW_WIDTH = 620
    WINDOW_HEIGHT = 820
    MIN_WINDOW_WIDTH = 580
    MIN_WINDOW_HEIGHT = 620
    WINDOW_TITLE = "Settings - Bitget BTC Ticker"
    ALERTS_TAB_TITLE = "Price Alerts"
    INTERVAL_TAB_TITLE = "Refresh Interval"
    DISPLAY_TAB_TITLE = "Display"
    SAVE_BUTTON_LABEL = "Save"
    CANCEL_BUTTON_LABEL = "Cancel"
    DRAG_GUIDE_TEXT = "Drag the overlay with the mouse to save its position."
    MARKET_TYPE_FUTURES_LABEL = "Futures"
    MARKET_TYPE_SPOT_LABEL = "Spot"
    POPUP_MODE_LABEL = "Popup"
    NOTIFICATION_MODE_LABEL = "Notification"
    CHART_TIMEFRAME_TITLE = "Hover Chart Timeframe"
    CHART_TIMEFRAME_5M_LABEL = "5 min"
    CHART_TIMEFRAME_15M_LABEL = "15 min"
    CHART_GUIDE_TEXT = "Hover over the overlay for 2 seconds to open the mini chart."

    TAB_ACTIVE_BG = "#ffffff"
    TAB_INACTIVE_BG = "#e8e8e8"

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
        self._content_area: tk.Frame | None = None
        self.alarm_vars: list[tk.StringVar] = []
        self.alarm_enabled_vars: list[tk.BooleanVar] = []
        self.alarm_mode_vars: list[tk.StringVar] = []
        self.market_type_var: tk.StringVar | None = None
        self.chart_timeframe_var: tk.StringVar | None = None
        self.interval_var: tk.IntVar | None = None
        self.interval_label_var: tk.StringVar | None = None
        self.opacity_var: tk.IntVar | None = None
        self.opacity_label_var: tk.StringVar | None = None
        self._initial_opacity = 85
        self._tab_frames: list[tk.Frame] = []
        self._tab_buttons: list[tk.Label] = []
        self._active_tab = 0

    def show(self) -> None:
        logger.debug("show() called")

        # If the window already exists (hidden), rebuild content and show it
        if self.window is not None and self.window.winfo_exists():
            logger.debug("reusing existing window")
            self._rebuild_content()
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            return

        try:
            config = self.config_getter()
            logger.debug("config loaded: alarms=%d", len(config.get("alarms", [])))
            self._initial_opacity = int(float(config["opacity"]) * 100)

            self.window = tk.Toplevel(self.root)
            self.window.title(self.WINDOW_TITLE)
            self.window.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
            self.window.minsize(self.MIN_WINDOW_WIDTH, self.MIN_WINDOW_HEIGHT)
            self.window.resizable(True, True)
            self.window.attributes("-topmost", True)
            self.window.protocol("WM_DELETE_WINDOW", self._handle_close)
            logger.debug("window created")

            # --- Tab bar ---
            tab_bar = tk.Frame(self.window, bg=self.TAB_INACTIVE_BG)
            tab_bar.pack(fill="x", padx=12, pady=(12, 0))

            titles = [self.ALERTS_TAB_TITLE, self.INTERVAL_TAB_TITLE, self.DISPLAY_TAB_TITLE]
            self._tab_buttons = []
            for i, title in enumerate(titles):
                btn = tk.Label(
                    tab_bar,
                    text=title,
                    padx=14,
                    pady=6,
                    cursor="hand2",
                    bg=self.TAB_INACTIVE_BG,
                )
                btn.pack(side="left")
                btn.bind("<Button-1>", lambda e, idx=i: self._select_tab(idx))
                self._tab_buttons.append(btn)
            logger.debug("tab buttons created: %d", len(self._tab_buttons))

            # --- Separator ---
            ttk.Separator(self.window, orient="horizontal").pack(fill="x", padx=12)

            # --- Content area (persists across rebuilds) ---
            self._content_area = tk.Frame(self.window)
            self._content_area.pack(fill="both", expand=True, padx=12)

            self._build_all_tabs(config)

            # --- Action buttons ---
            actions = tk.Frame(self.window, pady=10)
            actions.pack(fill="x")
            tk.Button(actions, text=self.SAVE_BUTTON_LABEL, width=12, command=self._save).pack(
                side="right",
                padx=12,
            )
            tk.Button(actions, text=self.CANCEL_BUTTON_LABEL, width=12, command=self._handle_close).pack(
                side="right",
            )
            logger.debug("show() complete (first create)")
            self.window.after(200, self._debug_layout)
        except Exception:
            logger.exception("show() failed")

    def _rebuild_content(self) -> None:
        """Clear and rebuild tab content for an existing (hidden) window."""
        logger.debug("_rebuild_content()")
        try:
            config = self.config_getter()
            self._initial_opacity = int(float(config["opacity"]) * 100)

            # Destroy old tab frames
            for frame in self._tab_frames:
                frame.destroy()
            self._tab_frames = []

            self._build_all_tabs(config)
            logger.debug("_rebuild_content() complete")
            if self.window is not None:
                self.window.after(200, self._debug_layout)
        except Exception:
            logger.exception("_rebuild_content() failed")

    def _build_all_tabs(self, config: dict[str, Any]) -> None:
        """Build the three tab frames inside _content_area."""
        if self._content_area is None:
            return

        alarm_frame = tk.Frame(self._content_area)
        interval_frame = tk.Frame(self._content_area)
        display_frame = tk.Frame(self._content_area)
        self._tab_frames = [alarm_frame, interval_frame, display_frame]
        logger.debug("tab frames created")

        self._build_alarm_tab(alarm_frame, config)
        logger.debug("alarm tab built, alarm_vars=%d", len(self.alarm_vars))
        self._build_interval_tab(interval_frame, config)
        logger.debug("interval tab built")
        self._build_display_tab(display_frame, config)
        logger.debug("display tab built")

        self._select_tab(0)
        logger.debug("tab 0 selected")

    def _debug_layout(self) -> None:
        if self.window is None or not self.window.winfo_exists():
            return
        try:
            idx = self._active_tab
            frame = self._tab_frames[idx] if self._tab_frames else None
            content = self._content_area
            logger.debug(
                "LAYOUT window=%s content=[geo=%s mapped=%s] frame=[geo=%s mapped=%s children=%d]",
                self.window.geometry(),
                content.winfo_geometry() if content else "N/A",
                content.winfo_ismapped() if content else "N/A",
                frame.winfo_geometry() if frame else "N/A",
                frame.winfo_ismapped() if frame else "N/A",
                len(frame.winfo_children()) if frame else 0,
            )
        except Exception:
            logger.exception("_debug_layout failed")

    def _select_tab(self, index: int) -> None:
        logger.debug("_select_tab(%d) frames=%d buttons=%d", index, len(self._tab_frames), len(self._tab_buttons))
        try:
            self._active_tab = index
            for frame in self._tab_frames:
                frame.pack_forget()
            self._tab_frames[index].pack(fill="both", expand=True)
            for i, btn in enumerate(self._tab_buttons):
                if i == index:
                    btn.config(bg=self.TAB_ACTIVE_BG, font=("TkDefaultFont", 9, "bold"))
                else:
                    btn.config(bg=self.TAB_INACTIVE_BG, font=("TkDefaultFont", 9))
            logger.debug("_select_tab(%d) done, frame packed", index)
        except Exception:
            logger.exception("_select_tab(%d) failed", index)

    def _build_alarm_tab(self, parent: tk.Frame, config: dict[str, Any]) -> None:
        alarms = list(config.get("alarms", []))[: self.ALARM_SLOT_COUNT]
        while len(alarms) < self.ALARM_SLOT_COUNT:
            alarms.append({"price": "", "enabled": True, "mode": "popup"})

        container = tk.Frame(parent)
        container.pack(fill="x", padx=18, pady=18)

        self.alarm_vars = []
        self.alarm_enabled_vars = []
        self.alarm_mode_vars = []
        for index, alarm in enumerate(alarms, start=1):
            price_value = ""
            enabled_value = True
            mode_value = "popup"
            if isinstance(alarm, dict):
                price_value = self._format_alarm_value(alarm.get("price", ""))
                enabled_value = bool(alarm.get("enabled", True))
                mode_value = str(alarm.get("mode", "popup"))
            else:
                price_value = self._format_alarm_value(alarm)

            var = tk.StringVar(value=price_value)
            enabled_var = tk.BooleanVar(value=enabled_value)
            mode_var = tk.StringVar(value=self._mode_to_label(mode_value))
            self.alarm_vars.append(var)
            self.alarm_enabled_vars.append(enabled_var)
            self.alarm_mode_vars.append(mode_var)

            row = tk.Frame(container)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"Alert {index} (USDT)", anchor="w", width=14).pack(
                side="left",
            )
            tk.Entry(row, textvariable=var, width=24).pack(
                side="left", padx=(12, 0), fill="x", expand=True,
            )
            tk.Checkbutton(row, text="Enabled", variable=enabled_var).pack(
                side="left", padx=(12, 0),
            )
            ttk.Combobox(
                row,
                textvariable=mode_var,
                values=(self.POPUP_MODE_LABEL, self.NOTIFICATION_MODE_LABEL),
                width=12,
                state="readonly",
            ).pack(side="left", padx=(12, 0))

        ttk.Separator(container, orient="horizontal").pack(
            fill="x", pady=(18, 18),
        )
        tk.Label(
            container,
            text="Each alert can use Popup or Notification independently.",
            fg="#666666",
            justify="left",
            wraplength=420,
        ).pack(anchor="w", pady=(10, 0))

    def _build_interval_tab(self, parent: tk.Frame, config: dict[str, Any]) -> None:
        container = tk.Frame(parent, padx=18, pady=18)
        container.pack(fill="both", expand=True)

        self.market_type_var = tk.StringVar(value=str(config.get("market_type", "futures")))
        self.chart_timeframe_var = tk.StringVar(value=str(config.get("chart_timeframe", "15m")))

        tk.Label(container, text="Market Type").pack(anchor="w")
        market_frame = tk.Frame(container)
        market_frame.pack(anchor="w", pady=(10, 18))
        tk.Radiobutton(
            market_frame,
            text=self.MARKET_TYPE_FUTURES_LABEL,
            variable=self.market_type_var,
            value="futures",
            anchor="w",
        ).pack(side="left")
        tk.Radiobutton(
            market_frame,
            text=self.MARKET_TYPE_SPOT_LABEL,
            variable=self.market_type_var,
            value="spot",
            anchor="w",
        ).pack(side="left", padx=(16, 0))

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=(0, 18))

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

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=(20, 18))

        tk.Label(container, text=self.CHART_TIMEFRAME_TITLE).pack(anchor="w")
        chart_frame = tk.Frame(container)
        chart_frame.pack(anchor="w", pady=(10, 10))
        tk.Radiobutton(
            chart_frame,
            text=self.CHART_TIMEFRAME_5M_LABEL,
            variable=self.chart_timeframe_var,
            value="5m",
            anchor="w",
        ).pack(side="left")
        tk.Radiobutton(
            chart_frame,
            text=self.CHART_TIMEFRAME_15M_LABEL,
            variable=self.chart_timeframe_var,
            value="15m",
            anchor="w",
        ).pack(side="left", padx=(16, 0))
        tk.Label(
            container,
            text=self.CHART_GUIDE_TEXT,
            fg="#666666",
            justify="left",
            wraplength=420,
        ).pack(anchor="w", pady=(0, 0))

    def _build_display_tab(self, parent: tk.Frame, config: dict[str, Any]) -> None:
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

        if (
            self.interval_var is None
            or self.opacity_var is None
            or self.market_type_var is None
            or self.chart_timeframe_var is None
        ):
            return

        current_config = self.config_getter()
        config = {
            "interval_seconds": int(self.interval_var.get()),
            "market_type": self.market_type_var.get(),
            "chart_timeframe": self.chart_timeframe_var.get(),
            "alarms": alarms,
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
        self._handle_close()

    def _parse_alarm_values(self) -> list[dict[str, object]]:
        alarms: list[dict[str, object]] = []
        for var, enabled_var, mode_var in zip(
            self.alarm_vars,
            self.alarm_enabled_vars,
            self.alarm_mode_vars,
            strict=True,
        ):
            value = var.get().strip()
            if not value:
                continue
            try:
                alarms.append(
                    {
                        "price": float(value),
                        "enabled": bool(enabled_var.get()),
                        "mode": self._label_to_mode(mode_var.get()),
                    }
                )
            except ValueError as exc:
                raise ValueError("Alert values must be numeric.") from exc
        return alarms

    def _handle_close(self) -> None:
        logger.debug("_handle_close()")
        self.root.attributes("-alpha", self._initial_opacity / 100)
        # Hide instead of destroy — avoids Windows Toplevel re-creation rendering bug
        if self.window is not None and self.window.winfo_exists():
            self.window.withdraw()

    def _destroy_window(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        self.window = None
        self._content_area = None
        self._tab_frames = []
        self._tab_buttons = []

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

    def _mode_to_label(self, mode: str) -> str:
        return self.NOTIFICATION_MODE_LABEL if mode == "notification" else self.POPUP_MODE_LABEL

    def _label_to_mode(self, label: str) -> str:
        return "notification" if label == self.NOTIFICATION_MODE_LABEL else "popup"

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from bitget_ticker.components.alarm import AlarmEngine

Candle = tuple[int, float, float, float, float, float]  # (ts, open, high, low, close, volume)


class OverlayWindow:
    """Bottom overlay window for BTC price display."""

    WIDTH = 260
    HEIGHT = 38
    CHART_WIDTH = 320
    CHART_HEIGHT = 280
    CHART_GAP = 12
    SCREEN_MARGIN = 24
    CHART_HOVER_DELAY_MS = 2000
    CHART_HIDE_DELAY_MS = 180
    NOTIFICATION_DURATION_MS = 5000
    NOTIFICATION_FLASH_INTERVAL_MS = 400
    SETTINGS_MENU_LABEL = "Settings"
    SHOW_HIDE_MENU_LABEL = "Show/Hide"
    QUIT_MENU_LABEL = "Quit"
    VOLUME_UP_COLOR = "#00d4aa40"
    VOLUME_DOWN_COLOR = "#ff6b6b40"
    BACKGROUND = "#0d1117"
    CHART_BACKGROUND = "#161b22"
    CHART_BORDER = "#30363d"
    CHART_LINE_COLOR = "#58a6ff"
    CHART_GRID_COLOR = "#2d333b"
    ICON_COLOR = "#f7931a"
    UP_COLOR = "#00d4aa"
    DOWN_COLOR = "#ff6b6b"
    FLAT_COLOR = "#c9d1d9"
    NOTIFICATION_COLOR = "#ffd166"
    NOTIFICATION_TEXT_COLOR = "#0d1117"

    def __init__(
        self,
        opacity: float,
        custom_position: dict[str, int] | None,
        on_open_settings: Callable[[], None],
        on_quit: Callable[[], None],
        on_position_change: Callable[[dict[str, int]], None] | None = None,
        on_toggle_visibility: Callable[[], None] | None = None,
    ) -> None:
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", opacity)
        self.root.configure(bg=self.BACKGROUND)

        self._drag_x = 0
        self._drag_y = 0
        self._custom_position = custom_position
        self._on_position_change = on_position_change
        self._alarm_engine: AlarmEngine | None = None
        self._alarms_provider: Callable[[], list[dict[str, object]]] | None = None
        self._on_toggle_visibility = on_toggle_visibility
        self._latest_price_text = "Loading..."
        self._latest_direction_text = "─"
        self._latest_color = self.FLAT_COLOR
        self._notification_message: str | None = None
        self._notification_flash_on = False
        self._notification_flash_job: str | None = None
        self._notification_clear_job: str | None = None
        self._chart_points: list[Candle] = []
        self._chart_timeframe = "15m"
        self._chart_market_type = "futures"
        self._chart_window: tk.Toplevel | None = None
        self._chart_title_label: tk.Label | None = None
        self._chart_detail_label: tk.Label | None = None
        self._chart_canvas: tk.Canvas | None = None
        self._chart_hover_job: str | None = None
        self._chart_hide_job: str | None = None
        self._overlay_hovering = False
        self._chart_hovering = False
        self._build_layout()
        self._create_context_menu(on_open_settings, on_quit, on_toggle_visibility)
        self.set_position(custom_position)
        self._bind_interactions()

    def attach_alarm_engine(
        self,
        alarm_engine: AlarmEngine,
        alarms_provider: Callable[[], list[dict[str, object]]],
    ) -> None:
        self._alarm_engine = alarm_engine
        self._alarms_provider = alarms_provider

    def set_opacity(self, opacity: float) -> None:
        self.root.attributes("-alpha", opacity)

    def set_position(self, custom_position: dict[str, int] | None = None) -> None:
        self._custom_position = dict(custom_position) if custom_position is not None else None

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x, y = self.resolve_position(
            screen_w=screen_w,
            screen_h=screen_h,
            custom_position=self._custom_position,
        )
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self._reposition_chart()

    def update_display(self, price: float, prev_price: float | None) -> None:
        arrow = "─"
        color = self.FLAT_COLOR
        if prev_price is None:
            color = self.FLAT_COLOR
        elif price > prev_price:
            arrow = "▲"
            color = self.UP_COLOR
        elif price < prev_price:
            arrow = "▼"
            color = self.DOWN_COLOR

        self._latest_price_text = f"${price:,.2f}"
        self._latest_direction_text = arrow
        self._latest_color = color
        self._render_display()

        if self._alarm_engine is not None and self._alarms_provider is not None:
            self._alarm_engine.check(price, self._alarms_provider())

    def show_error(self, message: str = "Error") -> None:
        self._latest_price_text = message
        self._latest_direction_text = "!"
        self._latest_color = self.DOWN_COLOR
        self._render_display()

    def show_notification(self, alarm_price: float, current_price: float) -> None:
        self._notification_message = self.build_notification_message(alarm_price, current_price)
        self._notification_flash_on = True
        self._cancel_notification_jobs()
        self._render_display()
        self._notification_flash_job = self.root.after(
            self.NOTIFICATION_FLASH_INTERVAL_MS,
            self._toggle_notification_flash,
        )
        self._notification_clear_job = self.root.after(
            self.NOTIFICATION_DURATION_MS,
            self._clear_notification,
        )

    def update_chart_data(
        self,
        candles: list[Candle],
        timeframe: str,
        market_type: str,
    ) -> None:
        normalized: list[Candle] = []
        for candle in candles:
            if len(candle) >= 6:
                ts, o, h, l, c, v = candle[0], candle[1], candle[2], candle[3], candle[4], candle[5]
            else:
                ts, o, h, l, c = candle[0], candle[1], candle[2], candle[3], candle[4]
                v = 0.0
            normalized.append((int(ts), float(o), float(h), float(l), float(c), float(v)))
        self._chart_points = sorted(normalized, key=lambda item: item[0])
        self._chart_timeframe = "5m" if timeframe == "5m" else "15m"
        self._chart_market_type = "spot" if market_type == "spot" else "futures"
        self._render_chart()

    def _build_layout(self) -> None:
        self.container = tk.Frame(self.root, bg=self.BACKGROUND, padx=10, pady=6)
        self.container.pack(fill="both", expand=True)

        self.icon_label = tk.Label(
            self.container,
            text="₿",
            bg=self.BACKGROUND,
            fg=self.ICON_COLOR,
            font=("Segoe UI", 14, "bold"),
        )
        self.icon_label.pack(side="left")

        self.price_label = tk.Label(
            self.container,
            text="Loading...",
            bg=self.BACKGROUND,
            fg=self.FLAT_COLOR,
            font=("Consolas", 13, "bold"),
            padx=8,
        )
        self.price_label.pack(side="left")

        self.direction_label = tk.Label(
            self.container,
            text="─",
            bg=self.BACKGROUND,
            fg=self.FLAT_COLOR,
            font=("Segoe UI", 11, "bold"),
        )
        self.direction_label.pack(side="left")

    def _create_context_menu(
        self,
        on_open_settings: Callable[[], None],
        on_quit: Callable[[], None],
        on_toggle_visibility: Callable[[], None] | None = None,
    ) -> None:
        self.context_menu = tk.Menu(self.root, tearoff=False)
        self.context_menu.add_command(label=self.SETTINGS_MENU_LABEL, command=on_open_settings)
        if on_toggle_visibility is not None:
            self.context_menu.add_command(label=self.SHOW_HIDE_MENU_LABEL, command=on_toggle_visibility)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.QUIT_MENU_LABEL, command=on_quit)

    @classmethod
    def resolve_position(
        cls,
        screen_w: int,
        screen_h: int,
        custom_position: dict[str, int] | None = None,
    ) -> tuple[int, int]:
        max_x = max(0, screen_w - cls.WIDTH)
        max_y = max(0, screen_h - cls.HEIGHT)

        if custom_position is not None:
            x = min(max(0, int(custom_position["x"])), max_x)
            y = min(max(0, int(custom_position["y"])), max_y)
            return x, y

        return (
            max(0, screen_w - cls.WIDTH - cls.SCREEN_MARGIN),
            max(0, screen_h - cls.HEIGHT - cls.SCREEN_MARGIN),
        )

    @classmethod
    def resolve_chart_position(
        cls,
        overlay_x: int,
        overlay_y: int,
        screen_w: int,
        screen_h: int,
    ) -> tuple[int, int]:
        max_x = max(0, screen_w - cls.CHART_WIDTH)
        max_y = max(0, screen_h - cls.CHART_HEIGHT)
        preferred_x = overlay_x + cls.WIDTH - cls.CHART_WIDTH
        x = min(max(0, preferred_x), max_x)
        above_y = overlay_y - cls.CHART_HEIGHT - cls.CHART_GAP
        if above_y >= 0:
            return x, above_y

        below_y = overlay_y + cls.HEIGHT + cls.CHART_GAP
        return x, min(max(0, below_y), max_y)

    def _bind_interactions(self) -> None:
        widgets = [
            self.root,
            self.container,
            self.icon_label,
            self.price_label,
            self.direction_label,
        ]
        for widget in widgets:
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)
            widget.bind("<ButtonRelease-1>", self._finish_drag)
            widget.bind("<Button-3>", self._show_context_menu)
            widget.bind("<Enter>", self._handle_overlay_enter, add="+")
            widget.bind("<Leave>", self._handle_overlay_leave, add="+")

    def _start_drag(self, event: tk.Event) -> None:
        self._cancel_chart_jobs()
        self._hide_chart_panel()
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
        self._reposition_chart()

    def _finish_drag(self, _event: tk.Event) -> None:
        position = {
            "x": self.root.winfo_x(),
            "y": self.root.winfo_y(),
        }
        self._custom_position = position
        if self._on_position_change is not None:
            self._on_position_change(position)

    def _render_display(self) -> None:
        if self._notification_message is not None:
            background = self.NOTIFICATION_COLOR if self._notification_flash_on else self.BACKGROUND
            color = self.NOTIFICATION_TEXT_COLOR if self._notification_flash_on else self.NOTIFICATION_COLOR
            self._apply_display_theme(background)
            self.icon_label.config(text="!", fg=color)
            self.price_label.config(text=self._notification_message, fg=color)
            self.direction_label.config(text="", fg=color)
            return

        self._apply_display_theme(self.BACKGROUND)
        self.icon_label.config(text="₿", fg=self.ICON_COLOR)
        self.price_label.config(text=self._latest_price_text, fg=self._latest_color)
        self.direction_label.config(text=self._latest_direction_text, fg=self._latest_color)

    def _toggle_notification_flash(self) -> None:
        if self._notification_message is None:
            self._notification_flash_job = None
            return

        self._notification_flash_on = not self._notification_flash_on
        self._render_display()
        self._notification_flash_job = self.root.after(
            self.NOTIFICATION_FLASH_INTERVAL_MS,
            self._toggle_notification_flash,
        )

    def _clear_notification(self) -> None:
        self._cancel_notification_jobs()
        self._notification_message = None
        self._notification_flash_on = False
        self._render_display()

    def _cancel_notification_jobs(self) -> None:
        for job_name in ("_notification_flash_job", "_notification_clear_job"):
            job = getattr(self, job_name)
            if job is None:
                continue
            try:
                self.root.after_cancel(job)
            except ValueError:
                pass
            setattr(self, job_name, None)

    def _handle_overlay_enter(self, _event: tk.Event) -> None:
        self._overlay_hovering = True
        self._cancel_chart_hide_job()
        if self._chart_window is not None and self._chart_window.winfo_exists():
            return
        self._schedule_chart_show()

    def _handle_overlay_leave(self, _event: tk.Event) -> None:
        self._overlay_hovering = False
        self._cancel_chart_hover_job()
        if not self._chart_hovering:
            self._schedule_chart_hide()

    def _handle_chart_enter(self, _event: tk.Event) -> None:
        self._chart_hovering = True
        self._cancel_chart_hide_job()

    def _handle_chart_leave(self, _event: tk.Event) -> None:
        self._chart_hovering = False
        if not self._overlay_hovering:
            self._schedule_chart_hide()

    def _schedule_chart_show(self) -> None:
        self._cancel_chart_hover_job()
        self._chart_hover_job = self.root.after(
            self.CHART_HOVER_DELAY_MS,
            self._show_chart_panel,
        )

    def _schedule_chart_hide(self) -> None:
        self._cancel_chart_hide_job()
        self._chart_hide_job = self.root.after(
            self.CHART_HIDE_DELAY_MS,
            self._hide_chart_panel,
        )

    def _show_chart_panel(self) -> None:
        self._chart_hover_job = None
        if self._chart_window is not None and self._chart_window.winfo_exists():
            self._render_chart()
            return

        self._chart_window = tk.Toplevel(self.root)
        self._chart_window.overrideredirect(True)
        self._chart_window.attributes("-topmost", True)
        self._chart_window.configure(bg=self.CHART_BORDER)

        frame = tk.Frame(self._chart_window, bg=self.CHART_BACKGROUND, padx=10, pady=10)
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        self._chart_title_label = tk.Label(
            frame,
            text="BTCUSDT",
            bg=self.CHART_BACKGROUND,
            fg="#f0f6fc",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self._chart_title_label.pack(fill="x")

        self._chart_detail_label = tk.Label(
            frame,
            text="Waiting for candles...",
            bg=self.CHART_BACKGROUND,
            fg="#8b949e",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self._chart_detail_label.pack(fill="x", pady=(2, 8))

        self._chart_canvas = tk.Canvas(
            frame,
            width=self.CHART_WIDTH - 22,
            height=self.CHART_HEIGHT - 70,
            bg=self.CHART_BACKGROUND,
            highlightthickness=0,
            bd=0,
        )
        self._chart_canvas.pack(fill="both", expand=True)

        chart_widgets = [
            self._chart_window,
            frame,
            self._chart_title_label,
            self._chart_detail_label,
            self._chart_canvas,
        ]
        for widget in chart_widgets:
            widget.bind("<Enter>", self._handle_chart_enter, add="+")
            widget.bind("<Leave>", self._handle_chart_leave, add="+")

        self._reposition_chart()
        self._render_chart()

    def _hide_chart_panel(self) -> None:
        self._cancel_chart_jobs()
        self._chart_hovering = False
        if self._chart_window is None:
            return
        if self._chart_window.winfo_exists():
            self._chart_window.destroy()
        self._chart_window = None
        self._chart_title_label = None
        self._chart_detail_label = None
        self._chart_canvas = None

    def _reposition_chart(self) -> None:
        if self._chart_window is None or not self._chart_window.winfo_exists():
            return

        x, y = self.resolve_chart_position(
            overlay_x=self.root.winfo_x(),
            overlay_y=self.root.winfo_y(),
            screen_w=self.root.winfo_screenwidth(),
            screen_h=self.root.winfo_screenheight(),
        )
        self._chart_window.geometry(f"{self.CHART_WIDTH}x{self.CHART_HEIGHT}+{x}+{y}")

    def _render_chart(self) -> None:
        self._reposition_chart()
        if (
            self._chart_window is None
            or not self._chart_window.winfo_exists()
            or self._chart_canvas is None
            or self._chart_title_label is None
            or self._chart_detail_label is None
        ):
            return

        market_label = "Spot" if self._chart_market_type == "spot" else "Futures"
        timeframe_label = "5 min" if self._chart_timeframe == "5m" else "15 min"
        self._chart_title_label.config(text=f"BTCUSDT {market_label} {timeframe_label}")

        canvas = self._chart_canvas
        self._chart_window.update_idletasks()
        canvas.delete("all")
        width = self.resolve_canvas_dimension(canvas.winfo_width(), int(canvas.cget("width")))
        height = self.resolve_canvas_dimension(canvas.winfo_height(), int(canvas.cget("height")))

        if len(self._chart_points) < 2:
            self._chart_detail_label.config(text="Waiting for candles...")
            canvas.create_text(
                width / 2,
                height / 2,
                text="Chart unavailable",
                fill="#8b949e",
                font=("Segoe UI", 10),
            )
            return

        lows = [lp for _ts, _o, _h, lp, _c, _v in self._chart_points]
        highs = [hp for _ts, _o, hp, _l, _c, _v in self._chart_points]
        closes = [cp for _ts, _o, _h, _l, cp, _v in self._chart_points]
        volumes = [v for _ts, _o, _h, _l, _c, v in self._chart_points]
        minimum = min(lows)
        maximum = max(highs)
        if minimum == maximum:
            minimum -= 1
            maximum += 1
        latest = closes[-1]
        self._chart_detail_label.config(
            text=(
                f"Last {len(closes)} candles  "
                f"High ${maximum:,.2f}  Low ${minimum:,.2f}  Last ${latest:,.2f}"
            )
        )

        # Layout: price chart takes top 70%, volume bars take bottom 25%, 5% gap
        left_pad = 56
        right_pad = 12
        top_pad = 12
        bottom_pad = 8
        gap = 8
        total_chart_w = max(1, width - left_pad - right_pad)
        price_area_h = int((height - top_pad - bottom_pad - gap) * 0.70)
        vol_area_h = int((height - top_pad - bottom_pad - gap) * 0.25)
        price_top = top_pad
        price_bottom = price_top + price_area_h
        vol_top = price_bottom + gap
        vol_bottom = vol_top + vol_area_h

        # Y-axis price labels
        price_range = maximum - minimum
        for step in range(4):
            ratio = step / 3
            y = price_top + (price_area_h * ratio)
            price_val = maximum - (price_range * ratio)
            canvas.create_line(left_pad, y, width - right_pad, y, fill=self.CHART_GRID_COLOR, width=1)
            canvas.create_text(
                left_pad - 4, y, text=f"${price_val:,.0f}", anchor="e",
                fill="#8b949e", font=("Consolas", 7),
            )

        # Separator between price and volume
        canvas.create_line(left_pad, vol_top - gap // 2, width - right_pad, vol_top - gap // 2,
                           fill=self.CHART_GRID_COLOR, width=1)

        # Candle geometry
        n = len(self._chart_points)
        slot_width = total_chart_w / max(1, n)
        body_width = max(4.0, min(12.0, slot_width * 0.6))

        def price_to_y(price: float) -> float:
            r = (price - minimum) / price_range
            return price_bottom - (r * price_area_h)

        max_vol = max(volumes) if volumes and max(volumes) > 0 else 1.0

        for i, (_ts, open_p, high_p, low_p, close_p, vol) in enumerate(self._chart_points):
            cx = left_pad + (slot_width * i) + (slot_width / 2)
            color = self.UP_COLOR if close_p >= open_p else self.DOWN_COLOR

            # Candle wick + body
            canvas.create_line(cx, price_to_y(high_p), cx, price_to_y(low_p), fill=color, width=1)
            oy = price_to_y(open_p)
            cy = price_to_y(close_p)
            bt = min(oy, cy)
            bb = max(oy, cy)
            if abs(bb - bt) < 2:
                bb = bt + 2
            canvas.create_rectangle(
                cx - body_width / 2, bt, cx + body_width / 2, bb,
                fill=color, outline=color,
            )

            # Volume bar
            if max_vol > 0 and vol > 0:
                vol_h = (vol / max_vol) * vol_area_h
                vol_color = self.UP_COLOR if close_p >= open_p else self.DOWN_COLOR
                canvas.create_rectangle(
                    cx - body_width / 2, vol_bottom - vol_h,
                    cx + body_width / 2, vol_bottom,
                    fill=vol_color, outline=vol_color, stipple="gray50",
                )

        # Volume Y-axis label
        canvas.create_text(
            left_pad - 4, vol_top, text=f"{max_vol:,.0f}", anchor="e",
            fill="#8b949e", font=("Consolas", 7),
        )

    def _apply_display_theme(self, background: str) -> None:
        self.root.configure(bg=background)
        self.container.configure(bg=background)
        self.icon_label.configure(bg=background)
        self.price_label.configure(bg=background)
        self.direction_label.configure(bg=background)

    def _cancel_chart_hover_job(self) -> None:
        if self._chart_hover_job is None:
            return
        try:
            self.root.after_cancel(self._chart_hover_job)
        except ValueError:
            pass
        self._chart_hover_job = None

    def _cancel_chart_hide_job(self) -> None:
        if self._chart_hide_job is None:
            return
        try:
            self.root.after_cancel(self._chart_hide_job)
        except ValueError:
            pass
        self._chart_hide_job = None

    def _cancel_chart_jobs(self) -> None:
        self._cancel_chart_hover_job()
        self._cancel_chart_hide_job()

    @staticmethod
    def resolve_canvas_dimension(measured: int, configured: int) -> int:
        if measured <= 1:
            return configured
        return measured

    @staticmethod
    def build_notification_message(alarm_price: float, current_price: float) -> str:
        return f"Hit {OverlayWindow._format_alert_price(alarm_price)}"

    @classmethod
    def build_candle_geometry(
        cls,
        candles: list[Candle],
        width: int,
        height: int,
        padding: int,
    ) -> list[dict[str, float | str]]:
        if len(candles) < 1:
            return []

        lows = [c[3] for c in candles]
        highs = [c[2] for c in candles]
        minimum = min(lows)
        maximum = max(highs)
        if minimum == maximum:
            minimum -= 1
            maximum += 1

        chart_width = max(1, width - padding * 2)
        chart_height = max(1, height - padding * 2)
        slot_width = chart_width / max(1, len(candles))
        body_width = max(4.0, min(12.0, slot_width * 0.6))
        price_range = maximum - minimum

        def price_to_y(price: float) -> float:
            ratio = (price - minimum) / price_range
            return height - padding - (ratio * chart_height)

        geometry: list[dict[str, float | str]] = []
        for index, candle in enumerate(candles):
            _timestamp, open_price, high_price, low_price, close_price = candle[0], candle[1], candle[2], candle[3], candle[4]
            center_x = padding + (slot_width * index) + (slot_width / 2)
            open_y = price_to_y(open_price)
            close_y = price_to_y(close_price)
            high_y = price_to_y(high_price)
            low_y = price_to_y(low_price)
            body_top = min(open_y, close_y)
            body_bottom = max(open_y, close_y)
            if abs(body_bottom - body_top) < 2:
                body_bottom = body_top + 2
            color = cls.UP_COLOR if close_price >= open_price else cls.DOWN_COLOR
            geometry.append(
                {
                    "center_x": center_x,
                    "wick_top": high_y,
                    "wick_bottom": low_y,
                    "body_left": center_x - (body_width / 2),
                    "body_right": center_x + (body_width / 2),
                    "body_top": body_top,
                    "body_bottom": body_bottom,
                    "color": color,
                }
            )
        return geometry

    def toggle_visibility(self) -> None:
        if self.root.state() == "withdrawn":
            self.root.deiconify()
        else:
            self._hide_chart_panel()
            self.root.withdraw()

    @staticmethod
    def _format_alert_price(alarm_price: float) -> str:
        if alarm_price.is_integer():
            return f"${alarm_price:,.0f}"
        return f"${alarm_price:,.2f}"

    def _show_context_menu(self, event: tk.Event) -> None:
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from bitget_ticker.components.alarm import AlarmEngine


class OverlayWindow:
    """Bottom overlay window for BTC price display."""

    WIDTH = 260
    HEIGHT = 38
    CHART_WIDTH = 320
    CHART_HEIGHT = 200
    CHART_GAP = 12
    SCREEN_MARGIN = 24
    CHART_HOVER_DELAY_MS = 2000
    CHART_HIDE_DELAY_MS = 180
    NOTIFICATION_DURATION_MS = 5000
    NOTIFICATION_FLASH_INTERVAL_MS = 400
    SETTINGS_MENU_LABEL = "Settings"
    QUIT_MENU_LABEL = "Quit"
    BACKGROUND = "#0d1117"
    CHART_BACKGROUND = "#161b22"
    CHART_BORDER = "#30363d"
    CHART_LINE_COLOR = "#58a6ff"
    CHART_GRID_COLOR = "#2d333b"
    UP_COLOR = "#00d4aa"
    DOWN_COLOR = "#ff6b6b"
    FLAT_COLOR = "#c9d1d9"
    NOTIFICATION_COLOR = "#ffd166"

    def __init__(
        self,
        opacity: float,
        custom_position: dict[str, int] | None,
        on_open_settings: Callable[[], None],
        on_quit: Callable[[], None],
        on_position_change: Callable[[dict[str, int]], None] | None = None,
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
        self._latest_price_text = "Loading..."
        self._latest_direction_text = "─"
        self._latest_color = self.FLAT_COLOR
        self._notification_message: str | None = None
        self._notification_flash_on = False
        self._notification_flash_job: str | None = None
        self._notification_clear_job: str | None = None
        self._chart_points: list[tuple[int, float]] = []
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
        self._create_context_menu(on_open_settings, on_quit)
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
        del current_price
        self._notification_message = f"Hit {self._format_alert_price(alarm_price)}"
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
        candles: list[tuple[int, float]],
        timeframe: str,
        market_type: str,
    ) -> None:
        self._chart_points = sorted(
            [(int(timestamp), float(close_price)) for timestamp, close_price in candles],
            key=lambda item: item[0],
        )
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
            fg="#f7931a",
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
    ) -> None:
        self.context_menu = tk.Menu(self.root, tearoff=False)
        self.context_menu.add_command(label=self.SETTINGS_MENU_LABEL, command=on_open_settings)
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
            color = self.NOTIFICATION_COLOR if self._notification_flash_on else self._latest_color
            self.price_label.config(text=self._notification_message, fg=color)
            self.direction_label.config(text="!", fg=color)
            return

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
        canvas.delete("all")
        width = int(canvas.winfo_width() or canvas.cget("width"))
        height = int(canvas.winfo_height() or canvas.cget("height"))

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

        closes = [close_price for _, close_price in self._chart_points]
        minimum = min(closes)
        maximum = max(closes)
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

        padding = 16
        chart_width = max(1, width - padding * 2)
        chart_height = max(1, height - padding * 2)

        for step in range(4):
            y = padding + (chart_height * step / 3)
            canvas.create_line(
                padding,
                y,
                width - padding,
                y,
                fill=self.CHART_GRID_COLOR,
                width=1,
            )

        range_size = maximum - minimum
        points: list[float] = []
        for index, close_price in enumerate(closes):
            x = padding + (chart_width * index / (len(closes) - 1))
            ratio = (close_price - minimum) / range_size
            y = height - padding - (ratio * chart_height)
            points.extend((x, y))

        canvas.create_line(
            *points,
            fill=self.CHART_LINE_COLOR,
            width=2,
            smooth=True,
        )
        canvas.create_oval(
            points[-2] - 3,
            points[-1] - 3,
            points[-2] + 3,
            points[-1] + 3,
            fill=self.CHART_LINE_COLOR,
            outline="",
        )

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
    def _format_alert_price(alarm_price: float) -> str:
        if alarm_price.is_integer():
            return f"${alarm_price:,.0f}"
        return f"${alarm_price:,.2f}"

    def _show_context_menu(self, event: tk.Event) -> None:
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

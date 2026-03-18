from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from bitget_ticker.components.alarm import AlarmEngine


class OverlayWindow:
    """Bottom overlay window for BTC price display."""

    WIDTH = 260
    HEIGHT = 38
    SCREEN_MARGIN = 24
    NOTIFICATION_DURATION_MS = 5000
    NOTIFICATION_FLASH_INTERVAL_MS = 400
    SETTINGS_MENU_LABEL = "Settings"
    QUIT_MENU_LABEL = "Quit"
    BACKGROUND = "#0d1117"
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

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

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

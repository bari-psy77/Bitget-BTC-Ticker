from __future__ import annotations

import threading
import time
from tkinter import messagebox

from bitget_ticker.components.alarm import AlarmEngine
from bitget_ticker.components.config import ConfigManager
from bitget_ticker.components.fetcher import PriceFetcher
from bitget_ticker.components.overlay import OverlayWindow
from bitget_ticker.components.settings import SettingsDialog
from bitget_ticker.components.tray import TrayIcon


class BitgetBTCTicker:
    """Coordinate configuration, UI, tray, alarms, and price polling."""

    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self.price_fetcher = PriceFetcher()

        self.running = True
        self.previous_price: float | None = None
        self.update_thread: threading.Thread | None = None
        self._config_changed = threading.Event()

        self.overlay = OverlayWindow(
            opacity=float(self.config["opacity"]),
            position=str(self.config["position"]),
            custom_position=self._copy_custom_position(self.config.get("custom_position")),
            on_open_settings=self.open_settings,
            on_quit=self.quit_app,
            on_position_change=self.on_position_change,
        )
        self.root = self.overlay.root

        self.alarm_engine = AlarmEngine(on_alarm=self.on_alarm)
        self.overlay.attach_alarm_engine(self.alarm_engine, self._current_alarms)

        self.settings_dialog = SettingsDialog(
            root=self.root,
            config_manager=self.config_manager,
            config_getter=self._current_config,
            on_save=self.apply_settings,
        )
        self.tray_icon = TrayIcon(
            root=self.root,
            on_open_settings=self.open_settings,
            on_quit=self.quit_app,
        )

    def run(self) -> None:
        self.tray_icon.start()
        self.root.after(100, self.fetch_price_async)
        self.update_thread = threading.Thread(target=self.price_update_loop, daemon=True)
        self.update_thread.start()
        self.root.mainloop()

    def fetch_price_async(self) -> None:
        threading.Thread(target=self._fetch_and_dispatch, daemon=True).start()

    def price_update_loop(self) -> None:
        time.sleep(5)
        while self.running:
            wait_seconds = int(self.config["interval_seconds"])
            should_fetch = True

            for _ in range(wait_seconds):
                if not self.running:
                    return
                if self._config_changed.is_set():
                    self._config_changed.clear()
                    should_fetch = False
                    break
                time.sleep(1)

            if should_fetch:
                self._fetch_and_dispatch()

    def apply_settings(self, config: dict[str, object]) -> None:
        self.config = {
            "interval_seconds": int(config["interval_seconds"]),
            "alarms": list(config["alarms"]),
            "opacity": float(config["opacity"]),
            "position": str(config["position"]),
            "custom_position": self._copy_custom_position(config.get("custom_position")),
        }
        self.overlay.set_opacity(float(self.config["opacity"]))
        self.overlay.set_position(
            str(self.config["position"]),
            self._copy_custom_position(self.config.get("custom_position")),
        )
        self.alarm_engine.reset()
        self._config_changed.set()
        self.fetch_price_async()

    def open_settings(self) -> None:
        self.settings_dialog.show()

    def quit_app(self) -> None:
        if not self.running:
            return

        self.running = False
        self.tray_icon.stop()
        self.root.after(0, self._shutdown_ui)

    def on_alarm(self, alarm_price: float, current_price: float) -> None:
        message = (
            f"알람 가격 ${alarm_price:,.2f} 구간을 통과했습니다.\n"
            f"현재 BTC 가격: ${current_price:,.2f}"
        )
        messagebox.showinfo("가격 알람", message, parent=self.root)

    def on_position_change(self, position: str, custom_position: dict[str, int]) -> None:
        self.config["position"] = position
        self.config["custom_position"] = dict(custom_position)
        try:
            self.config_manager.save(self.config)
        except OSError:
            return

    def _fetch_and_dispatch(self) -> None:
        price = self.price_fetcher.get_btc_price()
        if price is None:
            self.root.after(0, lambda: self.overlay.show_error("Error"))
            return

        self.root.after(0, lambda: self._apply_price(price))

    def _apply_price(self, price: float) -> None:
        self.overlay.update_display(price, self.previous_price)
        self.previous_price = price

    def _current_alarms(self) -> list[float]:
        return list(self.config.get("alarms", []))

    def _current_config(self) -> dict[str, object]:
        return dict(self.config)

    def _shutdown_ui(self) -> None:
        self.root.quit()
        self.root.destroy()

    @staticmethod
    def _copy_custom_position(
        value: object,
    ) -> dict[str, int] | None:
        if not isinstance(value, dict):
            return None
        try:
            return {
                "x": int(value["x"]),
                "y": int(value["y"]),
            }
        except (KeyError, TypeError, ValueError):
            return None


def main() -> None:
    app = BitgetBTCTicker()
    app.run()


if __name__ == "__main__":
    main()

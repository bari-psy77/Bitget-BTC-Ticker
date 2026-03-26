from __future__ import annotations

import threading
import time
from tkinter import messagebox

from bitget_ticker.components.alarm import AlarmEngine
from bitget_ticker.components.config import ConfigManager
from bitget_ticker.components.fetcher import Candle, PriceFetcher
from bitget_ticker.components.overlay import OverlayWindow
from bitget_ticker.components.settings import SettingsDialog
from bitget_ticker.components.tray import TrayIcon


class BitgetBTCTicker:
    """Coordinate configuration, UI, tray, alarms, and price polling."""

    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self.price_fetcher = PriceFetcher(market_type=str(self.config.get("market_type", "futures")))

        self.running = True
        self.previous_price: float | None = None
        self.chart_points: list[Candle] = []
        self.update_thread: threading.Thread | None = None
        self._config_changed = threading.Event()

        self.overlay = OverlayWindow(
            opacity=float(self.config["opacity"]),
            custom_position=self._copy_custom_position(self.config.get("custom_position")),
            on_open_settings=self.open_settings,
            on_quit=self.quit_app,
            on_position_change=self.on_position_change,
            on_toggle_chart_always_visible=self.toggle_chart_always_visible,
            on_toggle_chart_hover_enabled=self.toggle_chart_hover_enabled,
            on_chart_timeframe_change=self.change_chart_timeframe,
            on_chart_panel_opened=self.request_chart_refresh,
            chart_timeframe=str(self.config.get("chart_timeframe", "15m")),
            chart_always_visible=bool(self.config.get("chart_always_visible", False)),
            chart_hover_enabled=bool(self.config.get("chart_hover_enabled", True)),
        )
        self.root = self.overlay.root

        self.alarm_engine = AlarmEngine(on_alarm=self.on_alarm)
        self.overlay.attach_alarm_engine(self.alarm_engine, self._current_alarms)
        self.overlay.update_chart_data(
            candles=[],
            timeframe=str(self.config.get("chart_timeframe", "15m")),
            market_type=str(self.config.get("market_type", "futures")),
        )

        self.settings_dialog = SettingsDialog(
            root=self.root,
            config_manager=self.config_manager,
            config_getter=self._current_config,
            on_save=self.apply_settings,
            on_preview_opacity=self.overlay.set_opacity,
        )
        self.tray_icon = TrayIcon(
            root=self.root,
            on_open_settings=self.open_settings,
            on_quit=self.quit_app,
            on_toggle_visibility=self.toggle_visibility,
        )
        self.overlay.set_chart_behavior(
            chart_always_visible=bool(self.config.get("chart_always_visible", False)),
            chart_hover_enabled=bool(self.config.get("chart_hover_enabled", True)),
        )

    def run(self) -> None:
        self.tray_icon.start()
        self.root.after(100, self.fetch_price_async)
        self.update_thread = threading.Thread(target=self.price_update_loop, daemon=True)
        self.update_thread.start()
        self.root.mainloop()

    def fetch_price_async(self, force_chart_refresh: bool = False) -> None:
        threading.Thread(
            target=self._fetch_and_dispatch,
            args=(force_chart_refresh,),
            daemon=True,
        ).start()

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
                self._fetch_and_dispatch(force_chart_refresh=False)

    def apply_settings(self, config: dict[str, object]) -> None:
        self.config = {
            "interval_seconds": int(config["interval_seconds"]),
            "market_type": str(config.get("market_type", "futures")),
            "chart_timeframe": str(config.get("chart_timeframe", "15m")),
            "chart_always_visible": bool(config.get("chart_always_visible", False)),
            "chart_hover_enabled": bool(config.get("chart_hover_enabled", True)),
            "alarms": self._copy_alarm_items(config.get("alarms")),
            "opacity": float(config["opacity"]),
            "custom_position": self._copy_custom_position(config.get("custom_position")),
        }
        self.price_fetcher.set_market_type(str(self.config["market_type"]))
        self.overlay.set_opacity(float(self.config["opacity"]))
        self.overlay.set_position(self._copy_custom_position(self.config.get("custom_position")))
        self.overlay.set_chart_behavior(
            chart_always_visible=bool(self.config.get("chart_always_visible", False)),
            chart_hover_enabled=bool(self.config.get("chart_hover_enabled", True)),
        )
        self.chart_points = []
        self.overlay.update_chart_data(
            candles=[],
            timeframe=str(self.config["chart_timeframe"]),
            market_type=str(self.config["market_type"]),
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

    def on_alarm(self, alarm_price: float, current_price: float, mode: str) -> None:
        if mode == "notification":
            self.overlay.show_notification(alarm_price, current_price)
            return

        message = (
            f"Crossed alert level ${alarm_price:,.2f}.\n"
            f"Current BTC price: ${current_price:,.2f}"
        )
        messagebox.showinfo("Price Alert", message, parent=self.root)

    def on_position_change(self, custom_position: dict[str, int]) -> None:
        self.config["custom_position"] = dict(custom_position)
        self._persist_config()

    def toggle_visibility(self) -> None:
        self.overlay.toggle_visibility()

    def toggle_chart_always_visible(self) -> None:
        self.config["chart_always_visible"] = not bool(self.config.get("chart_always_visible", False))
        self.overlay.set_chart_behavior(
            chart_always_visible=bool(self.config.get("chart_always_visible", False)),
            chart_hover_enabled=bool(self.config.get("chart_hover_enabled", True)),
        )
        self._persist_config()
        if bool(self.config.get("chart_always_visible", False)):
            self.request_chart_refresh()

    def toggle_chart_hover_enabled(self) -> None:
        self.config["chart_hover_enabled"] = not bool(self.config.get("chart_hover_enabled", True))
        self.overlay.set_chart_behavior(
            chart_always_visible=bool(self.config.get("chart_always_visible", False)),
            chart_hover_enabled=bool(self.config.get("chart_hover_enabled", True)),
        )
        self._persist_config()

    def change_chart_timeframe(self, timeframe: str) -> None:
        self.config["chart_timeframe"] = str(timeframe)
        self.chart_points = []
        self.overlay.update_chart_data(
            candles=[],
            timeframe=str(self.config.get("chart_timeframe", "15m")),
            market_type=str(self.config.get("market_type", "futures")),
        )
        self.settings_dialog.set_chart_timeframe(str(self.config["chart_timeframe"]))
        self._persist_config()
        self.request_chart_refresh()

    def request_chart_refresh(self) -> None:
        if not self.running:
            return
        self.fetch_price_async(force_chart_refresh=True)

    def _fetch_and_dispatch(self, force_chart_refresh: bool = False) -> None:
        price = self.price_fetcher.get_btc_price()
        if price is None:
            self.root.after(0, lambda: self.overlay.show_error("Error"))
            return

        if not self._should_refresh_chart(force_chart_refresh):
            self.root.after(0, lambda: self._apply_price_only(price))
            return

        timeframe = str(self.config.get("chart_timeframe", "15m"))
        market_type = str(self.config.get("market_type", "futures"))
        candles = self.price_fetcher.get_btc_candles(
            timeframe=timeframe
        )

        self.root.after(0, lambda: self._apply_market_snapshot(price, candles, timeframe, market_type))

    def _apply_price_only(self, price: float) -> None:
        self.overlay.update_display(price, self.previous_price)
        self.previous_price = price

    def _apply_market_snapshot(
        self,
        price: float,
        candles: list[tuple],
        timeframe: str,
        market_type: str,
    ) -> None:
        self.overlay.update_display(price, self.previous_price)
        self.previous_price = price
        self.chart_points = list(candles)
        self.overlay.update_chart_data(
            candles=list(self.chart_points),
            timeframe=timeframe,
            market_type=market_type,
        )

    def _should_refresh_chart(self, force_chart_refresh: bool) -> bool:
        return force_chart_refresh or self.overlay.is_chart_visible()

    def _current_alarms(self) -> list[dict[str, object]]:
        return self._copy_alarm_items(self.config.get("alarms"))

    def _current_config(self) -> dict[str, object]:
        return {
            "interval_seconds": int(self.config["interval_seconds"]),
            "market_type": str(self.config.get("market_type", "futures")),
            "chart_timeframe": str(self.config.get("chart_timeframe", "15m")),
            "chart_always_visible": bool(self.config.get("chart_always_visible", False)),
            "chart_hover_enabled": bool(self.config.get("chart_hover_enabled", True)),
            "alarms": self._copy_alarm_items(self.config.get("alarms")),
            "opacity": float(self.config["opacity"]),
            "custom_position": self._copy_custom_position(self.config.get("custom_position")),
        }

    def _persist_config(self) -> None:
        try:
            self.config = self.config_manager.save(self.config)
        except OSError:
            return

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

    @staticmethod
    def _copy_alarm_items(
        value: object,
    ) -> list[dict[str, object]]:
        if not isinstance(value, list):
            return []

        alarms: list[dict[str, object]] = []
        for alarm in value:
            if not isinstance(alarm, dict):
                continue
            try:
                price = float(alarm["price"])
            except (KeyError, TypeError, ValueError):
                continue
            alarms.append(
                {
                    "price": price,
                    "enabled": bool(alarm.get("enabled", True)),
                    "mode": "notification" if alarm.get("mode") == "notification" else "popup",
                }
            )
        return alarms


def main() -> None:
    app = BitgetBTCTicker()
    app.run()


if __name__ == "__main__":
    main()

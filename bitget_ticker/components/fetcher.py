from __future__ import annotations

from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - runtime dependency fallback
    requests = None  # type: ignore[assignment]


SPOT_TICKER_URL = "https://api.bitget.com/api/v2/spot/market/tickers"
FUTURES_TICKER_URL = "https://api.bitget.com/api/v2/mix/market/ticker"
SPOT_CANDLES_URL = "https://api.bitget.com/api/v2/spot/market/candles"
FUTURES_CANDLES_URL = "https://api.bitget.com/api/v2/mix/market/candles"
BTC_SYMBOL = "BTCUSDT"
FUTURES_PRODUCT_TYPE = "USDT-FUTURES"
DEFAULT_CANDLE_LIMIT = 40
SPOT_TIMEFRAME_GRANULARITY_MAP = {
    "5m": "5min",
    "15m": "15min",
}
FUTURES_TIMEFRAME_GRANULARITY_MAP = {
    "5m": "5m",
    "15m": "15m",
}
Candle = tuple[int, float, float, float, float]


class PriceFetcher:
    """Fetch BTC/USDT price from Bitget REST API."""

    def __init__(
        self,
        session: Any | None = None,
        timeout: int = 10,
        market_type: str = "futures",
    ) -> None:
        self.timeout = timeout
        self.market_type = self._normalize_market_type(market_type)
        if session is not None:
            self.session = session
        elif requests is not None:
            self.session = requests.Session()
        else:
            self.session = None

    def set_market_type(self, market_type: str) -> None:
        self.market_type = self._normalize_market_type(market_type)

    def get_btc_price(self) -> float | None:
        if self.session is None:
            return None

        url, params = self._build_request(self.market_type)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") != "00000":
                return None

            data = payload["data"]
            if not data:
                return None

            return float(data[0]["lastPr"])
        except Exception:
            return None

    def get_btc_candles(
        self,
        timeframe: str = "15m",
        limit: int = DEFAULT_CANDLE_LIMIT,
    ) -> list[Candle]:
        if self.session is None:
            return []

        url, params = self._build_candles_request(self.market_type, timeframe, limit)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") != "00000":
                return []

            data = payload.get("data")
            if not isinstance(data, list):
                return []

            candles: list[Candle] = []
            for row in data:
                if not isinstance(row, (list, tuple)) or len(row) < 5:
                    continue
                try:
                    candles.append(
                        (
                            int(row[0]),
                            float(row[1]),
                            float(row[2]),
                            float(row[3]),
                            float(row[4]),
                        )
                    )
                except (TypeError, ValueError):
                    continue
            candles.sort(key=lambda item: item[0])
            return candles
        except Exception:
            return []

    @staticmethod
    def _normalize_market_type(market_type: str) -> str:
        return "spot" if market_type == "spot" else "futures"

    @staticmethod
    def _normalize_timeframe(timeframe: str) -> str:
        return "5m" if timeframe == "5m" else "15m"

    @classmethod
    def _build_request(cls, market_type: str) -> tuple[str, dict[str, str]]:
        if market_type == "spot":
            return SPOT_TICKER_URL, {"symbol": BTC_SYMBOL}

        return FUTURES_TICKER_URL, {
            "symbol": BTC_SYMBOL,
            "productType": FUTURES_PRODUCT_TYPE,
        }

    @classmethod
    def _build_candles_request(
        cls,
        market_type: str,
        timeframe: str,
        limit: int,
    ) -> tuple[str, dict[str, str | int]]:
        normalized_timeframe = cls._normalize_timeframe(timeframe)

        if market_type == "spot":
            return SPOT_CANDLES_URL, {
                "symbol": BTC_SYMBOL,
                "granularity": SPOT_TIMEFRAME_GRANULARITY_MAP[normalized_timeframe],
                "limit": int(limit),
            }

        return FUTURES_CANDLES_URL, {
            "symbol": BTC_SYMBOL,
            "productType": FUTURES_PRODUCT_TYPE,
            "granularity": FUTURES_TIMEFRAME_GRANULARITY_MAP[normalized_timeframe],
            "limit": int(limit),
        }


def get_btc_price() -> float | None:
    return PriceFetcher().get_btc_price()


if __name__ == "__main__":
    price = get_btc_price()
    if price is None:
        print("BTC: unavailable")
    else:
        print(f"BTC: ${price:,.2f}")

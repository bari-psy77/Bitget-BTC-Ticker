from __future__ import annotations

from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - runtime dependency fallback
    requests = None  # type: ignore[assignment]


SPOT_TICKER_URL = "https://api.bitget.com/api/v2/spot/market/tickers"
FUTURES_TICKER_URL = "https://api.bitget.com/api/v2/mix/market/ticker"
BTC_SYMBOL = "BTCUSDT"
FUTURES_PRODUCT_TYPE = "USDT-FUTURES"


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

    @staticmethod
    def _normalize_market_type(market_type: str) -> str:
        return "spot" if market_type == "spot" else "futures"

    @classmethod
    def _build_request(cls, market_type: str) -> tuple[str, dict[str, str]]:
        if market_type == "spot":
            return SPOT_TICKER_URL, {"symbol": BTC_SYMBOL}

        return FUTURES_TICKER_URL, {
            "symbol": BTC_SYMBOL,
            "productType": FUTURES_PRODUCT_TYPE,
        }


def get_btc_price() -> float | None:
    return PriceFetcher().get_btc_price()


if __name__ == "__main__":
    price = get_btc_price()
    if price is None:
        print("BTC: unavailable")
    else:
        print(f"BTC: ${price:,.2f}")

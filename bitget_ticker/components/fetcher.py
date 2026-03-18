from __future__ import annotations

from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - runtime dependency fallback
    requests = None  # type: ignore[assignment]


BITGET_TICKER_URL = "https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT"


class PriceFetcher:
    """Fetch BTC/USDT price from Bitget REST API."""

    def __init__(self, session: Any | None = None, timeout: int = 10) -> None:
        self.timeout = timeout
        if session is not None:
            self.session = session
        elif requests is not None:
            self.session = requests.Session()
        else:
            self.session = None

    def get_btc_price(self) -> float | None:
        if self.session is None:
            return None

        try:
            response = self.session.get(BITGET_TICKER_URL, timeout=self.timeout)
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


def get_btc_price() -> float | None:
    return PriceFetcher().get_btc_price()


if __name__ == "__main__":
    price = get_btc_price()
    if price is None:
        print("BTC: unavailable")
    else:
        print(f"BTC: ${price:,.2f}")

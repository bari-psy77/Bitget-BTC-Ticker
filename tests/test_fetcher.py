from __future__ import annotations

import unittest
from unittest.mock import Mock

from bitget_ticker.components.fetcher import (
    FUTURES_TICKER_URL,
    SPOT_TICKER_URL,
    PriceFetcher,
)


class PriceFetcherTests(unittest.TestCase):
    def test_get_btc_price_defaults_to_futures_market(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "code": "00000",
            "data": [{"lastPr": "98500.12"}],
        }
        session = Mock()
        session.get.return_value = response

        fetcher = PriceFetcher(session=session)

        price = fetcher.get_btc_price()

        self.assertEqual(price, 98500.12)
        session.get.assert_called_once_with(
            FUTURES_TICKER_URL,
            params={"symbol": "BTCUSDT", "productType": "USDT-FUTURES"},
            timeout=10,
        )

    def test_get_btc_price_can_switch_to_spot_market(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "code": "00000",
            "data": [{"lastPr": "97500.01"}],
        }
        session = Mock()
        session.get.return_value = response

        fetcher = PriceFetcher(session=session)
        fetcher.set_market_type("spot")

        price = fetcher.get_btc_price()

        self.assertEqual(price, 97500.01)
        session.get.assert_called_once_with(
            SPOT_TICKER_URL,
            params={"symbol": "BTCUSDT"},
            timeout=10,
        )

    def test_get_btc_price_returns_none_when_api_reports_error(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"code": "10000", "msg": "error", "data": []}
        session = Mock()
        session.get.return_value = response

        fetcher = PriceFetcher(session=session)

        self.assertIsNone(fetcher.get_btc_price())


if __name__ == "__main__":
    unittest.main()

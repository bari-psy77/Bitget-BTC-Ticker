from __future__ import annotations

import unittest
from unittest.mock import Mock

from bitget_ticker.components.fetcher import (
    FUTURES_CANDLES_URL,
    FUTURES_TICKER_URL,
    SPOT_CANDLES_URL,
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

    def test_get_btc_candles_defaults_to_futures_market(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "code": "00000",
            "data": [
                ["1710000000000", "90000", "90500", "89500", "90300", "0", "0"],
                ["1710000900000", "90300", "91000", "90200", "90850", "0", "0"],
            ],
        }
        session = Mock()
        session.get.return_value = response

        fetcher = PriceFetcher(session=session)

        candles = fetcher.get_btc_candles()

        self.assertEqual(
            candles,
            [
                (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0),
                (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0),
            ],
        )
        session.get.assert_called_once_with(
            FUTURES_CANDLES_URL,
            params={
                "symbol": "BTCUSDT",
                "productType": "USDT-FUTURES",
                "granularity": "15m",
                "limit": 40,
            },
            timeout=10,
        )

    def test_get_btc_candles_can_switch_to_spot_market_and_timeframe(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "code": "00000",
            "data": [
                ["1710000000000", "90000", "90500", "89500", "90300", "0", "0"],
            ],
        }
        session = Mock()
        session.get.return_value = response

        fetcher = PriceFetcher(session=session)
        fetcher.set_market_type("spot")

        candles = fetcher.get_btc_candles("5m")

        self.assertEqual(candles, [(1710000000000, 90000.0, 90500.0, 89500.0, 90300.0)])
        session.get.assert_called_once_with(
            SPOT_CANDLES_URL,
            params={
                "symbol": "BTCUSDT",
                "granularity": "5min",
                "limit": 40,
            },
            timeout=10,
        )


if __name__ == "__main__":
    unittest.main()

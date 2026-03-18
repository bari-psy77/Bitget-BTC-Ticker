from __future__ import annotations

import unittest
from unittest.mock import Mock

from bitget_ticker.components.fetcher import PriceFetcher


class PriceFetcherTests(unittest.TestCase):
    def test_get_btc_price_returns_float_from_bitget_payload(self) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "code": "00000",
            "data": [{"lastPr": "98500.12"}],
        }
        session = Mock()
        session.get.return_value = response

        fetcher = PriceFetcher(session=session)

        self.assertEqual(fetcher.get_btc_price(), 98500.12)

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

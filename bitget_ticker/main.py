from __future__ import annotations

import logging
import sys
from pathlib import Path

from bitget_ticker.ticker import main


def _setup_logging() -> None:
    log_path = Path.home() / ".bitget_ticker.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(str(log_path), encoding="utf-8"),
        ],
    )
    sys.excepthook = _log_unhandled_exception


def _log_unhandled_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_tb: object,
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logging.getLogger("bitget_ticker").critical(
        "Unhandled exception", exc_info=(exc_type, exc_value, exc_tb),
    )


if __name__ == "__main__":
    _setup_logging()
    logging.getLogger("bitget_ticker").info("Application starting")
    main()

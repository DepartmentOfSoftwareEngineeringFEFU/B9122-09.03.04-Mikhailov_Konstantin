import argparse
from loguru import logger

from forecasting_service.utils.logging_setup import setup_logging
from forecasting_service.data.storage import FlatStorage
from forecasting_service.parsers.domclick.parser import (
    DomclickListingParser,
)


def main():
    parser = argparse.ArgumentParser(
        description="Сбор деталей DomClick"
    )
    parser.add_argument(
        "--dc-cookie",
        type=str,
        required=True,
        help="qrator_jsid2 cookie из браузера",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=100,
        help="Макс. объявлений за сессию",
    )
    parser.add_argument(
        "--db",
        default="flats.db",
        help="Имя файла БД",
    )

    args = parser.parse_args()
    setup_logging(log_prefix="dc_details")

    storage = FlatStorage(db_name=args.db)

    dc_parser = DomclickListingParser(
        qrator_cookie=args.dc_cookie,
        storage=storage,
    )

    try:
        dc_parser.collect_details(batch_size=args.batch)
    finally:
        dc_parser.close()
        storage.close()


if __name__ == "__main__":
    main()
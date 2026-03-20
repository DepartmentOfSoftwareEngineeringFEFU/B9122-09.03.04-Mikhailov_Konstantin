import argparse
import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | {message}"
    ),
    level="INFO",
)
logger.add(
    "logs/listings_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    rotation="10 MB",
)


def main():
    parser = argparse.ArgumentParser(
        description="Фаза 1: Сбор листинга ЦИАН"
    )
    parser.add_argument(
        "--location", default="Владивосток",
    )
    parser.add_argument(
        "--pages", type=int, nargs=2, default=[1, 54],
        metavar=("START", "END"),
    )
    parser.add_argument(
        "--rooms", nargs="+", default=["1", "2", "3"],
    )
    parser.add_argument(
        "--headless", action="store_true",
    )
    parser.add_argument(
        "--db", default="flats.db",
        help="Имя файла БД",
    )

    args = parser.parse_args()

    rooms = []
    for r in args.rooms:
        rooms.append("studio" if r == "studio" else int(r))

    logger.info("═" * 60)
    logger.info(" ФАЗА 1: СБОР ЛИСТИНГА")
    logger.info(f"   Город:    {args.location}")
    logger.info(f"   Стр.:     {args.pages[0]}–{args.pages[1]}")
    logger.info(f"   Комнаты:  {rooms}")
    logger.info(f"   БД:       {args.db}")
    logger.info("═" * 60)

    from forecasting_service.parsers.cian.parser import (
        CianListingParser,
    )
    from forecasting_service.data.storage import FlatStorage

    storage = FlatStorage(db_name=args.db)

    cian = CianListingParser(
        location=args.location,
        headless=args.headless,
        storage=storage,
    )

    cian.collect(
        rooms=tuple(rooms),
        start_page=args.pages[0],
        end_page=args.pages[1],
    )

    storage.close()


if __name__ == "__main__":
    main()
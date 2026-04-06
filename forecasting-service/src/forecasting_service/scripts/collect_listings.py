import argparse

from forecasting_service.utils.logging_setup import setup_logging
from forecasting_service.data.collector import DataCollector

from loguru import logger


def _parse_rooms(raw: list[str]) -> tuple:
    result = []
    for r in raw:
        result.append("studio" if r == "studio" else int(r))
    return tuple(result)


def main():
    parser = argparse.ArgumentParser(
        description="Фаза 1: Сбор листинга ЦИАН"
    )
    parser.add_argument(
        "--location", default="Владивосток",
        help="Город (по умолчанию: Владивосток)",
    )
    parser.add_argument(
        "--pages", type=int, nargs=2, default=[1, 54],
        metavar=("START", "END"),
        help="Диапазон страниц",
    )
    parser.add_argument(
        "--rooms", nargs="+", default=["1", "2", "3"],
        help="Комнатность (1 2 3 studio)",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Headless режим",
    )
    parser.add_argument(
        "--db", default="flats.db",
        help="Имя файла БД",
    )
    parser.add_argument(
        "--source", 
        choices=["cian", "domclick"], 
        default="cian"
    )
    parser.add_argument(
        "--dc-cookie", 
        type=str, 
        help="qrator_jsid2 cookie для ДомКлика"
    )


    args = parser.parse_args()

    setup_logging(log_prefix="listings")

    rooms = _parse_rooms(args.rooms)

    with DataCollector(
        location=args.location,
        db_name=args.db,
    ) as collector:
        if args.source == "domclick":
            if not args.dc_cookie:
                logger.error("Для ДомКлика обязателен аргумент --dc-cookie")
                return
                
            from forecasting_service.parsers.domclick.parser import DomclickListingParser
            from forecasting_service.data.storage import FlatStorage
            
            storage = FlatStorage(args.db)
            parser = DomclickListingParser(qrator_cookie=args.dc_cookie, storage=storage)
            parser.collect(rooms=rooms, start_page=args.pages[0], end_page=args.pages[1])
            logger.info(f"Итого в БД: {storage.get_stats()}")
            
        else:
            collector.collect_listings(
                rooms=rooms,
                start_page=args.pages[0],
                end_page=args.pages[1],
                headless=args.headless,
            )


if __name__ == "__main__":
    main()
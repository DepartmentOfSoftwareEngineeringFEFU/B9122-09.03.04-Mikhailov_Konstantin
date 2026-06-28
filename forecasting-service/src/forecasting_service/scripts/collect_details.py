import argparse

from forecasting_service.utils.logging_setup import setup_logging

from forecasting_service.data.collector import DataCollector

def main():

    parser = argparse.ArgumentParser(

        description="Фаза 2: Сбор деталей объявлений"

    )

    parser.add_argument(

        "--db", default="flats.db",

        help="Имя файла БД",

    )

    parser.add_argument(

        "--batch", type=int, default=5,

        help="Макс. объявлений за сессию",

    )

    parser.add_argument(

        "--min-delay", type=float, default=10.0,

        help="Минимальная задержка между запросами (сек)",

    )

    parser.add_argument(

        "--max-delay", type=float, default=15.0,

        help="Максимальная задержка между запросами (сек)",

    )

    parser.add_argument(

        "--restart-every", type=int, default=5,

        help="Рестарт браузера каждые N объявлений",

    )

    parser.add_argument(

        "--headless", action="store_true",

        help="Headless режим (НЕ рекомендуется для деталей)",

    )

    parser.add_argument(

        "--reset-blocked", action="store_true",

        help="Сбросить blocked → pending перед запуском",

    )

    parser.add_argument(

        "--max-captcha", type=int, default=10,

        help="Макс. CAPTCHA до остановки",

    )

    args = parser.parse_args()

    setup_logging(log_prefix="details")

    if args.headless:

        from loguru import logger

        logger.warning(

            "  Headless режим! CAPTCHA нельзя пройти вручную. "

            "Рекомендуется запуск БЕЗ --headless"

        )

    with DataCollector(db_name=args.db) as collector:

        collector.collect_details(

            batch_size=args.batch,

            detail_delay=(args.min_delay, args.max_delay),

            restart_every=args.restart_every,

            headless=args.headless,

            reset_blocked=args.reset_blocked,

            max_captcha=args.max_captcha,

        )

if __name__ == "__main__":

    main()

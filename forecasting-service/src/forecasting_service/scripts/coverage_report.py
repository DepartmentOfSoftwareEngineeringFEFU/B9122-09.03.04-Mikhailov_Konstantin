import argparse

from forecasting_service.utils.logging_setup import setup_logging
from forecasting_service.data.collector import DataCollector


def main():
    parser = argparse.ArgumentParser(
        description="Отчёт о покрытии датасета"
    )
    parser.add_argument(
        "--db", default="flats.db",
        help="Имя файла БД",
    )

    args = parser.parse_args()

    setup_logging(log_prefix="coverage", console_level="WARNING")

    with DataCollector(db_name=args.db) as collector:
        collector.print_coverage()


if __name__ == "__main__":
    main()
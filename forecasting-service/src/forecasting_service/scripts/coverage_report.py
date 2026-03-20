import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="{message}")


def main():
    from forecasting_service.data.storage import FlatStorage

    storage = FlatStorage()

    stats = storage.get_stats()
    coverage = storage.get_coverage()

    print("\n" + "═" * 60)
    print(" ОТЧЁТ О СОСТОЯНИИ ДАТАСЕТА")
    print("═" * 60)

    print(f"\n Всего объявлений: {stats['total']}")
    print(f"    Done:    {stats['done']}")
    print(f"    Pending: {stats['pending']}")
    print(f"    Failed:  {stats['failed']}")
    print(f"    Blocked: {stats['blocked']}")

    if not coverage:
        print("\n Нет данных для покрытия")
        return

    total = stats["total"]
    done_pct = (
        stats["done"] / total * 100 if total else 0
    )

    print(f"\n Покрытие деталями: {done_pct:.1f}%")
    print(f"\n{'Поле':<25} {'Заполнено':>10} {'%':>8}")
    print("─" * 50)

    for field, pct in sorted(
        coverage.items(), key=lambda x: -x[1]
    ):
        filled = int(pct / 100 * total)
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"   {field:<22} {bar} {filled:>5}/{total}  {pct:>5.1f}%")

    # Подсветка критичных полей для ML
    critical_fields = [
        "price", "total_meters", "rooms_count",
        "district", "floor", "floors_count",
        "year_of_construction", "house_material_type",
        "finish_type",
    ]

    print(f"\n Критичные поля для ML:")
    for field in critical_fields:
        pct = coverage.get(field, 0)
        status = "" if pct >= 75 else "" if pct >= 50 else ""
        print(f"   {status} {field:<25} {pct:.1f}%")

    storage.close()


if __name__ == "__main__":
    main()
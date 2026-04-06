def progress_bar(pct: float, width: int = 20) -> str:
    filled = int(pct / (100 / width))
    filled = max(0, min(filled, width))
    return "█" * filled + "░" * (width - filled)


def format_stats_block(stats: dict, title: str = "СОСТОЯНИЕ БД") -> str:
    lines = [
        f"\n{'═' * 50}",
        f"  {title}:",
        f"  Всего:   {stats.get('total', 0)}",
        f"  Pending: {stats.get('pending', 0)}",
        f"  Done:    {stats.get('done', 0)}",
        f"  Failed:  {stats.get('failed', 0)}",
        f"  Blocked: {stats.get('blocked', 0)}",
        f"{'═' * 50}",
    ]
    return "\n".join(lines)


def format_coverage_block(coverage: dict, total: int) -> str:
    if not coverage:
        return "  Нет данных о покрытии"

    lines = [f"\n  {'Поле':<25} {'Покрытие':>10}",  "─" * 50]

    for field, pct in sorted(coverage.items(), key=lambda x: -x[1]):
        filled = int(pct / 100 * total)
        bar = progress_bar(pct)
        lines.append(f"  {field:<22} {bar} {filled:>4}/{total} {pct:>5.1f}%")

    return "\n".join(lines)


def format_critical_fields(
    coverage: dict,
    critical_fields: tuple[str, ...],
) -> str:
    lines = ["\n  Критичные поля для ML:"]

    for field in critical_fields:
        pct = coverage.get(field, 0)
        status = "Good" if pct >= 75 else "Warning" if pct >= 50 else "Bad"
        lines.append(f"  {status} {field:<25} {pct:.1f}%")

    return "\n".join(lines)


def format_session_report(
    processed: int,
    success: int,
    captcha_count: int,
    multiplier: float,
    stats: dict,
    coverage: dict | None = None,
) -> str:
    lines = [
        f"\n{'═' * 60}",
        "  РЕЗУЛЬТАТ СЕССИИ",
        f"  Обработано: {processed}",
        f"  Успешно:    {success}",
        f"  CAPTCHA:    {captcha_count}",
        f"  Множитель:  ×{multiplier:.1f}",
        f"\n  СОСТОЯНИЕ БД",
        f"  Всего:   {stats.get('total', 0)}",
        f"  Done:    {stats.get('done', 0)}",
        f"  Pending: {stats.get('pending', 0)}",
        f"  Failed:  {stats.get('failed', 0)}",
        f"  Blocked: {stats.get('blocked', 0)}",
    ]

    if coverage:
        lines.append(f"\n  ПОКРЫТИЕ ПОЛЕЙ")
        for field, pct in sorted(coverage.items(), key=lambda x: -x[1]):
            bar = progress_bar(pct)
            lines.append(f"  {field:<25} {bar} {pct}%")

    lines.append(f"{'═' * 60}")
    return "\n".join(lines)
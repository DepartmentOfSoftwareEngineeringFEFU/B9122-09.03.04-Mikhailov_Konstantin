import json

import sqlite3

from pathlib import Path

from loguru import logger

from forecasting_service.parsers.domclick.http_client import DomclickClient

from forecasting_service.parsers.domclick.ssr_state import extract_ssr_state

from forecasting_service.data.storage import FlatStorage

from forecasting_service.config import DEFAULT_DB_NAME

QRATOR_JSID = "v2.0.1775797162.167.57e14b78fcCOW2mA|lM7O4rTHxVK9cCDB|7BCJdHavBGYsyrNYLYo6PkPtSCc4+6GsBHaAUAZIm0tLu2jNpZXhogqcOWjy2HaHo1RqxsgdWVV/bPhc8i3gliR4vRzfLJrjtOtuzUUi6ChqZeiYYj6rkvyGFQ8Fl3gaq7lqM+7ADZ3j8fmH2CT6kSSt6YzBV8NC32FizfPGddQ=-dJMZyaegS0mn8o0seK1wwptvlRY="

OUTPUT_DIR = "debug_ssr_states"

def run_debug_dump():

    output_path = Path(OUTPUT_DIR)

    output_path.mkdir(exist_ok=True)

    storage = FlatStorage(db_name=DEFAULT_DB_NAME)

    client = DomclickClient(QRATOR_JSID)

    conn = storage._get_conn()

    query = "SELECT id, url FROM flats WHERE url LIKE '%domclick.ru%'"

    rows = conn.execute(query).fetchall()

    logger.info(f"Начинаю обработку {len(rows)} объектов...")

    try:

        for row in rows:

            flat_id, url = row['id'], row['url']

            logger.info(f"[{flat_id}] Загрузка: {url}")

            try:

                html = client.get_page(url)

                raw_ssr = extract_ssr_state(html)

                if not raw_ssr:

                    logger.warning(f"  [!] SSR не найден для ID {flat_id}. Возможно, Qrator заблокировал запрос.")

                    (output_path / f"error_{flat_id}.html").write_text(html, encoding="utf-8")

                    continue

                if isinstance(raw_ssr, dict):

                    ssr_str = json.dumps(raw_ssr)

                else:

                    ssr_str = str(raw_ssr)

                clean_json_str = ssr_str.replace(": undefined", ": null")

                try:

                    final_data = json.loads(clean_json_str)

                    file_path = output_path / f"state_{flat_id}.json"

                    with open(file_path, "w", encoding="utf-8") as f:

                        json.dump(final_data, f, ensure_ascii=False, indent=4)

                    logger.success(f"  [+] Сохранено: {file_path.name}")

                except json.JSONDecodeError as je:

                    logger.error(f"  [!] Ошибка декодирования JSON для ID {flat_id}: {je}")

                    (output_path / f"raw_bad_{flat_id}.txt").write_text(clean_json_str, encoding="utf-8")

            except Exception as e:

                logger.error(f"  [!] Ошибка при запросе {flat_id}: {e}")

    finally:

        storage.close()

        logger.info("Скрипт завершил работу.")

if __name__ == "__main__":

    if QRATOR_JSID == "":

        logger.critical("НЕОБХОДИМО ВСТАВИТЬ QRATOR_JSID В СКРИПТ!")

    else:

        run_debug_dump()

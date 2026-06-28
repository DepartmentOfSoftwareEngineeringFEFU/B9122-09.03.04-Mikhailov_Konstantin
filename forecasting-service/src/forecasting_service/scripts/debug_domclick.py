import requests

QRATOR_COOKIE = "v2.0.1775797162.167.57e14b78fcCOW2mA|lM7O4rTHxVK9cCDB|7BCJdHavBGYsyrNYLYo6PkPtSCc4+6GsBHaAUAZIm0tLu2jNpZXhogqcOWjy2HaHo1RqxsgdWVV/bPhc8i3gliR4vRzfLJrjtOtuzUUi6ChqZeiYYj6rkvyGFQ8Fl3gaq7lqM+7ADZ3j8fmH2CT6kSSt6YzBV8NC32FizfPGddQ=-dJMZyaegS0mn8o0seK1wwptvlRY="

cookies = {

    "qrator_jsid2": QRATOR_COOKIE,

}

headers = {

    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",

    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",

    "Accept-Encoding": "gzip, deflate, br",

    "Sec-Fetch-Dest": "document",

    "Sec-Fetch-Mode": "navigate",

    "Sec-Fetch-Site": "none",

    "Sec-Fetch-User": "?1",

}

url = (

    "https://vladivostok.domclick.ru/search?"

    "deal_type=sale&category=living"

    "&offer_type=flat&offer_type=layout"

    "&aids=57471&rooms=1&offset=0"

)

detail_url = "https://vladivostok.domclick.ru/card/sale__new_flat__2074994630"

resp2 = requests.get(detail_url, headers=headers, cookies=cookies)

print(f"\nDetail Status: {resp2.status_code}")

print(f"Detail Length: {len(resp2.text)}")

print(f"Has building-info: {'building-info-block' in resp2.text}")

with open("domclick_detail_test.html", "w", encoding="utf-8") as f:

    f.write(resp2.text)

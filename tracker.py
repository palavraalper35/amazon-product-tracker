import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

AMAZON_URL = "https://www.amazon.com.tr/s?i=computers&srs=44219324031&bbn=44219324031&rh=n%3A44219324031&s=date-desc-rank&dc&ds=v1%3ArZP2GkQs4E5JYA%2BXl%2FaEfcb4TtVHvghUqIlBRS1yKxk&qid=1795073918&ref=sr_ex_n_1"
STATE_FILE = "products.json"

def get_products():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9"
    }

    response = requests.get(AMAZON_URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    products = {}

    for item in soup.select('[data-asin]'):
        asin = item.get("data-asin", "").strip()

        if not asin or len(asin) != 10:
            continue

        title_element = item.select_one("h2 a")
        if not title_element:
            continue

        title = title_element.get_text(" ", strip=True)
        link = title_element.get("href")

        if title and link:
            products[asin] = {
                "title": title,
                "url": urljoin("https://www.amazon.com.tr", link)
            }

    if len(products) < 5:
        raise RuntimeError(
            f"Amazon sayfası düzgün okunamadı. Bulunan ürün: {len(products)}"
        )

    return products

def send_telegram(message):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=30
    )
    response.raise_for_status()

def main():
    current = get_products()

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            previous = json.load(f)
    else:
        previous = None

    # İlk çalıştırma: mevcut ürünleri kaydet, bildirim gönderme.
    if previous is None:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        print(f"İlk kayıt tamamlandı: {len(current)} ürün.")
        return

    new_asins = set(current) - set(previous)

    for asin in new_asins:
        product = current[asin]
        message = (
            "🆕 AMAZON'A YENİ ÜRÜN EKLENDİ!\n\n"
            f"{product['title']}\n\n"
            f"{product['url']}"
        )
        send_telegram(message)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    print(f"Kontrol tamamlandı: {len(current)} ürün, {len(new_asins)} yeni ürün.")

if __name__ == "__main__":
    main()

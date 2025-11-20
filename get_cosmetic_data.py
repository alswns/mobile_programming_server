import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.oliveyoung.co.kr"
RANK_URL = f"{BASE_URL}/store/main/getBestList.do"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/110.0.0.0 Safari/537.36"),
    "Referer": "https://www.oliveyoung.co.kr",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

def fetch_rankings():
    res = requests.get(RANK_URL, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "lxml")

    items = []
    for card in soup.select(".outlook-card"):  # 실제 클래스 이름은 서비스에 따라 다름
        name = card.select_one(".name").get_text(strip=True)
        rating_tag = card.select_one(".star-rating")
        rating = float(rating_tag["data-rating"]) if rating_tag else None
        price = card.select_one(".price").get_text(strip=True)
        img_url = card.select_one("img")["src"]

        items.append({
            "name": name,
            "rating": rating,
            "price": price,
            "image_url": img_url
        })

        if len(items) >= 100:
            break

    return items

def main():
    rankings = fetch_rankings()
    with open("oliveyoung_rankings.json", "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

    print("JSON 파일 저장 완료. 파일명: oliveyoung_rankings.json")

if __name__ == "__main__":
    main()
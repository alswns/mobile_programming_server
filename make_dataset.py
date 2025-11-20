import os
import requests
from typing import List, Dict, Optional
import pandas as pd


RAPIDAPI_KEY = "0e20c9c57emsh4525ea6f0dd288cp17bdb6jsn11ac75c63e28"
RAPIDAPI_HOST ="sephora.p.rapidapi.com"
RAPIDAPI_SEPHORA_URL = "https://sephora.p.rapidapi.com/us/products/v2/list"   # 필요하면 설정

# zsh에서 세션에 설정 (영구 저장하려면 ~/.zshrc에 추가)



def _headers():
    headers = {}
    if RAPIDAPI_KEY:
        headers['x-rapidapi-key'] = RAPIDAPI_KEY
    if RAPIDAPI_HOST:
        headers['x-rapidapi-host'] = RAPIDAPI_HOST
    return headers
def _params():
    params = {
        'currentPage': 1,
        'categoryId': 'cat150006'  # categoryId는 필요에 따라 변경 가능
    }
    return params


def fetch_products_from_sephora(currentPage: int = 1, keyword: Optional[str] = None) -> List[Dict]:
    """Fetch products from Sephora via RapidAPI.

    Notes:
    - You must set environment variables `RAPIDAPI_KEY` and `RAPIDAPI_SEPHORA_URL` (and optionally `RAPIDAPI_HOST`).
    - `RAPIDAPI_SEPHORA_URL` should be the full RapidAPI endpoint URL for product listing (from the playground link).
    - This function attempts a GET request with `limit` and `keyword` as query params.

    Returns a list of product dicts in a normalized format (best-effort). If the request fails or
    environment is not configured, returns an empty list.
    """
    if not RAPIDAPI_SEPHORA_URL or not RAPIDAPI_KEY:
        return []

    params = _params()  # categoryId는 필요에 따라 변경 가능
    params['currentPage'] = currentPage

    if keyword:
        params['keyword'] = keyword
    
    try:
        resp = requests.get(RAPIDAPI_SEPHORA_URL, headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
    except Exception as e:
        print(f"Error fetching products from Sephora: {e}")
        return []

    # The exact shape of the RapidAPI Sephora response can vary; try to extract common fields
    products = []
    items = []
    # try common locations
    if isinstance(data, dict):
        # search for list-like values
        for key in ('products', 'items', 'result', 'data'):
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        # sometimes API returns list at top
        if not items:
            for v in data.values():
                if isinstance(v, list):
                    items = v
                    break
    elif isinstance(data, list):
        items = data

    for it in items:
        try:
            # best-effort normalization
            pid = it.get('productId')
            image_url= it.get('heroImage') or it.get('altImage')
            name = it.get('displayName')
            brand = it.get('brandName')
            rating = None
            if it.get('rating'):
                try:
                    rating = float(it.get('rating'))
                except Exception:
                    rating = None
            try:
                reviews = it.get('reviews')
            except Exception:
                reviews = None

            target_url= it.get('targetUrl')
            sku= it.get('currentSku')

            price = None
            # price may be nested
            listPrice=sku.get('listPrice')
            skuId=sku.get('skuId')

            products.append({
                'product_id': pid,
                'product_name': name,
                'brand_name': brand,
                'rating': rating,
                'reviews': reviews,
                'image_url': image_url,
                'target_url': target_url,
                'listPrice': listPrice,
                'skuId': skuId
            })
        except Exception:
            continue

    return products


if __name__ == "__main__":
    # Example usage
    i=3
    for j in range(i,61):
            print(f"Fetching products from Sephora, page {j}...")
            products = fetch_products_from_sephora(currentPage=j)
            print(f"Fetched {len(products)} products from Sephora.")
            pd.DataFrame(products).to_csv(f"./dataset/sephora/sephora_products_page{j}.csv", index=False)
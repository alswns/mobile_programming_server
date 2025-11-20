
from typing import List, Dict, Optional
import requests
RAPIDAPI_KEY = "0e20c9c57emsh4525ea6f0dd288cp17bdb6jsn11ac75c63e28"
RAPIDAPI_HOST ="sephora.p.rapidapi.com"
RAPIDAPI_SEPHORA_URL = "https://sephora.p.rapidapi.com/us/products/v2/detail"   # 필요하면 설정

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
        'productId': None,
        'preferedSku': None  # categoryId는 필요에 따라 변경 가능
    }
    return params


def get_detail_from_sephora(productId:str,preferedSku:str) -> List[Dict]:
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
    if productId == None or preferedSku ==None:
        return []
    params['productId'] = productId
    params['preferedSku'] = preferedSku

    
    try:
        resp = requests.get(RAPIDAPI_SEPHORA_URL, headers=_headers(), params=params, timeout=10)
        print(resp.url)
        resp.raise_for_status()
        data = resp.json()
        
    except Exception as e:
        print(f"Error fetching products from Sephora: {e}")
        return []

    return data
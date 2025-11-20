import requests
import json
from bs4 import BeautifulSoup

def scrape_hwahae_from_html(url):
    """
    화해 랭킹 페이지의 HTML에 포함된 초기 데이터를 스크래핑합니다.
    Next.js 앱의 __NEXT_DATA__ 스크립트 태그에 포함된 JSON을 추출하는 방식입니다.
    
    Args:
        url (str): 크롤링할 화해 랭킹 페이지 URL.
    
    Returns:
        list: 수집된 제품 정보 딕셔너리의 리스트.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"URL에서 데이터 스크래핑을 시작합니다: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Next.js 앱은 __NEXT_DATA__ 라는 id를 가진 script 태그에 초기 데이터를 저장합니다.
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not next_data_script:
            print("페이지에서 '__NEXT_DATA__' 스크립트를 찾을 수 없습니다. 웹사이트 구조가 변경되었을 수 있습니다.")
            return []
            
        # 스크립트 태그의 내용을 JSON으로 파싱
        preloaded_data = json.loads(next_data_script.string)
        
        # JSON 데이터 구조를 탐색하여 제품 목록 찾기
        # 구조: props -> pageProps -> dehydratedState -> queries -> [N] -> state -> data -> body -> items
        items = []
        queries = preloaded_data.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', [])
        for query in queries:
            if 'rankings/themed' in query.get('queryKey', [''])[0]:
                 # 페이지 데이터가 여러 개 있을 수 있으므로 'pages'를 순회
                pages = query.get('state', {}).get('data', {}).get('pages', [])
                for page in pages:
                    page_items = page.get('body', {}).get('items', [])
                    if page_items:
                        items.extend(page_items)

        if not items:
            print("JSON 데이터에서 제품 목록을 찾을 수 없습니다. 데이터 구조를 확인하세요.")
            return []

        print(f"총 {len(items)}개의 제품 정보를 찾았습니다. 데이터를 가공합니다.")
        
        all_products = []
        for item in items:
            product_info = {
                "rank": item.get("rank"),
                "brand": item.get("brand", {}).get("name", "N/A"),
                "product_name": item.get("name", "N/A"),
                "volume": item.get("volume", "N/A"),
                "price": item.get("price", 0)
            }
            all_products.append(product_info)
            
        return all_products

    except requests.exceptions.RequestException as e:
        print(f"페이지를 가져오는 중 오류가 발생했습니다: {e}")
        return []
    except json.JSONDecodeError:
        print("JSON 데이터를 파싱하는 데 실패했습니다.")
        return []
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")
        return []

def save_to_json(data, filename):
    """
    데이터를 JSON 파일로 저장합니다.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"총 {len(data)}개의 제품 정보가 '{filename}' 파일에 성공적으로 저장되었습니다.")
    except IOError as e:
        print(f"파일 저장 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    TARGET_URL = "https://www.hwahae.co.kr/rankings?english_name=skin&theme_id=174"
    OUTPUT_FILENAME = "hwahae_ranking.json"
    
    ranked_products = scrape_hwahae_from_html(TARGET_URL)
    
    if ranked_products:
        save_to_json(ranked_products, OUTPUT_FILENAME)
    else:
        print("수집된 제품 정보가 없어 파일을 저장하지 않았습니다.")
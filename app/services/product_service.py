import csv
import ast
import os
from app.utils.apis import get_detail_from_sephora
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset', 'product_info.csv')

_PRODUCTS = None

class ProductService:
    @staticmethod
    def _safe_parse_list_field(value):
        if not value:
            return []
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed]
        except Exception:
            # fallback: try to split on common separators
            v = value.strip()
            if v.startswith("[") and v.endswith("]"):
                v = v[1:-1]
            parts = [p.strip().strip("'\"") for p in v.split(",") if p.strip()]
            return parts
        return []

    @staticmethod
    def load_products(csv_path=None):
        global _PRODUCTS
        if _PRODUCTS is not None:
            return _PRODUCTS
        path = csv_path or DATASET_PATH
        products = []
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # normalize some fields
                    row['rating'] = float(row.get('rating') or 0)
                    row['loves_count'] = int(row.get('loves_count') or 0)
                    row['highlights_parsed'] = _safe_parse_list_field(row.get('highlights', ''))
                    row['ingredients_parsed'] = _safe_parse_list_field(row.get('ingredients', ''))
                    row['primary_category'] = row.get('primary_category') or ''
                    # try to parse price fields if present
                    try:
                        row['price_usd'] = float(row.get('price_usd')) if row.get('price_usd') else None
                    except Exception:
                        row['price_usd'] = None
                    products.append(row)
        except FileNotFoundError:
            _PRODUCTS = []
            return _PRODUCTS
        _PRODUCTS = products
        return _PRODUCTS

    @staticmethod
    def _build_keywords(skin_info):
        # Accepts skin_info like {'skin_type':'dry', 'concerns':['acne','sensitivity']}
        keywords = []
        st = (skin_info.get('skin_type') or '').lower()
        concerns = [c.lower() for c in (skin_info.get('concerns') or [])]
        if st:
            keywords.append(st)
            if st == 'dry':
                keywords += ['dryness', 'hydrating']
            if st == 'oily':
                keywords += ['oil', 'oily']
            if st == 'sensitive':
                keywords += ['sensitive', 'soothing']
        for c in concerns:
            keywords.append(c)
        # dedupe
        return list(dict.fromkeys([k for k in keywords if k]))

    @staticmethod
    def recommend_products(skin_info: dict, top_n: int = 10, csv_path: str = None):
        """Return a list of product dicts best matching the provided skin_info.

        skin_info example: {'skin_type':'dry', 'concerns':['acne','sensitivity']}
        """
        products = load_products(csv_path)
        if not products:
            return []

        # extended scoring: consider highlights, ingredients, name and category
        keywords = _build_keywords(skin_info)
        avoid_ingredients = [i.lower() for i in (skin_info.get('avoid_ingredients') or [])]
        price_min = skin_info.get('price_min')
        price_max = skin_info.get('price_max')

        results = []
        for p in products:
            # price filtering
            p_price = p.get('price_usd')
            if p_price is not None:
                if price_min is not None and p_price < price_min:
                    continue
                if price_max is not None and p_price > price_max:
                    continue

            ing_list = [i.lower() for i in (p.get('ingredients_parsed') or [])]
            # skip if contains avoided ingredients
            if avoid_ingredients:
                if any(ai in ing for ai in avoid_ingredients for ing in ing_list):
                    continue

            score = 0.0
            hl = ' '.join(p.get('highlights_parsed') or []).lower()
            name = (p.get('product_name') or '').lower()
            cat = (p.get('primary_category') or '').lower()

            for kw in keywords:
                # strong match when highlights explicitly mark Good for
                if f'good for: {kw}' in hl:
                    score += 25
                if kw in hl:
                    score += 15
                if kw in name or kw in cat:
                    score += 7
                # ingredients match is supportive signal
                if any(kw in ing for ing in ing_list):
                    score += 3

            # small category boost
            preferred_category = (skin_info.get('primary_category') or '').lower()
            if preferred_category and preferred_category in cat:
                score += 8

            # popularity and rating bumps
            try:
                rating = float(p.get('rating') or 0)
            except Exception:
                rating = 0.0
            loves = int(p.get('loves_count') or 0)
            score += rating * 2.0
            score += min(loves / 200.0, 8.0)

            if score > 0:
                results.append((score, p))

        # sort by score descending then loves_count then rating
        results.sort(key=lambda x: (x[0], x[1].get('loves_count', 0), x[1].get('rating', 0)), reverse=True)

        out = []
        for score, p in results[:top_n]:
            out.append({
                'product_id': p.get('product_id'),
                'product_name': p.get('product_name'),
                'brand_name': p.get('brand_name'),
                'rating': p.get('rating'),
                'loves_count': p.get('loves_count'),
                'primary_category': p.get('primary_category'),
                'highlights': p.get('highlights_parsed'),
                'ingredients': p.get('ingredients_parsed'),
                'price_usd': p.get('price_usd'),
                'score': round(score, 2)
            })

        return out

    @staticmethod
    def get_global_ranking(top_n: int = 20, csv_path: str = None):
        """
        Return top N products across all users by a simple popularity+rating score.
        ---
        200:
        top_n: number of products to return
        csv_path: optional path to product_info.csv
        Returns: list of product dicts
        
        
        """

        # Prefer product_item.csv when available (contains image_url, target_url, reviews)
        product_item_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset', 'product_item.csv')
        products = []
        if os.path.exists(product_item_path):
            # load product_item.csv
            try:
                with open(product_item_path, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # normalize fields
                        # product_item.csv has columns: product_id,product_name,brand_name,rating,reviews,image_url,target_url,listPrice,skuId
                        try:
                            row['rating'] = float(row.get('rating') or 0)
                        except Exception:
                            row['rating'] = 0.0
                        try:
                            # 'reviews' column stores review count
                            row['reviews'] = int(row.get('reviews') or 0)
                        except Exception:
                            row['reviews'] = 0
                        row['image_url'] = row.get('image_url')
                        row['target_url'] = row.get('target_url')
                        row['listPrice'] = row.get('listPrice')
                        products.append(row)
            except Exception:
                products = load_products(csv_path)
        else:
            products = load_products(csv_path)
        if not products:
            return []

        scored = []
        for p in products:
            try:
                rating = float(p.get('rating') or 0)
            except Exception:
                rating = 0.0
            # use 'reviews' if present (product_item.csv), otherwise fall back to loves_count
            if p.get('reviews') is not None:
                pop = int(p.get('reviews') or 0)
            else:
                pop = int(p.get('loves_count') or 0)
            # Simple score: rating weighted + popularity with diminishing returns
            score = rating * 3.0 + min(pop / 100.0, 20.0)
            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, p in scored[:top_n]:
            out.append({
                'product_id': p.get('product_id'),
                'product_name': p.get('product_name'),
                'brand_name': p.get('brand_name'),
                'rating': p.get('rating'),
                # include reviews count when available
                'reviews': p.get('reviews') if p.get('reviews') is not None else p.get('loves_count'),
                'primary_category': p.get('primary_category'),
                'price_usd': p.get('price_usd') or p.get('listPrice'),
                'image_url': p.get('image_url'),
                'target_url': p.get('target_url'),
                'skuId': p.get('skuId'),
                'score': round(score, 2)
            })
        return out

    @staticmethod
    def score_products_and_rank(products: list, top_n: int = 20):
        """Score an external list of product dicts and return top_n in same shape as get_global_ranking."""
        scored = []
        for p in products:
            try:
                rating = float(p.get('rating') or 0)
            except Exception:
                rating = 0.0
            loves = int(p.get('loves_count') or 0) if p.get('loves_count') is not None else 0
            score = rating * 3.0 + min(loves / 100.0, 20.0)
            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, p in scored[:top_n]:
            out.append({
                'product_id': p.get('product_id'),
                'product_name': p.get('product_name'),
                'brand_name': p.get('brand_name'),
                'rating': p.get('rating'),
                'loves_count': p.get('loves_count'),
                'primary_category': p.get('primary_category'),
                'price_usd': p.get('price_usd'),
                
                'score': round(score, 2)
            })
        return out

    @staticmethod
    def _strip_html_tags(text: str):
        import re
        if not text:
            return ''
        cleaned = re.sub(r'<[^>]+>', '', text)
        return cleaned.strip()

    @staticmethod
    def _extract_ingredients_from_desc(desc: str):
        """Try to find a comma-separated ingredient list inside a longer description or HTML."""
        if not desc:
            return []
        txt = ProductService._strip_html_tags(desc)
        candidates = []
        for token in ['Aqua', 'Water', 'Glycerin', 'Aqua/Water', 'Glycerin,']:
            if token in txt:
                idx = txt.find(token)
                candidates.append(txt[idx:])
        if not candidates:
            parts = [p for p in txt.split('\n') if p and p.count(',') > 3]
            if parts:
                candidates = parts
        if not candidates:
            parts = [p.strip() for p in txt.split(',') if p.strip()]
            return parts[:200]

        candidate = max(candidates, key=len)
        parts = [p.strip() for p in candidate.split(',') if p.strip()]
        return parts[:200]

    @staticmethod
    def _extract_images(obj: dict):
        imgs = []
        try:
            cur = obj.get('currentSku') or obj.get('current_sku')
            if cur:
                si = cur.get('skuImages') or cur.get('sku_images')
                if si and isinstance(si, dict):
                    url = si.get('imageUrl') or si.get('image_url')
                    if url:
                        imgs.append(url)
                alt = cur.get('alternateImages') or cur.get('alternate_images') or cur.get('alternateImages', [])
                if alt and isinstance(alt, list):
                    for a in alt:
                        if isinstance(a, dict):
                            u = a.get('imageUrl') or a.get('image_url') or a.get('image250')
                            if u:
                                imgs.append(u)
        except Exception:
            pass

        try:
            anc = obj.get('ancillarySkus') or obj.get('ancillary_skus') or []
            for a in anc:
                if isinstance(a, dict):
                    u = a.get('skuImages', {}) if isinstance(a.get('skuImages', {}), dict) else {}
                    if isinstance(u, dict):
                        url = u.get('imageUrl') or u.get('image_url') or u.get('image250')
                        if url:
                            imgs.append(url)
                    if a.get('image'):
                        imgs.append(a.get('image'))
        except Exception:
            pass

        try:
            pd = obj.get('productDetails') or {}
            if pd:
                hero = pd.get('image') or pd.get('heroImage') or pd.get('heroImageAltText')
                if hero and isinstance(hero, str) and hero.startswith('http'):
                    imgs.append(hero)
                seo = obj.get('productSeoJsonLd') or obj.get('productSeoJsonld')
                if seo and isinstance(seo, str) and '"image":' in seo:
                    import re
                    m = re.search(r'"image"\s*:\s*"([^"]+)"', seo)
                    if m:
                        imgs.append(m.group(1))
        except Exception:
            pass

        seen = set()
        out = []
        for u in imgs:
            if not u:
                continue
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    @staticmethod
    def process_sephora_product_detail(productID, preferedSku):
        """Normalize a Sephora product detail payload into a compact product object.

        Returns a dict with keys:
          - product_id, product_name, brand_name, rating, reviews, loves_count,
            price, images (list), main_image, highlights (list of strings), ingredients (list),
            short_description, long_description, target_url
        """

        raw = get_detail_from_sephora(productID, preferedSku)
        if len(raw) == 0:
            return {'error': 'no data returned from Sephora API'}
        
        if not isinstance(raw, dict):
            return {'error': 'invalid payload'}

        out = {}
        out['product_id'] = raw.get('productId') or raw.get('product_id') or (raw.get('productDetails') or {}).get('productId') or (raw.get('productDetails') or {}).get('productId')
        out['product_name'] = raw.get('productName') or raw.get('product_name') or (raw.get('productDetails') or {}).get('displayName') or raw.get('header1')
        brand = raw.get('brandName') or raw.get('brand_name') or (raw.get('productDetails') or {}).get('brand', {})
        if isinstance(brand, dict):
            out['brand_name'] = brand.get('displayName') or brand.get('brandName') or brand.get('name')
        else:
            out['brand_name'] = brand

        try:
            out['rating'] = float(raw.get('rating') or (raw.get('productDetails') or {}).get('rating') or 0)
        except Exception:
            out['rating'] = 0.0
        out['loves_count'] = int(raw.get('lovesCount') or (raw.get('productDetails') or {}).get('lovesCount') or 0)
        out['reviews'] = int(raw.get('reviews') or (raw.get('productDetails') or {}).get('reviews') or 0)

        price = None
        try:
            cur = raw.get('currentSku') or raw.get('current_sku') or {}
            price = cur.get('listPrice') or cur.get('list_price')
        except Exception:
            price = None
        if not price:
            price = raw.get('listPrice') or raw.get('list_price') or (raw.get('productDetails') or {}).get('listPrice')
        out['price'] = price

        imgs = ProductService._extract_images(raw)
        out['images'] = imgs
        out['main_image'] = imgs[0] if imgs else None

        try:
            hl = raw.get('highlights') or (raw.get('currentSku') or {}).get('highlights') or (raw.get('productDetails') or {}).get('highlights') or []
            if isinstance(hl, list):
                out['highlights'] = [h.get('name') if isinstance(h, dict) else str(h) for h in hl]
            else:
                out['highlights'] = [str(hl)]
        except Exception:
            out['highlights'] = []

        ingredient_desc = raw.get('ingredientDesc') or raw.get('ingredient_desc') or (raw.get('currentSku') or {}).get('ingredientDesc') or (raw.get('productDetails') or {}).get('longDescription') or raw.get('longDescription') or raw.get('shortDescription')
        out['ingredients'] = ProductService._extract_ingredients_from_desc(ingredient_desc)

        out['short_description'] = ProductService._strip_html_tags(raw.get('shortDescription') or (raw.get('productDetails') or {}).get('shortDescription') or '')
        out['long_description'] = ProductService._strip_html_tags(raw.get('longDescription') or (raw.get('productDetails') or {}).get('longDescription') or '')

        out['target_url'] = raw.get('fullSiteProductUrl') or raw.get('full_site_product_url') or raw.get('targetUrl') or raw.get('target_url') or (raw.get('currentSku') or {}).get('targetUrl')

        try:
            skus = raw.get('regularChildSkus') or raw.get('regular_child_skus') or raw.get('ancillarySkus') or raw.get('ancillary_skus') or []
            parsed_skus = []
            for s in skus:
                if not isinstance(s, dict):
                    continue
                parsed_skus.append({
                    'skuId': s.get('skuId') or s.get('skuId') or s.get('skuId'),
                    'productId': s.get('productId') or s.get('productId') or s.get('productId'),
                    'size': s.get('size') or s.get('variationValue'),
                    'image': (s.get('skuImages') or {}).get('imageUrl') if isinstance(s.get('skuImages'), dict) else s.get('image')
                })
            out['skus'] = parsed_skus
        except Exception:
            out['skus'] = []

        return out

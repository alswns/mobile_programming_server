import csv
import ast
import os

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset', 'product_info.csv')

_PRODUCTS = None


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


def get_global_ranking(top_n: int = 20, csv_path: str = None):
    """
    Return top N products across all users by a simple popularity+rating score.
    ---
    200:
    top_n: number of products to return
    csv_path: optional path to product_info.csv
    Returns: list of product dicts
    
    
    """

    products = load_products(csv_path)
    if not products:
        return []

    scored = []
    for p in products:
        try:
            rating = float(p.get('rating') or 0)
        except Exception:
            rating = 0.0
        loves = int(p.get('loves_count') or 0)
        # Simple score: rating weighted + popularity with diminishing returns
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

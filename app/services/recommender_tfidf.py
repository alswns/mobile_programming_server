from typing import List, Dict, Optional
import os
from .recommender_service import load_products, _build_keywords

# Lazy import sklearn to avoid hard dependency at import time
_VECTORIZER = None
_MATRIX = None
_PRODUCTS = None
_PRODUCT_INDEX = None


def _build_corpus(products: List[Dict]) -> List[str]:
    corpus = []
    for p in products:
        parts = []
        parts.append(p.get('product_name') or '')
        parts += p.get('highlights_parsed') or []
        parts += p.get('ingredients_parsed') or []
        corpus.append(' '.join([str(x) for x in parts if x]))
    return corpus


def _ensure_vector_index(csv_path: Optional[str] = None):
    global _VECTORIZER, _MATRIX, _PRODUCTS, _PRODUCT_INDEX
    if _MATRIX is not None and _PRODUCTS is not None:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import linear_kernel
    except Exception as e:
        raise

    products = load_products(csv_path)
    corpus = _build_corpus(products)
    vec = TfidfVectorizer(max_features=20000, ngram_range=(1,2), stop_words='english')
    mat = vec.fit_transform(corpus)

    _VECTORIZER = vec
    _MATRIX = mat
    _PRODUCTS = products
    _PRODUCT_INDEX = {i: p for i, p in enumerate(products)}


def recommend_products_tfidf(skin_info: dict, top_n: int = 10, csv_path: Optional[str] = None):
    """Recommend using TF-IDF similarity between skin_info keywords and product text.
    Returns same format as rule-based recommender.
    """
    try:
        from sklearn.metrics.pairwise import linear_kernel
    except Exception:
        raise ImportError('scikit-learn is required for TF-IDF recommender')

    _ensure_vector_index(csv_path)

    # build query from keywords
    keywords = _build_keywords(skin_info)
    query_parts = []
    if keywords:
        query_parts += keywords
    # also include explicit concerns and primary_category
    query_parts += [c for c in (skin_info.get('concerns') or [])]
    if skin_info.get('primary_category'):
        query_parts.append(skin_info.get('primary_category'))

    query_text = ' '.join([str(x) for x in query_parts if x])
    if not query_text:
        return []

    q_vec = _VECTORIZER.transform([query_text])
    sim = linear_kernel(q_vec, _MATRIX).flatten()

    # filter and score
    avoid_ingredients = [i.lower() for i in (skin_info.get('avoid_ingredients') or [])]
    price_min = skin_info.get('price_min')
    price_max = skin_info.get('price_max')

    candidates = []
    for idx, score in enumerate(sim):
        p = _PRODUCT_INDEX[idx]
        p_price = p.get('price_usd')
        if p_price is not None:
            if price_min is not None and p_price < price_min:
                continue
            if price_max is not None and p_price > price_max:
                continue

        ing_list = [i.lower() for i in (p.get('ingredients_parsed') or [])]
        if avoid_ingredients and any(ai in ing for ai in avoid_ingredients for ing in ing_list):
            continue

        # Combine TF-IDF similarity with rating/loves as small boosts
        try:
            rating = float(p.get('rating') or 0)
        except Exception:
            rating = 0.0
        loves = int(p.get('loves_count') or 0)
        final_score = float(score) * 100.0 + rating * 2.0 + min(loves / 200.0, 8.0)
        if final_score > 0:
            candidates.append((final_score, p))

    candidates.sort(key=lambda x: x[0], reverse=True)

    out = []
    for final_score, p in candidates[:top_n]:
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
            'score': round(final_score, 2)
        })

    return out

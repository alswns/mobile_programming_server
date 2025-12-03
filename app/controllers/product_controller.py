from flask import Blueprint, request, jsonify
from app.services.user_service import UserService
from flask_jwt_extended import create_access_token, create_refresh_token,jwt_required,get_jwt_identity
from app.services.product_service import ProductService
product_bp = Blueprint('products', __name__)


# 추천 엔드포인트: 사용자 피부정보(또는 간단한 요청)를 받아 추천 목록 반환
# @product_bp.route('/recommend', methods=['POST'])
# @jwt_required()
# def recommend():
#     """유저 피부 기반 상품 추천 API
#       ---
#     parameters:
#       - name: recommendation_request
#         in: body
#         required: true
#         schema:
#           type: object
#           properties:
#             skin_info:
#               type: object
#               description: Skin information like {"skin_type":"dry","concerns":["acne"]}      
            
#             top_n:
#               type: integer
#               description: Number of top recommendations to return
#             method:
#               type: string
#               description: Recommendation method, either "tfidf" or "rule"
#     responses:
#       200:
#         description: 추천 성공
#         schema:
#           type: object
#           properties:
#             recommendations:
#               type: array
#               items:
#                 type: object
#       400:
#         description: 추천 실패
#         schema:
#           type: object
#           properties:
#             message:
#               type: string
#     tags:
#       - Users 
#     """
#     data = request.json or {}
#     # expected structure: {"skin_info": {"skin_type": "dry", "concerns": ["acne"]}, "top_n": 10}
#     # If skin_info not provided, use the authenticated user's saved profile from JWT
#     skin_info = data.get('skin_info', {})
#     if not skin_info:
#       current_identity = get_jwt_identity()
#       if current_identity:
#         user = UserService.get_user(current_identity)
#         if user and user.get('skin_profile'):
#           skin_info = user.get('skin_profile')
#     top_n = data.get('top_n', 10)
#     method = (data.get('method') or 'tfidf').lower()
#     recs = []
#     if method == 'tfidf':
#         try:
#             from app.services.recommender_tfidf import recommend_products_tfidf
#             recs = recommend_products_tfidf(skin_info, top_n=top_n)
#         except Exception:
#             # fallback to rule-based if TF-IDF not available
#             recs = recommend_products(skin_info, top_n=top_n)
#     else:
#         recs = recommend_products(skin_info, top_n=top_n)

#     return jsonify({'recommendations': recs}), 200





@product_bp.route('/search', methods=['GET'])
def search_product():
    """
    제품 이름 검색 API - 가장 유사한 제품의 메인 이미지 반환
    ---
    parameters:
      - name: query
        in: query
        required: true
        type: string
        description: Product name to search for
      - name: top_n
        in: query
        required: false
        type: integer
        description: Number of results to return (default 1)
    responses:
      200:
        description: 검색 성공
        schema:
          type: object
          properties:
            results:
              type: array
              items:
                type: object
                properties:
                  product_id:
                    type: string
                  product_name:
                    type: string
                  brand_name:
                    type: string
                  image_url:
                    type: string
                  rating:
                    type: number
                  reviews:
                    type: integer
                  similarity_score:
                    type: number
      400:
        description: 검색 실패
    tags:
      - Products
    """
    query = request.args.get('query')
    if not query:
        return jsonify({'message': 'query parameter is required'}), 400
    
    try:
        top_n = int(request.args.get('top_n', 1))
    except Exception:
        top_n = 1
    
    results = ProductService.find_product_by_name(query, top_n=top_n)
    return jsonify({'results': results}), 200


@product_bp.route('/<product_id>/similar', methods=['GET'])
def get_similar_products(product_id):
    """
    유사 제품 추천 API
    ---
    parameters:
      - name: product_id
        in: path
        required: true
        type: string
        description: Product ID to find similar products for
      - name: top_n
        in: query
        required: false
        type: integer
        description: Number of similar products to return (default 10)
    responses:
      200:
        description: 유사 제품 조회 성공
        schema:
          type: object
          properties:
            product_id:
              type: string
            similar_products:
              type: array
              items:
                type: object
                properties:
                  product_id:
                    type: string
                  product_name:
                    type: string
                  brand_name:
                    type: string
                  rating:
                    type: number
                  reviews:
                    type: integer
                  price:
                    type: string
                  similarity_score:
                    type: number
      404:
        description: 제품을 찾을 수 없음
    tags:
      - Products
    """
    try:
        top_n = int(request.args.get('top_n', 10))
    except Exception:
        top_n = 10
    
    similar = ProductService.find_similar_products(product_id, top_n=top_n)
    
    if not similar:
        return jsonify({
            'message': 'Product not found or no similar products available',
            'product_id': product_id,
            'similar_products': []
        }), 404
    
    return jsonify({
        'product_id': product_id,
        'similar_products': similar
    }), 200


@product_bp.route('/detail', methods=['GET'])
def parse_product_detail():
    """
    상품 상세 정보 파싱 API
    ---
    parameters:
      - name: productId
        in: query
        required: true
        type: string
        description: Product ID (e.g., "P510337")
      - name: preferedSku
        in: query
        required: true
        type: string
        description: Preferred SKU ID (e.g., "2758951")
    responses:
      200:
        description: 상품 상세 정보 파싱 성공
        schema:
          type: object
          properties:
            product:
              type: object
      400:
        description: 상품 상세 정보 파싱 실패
        schema:
          type: object
          properties:
            message:
              type: string
    tags:
      - Products  
    """
    productId = request.args.get('productId')
    preferedSku = request.args.get('preferedSku')

    if not productId or not preferedSku:
        return jsonify({'message': 'productId and preferedSku are required'}), 400

    processed = ProductService.process_sephora_product_detail(productId, preferedSku)
    return jsonify({'product': processed}), 200


@product_bp.route('/ranking', methods=['GET'])
def ranking(top_n=20):
    """
    글로벌 상품 랭킹 조회 API (카테고리 필터 지원)
    ---
    parameters:
      - name: top_n
        in: query
        required: false
        type: integer
        description: Number of top ranked products to return (default is 20)
      - name: category
        in: query
        required: false
        type: string
        description: Category name to filter (e.g., 'Skincare', 'Fragrance')
      - name: level
        in: query
        required: false
        type: string
        description: Category level - 'primary', 'secondary', or 'tertiary' (default is 'primary')
    responses:
      200:
        description: 글로벌 상품 랭킹 조회 성공
        schema:
          type: object
          properties:
            ranking:
              type: array       
              items:
                type: object
      400:
        description: 글로벌 상품 랭킹 조회 실패
        schema:
          type: object
          properties:
            message:
              type: string
    tags:
      - Products
      """
    top_n = request.args.get('top_n', default=20, type=int)
    category = request.args.get('category', default=None, type=str)
    level = request.args.get('level', default='primary', type=str)
    
    # Validate level
    if level not in ['primary', 'secondary', 'tertiary']:
        level = 'primary'
    
    if category:
        # Use category-based ranking
        recs = ProductService.get_ranking_by_category(category=category, level=level, top_n=top_n)
    else:
        # Use original global ranking
        recs = ProductService.get_global_ranking(top_n=top_n)
    
    return jsonify({'ranking': recs}), 200


@product_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    카테고리 목록 조회 API
    ---
    parameters:
      - name: level
        in: query
        required: false
        type: string
        description: Category level - 'primary', 'secondary', 'tertiary', or 'all' (default is 'primary')
    responses:
      200:
        description: 카테고리 목록 조회 성공
        schema:
          type: object
          properties:
            primary_categories:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  count:
                    type: integer
      400:
        description: 카테고리 목록 조회 실패
    tags:
      - Products
    """
    level = request.args.get('level', default='primary', type=str)
    
    # Validate level
    if level not in ['primary', 'secondary', 'tertiary', 'all']:
        level = 'primary'
    
    categories = ProductService.get_categories_list(level=level)
    return jsonify(categories), 200
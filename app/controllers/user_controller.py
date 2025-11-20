from flask import Blueprint, request, jsonify
from app.services.user_service import UserService
from flask_jwt_extended import create_access_token, create_refresh_token,jwt_required,get_jwt_identity
from app.services.recommender_service import recommend_products
user_bp = Blueprint('users', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    """
    사용자 로그인 API
    ---
    parameters:
      - name: user
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: 로그인 성공
        schema:
          type: object
          properties:
            message:
              type: string
            access_token:
              type: string
            refresh_token:
              type: string
      401:
        description: 로그인 실패
        schema:
          type: object
          properties:
            message:
              type: string
    tags:
      - Users"""

    data = request.json
    email = data.get('email')
    password = data.get('password')

    success, msg = UserService.authenticate_user(email, password)
    status_code = 200 if success else 401
    if status_code == 200:
      # use email as JWT identity so endpoints can retrieve user by email
      access_token = create_access_token(identity=email)
      refresh_token = create_refresh_token(identity=email)
      return jsonify({"message": msg, "access_token": access_token, "refresh_token": refresh_token}), status_code
    else:
      return jsonify({"message": msg}), status_code


@user_bp.route('/register', methods=['POST'])
def register():
    """
    사용자 생성 API
    ---
    parameters:
      - name: user
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            username:
              type: string
            password:
                type: string
    responses:
      201:
        description: 사용자 생성 성공
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: 사용자 생성 실패
        schema:
          type: object
          properties:
            message:
              type: string
    tags:
      - Users
    """
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    success, msg = UserService.register_user(email, username, password)
    status_code = 201 if success else 400
    return jsonify({"message": msg}), status_code

@user_bp.route('/profile', methods=['GET'])
def profile():
    """
    사용자 프로필 조회 API
    ---
    parameters:
      - email: email
        in: query
        required: true
        type: string
    responses:
      200:
        description: 사용자 프로필 조회 성공
        schema:
          type: object
          properties:
            email:
              type: string
      404:
        description: 사용자 프로필 조회 실패
        schema:
          type: object
          properties:
            message:
              type: string
    tags:
      - Users
    """
    email = request.args.get('email')
    user = UserService.get_user(email)
    if user:
        return jsonify({"email": user['email']}), 200
    else:
        return jsonify({"message": "User not found"}), 404


@user_bp.route('/profile', methods=['POST'])
def update_profile():
    """Update user profile (skin profile). Expects JSON: {"email":..., "skin_profile": {...}}"""
    data = request.json or {}
    email = data.get('email')
    profile = data.get('skin_profile') or {}
    success, msg = UserService.set_user_profile(email, profile)
    status = 200 if success else 404
    return jsonify({"message": msg}), status


# 보호된 리소스 접근
@user_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    보호된 리소스 접근 API
    ---
    responses:
      200:
        description: 보호된 리소스 접근 성공
        schema:
          type: object
          properties:
            logged_in_as:
              type: string
      401:
        description: 보호된 리소스 접근 실패
        schema:
          type: object
          properties:
            msg:
              type: string
    tags:
      - Users
    """
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# 토큰 갱신 엔드포인트
@user_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_access_token), 200

# 추천 엔드포인트: 사용자 피부정보(또는 간단한 요청)를 받아 추천 목록 반환
@user_bp.route('/recommend', methods=['POST'])
@jwt_required()
def recommend():
    """유저 피부 기반 상품 추천 API
      ---
    parameters:
      - name: recommendation_request
        in: body
        required: true
        schema:
          type: object
          properties:
            skin_info:
              type: object
              description: Skin information like {"skin_type":"dry","concerns":["acne"]}      
            
            top_n:
              type: integer
              description: Number of top recommendations to return
            method:
              type: string
              description: Recommendation method, either "tfidf" or "rule"
    responses:
      200:
        description: 추천 성공
        schema:
          type: object
          properties:
            recommendations:
              type: array
              items:
                type: object
      400:
        description: 추천 실패
        schema:
          type: object
          properties:
            message:
              type: string
    tags:
      - Users 
    """
    data = request.json or {}
    # expected structure: {"skin_info": {"skin_type": "dry", "concerns": ["acne"]}, "top_n": 10}
    # If skin_info not provided, use the authenticated user's saved profile from JWT
    skin_info = data.get('skin_info', {})
    if not skin_info:
      current_identity = get_jwt_identity()
      if current_identity:
        user = UserService.get_user(current_identity)
        if user and user.get('skin_profile'):
          skin_info = user.get('skin_profile')
    top_n = data.get('top_n', 10)
    method = (data.get('method') or 'tfidf').lower()
    recs = []
    if method == 'tfidf':
        try:
            from app.services.recommender_tfidf import recommend_products_tfidf
            recs = recommend_products_tfidf(skin_info, top_n=top_n)
        except Exception:
            # fallback to rule-based if TF-IDF not available
            recs = recommend_products(skin_info, top_n=top_n)
    else:
        recs = recommend_products(skin_info, top_n=top_n)

    return jsonify({'recommendations': recs}), 200


@user_bp.route('/ranking', methods=['GET'])
def ranking():
    """
    글로벌 상품 랭킹 조회 API
    ---
    parameters:
      - name: top_n
        in: query
        required: false
        type: integer
        description: Number of top ranked products to return (default is 20)
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
      - Users
      """
    try:
        top_n = int(request.args.get('top_n', 20))
    except Exception:
        top_n = 20
    from app.services.recommender_service import get_global_ranking
    recs = get_global_ranking(top_n=top_n)
    return jsonify({'ranking': recs}), 200

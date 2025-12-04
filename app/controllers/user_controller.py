from flask import Blueprint, request, jsonify
from app.services.user_service import UserService
from flask_jwt_extended import create_access_token, create_refresh_token,jwt_required,get_jwt_identity

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
            error_code:
              type: "null"
      400:
        description: 빈칸이 있는 경우
        schema:
          type: object
          properties:
            message:
              type: string
            error_code:
              type: string
              example: EMPTY_FIELD
      401:
        description: 인증 실패 (이메일 또는 비밀번호가 올바르지 않음)
        schema:
          type: object
          properties:
            message:
              type: string
            error_code:
              type: string
              example: INVALID_CREDENTIALS
      500:
        description: 서버 오류가 발생한 경우
        schema:
          type: object
          properties:
            message:
              type: string
            error_code:
              type: string
              example: SERVER_ERROR
    tags:
      - Users"""

    data = request.json
    email = data.get('email')
    password = data.get('password')

    success, error_code, msg = UserService.authenticate_user(email, password)
    
    # 오류 코드에 따른 상태 코드 매핑
    if success:
        status_code = 200  # 성공한 경우
        # use email as JWT identity so endpoints can retrieve user by email
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify({
            "message": msg,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "error_code": None
        }), status_code
    elif error_code == "EMPTY_FIELD":
        status_code = 400  # 빈칸이 있는 경우
    elif error_code == "INVALID_CREDENTIALS":
        status_code = 401  # 인증 실패
    else:
        status_code = 500  # 실패한 경우 (기타 서버 오류)
    
    return jsonify({"message": msg, "error_code": error_code}), status_code


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
            error_code:
              type: "null"
      400:
        description: 빈칸이 있는 경우
        schema:
          type: object
          properties:
            message:
              type: string
            error_code:
              type: string
              example: EMPTY_FIELD
      409:
        description: 유저가 이미 있는 경우
        schema:
          type: object
          properties:
            message:
              type: string
            error_code:
              type: string
              example: USER_EXISTS
      500:
        description: 서버 오류가 발생한 경우
        schema:
          type: object
          properties:
            message:
              type: string
            error_code:
              type: string
              example: SERVER_ERROR
    tags:
      - Users
    """
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    success, error_code, msg = UserService.register_user(email, username, password)
    
    # 오류 코드에 따른 상태 코드 매핑
    if success:
        status_code = 201  # 성공한 경우
    elif error_code == "EMPTY_FIELD":
        status_code = 400  # 빈칸이 있는 경우
    elif error_code == "USER_EXISTS":
        status_code = 409  # 유저가 이미 있는 경우
    else:
        status_code = 500  # 실패한 경우 (기타 서버 오류)
    
    return jsonify({"message": msg, "error_code": error_code if not success else None}), status_code

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


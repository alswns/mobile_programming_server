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
            success:
              type: boolean
              example: true
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
            success:
              type: boolean
              example: false
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
            success:
              type: boolean
              example: false
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
            success:
              type: boolean
              example: false
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
            "success": True,
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
    
    return jsonify({
        "success": False,
        "message": msg,
        "error_code": error_code
    }), status_code


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
            success:
              type: boolean
              example: true
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
            success:
              type: boolean
              example: false
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
            success:
              type: boolean
              example: false
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
            success:
              type: boolean
              example: false
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
        # use email as JWT identity so endpoints can retrieve user by email
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify({
            "success": True,
            "message": msg,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "error_code": None
        }), status_code
    elif error_code == "EMPTY_FIELD":
        status_code = 400  # 빈칸이 있는 경우
    elif error_code == "USER_EXISTS":
        status_code = 409  # 유저가 이미 있는 경우
    else:
        status_code = 500  # 실패한 경우 (기타 서버 오류)
    
    return jsonify({
        "success": False,
        "message": msg,
        "error_code": error_code
    }), status_code

@user_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_info():
    """
    사용자 정보 조회 API
    ---
    security:
      - Bearer: []
    responses:
      200:
        description: 사용자 정보 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
            data:
              type: object
              properties:
                email:
                  type: string
                username:
                  type: string
                skin_profile:
                  type: object
            error_code:
              type: "null"
      401:
        description: 토큰이 유효하지 않거나 만료된 경우
        schema:
          type: object
          properties:
            msg:
              type: string
      404:
        description: 유저를 찾을 수 없는 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: USER_NOT_FOUND
      500:
        description: 서버 오류가 발생한 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: SERVER_ERROR
    tags:
      - Users
    """
    # JWT 토큰에서 이메일 가져오기
    email = get_jwt_identity()
    user_info, error_code, msg = UserService.get_user(email)
    
    if user_info:
        status_code = 200
        return jsonify({
            "success": True,
            "message": msg,
            "data": user_info,
            "error_code": None
        }), status_code
    elif error_code == "USER_NOT_FOUND":
        status_code = 404
    else:
        status_code = 500
    
    return jsonify({
        "success": False,
        "message": msg,
        "error_code": error_code
    }), status_code


@user_bp.route('/profile', methods=['GET'])
def profile():
    """
    사용자 프로필 조회 API (기존 호환성 유지)
    ---
    parameters:
      - name: email
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
            username:
              type: string
            skin_profile:
              type: object
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
    user_info, error_code, msg = UserService.get_user(email)
    if user_info:
        return jsonify(user_info), 200
    else:
        return jsonify({"message": msg}), 404


@user_bp.route('/user', methods=['PUT'])
def update_user_info():
    """
    사용자 정보 수정 API
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
            skin_profile:
              type: object
    responses:
      200:
        description: 사용자 정보 수정 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
            error_code:
              type: "null"
      400:
        description: 빈칸이 있는 경우 또는 수정할 정보가 없는 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              examples: [EMPTY_FIELD, NO_UPDATE_DATA]
      404:
        description: 유저를 찾을 수 없는 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: USER_NOT_FOUND
      500:
        description: 서버 오류가 발생한 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: SERVER_ERROR
    tags:
      - Users
    """
    data = request.json or {}
    email = data.get('email')
    username = data.get('username')
    skin_profile = data.get('skin_profile')
    
    success, error_code, msg = UserService.update_user_info(email, username, skin_profile)
    
    if success:
        status_code = 200
        return jsonify({
            "success": True,
            "message": msg,
            "error_code": None
        }), status_code
    elif error_code == "EMPTY_FIELD" or error_code == "NO_UPDATE_DATA":
        status_code = 400
    elif error_code == "USER_NOT_FOUND":
        status_code = 404
    else:
        status_code = 500
    
    return jsonify({
        "success": False,
        "message": msg,
        "error_code": error_code
    }), status_code


@user_bp.route('/profile', methods=['POST'])
def update_profile():
    """
    사용자 스킨 프로필 수정 API (기존 호환성 유지)
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
            skin_profile:
              type: object
    responses:
      200:
        description: 프로필 수정 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
            error_code:
              type: "null"
      400:
        description: 빈칸이 있는 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: EMPTY_FIELD
      404:
        description: 유저를 찾을 수 없는 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: USER_NOT_FOUND
      500:
        description: 서버 오류가 발생한 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: SERVER_ERROR
    tags:
      - Users
    """
    data = request.json or {}
    email = data.get('email')
    profile = data.get('skin_profile') or {}
    
    success, error_code, msg = UserService.set_user_profile(email, profile)
    
    if success:
        status_code = 200
        return jsonify({
            "success": True,
            "message": msg,
            "error_code": None
        }), status_code
    elif error_code == "EMPTY_FIELD":
        status_code = 400
    elif error_code == "USER_NOT_FOUND":
        status_code = 404
    else:
        status_code = 500
    
    return jsonify({
        "success": False,
        "message": msg,
        "error_code": error_code
    }), status_code


@user_bp.route('/skin_info', methods=['PUT'])
def update_skin_info():
    """
    사용자 스킨 타입 수정 API
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
            skin_type:
              type: string
    responses:
      200:
        description: 스킨 타입 수정 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
            error_code:
              type: "null"
      400:
        description: 빈칸이 있는 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: EMPTY_FIELD
      404:
        description: 유저를 찾을 수 없는 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: USER_NOT_FOUND
      500:
        description: 서버 오류가 발생한 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
            error_code:
              type: string
              example: SERVER_ERROR
    tags:
      - Users
    """
    data = request.json or {}
    email = data.get('email')
    skin_type = data.get('skin_type')
    
    success, error_code, msg = UserService.update_skin_type(email, skin_type)
    
    if success:
        status_code = 200
        return jsonify({
            "success": True,
            "message": msg,
            "error_code": None
        }), status_code
    elif error_code == "EMPTY_FIELD":
        status_code = 400
    elif error_code == "USER_NOT_FOUND":
        status_code = 404
    else:
        status_code = 500
    
    return jsonify({
        "success": False,
        "message": msg,
        "error_code": error_code
    }), status_code


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


from flask import Blueprint, request, jsonify
from app.services.user_service import UserService
from flask_jwt_extended import create_access_token, create_refresh_token,jwt_required,get_jwt_identity
user_bp = Blueprint('users', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    success, msg = UserService.authenticate_user(email, password)
    status_code = 200 if success else 401
    if status_code == 200:
        username = UserService.get_user(email)['username']
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        return jsonify({"message": msg, "access_token": access_token, "refresh_token": refresh_token}), status_code
    else:
        return jsonify({"message": msg}), status_code

@user_bp.route('/profile', methods=['GET'])
def profile():
    username = request.args.get('username')
    user = UserService.get_user(username)
    if user:
        return jsonify({"username": user['username']}), 200
    else:
        return jsonify({"message": "User not found"}), 404

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    success, msg = UserService.register_user(email, username, password)
    status_code = 201 if success else 400
    return jsonify({"message": msg}), status_code

# 보호된 리소스 접근
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# 토큰 갱신 엔드포인트
@app.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_access_token), 200

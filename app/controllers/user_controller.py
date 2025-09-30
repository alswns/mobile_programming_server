from flask import Blueprint, request, jsonify
from app.services.user_service import UserService

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    success, msg = UserService.authenticate_user(email, password)
    status_code = 200 if success else 401
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

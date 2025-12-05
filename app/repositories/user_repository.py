from app import mongoDb
from werkzeug.security import generate_password_hash, check_password_hash

class UserRepository:
    @staticmethod
    def add_user(email,username, password, skin_profile=None):
        password_hash = generate_password_hash(password)
        user = {
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "skin_profile": skin_profile or {}
        }
        mongoDb.db.users.insert_one(user)

    
    @staticmethod
    def get_user_by_email(email):
        return mongoDb.db.users.find_one({"email": email})
    
    @staticmethod
    def check_password(hashed_password, password):
        return check_password_hash(hashed_password, password)   

    @staticmethod
    def update_profile(email, profile: dict):
        return mongoDb.db.users.update_one({"email": email}, {"$set": {"skin_profile": profile}})
    
    @staticmethod
    def update_user(email, update_data: dict):
        """유저 정보 업데이트 (일반적인 필드들)"""
        return mongoDb.db.users.update_one({"email": email}, {"$set": update_data})
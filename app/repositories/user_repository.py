from app import mongoDb
from werkzeug.security import generate_password_hash, check_password_hash

class UserRepository:
    @staticmethod
    def add_user(email,username, password):
        password_hash = generate_password_hash(password)
        user = {"username": username, "password_hash": password_hash,"email":email}
        mongoDb.db.users.insert_one(user)

    
    @staticmethod
    def get_user_by_email(email):
        return mongoDb.db.users.find_one({"email": email})
    
    @staticmethod
    def check_password(hashed_password, password):
        return check_password_hash(hashed_password, password)   
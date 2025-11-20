from app.repositories.user_repository import UserRepository

class UserService:
    @staticmethod
    def register_user(email,username, password):
        if UserRepository.get_user_by_email(email):
            return False, "User already exists"
        UserRepository.add_user(email,username, password)
        return True, "User registered successfully"
    @staticmethod
    def get_user(email):
        return UserRepository.get_user_by_email(email)
    @staticmethod
    def authenticate_user(email,password):
        user = UserRepository.get_user_by_email(email)
        if user and UserRepository.check_password(user['password_hash'], password):
            return True, "Authentication successful"
        return False, "Invalid credentials"
    @staticmethod
    def set_user_profile(email, profile: dict):
        user = UserRepository.get_user_by_email(email)
        if not user:
            return False, "User not found"
        UserRepository.update_profile(email, profile)
        return True, "Profile updated"
        
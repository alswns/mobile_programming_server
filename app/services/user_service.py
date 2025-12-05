from app.repositories.user_repository import UserRepository

class UserService:
    @staticmethod
    def register_user(email, username, password):
        # 빈칸 체크
        if not email or not username or not password:
            return False, "EMPTY_FIELD", "모든 필드를 입력해주세요"
        
        # 유저가 이미 있는 경우
        if UserRepository.get_user_by_email(email):
            return False, "USER_EXISTS", "이미 존재하는 사용자입니다"
        
        try:
            # 성공한 경우
            UserRepository.add_user(email, username, password)
            return True, "SUCCESS", "회원가입이 완료되었습니다"
        except Exception as e:
            # 실패한 경우
            return False, "SERVER_ERROR", f"서버 오류가 발생했습니다: {str(e)}"
    @staticmethod
    def get_user(email):
        """유저 정보 조회"""
        if not email:
            return None, "EMPTY_FIELD", "이메일을 입력해주세요"
        
        try:
            user = UserRepository.get_user_by_email(email)
            if user:
                # 비밀번호 해시는 제외하고 반환
                user_info = {
                    "email": user.get("email"),
                    "username": user.get("username"),
                    "skin_profile": user.get("skin_profile", {})
                }
                return user_info, "SUCCESS", "유저 정보 조회 성공"
            else:
                return None, "USER_NOT_FOUND", "유저를 찾을 수 없습니다"
        except Exception as e:
            return None, "SERVER_ERROR", f"서버 오류가 발생했습니다: {str(e)}"
    
    @staticmethod
    def update_user_info(email, username=None, skin_profile=None):
        """유저 정보 수정"""
        if not email:
            return False, "EMPTY_FIELD", "이메일을 입력해주세요"
        
        try:
            user = UserRepository.get_user_by_email(email)
            if not user:
                return False, "USER_NOT_FOUND", "유저를 찾을 수 없습니다"
            
            update_data = {}
            if username is not None:
                if not username:
                    return False, "EMPTY_FIELD", "사용자 이름을 입력해주세요"
                update_data["username"] = username
            
            if skin_profile is not None:
                update_data["skin_profile"] = skin_profile
            
            if not update_data:
                return False, "NO_UPDATE_DATA", "수정할 정보가 없습니다"
            
            UserRepository.update_user(email, update_data)
            return True, "SUCCESS", "유저 정보가 수정되었습니다"
        except Exception as e:
            return False, "SERVER_ERROR", f"서버 오류가 발생했습니다: {str(e)}"
    
    @staticmethod
    def authenticate_user(email, password):
        # 빈칸 체크
        if not email or not password:
            return False, "EMPTY_FIELD", "이메일과 비밀번호를 입력해주세요"
        
        try:
            user = UserRepository.get_user_by_email(email)
            if user and UserRepository.check_password(user['password_hash'], password):
                # 성공한 경우
                return True, "SUCCESS", "로그인에 성공했습니다"
            else:
                # 인증 실패 (이메일 없음 또는 비밀번호 틀림)
                return False, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다"
        except Exception as e:
            # 실패한 경우 (서버 오류)
            return False, "SERVER_ERROR", f"서버 오류가 발생했습니다: {str(e)}"
    @staticmethod
    def set_user_profile(email, profile: dict):
        """스킨 프로필만 업데이트 (기존 메서드 유지)"""
        if not email:
            return False, "EMPTY_FIELD", "이메일을 입력해주세요"
        
        try:
            user = UserRepository.get_user_by_email(email)
            if not user:
                return False, "USER_NOT_FOUND", "유저를 찾을 수 없습니다"
            
            UserRepository.update_profile(email, profile)
            return True, "SUCCESS", "프로필이 업데이트되었습니다"
        except Exception as e:
            return False, "SERVER_ERROR", f"서버 오류가 발생했습니다: {str(e)}"
        
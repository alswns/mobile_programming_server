from flask import Flask
from flask_pymongo import PyMongo

mongoDb=PyMongo()
def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://mongodb:27017/mobile"
    
    mongoDb.init_app(app)
    # 블루프린트 등록 예시
    from .controllers.main_controller import main_bp
    from .controllers.user_controller import user_bp
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(user_bp, url_prefix='/users')
    
    # 기타 확장 초기화 코드 등 추가 가능
    
    return app

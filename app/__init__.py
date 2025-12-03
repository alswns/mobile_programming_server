from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flasgger import Swagger

mongoDb=PyMongo()
def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://mongodb:27017/mobile"
    app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # 비밀키 설정
    jwt = JWTManager(app)
    
    # Swagger 설정
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Mobile Programming Server API",
            "description": "화장품 추천 및 제품 검색 API",
            "version": "1.0.0",
            "contact": {
                "name": "API Support"
            }
        },
        "host": "localhost:8080",
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        }
    }
    
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    mongoDb.init_app(app)
    # 블루프린트 등록 예시
    from .controllers.main_controller import main_bp
    from .controllers.user_controller import user_bp
    from .controllers.product_controller import product_bp
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(product_bp, url_prefix='/products')
    
    # 기타 확장 초기화 코드 등 추가 가능
    
    return app

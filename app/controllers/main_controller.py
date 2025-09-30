from flask import Blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route("/", methods=["GET"])
def home():
    return "hello"

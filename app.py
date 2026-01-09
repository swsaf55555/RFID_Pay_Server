from flask import Flask, jsonify
from config import Config
from extensions import db

from routes.admin_routes import bp as admin_bp
from routes.card_routes import bp as card_bp
from routes.seller_routes import bp as seller_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    app.register_blueprint(admin_bp)
    app.register_blueprint(card_bp)
    app.register_blueprint(seller_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'code': 404, 'msg': 'not found', 'data': None}), 404

    @app.errorhandler(500)
    def internal(e):
        return jsonify({'code': 500, 'msg': 'internal error', 'data': None}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

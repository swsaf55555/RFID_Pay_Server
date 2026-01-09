import jwt
from flask import request, current_app, jsonify
from functools import wraps
from models import Admin
from extensions import db
from datetime import datetime, timedelta


def generate_token(admin_id, pwd_version):
    payload = {
        'admin_id': admin_id,
        "pwd_version": pwd_version,
        'exp': datetime.now() + timedelta(seconds=current_app.config['JWT_EXP_SECONDS'])
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def verify_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        admin_id = payload.get('admin_id')
        admin = Admin.query.get(admin_id)
        if payload.get("pwd_version") != admin.pwd_version:
            return None
        return admin
    except Exception:
        return None


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]
            admin = verify_token(token)
            if admin:
                # inject admin into flask.g if needed
                return fn(*args, **kwargs)
        return jsonify({'code': 401, 'msg': 'admin auth required', 'data': None}), 401

    return wrapper

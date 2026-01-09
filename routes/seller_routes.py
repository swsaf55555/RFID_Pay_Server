from flask import Blueprint, request, jsonify
from models import Seller

bp = Blueprint('seller', __name__, url_prefix='/api/seller')


@bp.route('/test', methods=['POST'])
def seller_test():
    data = request.get_json() or {}
    seller_id = data.get('seller_id')
    seller_passwd = data.get('seller_passwd')
    seller = Seller.query.filter_by(id=seller_id).first()
    if not seller_id or not seller_passwd:
        return jsonify({'code': 1, 'msg': 'information not full', 'data': None}), 400
    if not seller:
        return jsonify({'code': 1, 'msg': 'seller not bound', 'data': None}), 404
    try:
        if not seller.check_password(seller_passwd):
            return jsonify({'code': 1, 'msg': 'seller password error', 'data': None}), 400
    except Exception as e:
        return jsonify({'code': 1, 'msg': 'exception: ' + str(e), 'data': None}), 400
    return jsonify({'code': 0, 'msg': 'success', 'data': {
        'balance': str(seller.balance),
        'name': str(seller.name),
        'seller_name': str(seller.seller_name),
        'phone_number': str(seller.phone_number),
    }})

import base64
import urllib.parse
import config

from alipay.aop.api.util import SignatureUtils
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import Student, Transaction, Seller
from decimal import Decimal
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import time

bp = Blueprint('card', __name__, url_prefix='/api/card')
client_config = AlipayClientConfig()
client_config.server_url = config.Config.ALIPAY_SERVER_URL
client_config.app_id = config.Config.ALIPAY_APP_ID
client_config.app_private_key = config.Config.ALIPAY_PRIVATE_KEY
client_config.alipay_public_key = config.Config.ALIPAY_PUBLIC_KEY
client = DefaultAlipayClient(alipay_client_config=client_config, logger=None)


def alipay_sign_verify(params: dict, public_key: str) -> bool:
    sign = params.pop("sign", None)
    params.pop("sign_type", None)
    decoded_params = {k: urllib.parse.unquote(v) for k, v in params.items()}
    sorted_items = sorted(decoded_params.items(), key=lambda x: x[0])
    unsigned_str = "&".join([f"{k}={v}" for k, v in sorted_items])
    sign_bytes = base64.b64decode(sign)
    rsa_key = RSA.importKey(public_key)
    verifier = PKCS1_v1_5.new(rsa_key)
    digest = SHA256.new(unsigned_str.encode("utf-8"))
    return verifier.verify(digest, sign_bytes)


@bp.route('/query', methods=['POST'])
def query():
    data = request.get_json() or {}
    card_id = data.get('card_id')
    if not card_id:
        return jsonify({'code': 1, 'msg': 'card_id required', 'data': None}), 400
    student = Student.query.filter_by(card_id=card_id).first()
    if not student:
        return jsonify({'code': 1, 'msg': 'card not bound', 'data': None}), 404
    if student.status == 1:
        return jsonify({'code': 1, 'msg': 'card is lost', 'data': None}), 403
    return jsonify({'code': 0, 'msg': 'success',
                    'data': {'student_no': student.student_no, 'name': student.name, 'balance': str(student.balance),
                             'status': student.status}})


@bp.route('/consume', methods=['POST'])
def consume():
    data = request.get_json() or {}
    card_id = data.get('card_id')
    seller_id = data.get('seller_id')
    seller_passwd = data.get('seller_passwd')
    amount = data.get('amount')
    if not card_id or not amount or not seller_id or not seller_passwd:
        return jsonify({'code': 1, 'msg': 'information not full', 'data': None}), 400
    student = Student.query.filter_by(card_id=card_id).first()
    seller = Seller.query.filter_by(id=seller_id).first()
    if not seller:
        return jsonify({'code': 1, 'msg': 'seller not bound', 'data': None}), 404
    if not student:
        return jsonify({'code': 1, 'msg': 'card not bound', 'data': None}), 404
    if student.status == 1:
        return jsonify({'code': 1, 'msg': 'card is lost', 'data': None}), 403
    try:
        a = Decimal(str(amount))
    except Exception:
        return jsonify({'code': 1, 'msg': 'invalid amount', 'data': None}), 400
    if student.balance < a:
        return jsonify({'code': 1, 'msg': 'insufficient balance', 'data': None}), 400
    try:
        if not seller.check_password(seller_passwd):
            return jsonify({'code': 1, 'msg': 'seller password error', 'data': None}), 400
        student.balance = student.balance - a
        seller.balance = seller.balance + a
        txn = Transaction(student_id=student.id, type='consume', amount=a, seller_id=seller_id,
                          balance_after=student.balance)
        db.session.add(txn)
        db.session.commit()
    except Exception as e:
        return jsonify({'code': 1, 'msg': 'exception: ' + str(e), 'data': None}), 400
    return jsonify({'code': 0, 'msg': 'success', 'data': {'balance': str(student.balance)}})


@bp.route('/recharge', methods=['POST'])
def recharge():
    data = request.get_json() or {}
    card_id = data.get('card_id')
    amount = data.get('amount')
    if not card_id or amount is None:
        return jsonify({'code': 1, 'msg': 'card_id and amount required', 'data': None}), 400
    student = Student.query.filter_by(card_id=card_id).first()
    if not student:
        return jsonify({'code': 1, 'msg': 'student not found', 'data': None}), 404
    try:
        a = Decimal(str(amount))
        if a == 0:
            raise ValueError
    except Exception:
        return jsonify({'code': 1, 'msg': 'invalid amount', 'data': None}), 400
    client_config = AlipayClientConfig()
    client_config = AlipayClientConfig()
    client_config.server_url = config.Config.ALIPAY_SERVER_URL
    client_config.app_id = config.Config.ALIPAY_APP_ID
    client_config.app_private_key = config.Config.ALIPAY_PRIVATE_KEY
    client_config.alipay_public_key = config.Config.ALIPAY_PUBLIC_KEY
    client = DefaultAlipayClient(alipay_client_config=client_config, logger=None)
    out_trade_no = str(int(time.time()))

    model = AlipayTradePagePayModel()
    model.out_trade_no = out_trade_no
    model.total_amount = str(amount)
    model.subject = '充值' + str(amount) + '元'
    model.product_code = "FAST_INSTANT_TRADE_PAY"
    txn = Transaction(student_id=student.id, type='recharge', amount=str(amount),
                      balance_after=student.balance + Decimal(str(amount)), recharge_no=out_trade_no)
    db.session.add(txn)
    db.session.commit()
    request_obj = AlipayTradePagePayRequest()
    request_obj.biz_model = model
    request_obj.notify_url = config.Config.ALIPAY_NOTIFY_URL
    request_obj.return_url = config.Config.ALIPAY_RETURN_URL
    response = client.page_execute(request_obj, http_method="GET")

    return jsonify({
        "out_trade_no": out_trade_no,
        "pay_url": response
    })



@bp.route("/alipay_notify", methods=["POST"])
def alipay_notify():
    data = request.form.to_dict()
    current_app.logger.info(f"Alipay notify received: {data}")
    data_cp = data.copy()
    public_key = "-----BEGIN PUBLIC KEY-----\n" + client_config.alipay_public_key + "\n-----END PUBLIC KEY-----"
    current_app.logger.info(f"Public key length: {len(public_key)}")
    current_app.logger.info(f"Data copy for verification: {data_cp}")

    try:
        if alipay_sign_verify(data_cp, public_key):
            current_app.logger.info("Alipay signature verified successfully")
            if data.get("trade_status") in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
                out_trade_no = data["out_trade_no"]
                total_amount = data["total_amount"]
                current_app.logger.info(f"支付成功: {out_trade_no}, 金额: {total_amount}")

                transaction = Transaction.query.filter_by(recharge_no=out_trade_no).first()
                if not transaction:
                    current_app.logger.warning(f"Transaction not found: {out_trade_no}")
                    return jsonify({'code': 1, 'msg': 'order not found', 'data': None}), 404

                transaction.checked = True
                student = Student.query.filter_by(id=transaction.student_id).first()
                student.balance = student.balance + Decimal(total_amount)

                db.session.commit()

            return "success"
        else:
            current_app.logger.warning("Alipay signature verification failed")
    except Exception as e:
        current_app.logger.error(f"Exception in alipay_notify: {e}", exc_info=True)

    return "fail"



@bp.route("/pay_return", methods=["GET"])
def pay_return():
    out_trade_no = request.args.get("out_trade_no")
    if not out_trade_no:
        return "error"
    return f"支付完成，订单号: {out_trade_no}，你可以安全的关闭此页面。"


@bp.route('/transactions/seller', methods=['POST'])
def seller_transactions():
    data = request.get_json() or {}
    seller_id = data.get('seller_id')
    seller_passwd = data.get('seller_passwd')
    if not seller_id or not seller_passwd:
        return jsonify({'code': 1, 'msg': 'information not full', 'data': None}), 400
    seller = Seller.query.filter_by(id=seller_id).first()
    if not seller:
        return jsonify({'code': 1, 'msg': 'seller not bound', 'data': None}), 404
    try:
        if not seller.check_password(seller_passwd):
            return jsonify({'code': 1, 'msg': 'seller password error', 'data': None}), 400
    except Exception as e:
        return jsonify({'code': 1, 'msg': 'exception: ' + str(e), 'data': None}), 400
    txns = Transaction.query.filter_by(seller_id=seller_id).order_by(Transaction.id.desc()).all()
    arr = []
    for t in txns:
        arr.append({
            'id': t.id,
            'student_id': t.student_id,
            'amount': str(t.amount),
            'balance_after': str(t.balance_after),
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'type': t.type
        })

    return jsonify({'code': 0, 'msg': 'success', 'data': arr})

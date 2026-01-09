from flask import Blueprint, request, jsonify, render_template
from extensions import db
from models import Student, Admin, Transaction, Seller
from utils.jwt_auth import generate_token, admin_required
from decimal import Decimal
from utils.jwt_auth import verify_token

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/init')
def init_db():
    db.create_all()
    # create default admin if not exists
    if not Admin.query.filter_by(username='admin').first():
        a = Admin(username='admin')
        a.set_password('admin123')
        db.session.add(a)
        db.session.commit()
        return ('created default admin: admin / admin123')
    else:
        return ('admin exists')


@bp.route('/')
def admin():
    return render_template('admin.html')


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    token = data.get('token')
    if token:
        if not verify_token(token):
            return jsonify({'code': 1, 'msg': 'invalid credentials', 'data': None}), 401
    else:
        if not username or not password:
            return jsonify({'code': 1, 'msg': 'username/password required', 'data': None}), 400
        admin = Admin.query.filter_by(username=username).first()
        if not admin or not admin.check_password(password):
            return jsonify({'code': 1, 'msg': 'invalid credentials', 'data': None}), 401
        token = generate_token(admin.id, admin.pwd_version)
    return jsonify({'code': 0, 'msg': 'success', 'data': {'token': token}})


@bp.route('/logout', methods=['POST'])
@admin_required
def logout():
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        return jsonify({'code': 1, 'msg': 'admin not found', 'data': None}), 404
    try:
        admin.pwd_version += 1
        db.session.commit()
    except Exception as e:
        return jsonify({'code': 1, 'msg': 'logout exception: ' + str(e), 'data': None}), 400
    return jsonify({'code': 0, 'msg': 'logout success', 'data': None})


@bp.route('/student/add', methods=['POST'])
@admin_required
def add_student():
    data = request.get_json() or {}
    student_no = data.get('student_no')
    name = data.get('name')
    card_id = data.get('card_id')
    if not student_no or not name:
        return jsonify({'code': 1, 'msg': 'student_no and name required', 'data': None}), 400
    if Student.query.filter((Student.student_no == student_no) | (Student.card_id == card_id)).first():
        return jsonify({'code': 1, 'msg': 'student_no or card_id already exists', 'data': None}), 400
    student = Student(student_no=student_no, name=name, card_id=card_id, balance=Decimal('0.00'))
    db.session.add(student)
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': {'id': student.id}})


@bp.route('/student/edit', methods=['POST'])
@admin_required
def edit_student():
    data = request.get_json() or {}
    sid = data.get('id')
    card = data.get('card')
    if not sid:
        return jsonify({'code': 1, 'msg': 'id required', 'data': None}), 400
    student = Student.query.get(sid)
    if not student:
        return jsonify({'code': 1, 'msg': 'student not found', 'data': None}), 404
    name = data.get('name')
    balance = data.get('balance')
    if name is not None:
        student.name = name
    if card is not None:
        student.card_id = card
    if balance is not None:
        try:
            student.balance = Decimal(str(balance))
        except Exception:
            return jsonify({'code': 1, 'msg': 'invalid balance', 'data': None}), 400
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})


@bp.route('/student/lost', methods=['POST'])
@admin_required
def lost():
    data = request.get_json() or {}
    card_id = data.get('card_id')
    if not card_id:
        return jsonify({'code': 1, 'msg': 'card_id required', 'data': None}), 400
    student = Student.query.filter_by(card_id=card_id).first()
    if not student:
        return jsonify({'code': 1, 'msg': 'student not found', 'data': None}), 404
    student.status = 1
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})


@bp.route('/student/unlost', methods=['POST'])
@admin_required
def unlost():
    data = request.get_json() or {}
    card_id = data.get('card_id')
    if not card_id:
        return jsonify({'code': 1, 'msg': 'card_id required', 'data': None}), 400
    student = Student.query.filter_by(card_id=card_id).first()
    if not student:
        return jsonify({'code': 1, 'msg': 'student not found', 'data': None}), 404
    student.status = 0
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})


@bp.route('/recharge', methods=['POST'])
@admin_required
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
    except Exception:
        return jsonify({'code': 1, 'msg': 'invalid amount', 'data': None}), 400
    student.balance = student.balance + a
    # find admin id from token
    auth = request.headers.get('Authorization', '')
    token = auth.split(' ', 1)[1] if auth.startswith('Bearer ') else None
    admin = verify_token(token) if token else None
    admin_id = admin.id if admin else None
    txn = Transaction(student_id=student.id, type='recharge', amount=a, balance_after=student.balance,
                      admin_id=admin_id)
    db.session.add(txn)
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': {'balance': str(student.balance)}})


@bp.route('/students', methods=['GET'])
@admin_required
def list_students():
    q = Student.query.order_by(Student.id.desc()).all()
    arr = []
    for s in q:
        arr.append(
            {'id': s.id, 'student_no': s.student_no, 'name': s.name, 'card_id': s.card_id, 'balance': str(s.balance),
             'status': int(s.status)})
    return jsonify({'code': 0, 'msg': 'success', 'data': arr})


@bp.route('/sellers', methods=['GET'])
@admin_required
def list_sellers():
    q = Seller.query.order_by(Seller.id.desc()).all()
    arr = []
    for s in q:
        arr.append({'id': s.id, 'balance': str(s.balance), 'status': s.status, 'phone_number':str(s.phone_number), 'name':str(s.name), 'seller_name':str(s.seller_name)})
    return jsonify({'code': 0, 'msg': 'success', 'data': arr})


# 添加卖家
@bp.route('/seller/add', methods=['POST'])
@admin_required
def add_seller():
    data = request.get_json() or {}
    password = data.get('password')
    balance = data.get('balance', 0)
    name=data.get('name')
    seller_name=data.get('seller_name')
    phone_number=data.get('phone_number')
    if not password:
        return jsonify({'code': 1, 'msg': 'password required', 'data': None}), 400
    seller = Seller(balance=Decimal(str(balance)), name=name, seller_name=seller_name, phone_number=str(phone_number))
    seller.set_password(password)
    db.session.add(seller)
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': {'id': seller.id}})


@bp.route('/seller/edit', methods=['POST'])
@admin_required
def edit_seller():
    data = request.get_json() or {}
    id = data.get('id')
    name = data.get('name')
    seller_name = data.get('seller_name')
    phone_number = data.get('phone_number')
    if not id:
        return jsonify({'code': 1, 'msg': 'id required', 'data': None}), 400
    seller = Seller.query.get(id)
    if not seller:
        return jsonify({'code': 1, 'msg': 'seller not found', 'data': None}), 404
    balance = data.get('balance')
    if balance is not None:
        try:
            seller.balance = Decimal(str(balance))
        except Exception:
            return jsonify({'code': 1, 'msg': 'invalid balance', 'data': None}), 400
    if name is not None:
        try:
            seller.name = str(name)
        except Exception:
            return jsonify({'code': 1, 'msg': 'invalid name', 'data': None}), 400
    if seller_name is not None:
        try:
            seller.seller_name = str(seller_name)
        except Exception:
            return jsonify({'code': 1, 'msg': 'invalid seller name', 'data': None}), 400
    if phone_number is not None:
        try:
            seller.phone_number = str(phone_number)
        except Exception:
            return jsonify({'code': 1, 'msg': 'invalid phone number', 'data': None}), 400
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})

@bp.route('/seller/passwd', methods=['POST'])
@admin_required
def passwd_seller():
    data = request.get_json() or {}
    id = data.get('id')
    passwd_old = data.get('passwd_old')
    passwd_new = data.get('passwd_new')
    if passwd_old == passwd_new:
        return jsonify({'code': 1, 'msg': 'password old and new can not be same', 'data': None}), 404
    if not id:
        return jsonify({'code': 1, 'msg': 'id required', 'data': None}), 400
    seller = Seller.query.get(id)
    if not seller:
        return jsonify({'code': 1, 'msg': 'seller not found', 'data': None}), 404
    if passwd_old is not None and passwd_new is not None:
        try:
            if not seller.check_password(passwd_old):
                return jsonify({'code': 1, 'msg': 'old password error', 'data': None}), 400
            else:
                seller.set_password(passwd_new)
        except Exception as e:
            return jsonify({'code': 1, 'msg': 'password exception: '+str(e), 'data': None}), 400
    else:
        return jsonify({'code': 1, 'msg': 'need both new and old password', 'data': None}), 400
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})

@bp.route('/seller/ban', methods=['POST'])
@admin_required
def ban():
    data = request.get_json() or {}
    id = data.get('id')
    if not id:
        return jsonify({'code': 1, 'msg': 'sid required', 'data': None}), 400
    seller = Seller.query.filter_by(id=id).first()
    if not seller:
        return jsonify({'code': 1, 'msg': 'seller not found', 'data': None}), 404
    seller.status = 1
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})


@bp.route('/seller/active', methods=['POST'])
@admin_required
def active():
    data = request.get_json() or {}
    id = data.get('id')
    if not id:
        return jsonify({'code': 1, 'msg': 'sid required', 'data': None}), 400
    seller = Seller.query.filter_by(id=id).first()
    if not seller:
        return jsonify({'code': 1, 'msg': 'seller not found', 'data': None}), 404
    seller.status = 0
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})

@bp.route('/passwd', methods=['POST'])
@admin_required
def passwd_admin():
    data = request.get_json() or {}
    passwd_old = data.get('passwd_old')
    passwd_new = data.get('passwd_new')
    if passwd_old == passwd_new:
        return jsonify({'code': 1, 'msg': 'password old and new can not be same', 'data': None}), 404
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        return jsonify({'code': 1, 'msg': 'admin not found', 'data': None}), 404
    if passwd_old is not None and passwd_new is not None:
        try:
            if not admin.check_password(passwd_old):
                return jsonify({'code': 1, 'msg': 'old password error', 'data': None}), 400
            else:
                admin.set_password(passwd_new)
                admin.pwd_version += 1
        except Exception as e:
            return jsonify({'code': 1, 'msg': 'password exception: '+str(e), 'data': None}), 400
    else:
        return jsonify({'code': 1, 'msg': 'need both new and old password', 'data': None}), 400
    db.session.commit()
    return jsonify({'code': 0, 'msg': 'success', 'data': None})


@bp.route('/transactions/student', methods=['POST'])
@admin_required
def student_transactions():
    data = request.get_json() or {}
    sid = data.get('student_id')
    if not sid:
        return jsonify({'code': 1, 'msg': 'student_id required', 'data': None}), 400

    txns = Transaction.query.filter_by(student_id=sid).order_by(Transaction.id.desc()).all()

    arr = []
    for t in txns:
        if t.recharge_no:
            detail = '自助充值'
        elif t.seller_id:
            detail = '商家消费'
        else:
            detail = t.type

        arr.append({
            'id': t.id,
            'type': t.type,
            'amount': str(t.amount),
            'balance_after': str(t.balance_after),
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'recharge_no': t.recharge_no,
            'seller_id': t.seller_id,
            'detail': detail
        })

    return jsonify({'code': 0, 'msg': 'success', 'data': arr})
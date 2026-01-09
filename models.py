from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    card_id = db.Column(db.String(100), unique=True, nullable=True)
    balance = db.Column(db.Numeric(10, 2), default=0)
    status = db.Column(db.SmallInteger, default=0)  # 0=normal,1=lost
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    pwd_version = db.Column(db.Integer, default=1)
    def set_password(self, password):
        if not password == "":
            self.password_hash = generate_password_hash(password)
        else:
            raise ValueError('password can not be none')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    type = db.Column(db.Enum('recharge', 'consume', name='txn_type'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    balance_after = db.Column(db.Numeric(10, 2), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    recharge_no = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    checked = db.Column(db.Boolean, default=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id'), nullable=True)

    student = db.relationship('Student', backref='transactions')
    admin = db.relationship('Admin', backref='transactions')
    seller = db.relationship('Seller', backref='sellers')


class Seller(db.Model):
    __tablename__ = 'sellers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    seller_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.SmallInteger, default=0)  # 0=normal,1=baned

    def set_password(self, password):
        if not password == "":
            if self.status == 1:
                raise ValueError('this seller had been baned')
            self.password_hash = generate_password_hash(password)
        else:
            raise ValueError('password can not be none')

    def check_password(self, password):
        if self.status == 1:
            raise ValueError('this seller had been baned')
        return check_password_hash(self.password_hash, password)

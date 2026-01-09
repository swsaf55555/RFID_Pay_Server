import os

BASE_DIR = os.path.dirname(__file__)


class Config:
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root123'),
        'database': os.getenv('DB_NAME', 'student_card'),
        'charset': 'utf8mb4',
        'cursorclass': None,
        'autocommit': False,
    }
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_EXP_SECONDS = int(os.getenv('JWT_EXP_SECONDS', 86400))
    ALIPAY_SERVER_URL = os.getenv('ALIPAY_SERVER_URL', '0')
    ALIPAY_APP_ID = os.getenv('ALIPAY_APP_ID', '0')
    ALIPAY_PRIVATE_KEY = os.getenv('ALIPAY_PRIVATE_KEY', '0').strip()
    ALIPAY_PUBLIC_KEY = os.getenv('ALIPAY_PUBLIC_KEY', '0').strip()
    ALIPAY_NOTIFY_URL=os.getenv('ALIPAY_NOTIFY_URL', '0')
    ALIPAY_RETURN_URL = os.getenv('ALIPAY_RETURN_URL', '0')

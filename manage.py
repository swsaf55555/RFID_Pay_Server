import click
from app import create_app
from extensions import db
from models import Admin, Student

app = create_app()


@app.cli.command('init_db')
def init_db():
    with app.app_context():
        db.create_all()
        # create default admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            a = Admin(username='admin')
            a.set_password('admin123')
            db.session.add(a)
            db.session.commit()
            print('created default admin: admin / admin123')
        else:
            print('admin exists')


if __name__ == '__main__':
    init_db()

"""
Run this once to create (or update) the admin account.

In the VS Code terminal (inside the project folder, with venv active):
    python seed_admin.py
"""
from app import app
from models import db, Admin

with app.app_context():
    db.create_all()

    phone = input('Admin phone number: ').strip()
    password = input('Admin password: ').strip()

    admin = Admin.query.filter_by(phone=phone).first()
    if admin:
        admin.set_password(password)
        print(f'Password updated for admin {phone}.')
    else:
        admin = Admin(phone=phone)
        admin.set_password(password)
        db.session.add(admin)
        print(f'Admin {phone} created.')

    db.session.commit()

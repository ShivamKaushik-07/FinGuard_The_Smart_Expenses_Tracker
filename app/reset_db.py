# reset_db.py
from app import create_app
from app.db_manager import db

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ All tables dropped and recreated successfully.")

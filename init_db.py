from app import create_app
from app.db_manager import db, Budget, User, Expense, Signup

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Database and tables created successfully!")

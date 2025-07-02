from flask import Flask
from .routes import main
from .db_manager import db, User, Budget, Expense, Signup
from .auth import auth
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

load_dotenv()

db=db
# Create login manager instance
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Still needed for CSRF/session security
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)  # ✅ Properly indented
    login_manager.login_view = 'auth.login'  # Optional: redirect to login if not authenticated

    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(signup_id):
        return Signup.query.get(int(signup_id))

    return app

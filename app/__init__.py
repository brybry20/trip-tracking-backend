import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # ✅ CORS Setup - Tama na ito
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:5173",
        "https://trip-tracking-backend.onrender.com",
        "https://trip-tracking-frontend.onrender.com"
    ])
    
    app.config['SECRET_KEY'] = 'your-secret-key-123'
    
    # ===== SESSION COOKIE CONFIGURATION =====
    # ✅ Importante para sa cross-origin requests (frontend to backend)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Para sa cross-site requests
    app.config['SESSION_COOKIE_SECURE'] = True       # Para sa HTTPS (production)
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    # ========================================
    
    # ===== MULTIPLE DATABASES CONFIGURATION =====
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/database.db'  # Main DB
    # Get the absolute path para sure
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    HISTORICAL_DB_PATH = os.path.join(BASE_DIR, 'data_2025', 'trips_2025.db')

    app.config['SQLALCHEMY_BINDS'] = {
        'main': 'sqlite:///../instance/database.db',
        'historical': f'sqlite:///{HISTORICAL_DB_PATH}'  # ✅ bagong path
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # ============================================
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Import routes
    from app.routes.auth import auth_bp
    from app.routes.trips import trips_bp
    from app.routes.trips_2025 import trips2025_bp  # NEW: 2025 routes
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(trips2025_bp)  # Register 2025 routes
    
    # Create tables in main database only
    with app.app_context():
        # This creates tables ONLY in the main database (default bind)
        db.create_all()
        
        from app.models import User
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("="*50)
            print("✅ ADMIN CREATED!")
            print("Username: admin")
            print("Password: admin123")
            print("="*50)
    
    return app
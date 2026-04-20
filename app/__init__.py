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
        # JWT Secret Key
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-this')
    # DETECT ENVIRONMENT (local or production)
    is_local = os.environ.get('RENDER') is None
    
    # CORS Setup
    if is_local:
        CORS(app, 
             supports_credentials=True, 
             origins=[
                 "http://localhost:5173", 
                 "http://localhost:5000", 
                 "http://127.0.0.1:5173", 
                 "http://127.0.0.1:5000",
                 "exp://",
                 "http://localhost:19000",
                 "http://localhost:19006",
                 "*"  # For mobile testing
             ],
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
             expose_headers=["Content-Type", "Authorization"])
    else:
        # Production (Render) - allow mobile apps
        CORS(app, 
             supports_credentials=True, 
             origins=[
                 "https://trip-tracking-backend.onrender.com",
                 "https://trip-tracking-frontend.onrender.com",
                "https://trip-tracking-backend.onrender.com",
                 "https://trip-tracking-frontend.onrender.com",  # <-- ito ang web frontend mo
              "https://trip-tracking-frontend.onrender.com",  # web frontend
              "exp://",
             "http://localhost:19000",
             "http://localhost:19006",
             "https://expo.io",
             "https://*.expo.io",
             "*"

             ],
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
             expose_headers=["Content-Type", "Authorization"])
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
    
    # Session configuration
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    if is_local:
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['REMEMBER_COOKIE_SECURE'] = False
    else:
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['REMEMBER_COOKIE_SECURE'] = True
    
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600
    
    # DATABASE CONFIGURATION - SQLITE ONLY
    # Get the absolute path for the database
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    
    # Create instance folder if it doesn't exist
    if not os.path.exists(INSTANCE_PATH):
        os.makedirs(INSTANCE_PATH)
    
    # SQLite database path
    DB_PATH = os.path.join(INSTANCE_PATH, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    
    # Historical database
    HISTORICAL_DB_PATH = os.path.join(BASE_DIR, '..', 'data_2025', 'trips_2025.db')
    app.config['SQLALCHEMY_BINDS'] = {
        'main': f'sqlite:///{DB_PATH}',
        'historical': f'sqlite:///{HISTORICAL_DB_PATH}'
    }
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
    }
    
    print(f"✅ Database path: {DB_PATH}")
    print(f"✅ Historical DB path: {HISTORICAL_DB_PATH}")
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Import routes
    from app.routes.auth import auth_bp
    from app.routes.trips import trips_bp
    from app.routes.trips_2025 import trips2025_bp
    from app.routes.health import health_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(trips2025_bp)
    app.register_blueprint(health_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        from app.models import User
        
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
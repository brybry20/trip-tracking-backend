import os
from flask import Flask
import mongoengine as me
from flask_login import LoginManager
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-this')
    
    # Connect to MongoDB
    me.connect(host=app.config['MONGO_URI'])
    
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
                 "*"
             ],
             methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
             expose_headers=["Content-Type", "Authorization"])
    else:
        # Production (Render)
        CORS(app, 
             supports_credentials=True, 
             origins=[
                 "https://trip-tracking-backend.onrender.com",
                 "https://trip-tracking-backend-egfp.onrender.com",
                 "https://trip-tracking-frontend.onrender.com",
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
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        try:
            return User.objects(id=user_id).first()
        except:
            return None
    
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
    
    # CREATE ADMIN USER IF NOT EXISTS
    with app.app_context():
        from app.models import User
        
        try:
            admin = User.objects(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    role='admin'
                )
                admin.save()
                print("="*50)
                print("✅ ADMIN CREATED IN MONGODB!")
                print("Username: admin")
                print("Password: admin123")
                print("="*50)
        except Exception as e:
            print(f"Error checking/creating admin: {e}")
    
    return app

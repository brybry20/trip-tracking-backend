import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user, login_user
from app.models import User

# Secret key for JWT (store in environment variable in production)
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-this')

def generate_token(user_id, username, role):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def token_required(f):
    """Decorator to check if request has valid token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing!'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token is invalid or expired!'}), 401
        
        # Check if token matches the user's current token
        user = User.objects(id=payload['user_id']).first()
        if not user or user.current_token != token:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401
        
        # Update last active time
        user.last_active = datetime.utcnow()
        user.save()
        
        return f(*args, **kwargs)
    return decorated

def logout_user_from_all_devices(user_id):
    """Logout user from all devices by invalidating all tokens"""
    user = User.objects(id=user_id).first()
    if user:
        user.current_token = None
        user.token_created_at = None
        user.save()
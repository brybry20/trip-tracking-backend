from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Driver
from app.utils.auth import generate_token, verify_token, token_required, logout_user_from_all_devices
from datetime import datetime
import jwt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Handle OPTIONS preflight requests
@auth_bp.route('/login', methods=['OPTIONS'])
@auth_bp.route('/register', methods=['OPTIONS'])
@auth_bp.route('/logout', methods=['OPTIONS'])
@auth_bp.route('/check', methods=['OPTIONS'])
@auth_bp.route('/verify-token', methods=['OPTIONS'])
def handle_options():
    return '', 200

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        device_id = data.get('device_id', 'web')  # For mobile, send unique device ID
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Check if user is already logged in on another device/browser
            if user.current_token:
                # Optional: Send warning but still allow login
                # For now, we'll invalidate the old session
                pass
            
            # Generate new token
            token = generate_token(user.id, user.username, user.role)
            
            # Save token to user record
            user.current_token = token
            user.token_created_at = datetime.utcnow()
            user.last_active = datetime.utcnow()
            db.session.commit()
            
            # Also use Flask-Login for session management
            login_user(user)
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'role': user.role,
                'username': user.username,
                'token': token,
                'expires_in': 86400  # 24 hours in seconds
            })
        
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token_route():
    """Verify if current token is still valid"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'valid': False, 'message': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'valid': False, 'message': 'Token expired'}), 401
        
        # Check if token matches database
        user = User.query.get(payload['user_id'])
        if not user or user.current_token != token:
            return jsonify({'valid': False, 'message': 'Session invalid'}), 401
        
        return jsonify({'valid': True, 'user': {'username': user.username, 'role': user.role}})
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        # Invalidate token
        current_user.current_token = None
        current_user.token_created_at = None
        db.session.commit()
        
        logout_user()
        return jsonify({'success': True, 'message': 'Logged out'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout-all', methods=['POST'])
@login_required
def logout_all_devices():
    """Logout from all devices"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        
        logout_user_from_all_devices(user_id)
        return jsonify({'success': True, 'message': 'Logged out from all devices'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check existing
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username exists'}), 400
        
        if Driver.query.filter_by(license_number=data['license_number']).first():
            return jsonify({'success': False, 'message': 'License exists'}), 400
        
        if Driver.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email exists'}), 400
        
        # Create user
        new_user = User(
            username=data['username'],
            password_hash=generate_password_hash(data['password']),
            role='driver'
        )
        db.session.add(new_user)
        db.session.flush()
        
        # Create driver
        new_driver = Driver(
            user_id=new_user.id,
            full_name=data['full_name'],
            phone=data['phone'],
            license_number=data['license_number'],
            email=data['email']
        )
        db.session.add(new_driver)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/check', methods=['GET'])
def check():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'role': current_user.role,
            'username': current_user.username
        })
    return jsonify({'authenticated': False})

@auth_bp.route('/drivers', methods=['GET'])
@login_required
def get_all_drivers():
    try:
        if current_user.role == 'driver':
            driver = Driver.query.filter_by(user_id=current_user.id).first()
            if driver:
                return jsonify([{
                    'id': driver.id,
                    'full_name': driver.full_name,
                    'phone': driver.phone,
                    'license_number': driver.license_number,
                    'email': driver.email,
                    'username': current_user.username
                }])
            return jsonify([])
        
        drivers = Driver.query.all()
        drivers_list = []
        for driver in drivers:
            username = driver.user.username if driver.user else None
            drivers_list.append({
                'id': driver.id,
                'full_name': driver.full_name,
                'phone': driver.phone,
                'license_number': driver.license_number,
                'email': driver.email,
                'username': username,
                'created_at': driver.created_at.strftime('%Y-%m-%d') if driver.created_at else None
            })
        
        return jsonify(drivers_list)
    except Exception as e:
        print("Error in get_all_drivers:", str(e))
        return jsonify({'error': str(e)}), 500
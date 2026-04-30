from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
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
        
        user = User.objects(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Check if user is already logged in on another device/browser
            if user.current_token:
                # Optional: Send warning but still allow login
                # For now, we'll invalidate the old session
                pass
            
            # Generate new token
            token = generate_token(str(user.id), user.username, user.role)
            
            # Save token to user record
            user.current_token = token
            user.token_created_at = datetime.utcnow()
            user.last_active = datetime.utcnow()
            user.save()
            
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
        user = User.objects(id=payload['user_id']).first()
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
        current_user.save()
        
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
        if User.objects(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username exists'}), 400
        
        if Driver.objects(license_number=data['license_number']).first():
            return jsonify({'success': False, 'message': 'License exists'}), 400
        
        if Driver.objects(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email exists'}), 400
        
        # Create user
        new_user = User(
            username=data['username'],
            password_hash=generate_password_hash(data['password']),
            role='driver'
        )
        new_user.save()
        
        # Create driver
        new_driver = Driver(
            user=new_user,
            full_name=data['full_name'],
            phone=data['phone'],
            license_number=data['license_number'],
            email=data['email']
        )
        new_driver.save()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful!'
        })
    except Exception as e:
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
            driver = Driver.objects(user=current_user.id).first()
            if driver:
                return jsonify([{
                    'id': str(driver.id),
                    'full_name': driver.full_name,
                    'phone': driver.phone,
                    'license_number': driver.license_number,
                    'email': driver.email,
                    'username': current_user.username
                }])
            return jsonify([])
        
        drivers = Driver.objects.all()
        drivers_list = []
        for driver in drivers:
            username = driver.user.username if driver.user else None
            drivers_list.append({
                'id': str(driver.id),
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

@auth_bp.route('/drivers/<driver_id>', methods=['PUT'])
@login_required
def update_driver(driver_id):
    """Update driver details (Admin only)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        driver = Driver.objects(id=driver_id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Driver not found'}), 404
        
        # Check if license or email already exists for other drivers
        if 'license_number' in data and data['license_number'] != driver.license_number:
            if Driver.objects(license_number=data['license_number'], id__ne=driver_id).first():
                return jsonify({'success': False, 'message': 'License number already exists'}), 400
                
        if 'email' in data and data['email'] != driver.email:
            if Driver.objects(email=data['email'], id__ne=driver_id).first():
                return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        # Update driver details
        driver.full_name = data.get('full_name', driver.full_name)
        driver.phone = data.get('phone', driver.phone)
        driver.license_number = data.get('license_number', driver.license_number)
        driver.email = data.get('email', driver.email)
        driver.save()
        
        # If username is provided, update associated user
        if 'username' in data and driver.user:
            if User.objects(username=data['username'], id__ne=driver.user.id).first():
                return jsonify({'success': False, 'message': 'Username already exists'}), 400
            driver.user.username = data['username']
            driver.user.save()
            
        return jsonify({'success': True, 'message': 'Driver updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/drivers/<driver_id>', methods=['DELETE'])
@login_required
def delete_driver(driver_id):
    """Delete a driver and their associated user account (Admin only)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        driver = Driver.objects(id=driver_id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Driver not found'}), 404
        
        # Store user reference
        user = driver.user
        
        # Delete driver record
        driver.delete()
        
        # Delete user account if it exists
        if user:
            user.delete()
            
        return jsonify({'success': True, 'message': 'Driver and associated account deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
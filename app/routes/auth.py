from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Driver

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'role': user.role,
                'username': user.username
            })
        
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username exists'}), 400
        
        if Driver.query.filter_by(license_number=data['license_number']).first():
            return jsonify({'success': False, 'message': 'License exists'}), 400
        
        if Driver.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email exists'}), 400
        
        new_user = User(
            username=data['username'],
            password_hash=generate_password_hash(data['password']),
            role='driver'
        )
        db.session.add(new_user)
        db.session.flush()
        
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
        return jsonify({'success': False, 'error': str(e)}), 500
    
@auth_bp.route('/drivers', methods=['GET'])
@login_required
def get_all_drivers():
    """Get all drivers (for admin use)"""
    try:
        # Only admin can view all drivers
        if current_user.role != 'admin':
            # If driver, return only their own info
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
        
        # Admin view - all drivers
        drivers = Driver.query.all()
        drivers_list = []
        for driver in drivers:
            drivers_list.append({
                'id': driver.id,
                'full_name': driver.full_name,
                'phone': driver.phone,
                'license_number': driver.license_number,
                'email': driver.email,
                'username': driver.user.username if driver.user else None,
                'created_at': driver.created_at.strftime('%Y-%m-%d') if driver.created_at else None
            })
        
        return jsonify(drivers_list)
    except Exception as e:
        print("Error in get_all_drivers:", str(e))
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out'})

@auth_bp.route('/check', methods=['GET'])
def check():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'role': current_user.role,
            'username': current_user.username
        })
    return jsonify({'authenticated': False})
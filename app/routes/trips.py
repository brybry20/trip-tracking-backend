from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Trip, Driver, Invoice, Check
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone, timedelta

# Philippines timezone
PH_TIMEZONE = timezone(timedelta(hours=8))

trips_bp = Blueprint('trips', __name__, url_prefix='/trips')

# ========== GET ALL DRIVERS ==========
@trips_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        users = User.query.filter_by(role='driver').all()
        users_list = []
        for user in users:
            driver = Driver.query.filter_by(user_id=user.id).first()
            users_list.append({
                'id': user.id,
                'username': user.username,
                'full_name': driver.full_name if driver else user.username,
                'email': driver.email if driver else None,
                'phone': driver.phone if driver else None,
                'license_number': driver.license_number if driver else None,
                'role': user.role,
            })
        return jsonify(users_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== RESET PASSWORD ==========
@trips_bp.route('/reset-password', methods=['POST'])
@login_required
def reset_password():
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        if not user_id or not new_password:
            return jsonify({'success': False, 'message': 'User ID and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if user.role != 'driver':
            return jsonify({'success': False, 'message': 'Can only reset passwords for drivers'}), 400
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Password for {user.username} has been reset'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== GET ALL TRIPS ==========
@trips_bp.route('', methods=['GET'])
@login_required
def get_trips():
    try:
        if current_user.role == 'admin':
            trips = Trip.query.all()
        else:
            driver = Driver.query.filter_by(user_id=current_user.id).first()
            if not driver:
                return jsonify([])
            trips = Trip.query.filter_by(driver_id=driver.id).all()
        
        trips_list = []
        for trip in trips:
            invoices = []
            for inv in trip.invoices:
                invoices.append({'id': inv.id, 'invoice_no': inv.invoice_no, 'amount': inv.amount})
            
            checks = []
            for chk in trip.checks:
                checks.append({'id': chk.id, 'check_no': chk.check_no, 'amount': chk.amount})
            
            trips_list.append({
                'id': trip.id,
                'driver_id': trip.driver_id,
                'driver_name': trip.driver_name,
                'date': trip.date,
                'helper': trip.helper,
                'dealer': trip.dealer,
                'time_departure': trip.time_departure,
                'time_arrival': trip.time_arrival,
                'time_unload_end': trip.time_unload_end,
                'is_completed': trip.is_completed,
                'odometer': trip.odometer,
                'invoices': invoices,
                'checks': checks,
                'location_lat': trip.location_lat,
                'location_lng': trip.location_lng,
            })
        return jsonify(trips_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== START TRIP ==========
@trips_bp.route('', methods=['POST', 'OPTIONS'])
@login_required
def create_trip():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if current_user.role != 'driver':
            return jsonify({'success': False, 'message': 'Only drivers can create trips'}), 403
        
        data = request.get_json()
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Driver profile not found'}), 404
        
        now_ph = datetime.now(PH_TIMEZONE)
        time_departure_str = now_ph.strftime('%H:%M')
        
        location = data.get('location', {})
        
        new_trip = Trip(
            driver_id=driver.id,
            driver_name=driver.full_name,
            date=data['date'],
            helper=data.get('helper', ''),
            dealer=data.get('dealer', ''),
            time_departure=time_departure_str,
            time_arrival=None,
            time_unload_end=None,
            is_completed=False,
            odometer=None,
            location_lat=location.get('latitude'),
            location_lng=location.get('longitude'),
        )
        
        db.session.add(new_trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trip_id': new_trip.id,
            'time_departure': time_departure_str,
        })
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== ARRIVE ==========
@trips_bp.route('/<int:trip_id>/arrive', methods=['POST', 'OPTIONS'])
@login_required
def record_arrival(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver_id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not trip.time_departure:
            return jsonify({'success': False, 'message': 'Must start trip first'}), 400
        
        if trip.time_arrival:
            return jsonify({'success': False, 'message': 'Arrival already recorded'}), 400
        
        now_ph = datetime.now(PH_TIMEZONE)
        time_arrival_str = now_ph.strftime('%H:%M')
        
        trip.time_arrival = time_arrival_str
        db.session.commit()
        
        return jsonify({
            'success': True,
            'time_arrival': time_arrival_str,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== END TRIP ==========
@trips_bp.route('/<int:trip_id>/end-trip', methods=['POST', 'OPTIONS'])
@login_required
def end_trip(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver_id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not trip.time_departure:
            return jsonify({'success': False, 'message': 'Must start trip first'}), 400
        
        if trip.time_unload_end:
            return jsonify({'success': False, 'message': 'Trip already ended'}), 400
        
        now_ph = datetime.now(PH_TIMEZONE)
        time_unload_end_str = now_ph.strftime('%H:%M')
        
        trip.time_unload_end = time_unload_end_str
        trip.is_completed = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'time_unload_end': time_unload_end_str,
            'total_duration': 'Trip completed'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== UPDATE TRIP ==========
@trips_bp.route('/<int:trip_id>', methods=['PUT', 'OPTIONS'])
@login_required
def update_trip(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver_id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'helper' in data:
            trip.helper = data['helper']
        if 'dealer' in data:
            trip.dealer = data['dealer']
        if 'odometer' in data:
            try:
                trip.odometer = float(data['odometer']) if data['odometer'] else None
            except:
                trip.odometer = None
        
        # Update invoices
        if 'invoices' in data:
            Invoice.query.filter_by(trip_id=trip.id).delete()
            for inv in data['invoices']:
                if inv.get('invoice_no') and inv.get('amount'):
                    try:
                        invoice = Invoice(trip_id=trip.id, invoice_no=inv['invoice_no'], amount=float(inv['amount']))
                        db.session.add(invoice)
                    except:
                        pass
        
        # Update checks
        if 'checks' in data:
            Check.query.filter_by(trip_id=trip.id).delete()
            for chk in data['checks']:
                if chk.get('check_no') and chk.get('amount'):
                    try:
                        check = Check(trip_id=trip.id, check_no=chk['check_no'], amount=float(chk['amount']))
                        db.session.add(check)
                    except:
                        pass
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Trip updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== DELETE TRIP ==========
@trips_bp.route('/<int:trip_id>', methods=['DELETE', 'OPTIONS'])
@login_required
def delete_trip(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver_id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        db.session.delete(trip)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Trip deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
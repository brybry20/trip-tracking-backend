from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
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
        
        users = User.objects(role='driver').all()
        users_list = []
        for user in users:
            driver = Driver.objects(user=user).first()
            users_list.append({
                'id': str(user.id),
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
        
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if user.role != 'driver':
            return jsonify({'success': False, 'message': 'Can only reset passwords for drivers'}), 400
        
        user.password_hash = generate_password_hash(new_password)
        user.save()
        
        return jsonify({'success': True, 'message': f'Password for {user.username} has been reset'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== GET ALL TRIPS (with totals and distance) ==========
@trips_bp.route('', methods=['GET'])
@login_required
def get_trips():
    try:
        if current_user.role == 'admin':
            trips = Trip.objects.all()
        else:
            driver = Driver.objects(user=current_user.id).first()
            if not driver:
                return jsonify([])
            trips = Trip.objects(driver=driver).all()
        
        trips_list = []
        for trip in trips:
            invoices = []
            total_invoices = 0
            for inv in trip.invoices:
                invoices.append({'invoice_no': inv.invoice_no, 'amount': inv.amount})
                total_invoices += inv.amount
            
            checks = []
            total_checks = 0
            for chk in trip.checks:
                checks.append({'check_no': chk.check_no, 'amount': chk.amount})
                total_checks += chk.amount
            
            # Compute distance traveled
            distance = None
            if trip.departure_odometer and trip.arrival_odometer:
                distance = trip.arrival_odometer - trip.departure_odometer
                if distance < 0:
                    distance = 0
            
            trips_list.append({
                'id': str(trip.id),
                'driver_id': str(trip.driver.id) if trip.driver else None,
                'driver_name': trip.driver_name,
                'date': trip.date,
                'helper': trip.helper,
                'dealer': trip.dealer,
                'time_departure': trip.time_departure,
                'time_arrival': trip.time_arrival,
                'time_unload_end': trip.time_unload_end,
                'is_completed': trip.is_completed,
                'departure_odometer': trip.departure_odometer,
                'arrival_odometer': trip.arrival_odometer,
                'distance': distance,
                'odometer': trip.odometer,
                'total_invoices': total_invoices,
                'total_checks': total_checks,
                'invoices': invoices,
                'checks': checks,
                'location_lat': trip.location_lat,
                'location_lng': trip.location_lng,
            })
        return jsonify(trips_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== START TRIP (with departure odometer) ==========
@trips_bp.route('', methods=['POST', 'OPTIONS'])
@login_required
def create_trip():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if current_user.role != 'driver':
            return jsonify({'success': False, 'message': 'Only drivers can create trips'}), 403
        
        data = request.get_json()
        driver = Driver.objects(user=current_user.id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Driver profile not found'}), 404
        
        now_ph = datetime.now(PH_TIMEZONE)
        time_departure_str = now_ph.strftime('%H:%M')
        
        location = data.get('location', {})
        
        # Get departure odometer from request
        departure_odometer = data.get('departure_odometer')
        if departure_odometer:
            try:
                departure_odometer = float(departure_odometer)
            except:
                departure_odometer = None
        
        new_trip = Trip(
            driver=driver,
            driver_name=driver.full_name,
            date=data['date'],
            helper=data.get('helper', ''),
            dealer=data.get('dealer', ''),
            time_departure=time_departure_str,
            is_completed=False,
            departure_odometer=departure_odometer,
            odometer=departure_odometer,  # For backward compatibility
            location_lat=location.get('latitude'),
            location_lng=location.get('longitude'),
        )
        
        new_trip.save()
        
        return jsonify({
            'success': True,
            'trip_id': str(new_trip.id),
            'time_departure': time_departure_str,
            'departure_odometer': departure_odometer
        })
    except Exception as e:
        print("Error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== ARRIVE ==========
@trips_bp.route('/<string:trip_id>/arrive', methods=['POST', 'OPTIONS'])
@login_required
def record_arrival(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.objects(id=trip_id).first()
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.objects(user=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver.id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not trip.time_departure:
            return jsonify({'success': False, 'message': 'Must start trip first'}), 400
        
        if trip.time_arrival:
            return jsonify({'success': False, 'message': 'Arrival already recorded'}), 400
        
        now_ph = datetime.now(PH_TIMEZONE)
        time_arrival_str = now_ph.strftime('%H:%M')
        
        trip.time_arrival = time_arrival_str
        trip.save()
        
        return jsonify({
            'success': True,
            'time_arrival': time_arrival_str,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== END TRIP ==========
@trips_bp.route('/<string:trip_id>/end-trip', methods=['POST', 'OPTIONS'])
@login_required
def end_trip(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.objects(id=trip_id).first()
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.objects(user=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver.id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if not trip.time_departure:
            return jsonify({'success': False, 'message': 'Must start trip first'}), 400
        
        if trip.time_unload_end:
            return jsonify({'success': False, 'message': 'Trip already ended'}), 400
        
        now_ph = datetime.now(PH_TIMEZONE)
        time_unload_end_str = now_ph.strftime('%H:%M')
        
        trip.time_unload_end = time_unload_end_str
        trip.is_completed = True
        trip.save()
        
        # Calculate distance if both odometers are present
        distance = None
        if trip.departure_odometer and trip.arrival_odometer:
            distance = trip.arrival_odometer - trip.departure_odometer
            if distance < 0:
                distance = 0
        
        return jsonify({
            'success': True,
            'time_unload_end': time_unload_end_str,
            'total_duration': 'Trip completed',
            'distance': distance
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== UPDATE TRIP (with arrival odometer and totals) ==========
@trips_bp.route('/<string:trip_id>', methods=['PUT', 'OPTIONS'])
@login_required
def update_trip(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.objects(id=trip_id).first()
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.objects(user=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver.id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'helper' in data:
            trip.helper = data['helper']
        if 'dealer' in data:
            trip.dealer = data['dealer']
        
        # Handle arrival odometer
        if 'arrival_odometer' in data:
            try:
                arrival_odometer = float(data['arrival_odometer']) if data['arrival_odometer'] else None
                trip.arrival_odometer = arrival_odometer
                # Update odometer for backward compatibility
                if arrival_odometer:
                    trip.odometer = arrival_odometer
            except:
                pass
        
        # Handle departure odometer (for edits)
        if 'departure_odometer' in data:
            try:
                trip.departure_odometer = float(data['departure_odometer']) if data['departure_odometer'] else None
            except:
                pass
        
        # Handle old odometer field (backward compatibility)
        if 'odometer' in data and 'arrival_odometer' not in data:
            try:
                trip.odometer = float(data['odometer']) if data['odometer'] else None
            except:
                trip.odometer = None
        
        # Update invoices
        if 'invoices' in data:
            trip.invoices = []
            for inv in data['invoices']:
                if inv.get('invoice_no') and inv.get('amount'):
                    try:
                        invoice = Invoice(invoice_no=inv['invoice_no'], amount=float(inv['amount']))
                        trip.invoices.append(invoice)
                    except:
                        pass
        
        # Update checks
        if 'checks' in data:
            trip.checks = []
            for chk in data['checks']:
                if chk.get('check_no') and chk.get('amount'):
                    try:
                        check = Check(check_no=chk['check_no'], amount=float(chk['amount']))
                        trip.checks.append(check)
                    except:
                        pass
        
        trip.save()
        
        # Compute totals for response
        total_invoices = sum(inv.amount for inv in trip.invoices)
        total_checks = sum(chk.amount for chk in trip.checks)
        
        # Compute distance
        distance = None
        if trip.departure_odometer and trip.arrival_odometer:
            distance = trip.arrival_odometer - trip.departure_odometer
            if distance < 0:
                distance = 0
        
        return jsonify({
            'success': True, 
            'message': 'Trip updated',
            'total_invoices': total_invoices,
            'total_checks': total_checks,
            'distance': distance,
            'departure_odometer': trip.departure_odometer,
            'arrival_odometer': trip.arrival_odometer
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== DELETE TRIP ==========
@trips_bp.route('/<string:trip_id>', methods=['DELETE', 'OPTIONS'])
@login_required
def delete_trip(trip_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        trip = Trip.objects(id=trip_id).first()
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        driver = Driver.objects(user=current_user.id).first()
        if current_user.role != 'admin':
            if not driver or trip.driver.id != driver.id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        trip.delete()
        
        return jsonify({'success': True, 'message': 'Trip deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== GET SINGLE TRIP (with details) ==========
@trips_bp.route('/<string:trip_id>', methods=['GET'])
@login_required
def get_trip(trip_id):
    try:
        trip = Trip.objects(id=trip_id).first()
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404
        
        if current_user.role != 'admin':
            driver = Driver.objects(user=current_user.id).first()
            if not driver or trip.driver.id != driver.id:
                return jsonify({'error': 'Unauthorized'}), 403
        
        invoices = []
        total_invoices = 0
        for inv in trip.invoices:
            invoices.append({'invoice_no': inv.invoice_no, 'amount': inv.amount})
            total_invoices += inv.amount
        
        checks = []
        total_checks = 0
        for chk in trip.checks:
            checks.append({'check_no': chk.check_no, 'amount': chk.amount})
            total_checks += chk.amount
        
        # Compute distance
        distance = None
        if trip.departure_odometer and trip.arrival_odometer:
            distance = trip.arrival_odometer - trip.departure_odometer
            if distance < 0:
                distance = 0
        
        return jsonify({
            'id': str(trip.id),
            'driver_id': str(trip.driver.id) if trip.driver else None,
            'driver_name': trip.driver_name,
            'date': trip.date,
            'helper': trip.helper,
            'dealer': trip.dealer,
            'time_departure': trip.time_departure,
            'time_arrival': trip.time_arrival,
            'time_unload_end': trip.time_unload_end,
            'is_completed': trip.is_completed,
            'departure_odometer': trip.departure_odometer,
            'arrival_odometer': trip.arrival_odometer,
            'distance': distance,
            'odometer': trip.odometer,
            'total_invoices': total_invoices,
            'total_checks': total_checks,
            'invoices': invoices,
            'checks': checks,
            'location_lat': trip.location_lat,
            'location_lng': trip.location_lng,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
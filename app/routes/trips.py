from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Trip, Driver, Invoice, Check
from werkzeug.security import generate_password_hash
from datetime import datetime
import pytz

# ✅ Set Philippines timezone
PH_TIMEZONE = pytz.timezone('Asia/Manila')

trips_bp = Blueprint('trips', __name__, url_prefix='/trips')

# ========== GET ALL DRIVERS (FOR ADMIN) ==========
@trips_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Get all drivers only (admin only)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # ✅ Kunin lahat ng users na role = 'driver'
        users = User.query.filter_by(role='driver').all()
        users_list = []
        
        for user in users:
            # ✅ Kunin ang driver profile para sa full details
            driver = Driver.query.filter_by(user_id=user.id).first()
            
            users_list.append({
                'id': user.id,
                'username': user.username,
                'full_name': driver.full_name if driver else user.username,
                'email': driver.email if driver else None,
                'phone': driver.phone if driver else None,
                'license_number': driver.license_number if driver else None,
                'role': user.role,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else None
            })
        
        print(f"Returning {len(users_list)} drivers with full details")
        return jsonify(users_list)
    except Exception as e:
        print("Error in get_users:", str(e))
        return jsonify({'error': str(e)}), 500

# ========== RESET PASSWORD ==========
@trips_bp.route('/reset-password', methods=['POST'])
@login_required
def reset_password():
    """Reset password for a driver (admin only)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        print(f"🔄 Resetting password for user_id: {user_id}")
        
        if not user_id or not new_password:
            return jsonify({'success': False, 'message': 'User ID and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        # Kunin ang user
        user = User.query.get(user_id)
        if not user:
            print(f"❌ User not found with ID: {user_id}")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # ✅ I-verify na driver ang nirereset-an (hindi admin)
        if user.role != 'driver':
            print(f"❌ User {user.username} is {user.role}, not a driver")
            return jsonify({'success': False, 'message': 'Can only reset passwords for drivers'}), 400
        
        # Update password
        old_hash = user.password_hash  # For logging
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        print(f"✅ Password updated for user: {user.username} (ID: {user.id})")
        print(f"   Old hash: {old_hash[:30]}...")
        print(f"   New hash: {user.password_hash[:30]}...")
        
        return jsonify({
            'success': True,
            'message': f'Password for {user.username} has been reset successfully'
        })
        
    except Exception as e:
        print("❌ Error in reset_password:", str(e))
        db.session.rollback()
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
            # Get invoices for this trip
            invoices = []
            for inv in trip.invoices:
                invoices.append({
                    'id': inv.id,
                    'invoice_no': inv.invoice_no,
                    'amount': inv.amount
                })
            
            # Get checks for this trip
            checks = []
            for chk in trip.checks:
                checks.append({
                    'id': chk.id,
                    'check_no': chk.check_no,
                    'amount': chk.amount,
                    'bank': chk.bank,
                    'account_no': chk.account_no,
                    'check_date': chk.check_date
                })
            
            trips_list.append({
                'id': trip.id,
                'driver_id': trip.driver_id,
                'driver_name': trip.driver_name,
                'date': trip.date,
                'helper': trip.helper,
                'dealer': trip.dealer,
                'time_in': trip.time_in,
                'time_out': trip.time_out,
                'odometer': trip.odometer,
                'invoice_no': trip.invoice_no,
                'amount': trip.amount,
                'invoices': invoices,
                'checks': checks,
                'location_lat': trip.location_lat,
                'location_lng': trip.location_lng,
                'location_accuracy': trip.location_accuracy,
                'location_timestamp': trip.location_timestamp,
                'created_at': trip.created_at.strftime('%Y-%m-%d %H:%M') if trip.created_at else None
            })
        
        return jsonify(trips_list)
    except Exception as e:
        print("Error in get_trips:", str(e))
        return jsonify({'error': str(e)}), 500


# ========== START TRIP (CREATE + TIME IN) ==========
@trips_bp.route('', methods=['POST'])
@login_required
def create_trip():
    try:
        if current_user.role != 'driver':
            return jsonify({'success': False, 'message': 'Only drivers can create trips'}), 403
        
        data = request.get_json()
        print("Received start trip data:", data)
        
        # Get driver ID
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Driver profile not found'}), 404
        
        # Get current time in Philippines (Asia/Manila)
        now_ph = datetime.now(PH_TIMEZONE)
        time_in_str = now_ph.strftime('%H:%M')
        
        # Extract location data
        location = data.get('location', {})
        
        # Create main trip with ONLY basic info + TIME IN
        new_trip = Trip(
            driver_id=driver.id,
            driver_name=driver.full_name,
            date=data['date'],
            helper=data.get('helper', ''),
            dealer=data.get('dealer', ''),
            time_in=time_in_str,
            time_out=None,
            odometer=None,
            invoice_no='',
            amount=0,
            location_lat=location.get('latitude'),
            location_lng=location.get('longitude'),
            location_accuracy=location.get('accuracy'),
            location_timestamp=location.get('timestamp')
        )
        
        db.session.add(new_trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trip_id': new_trip.id,
            'time_in': time_in_str,
            'message': f'Trip started at {time_in_str} (PHT)'
        })
    except Exception as e:
        print("Error in create_trip:", str(e))
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== UPDATE TRIP (ADD INVOICES, CHECKS, ODOMETER) ==========
@trips_bp.route('/<int:trip_id>', methods=['PUT'])
@login_required
def update_trip(trip_id):
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        # Check ownership
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if not driver or trip.driver_id != driver.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Check if trip already ended
        if trip.time_out:
            return jsonify({'success': False, 'message': 'Cannot update trip after it has ended'}), 400
        
        data = request.get_json()
        
        # Update allowed fields (but NOT time_in/time_out)
        trip.helper = data.get('helper', trip.helper)
        trip.dealer = data.get('dealer', trip.dealer)
        trip.odometer = float(data.get('odometer', 0)) if data.get('odometer') else None
        
        # Delete old invoices
        Invoice.query.filter_by(trip_id=trip.id).delete()
        
        # Create new invoices
        invoice_count = 0
        for inv in data.get('invoices', []):
            if inv.get('invoice_no') and inv.get('amount'):
                invoice = Invoice(
                    trip_id=trip.id,
                    invoice_no=inv['invoice_no'],
                    amount=float(inv['amount'])
                )
                db.session.add(invoice)
                invoice_count += 1
        
        # Delete old checks
        Check.query.filter_by(trip_id=trip.id).delete()
        
        # Create new checks
        check_count = 0
        for chk in data.get('checks', []):
            if chk.get('check_no') and chk.get('amount'):
                check = Check(
                    trip_id=trip.id,
                    check_no=chk['check_no'],
                    amount=float(chk['amount']),
                    bank=chk.get('bank', ''),
                    account_no=chk.get('account_no', ''),
                    check_date=chk.get('check_date', '')
                )
                db.session.add(check)
                check_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Trip updated successfully with {invoice_count} invoice(s) and {check_count} check(s)'
        })
    except Exception as e:
        print("Error in update_trip:", str(e))
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== END TRIP (TIME OUT) ==========
@trips_bp.route('/<int:trip_id>/time-out', methods=['POST'])
@login_required
def time_out(trip_id):
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        # Check if trip belongs to current driver
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if not driver or trip.driver_id != driver.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Check if time in exists
        if not trip.time_in:
            return jsonify({'success': False, 'message': 'Must start trip first'}), 400
        
        # Check if already timed out
        if trip.time_out:
            return jsonify({'success': False, 'message': 'Trip already ended'}), 400
        
        # Get current time in Philippines
        now_ph = datetime.now(PH_TIMEZONE)
        time_out_str = now_ph.strftime('%H:%M')
        
        # Update trip
        trip.time_out = time_out_str
        db.session.commit()
        
        # Calculate duration
        time_in = datetime.strptime(trip.time_in, '%H:%M')
        time_out = datetime.strptime(time_out_str, '%H:%M')
        duration_minutes = (time_out - time_in).seconds // 60
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        return jsonify({
            'success': True,
            'message': 'Trip ended successfully',
            'time_out': time_out_str,
            'duration': f'{hours}h {minutes}m'
        })
    except Exception as e:
        print("Error in time_out:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== DELETE TRIP ==========
@trips_bp.route('/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_trip(trip_id):
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        # Check ownership
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if not driver or trip.driver_id != driver.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        db.session.delete(trip)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Trip deleted successfully'})
    except Exception as e:
        print("Error in delete_trip:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== GET SINGLE TRIP ==========
@trips_bp.route('/<int:trip_id>', methods=['GET'])
@login_required
def get_trip(trip_id):
    try:
        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404
        
        # Check authorization
        if current_user.role != 'admin':
            driver = Driver.query.filter_by(user_id=current_user.id).first()
            if not driver or trip.driver_id != driver.id:
                return jsonify({'error': 'Unauthorized'}), 403
        
        # Get invoices
        invoices = []
        for inv in trip.invoices:
            invoices.append({
                'id': inv.id,
                'invoice_no': inv.invoice_no,
                'amount': inv.amount
            })
        
        # Get checks
        checks = []
        for chk in trip.checks:
            checks.append({
                'id': chk.id,
                'check_no': chk.check_no,
                'amount': chk.amount,
                'bank': chk.bank,
                'account_no': chk.account_no,
                'check_date': chk.check_date
            })
        
        return jsonify({
            'id': trip.id,
            'driver_id': trip.driver_id,
            'driver_name': trip.driver_name,
            'date': trip.date,
            'helper': trip.helper,
            'dealer': trip.dealer,
            'time_in': trip.time_in,
            'time_out': trip.time_out,
            'odometer': trip.odometer,
            'invoice_no': trip.invoice_no,
            'amount': trip.amount,
            'invoices': invoices,
            'checks': checks,
            'location_lat': trip.location_lat,
            'location_lng': trip.location_lng,
            'location_accuracy': trip.location_accuracy,
            'location_timestamp': trip.location_timestamp,
            'created_at': trip.created_at.strftime('%Y-%m-%d %H:%M') if trip.created_at else None
        })
    except Exception as e:
        print("Error in get_trip:", str(e))
        return jsonify({'error': str(e)}), 500
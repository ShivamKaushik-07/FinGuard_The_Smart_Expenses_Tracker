from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app.db_manager import db, Expense
from app.db_manager import db, User
import random,time
from flask import session
from datetime import datetime, timedelta
from app.utils import send_email_otp, send_sms_otp
from flask import flash, redirect, url_for, request
from app.db_manager import Signup
from app.db_manager import User
from datetime import datetime, timedelta, time
import time
import random
from werkzeug.security import generate_password_hash
from app.db_manager import Budget
from flask import jsonify
from flask_login import current_user
import os
from flask import send_file, abort

auth = Blueprint('auth', __name__)


@auth.route("/login", methods=["POST", "GET"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    
    user = Signup.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash("Incorrect email or password.", "error")
        return redirect(url_for("main.index", show_login="true"))

    login_user(user)
    session['user_id'] = user.id
    # 🔁 Redirect to dashboard (or any page using base.html)
    return redirect(url_for("main.dashboard"))




 # ✅ Ensure you import it correctly

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    resend_seconds = 0
    identifier = ""
    otp_sent = False

    if request.method == 'POST':
        identifier = request.form.get('identifier')
        user = Signup.query.filter((Signup.email == identifier) | (Signup.phone == identifier)).first()

        if user:
            now = datetime.utcnow()
            last_sent_str = session.get('otp_sent_time')

            # Convert string back to datetime if exists
            last_sent = datetime.fromisoformat(last_sent_str) if last_sent_str else None

            # Allow resend after 30 seconds
            if not last_sent or (now - last_sent).total_seconds() >= 30:
                otp = str(random.randint(100000, 999999))
                session['otp'] = otp
                session['otp_user_id'] = user.id
                session['otp_expiry'] = (now + timedelta(minutes=5)).isoformat()
                session['otp_sent_time'] = now.isoformat()
                session['identifier'] = identifier

                # ✅ Send OTP (your functions)
                send_email_otp(user.email, otp)
                send_sms_otp(user.phone, otp)

                otp_sent = True
                resend_seconds = 30
                flash("OTP sent successfully!", "info")
            else:
                otp_sent = True
                resend_seconds = max(0, 30 - int((now - last_sent).total_seconds()))
                flash("Please wait before requesting another OTP.", "warning")
        else:
            flash("No user found with that email or phone.", "danger")

    return render_template("forgot_password.html", otp_sent=otp_sent, identifier=identifier, resend_seconds=resend_seconds)


@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    error = None
    RESEND_INTERVAL = 30
    current_time = int(time.time())

    # Handle resend countdown
    otp_sent_time_raw = session.get("otp_sent_time")
    if otp_sent_time_raw:
        try:
            otp_sent_dt = datetime.fromisoformat(otp_sent_time_raw)
            otp_sent_seconds = int(otp_sent_dt.timestamp())
            seconds_since_sent = current_time - otp_sent_seconds
            resend_seconds = max(0, RESEND_INTERVAL - seconds_since_sent)
        except Exception as e:
            print("OTP time parse error:", e)
            resend_seconds = 0
    else:
        resend_seconds = 0

    # Handle POST form submission
    if request.method == 'POST':
        user_input = request.form.get("otp").strip()
        expected_otp = session.get("otp")  # ✅ Correct key here

        print("[DEBUG] Entered OTP:", user_input)
        print("[DEBUG] Expected OTP from session:", expected_otp)

        if user_input == expected_otp:
            flash("OTP Verified Successfully", "success")
            session['otp_verified'] = True

            identifier = session.get("identifier")
            user = Signup.query.filter_by(email=identifier).first() or Signup.query.filter_by(phone=identifier).first()

            if user:
                session['reset_user_id'] = user.id
                return redirect(url_for('auth.reset_password'))
            else:
                flash("User not found.", "danger")
                return redirect(url_for('auth.forgot_password'))
        else:
            error = "Incorrect OTP. Please try again."

    return render_template(
        "verify_otp.html",
        resend_seconds=resend_seconds,
        error=error,
        otp_sent=True,
        otp_verified=False
    )



@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    user_id = session.get('reset_user_id')
    if not user_id:
        flash("Session expired or unauthorized.", "danger")
        return redirect(url_for('auth.login'))

    user = Signup.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(request.url)

        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(request.url)

        user.password = generate_password_hash(new_password)
        db.session.commit()
        session.clear()
        flash("Password reset successful!", "success")
        return redirect(url_for('main.home'))  # ✅ Redirect to main page

    return render_template("reset_password.html")


@auth.route('/signup', methods=['POST'])
def signup():
    phone = request.form['phone']
    email = request.form['email']
    name = request.form['name']

    # 🔍 Check if user already exists
    existing_user = Signup.query.filter(
        (Signup.phone == phone) | (Signup.email == email)
    ).first()

    if existing_user:
        flash('A user with that phone or email already exists.', 'error')
        return redirect(url_for('main.index', show_signup='true'))

    # ✅ Create new user in the correct model
    new_user = Signup(
        name=name,
        email=email,
        phone=phone,
        password=generate_password_hash(request.form['password'])
    )

    db.session.add(new_user)    
    db.session.commit()
    flash('Signup successful. You can now log in.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/resend-otp')
def resend_otp():

    identifier = session.get("identifier")
    if not identifier:
        flash("Session expired. Please start again.", "warning")
        return redirect(url_for('auth.forgot_password'))

    # Detect if input is email or phone (very basic check)
    is_email = "@" in identifier

    # Find user based on input
    user = None
    if is_email:
        user = User.query.filter_by(email=identifier).first()
    else:
        user = User.query.filter_by(phone=identifier).first()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.forgot_password'))

    # Generate new OTP and set session
    new_otp = str(random.randint(100000, 999999))
    session['otp'] = new_otp
    session['otp_sent_time'] = datetime.utcnow().isoformat()

    # Send only to email or phone
    if is_email:
        send_email_otp(user.email, new_otp)
        flash("OTP sent to your email address.", "info")
    else:
        send_sms_otp(user.phone, new_otp)
        flash("OTP sent to your phone number.", "info")

    return redirect(url_for('auth.verify_otp'))


@auth.route('/set-budget', methods=['POST'])
@login_required
def set_budget():
    if not current_user.is_authenticated:
        flash('Please log in first.', 'error')
        return redirect(url_for('auth.login'))
        
    budget = int(request.form.get('budget'))
    limit = int(request.form.get('limit', 0))
    
    # Create new budget entry
    new_budget = Budget(
        amount=budget,
        limit=limit,
        user_id=current_user.id
    )
    db.session.add(new_budget)
    db.session.commit()
    
    flash('Budget and limit updated successfully!', 'success')
    return redirect(url_for('main.dashboard'))


@auth.route('/get_budget', methods=['GET'])
def get_budget():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'budget': user.budget,
        'limit': user.limit,
       

    })


@auth.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))



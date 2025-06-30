from flask import Blueprint, render_template, request, current_app, abort, redirect, url_for, flash, jsonify, session
from app.voice_input import capture_voice_input
from app.db_manager import db, Expense, User, Signup
from datetime import datetime
import re
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from PIL import Image
from collections import defaultdict
from app.db_manager import Budget
from flask import send_file
from flask_login import current_user, login_required
import csv
import pdfkit
from app.exports import export_expenses_to_csv_pdf
import logging
import sys
import os.path
from app.bill_scanner import extract_amount

main = Blueprint('main', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set Tesseract path explicitly
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    logger.info(f"Using Tesseract from: {TESSERACT_CMD}")
else:
    logger.error(f"Tesseract not found at: {TESSERACT_CMD}")

@main.route('/')
def index():
    notifications = []  # Initialize empty notifications
    if current_user.is_authenticated:
        # Get latest budget info for notifications
        latest_budget = Budget.query.filter_by(user_id=current_user.id).order_by(Budget.id.desc()).first()
        if latest_budget:
            # Get current month's expenses
            current_month_expenses = Expense.query.filter(
                Expense.user_id == current_user.id,
                db.extract('month', Expense.date) == datetime.now().month,
                db.extract('year', Expense.date) == datetime.now().year
            ).all()
            
            total_expenses = sum(exp.amount for exp in current_month_expenses)
            
            # Generate notifications based on budget status
            if total_expenses > latest_budget.amount:
                diff = total_expenses - latest_budget.amount
                notifications.append(f"🚨 You have exceeded your monthly budget by ₹{diff:,.2f}")
            elif total_expenses >= latest_budget.amount * 0.9:
                remaining = latest_budget.amount - total_expenses
                notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} left in your budget")
            
            # Add limit notifications
            if latest_budget.limit:
                if total_expenses >= latest_budget.limit:
                    notifications.append("🚨 Final Alert: You've crossed your spending limit!")
                elif total_expenses >= latest_budget.limit - 1000:
                    remaining = latest_budget.limit - total_expenses
                    notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} until spending limit")
    
    return render_template('index.html', notifications=notifications)

@main.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get current date info
        today = datetime.now()
        current_month = today.month
        current_year = today.year

        # Get only current user's expenses
        all_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.id.desc()).all()

        # Initialize empty defaults
        daily_labels = []
        daily_data = []
        monthly_labels = []
        monthly_data = []
        yearly_labels = []
        yearly_data = []
        pie_labels = []
        pie_data = []
        total_expenses = 0
        notifications = []

        if all_expenses:
            # 📊 Daily summary (Today's expenses grouped by hour)
            today_expenses = [exp for exp in all_expenses if exp.date.date() == today.date()]
            daily_summary = defaultdict(float)
            for exp in today_expenses:
                hour_label = exp.date.strftime('%I %p')  # e.g., "01 PM"
                daily_summary[hour_label] += exp.amount
            daily_labels = sorted(daily_summary.keys())
            daily_data = [daily_summary[hour] for hour in daily_labels]

            # 📅 Monthly summary (Current month's expenses grouped by day)
            current_month_expenses = [
                exp for exp in all_expenses
                if exp.date.month == current_month and exp.date.year == current_year
            ]
            monthly_summary = defaultdict(float)
            for exp in current_month_expenses:
                day_label = exp.date.strftime('%d %b')  # e.g., "06 Jul"
                monthly_summary[day_label] += exp.amount
            monthly_labels = sorted(monthly_summary.keys())
            monthly_data = [monthly_summary[day] for day in monthly_labels]

            # 🗓️ Yearly summary (Grouped by year)
            yearly_summary = defaultdict(float)
            for exp in all_expenses:
                year = exp.date.strftime('%Y')
                yearly_summary[year] += exp.amount
            yearly_labels = sorted(yearly_summary.keys())
            yearly_data = [yearly_summary[year] for year in yearly_labels]

            # 🥧 Pie chart summary by source
            source_summary = defaultdict(float)
            for exp in current_month_expenses:
                source = exp.source if exp.source else 'Other'
                source_summary[source] += exp.amount
            pie_labels = list(source_summary.keys())
            pie_data = list(source_summary.values())

            # 💰 Total expenses (current month)
            total_expenses = sum(exp.amount for exp in current_month_expenses)

        # 📘 Get latest budget info
        latest_budget = Budget.query.filter_by(user_id=current_user.id).order_by(Budget.id.desc()).first()
        current_budget = latest_budget.amount if latest_budget else 0
        current_limit = latest_budget.limit if latest_budget and latest_budget.limit else 0
        
        # 🔔 Notifications
        if current_budget > 0:
            if total_expenses > current_budget:
                diff = total_expenses - current_budget
                notifications.append(f"🚨 You have exceeded your monthly budget by ₹{diff:,.2f}")
            elif total_expenses >= current_budget * 0.9:
                remaining = current_budget - total_expenses
                notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} left in your budget")
            elif total_expenses >= current_budget * 0.8:
                remaining = current_budget - total_expenses
                notifications.append(f"ℹ️ Notice: ₹{remaining:,.2f} remaining in your budget")

        if current_limit > 0:
            if total_expenses >= current_limit:
                notifications.append("🚨 Final Alert: You've crossed your spending limit!")
            elif total_expenses >= current_limit - 1000:
                remaining = current_limit - total_expenses
                notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} until spending limit")
            elif total_expenses >= current_limit - 2000:
                remaining = current_limit - total_expenses
                notifications.append(f"ℹ️ Notice: ₹{remaining:,.2f} until spending limit")

        return render_template('dashboard.html',
                               expenses=all_expenses,
                               daily_labels=daily_labels,
                               daily_data=daily_data,
                               monthly_labels=monthly_labels,
                               monthly_data=monthly_data,
                               yearly_labels=yearly_labels,
                               yearly_data=yearly_data,
                               pie_labels=pie_labels,
                               pie_data=pie_data,
                               total_expenses=total_expenses,
                               current_budget=current_budget,
                               current_limit=current_limit,
                               notifications=notifications,
                               server_data={
                                   "totalExpenses": total_expenses,
                                   "currentBudget": current_budget,
                                   "currentLimit": current_limit,
                                   "notifications": notifications,
                                   "chartData": {
                                       "daily": {"labels": daily_labels, "data": daily_data, "type": "line", "color": "#60a5fa"},
                                       "monthly": {"labels": monthly_labels, "data": monthly_data, "type": "bar", "color": "#34d399"},
                                       "yearly": {"labels": yearly_labels, "data": yearly_data, "type": "bar", "color": "#fbbf24"},
                                       "pie": {"labels": pie_labels, "data": pie_data, "type": "doughnut", "color": "#a78bfa"}
                                   }
                               }
                               )

    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        flash("An error occurred while loading the dashboard. Please try again.", "error")
        return render_template('dashboard.html',
                               expenses=[],
                               daily_labels=[], daily_data=[],
                               monthly_labels=[], monthly_data=[],
                               yearly_labels=[], yearly_data=[],
                               pie_labels=[], pie_data=[],
                               total_expenses=0,
                               current_budget=0,
                               current_limit=0,
                               notifications=[])



def extract_amount(text_lines):
    """Extract amount from bill text using multiple patterns."""
    logger.debug("Starting amount extraction")
    amount = 0.0
    possible_amounts = []
    
    # Enhanced patterns for amount identification
    amount_patterns = [
        # Pattern: "Total: Rs. 1,234.56" or "Total: ₹1,234.56"
        r'(?:total|amount|payable|grand total|net amount|sum|bill amount).*?(?:rs\.?|inr|₹)\s*?([\d,.]+)',
        # Pattern: "Total: 1,234.56"
        r'(?:total|amount|payable|grand total|net amount|sum|bill amount)[^\d]*([\d,.]+)',
        # Pattern: "Rs. 1,234.56 only" or "₹1,234.56 only"
        r'(?:rs\.?|inr|₹)\s*?([\d,.]+)(?:\s*only)?',
        # Pattern: "1,234.56 Rs." or "1,234.56 /-"
        r'([\d,.]+)\s*(?:rs\.?|inr|₹|/-)',
        # Pattern: Just numbers with decimals (last resort)
        r'([\d,.]+)'
    ]
    
    for line in reversed(text_lines):
        line_lower = line.lower().strip()
        logger.debug(f"Processing line: {line_lower}")
        if any(word in line_lower for word in ['subtotal', 'sub total', 'tax', 'vat', 'gst', 'cgst', 'sgst']):
            continue
        for pattern in amount_patterns:
            match = re.search(pattern, line_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace(' ', '')
                    amount = float(amount_str)
                    logger.debug(f"Found amount: {amount} using pattern: {pattern}")
                    if any(word in line_lower for word in ['total', 'payable', 'grand', 'net amount', 'bill amount']):
                        return amount
                    possible_amounts.append(amount)
                except ValueError:
                    continue
    if possible_amounts:
        amount = max(possible_amounts)
        logger.debug(f"Selected largest amount: {amount}")
    else:
        logger.warning("No valid amounts found in text")
    return amount

@main.route('/upload', methods=['GET', 'POST'])
@login_required 
def upload():
    extracted_results = []
    notifications = []
    
    logger.debug("Starting upload route")
    
    try:
        test_image_path = os.path.join(current_app.root_path, 'static', 'image', 'sample_bill.jpg')
        if os.path.exists(test_image_path):
            test_text = pytesseract.image_to_string(Image.open(test_image_path))
            logger.debug("Tesseract test successful")
        else:
            logger.warning(f"Test image not found at: {test_image_path}")
    except Exception as e:
        error_msg = f"Tesseract error: {str(e)}"
        logger.error(error_msg)
        return render_template('upload.html',
                             result="⚠️ OCR System not available. Please make sure Tesseract is installed correctly.",
                             notifications=notifications)
    
    latest_budget = Budget.query.filter_by(user_id=current_user.id).order_by(Budget.id.desc()).first()
    if latest_budget:
        current_month_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            db.extract('month', Expense.date) == datetime.now().month,
            db.extract('year', Expense.date) == datetime.now().year
        ).all()
        
        total_expenses = sum(exp.amount for exp in current_month_expenses)
        
        if total_expenses > latest_budget.amount:
            diff = total_expenses - latest_budget.amount
            notifications.append(f"🚨 You have exceeded your monthly budget by ₹{diff:,.2f}")
        elif total_expenses >= latest_budget.amount * 0.9:
            remaining = latest_budget.amount - total_expenses
            notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} left in your budget")
        
        if latest_budget.limit:
            if total_expenses >= latest_budget.limit:
                notifications.append("🚨 Final Alert: You've crossed your spending limit!")
            elif total_expenses >= latest_budget.limit - 1000:
                remaining = latest_budget.limit - total_expenses
                notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} until spending limit")
    
    if request.method == 'POST':
        logger.debug("Processing POST request")
        if 'bills' not in request.files:
            logger.warning("No files were uploaded")
            return render_template('upload.html', 
                                 result='Please select at least one file to upload.',
                                 notifications=notifications)

        files = request.files.getlist('bills')
        valid_files = [f for f in files if f and f.filename and f.filename.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if not valid_files:
            logger.warning("No valid image files were uploaded")
            return render_template('upload.html', 
                                 result='Please select valid image files (JPG or PNG).',
                                 notifications=notifications)

        logger.debug(f"Processing {len(valid_files)} valid files")
        upload_folder = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        for file in valid_files:
            try:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(upload_folder, filename)
                logger.debug(f"Saving file to: {upload_path}")
                file.save(upload_path)

                try:
                    logger.debug(f"Starting OCR processing for: {filename}")
                    image = Image.open(upload_path)
                    extracted_text = pytesseract.image_to_string(image)
                    logger.debug(f"OCR completed. Extracted text length: {len(extracted_text)}")
                    
                    if not extracted_text.strip():
                        logger.warning(f"No text extracted from {filename}")
                        extracted_results.append((filename, "⚠️ No text could be extracted from this image. Please ensure the image is clear and contains readable text.", ""))
                        continue
                        
                    lines = extracted_text.splitlines()
                    
                    description = next((line.strip() for line in lines if line.strip()), "Scanned Bill")
                    logger.debug(f"Found description: {description}")

                    gst_number = None
                    for line in lines:
                        match = re.search(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b', line)
                        if match:
                            gst_number = match.group()
                            logger.debug(f"Found GST number: {gst_number}")
                            break

                    bill_date = None
                    date_patterns = [
                        r'(?:date|dt|dated|bill date|invoice date)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
                    ]
                    
                    for line in lines:
                        line_lower = line.lower()
                        for pattern in date_patterns:
                            date_match = re.search(pattern, line_lower)
                            if date_match:
                                date_str = date_match.group(1)
                                for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%y', '%d/%m/%y'):
                                    try:
                                        bill_date = datetime.strptime(date_str.replace('/', '-'), fmt)
                                        logger.debug(f"Found date: {bill_date}")
                                        break
                                    except ValueError:
                                        continue
                                if bill_date:
                                    break
                        if bill_date:
                            break

                    amount = extract_amount(lines)
                    logger.debug(f"Final extracted amount: {amount}")

                    if amount > 0:
                        new_expense = Expense(
                            description=description,
                            amount=amount,
                            date=bill_date or datetime.utcnow(),
                            source='upload',
                            ocr_text=extracted_text,
                            gst_number=gst_number,
                            user_id=current_user.id
                        )
                        db.session.add(new_expense)
                        db.session.commit()
                        logger.debug(f"Expense saved to DB with ID: {new_expense.id}")

                        result_text = (
                            f"Extracted Text:\n{extracted_text}\n\n"
                            f"Processed Information:\n"
                            f"Description: {description}\n"
                            f"Amount: ₹{amount:,.2f}\n"
                            + (f"GST: {gst_number}\n" if gst_number else "")
                            + (f"Date: {bill_date.strftime('%d-%m-%Y')}\n" if bill_date else "")
                        )
                        
                        extracted_results.append((
                            filename,
                            f"✅ Saved: {description} - ₹{amount:,.2f}",
                            result_text
                        ))
                        logger.debug(f"Successfully processed {filename}")
                    else:
                        debug_text = (
                            f"Extracted Text:\n{extracted_text}\n\n"
                            "Debug Info:\n"
                            "- No valid amount was detected\n"
                            "- Please ensure the bill shows a clear total amount\n"
                            "- The amount should be in the format: ₹1,234.56 or Rs. 1,234.56\n"
                            "- Check if the image is clear and properly oriented"
                        )
                        extracted_results.append((
                            filename,
                            "⚠️ Could not detect amount. Please verify the bill image.",
                            debug_text
                        ))
                        logger.warning(f"Could not detect amount in {filename}")

                except Exception as ocr_error:
                    logger.error(f"OCR error for {filename}: {str(ocr_error)}")
                    extracted_results.append((
                        filename,
                        f"❌ OCR Processing Error: {str(ocr_error)}",
                        "Failed to process image. Please ensure the image is clear and properly oriented."
                    ))

            except Exception as e:
                logger.error(f"File processing error for {filename}: {str(e)}")
                extracted_results.append((
                    filename,
                    f"❌ File Processing Error: {str(e)}",
                    "Failed to process the file. Please try again with a different image."
                ))

        if not extracted_results:
            logger.warning("No files were processed successfully")
            return render_template('upload.html',
                                 result='❌ No files were processed successfully.',
                                 notifications=notifications)

        success_count = sum(1 for _, msg, _ in extracted_results if "✅" in msg)
        total_count = len(extracted_results)
        overall_message = f"Processed {total_count} files: {success_count} successful, {total_count - success_count} with issues."
        logger.info(overall_message)
        logger.debug(f"Extracted results: {extracted_results}")
        
        return render_template('upload.html',
                             extracted_results=extracted_results,
                             result=overall_message,
                             notifications=notifications)

    return render_template('upload.html', notifications=notifications)



@main.route('/voice', methods=['GET', 'POST'])
@login_required
def voice_input():
    result = None
    notifications = []  # Initialize empty notifications
    
    # Get latest budget info for notifications
    latest_budget = Budget.query.filter_by(user_id=current_user.id).order_by(Budget.id.desc()).first()
    if latest_budget:
        # Get current month's expenses
        current_month_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            db.extract('month', Expense.date) == datetime.now().month,
            db.extract('year', Expense.date) == datetime.now().year
        ).all()
        
        total_expenses = sum(exp.amount for exp in current_month_expenses)
        
        # Generate notifications based on budget status
        if total_expenses > latest_budget.amount:
            diff = total_expenses - latest_budget.amount
            notifications.append(f"🚨 You have exceeded your monthly budget by ₹{diff:,.2f}")
        elif total_expenses >= latest_budget.amount * 0.9:
            remaining = latest_budget.amount - total_expenses
            notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} left in your budget")
        
        # Add limit notifications
        if latest_budget.limit:
            if total_expenses >= latest_budget.limit:
                notifications.append("🚨 Final Alert: You've crossed your spending limit!")
            elif total_expenses >= latest_budget.limit - 1000:
                remaining = latest_budget.limit - total_expenses
                notifications.append(f"⚠️ Warning: Only ₹{remaining:,.2f} until spending limit")
    
    if request.method == 'POST':
        try:
            # Check if form data is provided (from JavaScript)
            form_description = request.form.get('description')
            form_amount = request.form.get('amount')
            
            if form_description and form_amount:
                # Use the form data
                description = form_description
                amount = float(form_amount)
            else:
                # Use the voice input capture
                description, amount = capture_voice_input()

            if amount > 0 and description and description not in ["Could not understand", "API error"]:
                new_expense = Expense(
                    description=description,
                    amount=amount,
                    date=datetime.utcnow(),
                    source='voice',
                    user_id=current_user.id  # Add user_id to expense
                )
                db.session.add(new_expense)
                db.session.commit()

                result = f"✅ Saved: {description} - ₹{amount}"
            else:
                result = "❌ Could not extract amount and description. Please say something like 'I spent Rs 100 on groceries'."

        except Exception as e:
            print("Error:", e)
            result = "❌ Error occurred while saving. Please try again."

    return render_template('voice.html', result=result, notifications=notifications)

@main.route('/download_backup/<file_type>/<month_type>', methods=['GET'])
@login_required
def download_backup(file_type, month_type):
    if file_type not in ['csv', 'pdf'] or month_type not in ['current', 'last']:
        abort(400)

    now = datetime.now()
    if month_type == 'last':
        month = now.month - 1 if now.month > 1 else 12
        year = now.year if now.month > 1 else now.year - 1
    else:
        month = now.month
        year = now.year

    export_dir = os.path.join(current_app.root_path, 'exports')
    filename = f'expenses_{year}_{month}.{file_type}'
    file_path = os.path.join(export_dir, filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        flash("File not found. Please generate the backup first.", "error")
        return redirect(url_for('main.dashboard'))


@main.route('/generate_backup', methods=['GET', 'POST'])
def generate_backup():
    # --- Manual login check: adjust 'user_id' to your session key ---
    if 'user_id' not in session:
        # If AJAX/fetch request, return JSON error
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        # Otherwise, redirect to login page (for normal browser navigation)
        return redirect(url_for('login'))

    try:
        # --- Your backup logic here ---
        # For example, generate the backup file, etc.
        # If successful:
        return jsonify({'status': 'success'})
    except Exception as e:
        # If there is an error, return JSON error
        return jsonify({'status': 'error', 'message': str(e)}), 500



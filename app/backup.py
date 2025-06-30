from datetime import datetime
from app.db_manager import db, Expense, User
import csv
import os
import pdfkit
from flask_login import current_user

EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)


def export_expenses_to_csv_pdf(user=None, use_last_month=False):
    try:
        now = datetime.now()

        if use_last_month:
            month = now.month - 1 if now.month > 1 else 12
            year = now.year if now.month > 1 else now.year - 1
        else:
            month = now.month
            year = now.year

        EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'exports')
        os.makedirs(EXPORT_DIR, exist_ok=True)

        # Build initial query
        query = Expense.query.filter(
            db.extract('month', Expense.date) == month,
            db.extract('year', Expense.date) == year
        )

        # ✅ This is the MAIN FIX: filter using user.id, not the full user object
        if user and hasattr(user, 'id'):
            query = query.filter(Expense.user_id == user.id)

        expenses = query.all()
        if not expenses:
            return None, None  # nothing to export

        # CSV generation
        csv_path = os.path.join(EXPORT_DIR, f'expenses_{year}_{month}.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Description', 'Amount', 'Source', 'Category', 'GST Number'])
            for exp in expenses:
                writer.writerow([
                    exp.date.strftime('%Y-%m-%d'),
                    exp.description,
                    exp.amount,
                    exp.source,
                    getattr(exp, 'category', 'Other'),
                    getattr(exp, 'gst_number', 'N/A')
                ])

        # PDF generation
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ccc; padding: 10px; }}
                th {{ background-color: #f0f0f0; }}
                .total {{ font-weight: bold; background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h2 style="text-align:center;">Expense Report</h2>
            <p style="text-align:center;">Month: {month}, Year: {year}</p>
            <table>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Source</th>
                    <th>Category</th>
                    <th>GST Number</th>
                </tr>
        """

        total_amount = 0
        for exp in expenses:
            total_amount += exp.amount
            html_content += f"""
                <tr>
                    <td>{exp.date.strftime('%Y-%m-%d')}</td>
                    <td>{exp.description}</td>
                    <td>₹{exp.amount:,.2f}</td>
                    <td>{exp.source}</td>
                    <td>{getattr(exp, 'category', 'Other')}</td>
                    <td>{getattr(exp, 'gst_number', 'N/A')}</td>
                </tr>
            """

        html_content += f"""
                <tr class="total">
                    <td colspan="2">Total</td>
                    <td>₹{total_amount:,.2f}</td>
                    <td colspan="3"></td>
                </tr>
            </table>
        </body>
        </html>
        """

        pdf_path = os.path.join(EXPORT_DIR, f'expenses_{year}_{month}.pdf')

        try:
            wkhtmltopdf_paths = [
                r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
                r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
                '/usr/local/bin/wkhtmltopdf',
                '/usr/bin/wkhtmltopdf'
            ]

            config = None
            for path in wkhtmltopdf_paths:
                if os.path.exists(path):
                    config = pdfkit.configuration(wkhtmltopdf=path)
                    break

            if config:
                pdfkit.from_string(html_content, pdf_path, configuration=config)
            else:
                raise Exception("wkhtmltopdf not found.")

        except Exception as e:
            print(f"PDF error: {e}")
            with open(pdf_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write("PDF generation failed.\n\n")
                f.write(html_content)

        return csv_path, pdf_path

    except Exception as e:
        print(f"Export error: {e}")
        return None, None



def monthly_reset(app):
    with app.app_context():
        today = datetime.today()

        if today.day == 1:
            users = User.query.all()
            for user in users:
                try:
                    print(f" Exporting and resetting data for user: {user.email}")
                    export_expenses_to_csv_pdf(user)
                    Expense.query.filter_by(user_id=user.id).delete()
                except Exception as e:
                    print(f" Failed for user {user.email}: {e}")

            db.session.commit()
            print(" Monthly reset completed.")
        else:
            print(f" Not the first of the month: {today.strftime('%Y-%m-%d')}. Reset skipped.")
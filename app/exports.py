import os
import csv
from datetime import datetime
from flask import current_app
import pdfkit
from .db_manager import Expense, db


def export_expenses_to_csv_pdf(user_id):
    """Exports current month's expenses for the given user as CSV and PDF"""
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Get user's expenses for current month
    expenses = Expense.query.filter(
        db.extract('month', Expense.date) == current_month,
        db.extract('year', Expense.date) == current_year,
        Expense.user_id == user_id
    ).all()

    if not expenses:
        return None, None  # No expenses to export

    export_dir = os.path.join(current_app.root_path, 'exports')
    os.makedirs(export_dir, exist_ok=True)

    filename_base = f'expenses_{user_id}_{current_year}_{current_month}'
    csv_path = os.path.join(export_dir, f'{filename_base}.csv')
    pdf_path = os.path.join(export_dir, f'{filename_base}.pdf')

    # ✅ Write CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Description', 'Amount', 'Source'])
        for exp in expenses:
            writer.writerow([
                exp.date.strftime('%Y-%m-%d'),
                exp.description,
                exp.amount,
                exp.source
            ])

    # ✅ Generate PDF from HTML
    html_content = """
    <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .total { font-weight: bold; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>Expense Report</h1>
            <p>Period: {month} {year}</p>
            <table>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Source</th>
                </tr>
    """.format(month=datetime(current_year, current_month, 1).strftime('%B'), year=current_year)

    total = 0
    for exp in expenses:
        total += exp.amount
        html_content += f"""
            <tr>
                <td>{exp.date.strftime('%Y-%m-%d')}</td>
                <td>{exp.description}</td>
                <td>₹{exp.amount:.2f}</td>
                <td>{exp.source}</td>
            </tr>
        """

    html_content += f"""
            </table>
            <div class="total">Total: ₹{total:.2f}</div>
        </body>
    </html>
    """

    # ✅ Configure and generate PDF
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    if not os.path.exists(wkhtmltopdf_path):
        wkhtmltopdf_path = r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe"

    if os.path.exists(wkhtmltopdf_path):
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        pdfkit.from_string(html_content, pdf_path, configuration=config)
    else:
        current_app.logger.warning("wkhtmltopdf not found, skipping PDF generation.")
        pdf_path = None

    return csv_path, pdf_path

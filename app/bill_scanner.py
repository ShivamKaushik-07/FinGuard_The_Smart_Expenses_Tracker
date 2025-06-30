import re

def extract_amount(lines):
    """
    Extract the total payable amount from OCR text lines.
    Prioritizes keywords like 'Total', 'Amount Payable', etc.
    """
    amount = 0.0
    keywords = ['total', 'amount', 'amount payable', 'grand total', 'net amount', 'payable']

    for line in reversed(lines):
        lower_line = line.lower()

        if any(keyword in lower_line for keyword in keywords):
            # Match amounts like ₹1,234.56 or Rs. 1234.00
            matches = re.findall(r'[\₹Rs\.\s]*([\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?]+)', line)
            for match in reversed(matches):
                try:
                    cleaned = match.replace(',', '').replace('Rs.', '').replace('₹', '').strip()
                    val = float(cleaned)
                    if val > amount:
                        amount = val
                except ValueError:
                    continue
    return round(amount, 2)

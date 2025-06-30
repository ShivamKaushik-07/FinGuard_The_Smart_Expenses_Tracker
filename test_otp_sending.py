# test_otp_sending.py

from app.utils import send_email_otp, send_sms_otp  # Adjust the import path if needed

# Replace with your test data
test_email = "scsofficial@gmail.com"
test_phone = "+918329607731"
test_otp = "123456"

# Test email
if send_email_otp(test_email, test_otp):
    print("✅ Email sent successfully!")
else:
    print("❌ Email failed!")

# Test SMS
if send_sms_otp(test_phone, test_otp):
    print("✅ SMS sent successfully!")
else:
    print("❌ SMS failed!")

import smtplib
from email.message import EmailMessage
from twilio.rest import Client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()


def send_email_otp(recipient_email, otp):
    print("Sending email to:", recipient_email)
    try:
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASSWORD")  # Use Gmail App Password

        subject = "Your FinGuard OTP"
        body = f"""
        <h2>OTP Verification</h2>
        <p>Your One-Time Password (OTP) is: <strong>{otp}</strong></p>
        <p>This OTP is valid for 5 minutes.</p>
        """
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")

        return True
    except Exception as e:
        print("[ERROR] Email sending failed:", e)
        return False


def send_sms_otp(phone_number, otp):
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER", "FinGuard")
        to_number = phone_number

        client = Client(account_sid, auth_token)

        message_body = f"🔐 Your FinGuard OTP is: {otp}. It expires in 5 minutes."

        message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=to_number
        )

        print("SMS sent successfully!")
        return True
    except Exception as e:
        print("[ERROR] SMS sending failed:", e)
        return False

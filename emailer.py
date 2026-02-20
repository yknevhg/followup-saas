import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from crypto import decrypt

def _connect_smtp(user):
    password = decrypt(user.smtp_password)

    if user.smtp_port == 465:
        server = smtplib.SMTP_SSL(user.smtp_host, user.smtp_port, timeout=10)
    else:
        server = smtplib.SMTP(user.smtp_host, user.smtp_port, timeout=10)
        server.starttls()

    server.login(user.smtp_email, password)
    return server

def send_test_email(user):
    msg = MIMEMultipart()
    msg["From"] = user.smtp_email
    msg["To"] = user.smtp_email
    msg["Subject"] = "SMTP Test Successful"

    msg.attach(MIMEText("Your email settings are working correctly.", "plain"))

    server = _connect_smtp(user)
    server.send_message(msg)
    server.quit()

def send_followup(user, client):
    msg = MIMEMultipart()
    msg["From"] = user.smtp_email
    msg["To"] = client.email
    msg["Subject"] = "Quick follow-up"

    body = f"""Hi {client.name},

Just following up on my previous message.

Best regards,
{user.smtp_email}
"""
    msg.attach(MIMEText(body, "plain"))

    server = _connect_smtp(user)
    server.send_message(msg)
    server.quit()
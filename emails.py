from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import smtplib
import ssl


def send_simple_message(email_to, subject, content):

    port = 465  # For SSL
    smtp_server = os.getenv('SMTP_SERVER')
    sender_email = os.getenv('SMTP_USERNAME')
    password = os.getenv('SMTP_PASSWORD')
    context = ssl.create_default_context()

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = email_to

    part1 = MIMEText(content, "html")

    message.attach(part1)
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, email_to, message.as_string())

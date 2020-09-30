import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_simple_message(email_to, subject, content):
    message = Mail(
        from_email='gabrielf@eventbrite.com',
        to_emails=email_to,
        subject=subject,
        html_content=content,
    )
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)

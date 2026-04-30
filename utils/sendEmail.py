import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


def send_email(
    subject,
    body,
    recipient,
    sender_email=None,
    sender_password=None,
    attachment_data=None,
    filename="Report.pdf",
):
    """Send an email with optional PDF attachment using SMTP credentials from the environment."""

    sender_email = sender_email or os.getenv("SENDER_EMAIL", "")
    sender_password = sender_password or os.getenv("SENDER_PASSWORD", "")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))

    if not sender_email or not sender_password:
        raise ValueError("Missing SMTP credentials. Set SENDER_EMAIL and SENDER_PASSWORD in .env.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient
    message.set_content(body)

    if attachment_data:
        message.add_attachment(
            attachment_data,
            maintype="application",
            subtype="pdf",
            filename=filename,
        )

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(sender_email, sender_password)
        server.send_message(message)


# Backward-compatible alias for older imports.
sendEmail = send_email

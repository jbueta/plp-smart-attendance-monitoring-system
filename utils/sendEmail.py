import smtplib
from email.message import EmailMessage

# Ensure you use 'def', not 'function'
def sendEmail(subject, body, recipient, attachment_data=None, filename="Report.pdf"):
    # ... your code ...
    # CREDENTIALS
    SENDER_EMAIL = "amarelle2025@gmail.com"
    SENDER_PASSWORD = "momk krrn fcip dijh" 
    RECEIVER_EMAIL = recipient

    # CONSTRUCT
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(body)

    # ADD ATTACHMENT
    if attachment_data:
        msg.add_attachment(
            attachment_data,
            maintype='application',
            subtype='pdf',
            filename=filename
        )

    # SEND
    SMTP_SERVER = "smtp.gmail.com"
    PORT = 465 

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return {"success": True, "message": "Email sent successfully!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
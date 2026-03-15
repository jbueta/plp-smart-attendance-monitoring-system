import smtplib
from email.message import EmailMessage


function sendEmail(str:subject, str:body, str:recipient):
    # CREDENTIALS
    SENDER_EMAIL = "your_email@gmail.com"
    SENDER_PASSWORD = "your_16_digit_app_password_here" 
    RECEIVER_EMAIL = recipient

    # CONSTRUCT
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(body)

    # SEND
    SMTP_SERVER = "smtp.gmail.com"
    PORT = 465 

    try:
        print("Connecting to server...")
        # Using 'with' ensures the server connection is closed automatically
        with smtplib.SMTP_SSL(SMTP_SERVER, PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        print("Success! Email sent.")
    except smtplib.SMTPAuthenticationError:
        print("Error: Authentication failed. Did you use an App Password?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
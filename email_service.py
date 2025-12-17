import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_assignment_email(to_email, giver_name, receiver_name):
    """
    Sends the Secret Santa assignment email.
    """
    smtp_server = "smtp.gmail.com" # Default to Gmail, user can change if needed
    smtp_port = 465
    
    sender_email = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")

    if not sender_email or not password:
        print("Error: Email credentials missing in .env")
        return False

    subject = "🎅 Tu Amigo Invisible 2026 es..."
    
    # HTML Body
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h1 style="color: #d42426; text-align: center;">🎁 Amigo Invisible 2026 🎁</h1>
            <p><strong>¡Hola {giver_name}!</strong></p>
            <p>Ya se ha realizado el sorteo. Este año te ha tocado regalar a:</p>
            
            <div style="background-color: #f9f9f9; padding: 15px; text-align: center; margin: 20px 0; border-radius: 5px;">
                <h2 style="color: #0c0; margin: 0; font-size: 24px;">✨ {receiver_name} ✨</h2>
            </div>
            
            <p style="text-align: center; font-size: 12px; color: #777;">
                (Shhh... es un secreto. No se lo digas a nadie)
            </p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="text-align: center; font-size: 10px; color: #999;">
                Este mensaje ha sido enviado automáticamente por el sistema de Amigo Invisible de la Familia.
            </p>
        </div>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email
    message.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False

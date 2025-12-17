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

            <div style="background-color: #fff5f5; border: 1px solid #d42426; padding: 15px; margin: 20px 0; border-radius: 8px;">
                <h3 style="color: #d42426; margin-top: 0; font-size: 16px; text-align: center;">📜 NORMAS DE PARTICIPACIÓN</h3>
                <ul style="font-size: 14px; color: #555; padding-left: 20px; line-height: 1.5;">
                    <li>💰 El importe máximo es de <strong>30 €</strong></li>
                    <li>🎫 Hay que incluir <strong>ticket regalo</strong></li>
                    <li>💭 Si se piensa en el regalado es más fácil acertar :)</li>
                </ul>
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

def send_admin_notification(admin_email):
    """
    Sends a notification to Ricardo when all participants have registered.
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 465
    
    sender_email = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")

    if not sender_email or not password:
        return False

    subject = "✨ ¡La Magia está lista! Registro completado"
    
    html = f"""
    <html>
      <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 15px; border: 2px solid #d42426; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <span style="font-size: 50px;">🎅</span>
            </div>
            <h1 style="color: #d42426; text-align: center; margin-top: 0;">¡Hola Ricardo!</h1>
            <p style="font-size: 16px; line-height: 1.6; text-align: center;">
                Ya se han registrado todos los familiares en la aplicación del amigo invisible. ✨
            </p>
            <p style="font-size: 16px; line-height: 1.6; text-align: center; font-weight: bold; color: #0c0;">
                ¡Ya puedes activar el sorteo y enviaremos los mails a todos los participantes!
            </p>
            
            <div style="background-color: #fff5f5; border: 1px dashed #d42426; padding: 15px; text-align: center; margin: 25px 0; border-radius: 10px;">
                <p style="margin: 0; font-size: 14px; color: #555;">Recuerda usar tu ADMIN_SECRET_KEY para disparar el sorteo:</p>
                <code style="display: block; margin-top: 10px; font-size: 18px; color: #d42426; font-weight: bold;">/api/admin/draw?key=...</code>
            </div>

            <p style="text-align: center; font-size: 18px; color: #333; margin-top: 30px;">
                ¡Saludos y felices Reyes! 👑👑👑
            </p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="text-align: center; font-size: 10px; color: #999;">
                Enviado con magia desde tu servidor de Amigo Invisible 2026.
            </p>
        </div>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = admin_email
    message.attach(MIMEText(html, "html"))

    try:
        print(f"DEBUG SMTP: Connecting to {smtp_server}:{smtp_port}...")
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            print(f"DEBUG SMTP: Logging in as {sender_email}...")
            server.login(sender_email, password)
            print(f"DEBUG SMTP: Sending mail to {admin_email}...")
            server.sendmail(sender_email, admin_email, message.as_string())
        print("DEBUG SMTP: Success.")
        return True
    except Exception as e:
        print(f"DEBUG SMTP ERROR: {e}")
        return False

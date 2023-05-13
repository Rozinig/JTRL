import smtplib, ssl
from email.message import EmailMessage

def contactemail(email, name, usermessage, cred):
    message = EmailMessage()
    message["Subject"] = f"{name} sent you a message"
    message["From"] = cred['email']
    message["To"] = cred['email']
    message['reply-to'] = email

    body = f"""User, {name} with the {email} has sent you a message through the contact form on JTRL: {usermessage}"""
    
    message.set_content(body)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(cred['server'], cred['port'], context=context) as server:
        server.login(cred['email'], cred['pass'])
        server.sendmail(
            cred['email'], cred['email'], message.as_string()
        )

def resetemail(email, code, link, cred):
    message = EmailMessage()
    message["Subject"] = "JTRL Password Reset"
    message["From"] = cred['email']
    message["To"] = email

    body = f"""Your password reset code is: {code}
    Please enter it at {link}

    If you did not make this request please reply to this email."""
    
    message.set_content(body)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(cred['server'], cred['port'], context=context) as server:
        server.login(cred['email'], cred['pass'])
        server.sendmail(
            cred['email'], email, message.as_string()
        )

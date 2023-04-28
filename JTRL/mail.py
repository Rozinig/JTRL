import smtplib, ssl
from email.message import EmailMessage

def contactemail(email, name, usermessage, cred):
    print(cred['email'], cred['server'], cred['port'], cred['pass'])
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

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email(subject, body, to_email, files=[]):
    from_email = "shivamganeshjindal07@gmail.com"
    password = "Orange1234~"

    # Set up the MIME
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Attach files
    for file in files:
        attachment = open(file, "rb")
        p = MIMEBase('application', 'octet-stream')
        p.set_payload((attachment).read())
        encoders.encode_base64(p)
        p.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file)}")
        message.attach(p)

    # SMTP session
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    text = message.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

# Example usage
send_email("New Files", "Here are the new files.", "shivamj@forumam.com", [])


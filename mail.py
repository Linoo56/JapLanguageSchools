# Created by siwells https://github.com/siwells/teaching_set09103/

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import os


def send(to, gmail_psw, subject, text, attach=None):
    msg = MIMEMultipart("alternative")
    msg.set_charset("utf-8")
    gmail_user = "japlangsch.hikaweb@gmail.com"

    msg['From'] = gmail_user
    msg['To'] = to
    msg['Subject'] = subject
    
    msg.attach(MIMEText(text, "plain", "utf-8"))

    if attach is not None:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attach, 'rb').read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
        msg.attach(part)
    
    print(msg)

    try:
        mailServer = smtplib.SMTP("smtp.gmail.com", 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(gmail_user, gmail_psw)
        mailServer.sendmail(gmail_user, to, msg.as_string())
        # Should be mailServer.quit(), but that crashes...
        mailServer.close()
        return True
    except:
        print("Error on send")
        # app.loggger.error("Couldn't send confirmation email: " + str(text)) - Causes crash
        # TODO: fix error logging here so that it doesn't cause a crash.
        pass


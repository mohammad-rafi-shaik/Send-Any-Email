import socket
import smtplib
import mimetypes
import os.path as p
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging


def send_mail(*, recipients, subject, body_text=None, body_html=None, attachments=None, cc_recipients=None):
    if not body_text and not body_html:
        body_text = ''
    if issubclass(attachments.__class__, str):
        attachments = [attachments]
    from_address = ''

    recipients = recipients if recipients.__class__ in (list, tuple) else [recipients]

    outer = MIMEMultipart('mixed')
    outer['Subject'] = subject
    outer['From'] = from_address
    outer['To'] = ', '.join(recipients)
    if cc_recipients:
        cc_recipients = cc_recipients if cc_recipients.__class__ in (list, tuple) else [cc_recipients]
        outer['CC'] = ', '.join(cc_recipients)

    text_part = MIMEText(body_text, 'plain') if body_text else None
    html_part = MIMEText(body_html, 'html') if body_html else None

    if html_part:
        outer.attach(html_part)
    elif text_part:
        outer.attach(text_part)

    if attachments:
        for path in attachments:
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            if maintype == 'text':
                fp = open(path)
                # Note: we should handle calculating the charset
                msg = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'image':
                fp = open(path, 'rb')
                msg = MIMEImage(fp.read(), _subtype=subtype)
                msg.add_header('Content-Id', '<%s>' % p.basename(path))
                fp.close()
            elif maintype == 'audio':
                fp = open(path, 'rb')
                msg = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(path, 'rb')
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
                fp.close()
                # Encode the payload using Base64
                encoders.encode_base64(msg)
            # Set the filename parameter
            msg.add_header('Content-Disposition', 'attachment', filename=p.basename(path))
            outer.attach(msg)

    if cc_recipients is not None:
        recipients = recipients + cc_recipients

    payload = dict(from_addr=from_address, to_addrs=recipients, msg=outer.as_string())

    try:
        smtp_host = ''
        s = smtplib.SMTP(smtp_host)
        s.sendmail(**payload)
        s.quit()
    except socket.gaierror as e:
        logging.exception(str(e))
        logging.info(payload)

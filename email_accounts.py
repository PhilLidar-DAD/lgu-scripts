#!/usr/bin/python2

import smtplib
from email.mime.text import MIMEText

_version = '0.03.4'
mail_server = 'mail.dream.upd.edu.ph'
sender = 'support@dream.upd.edu.ph'

template = '''
Hi <name>,

Here are your account details.

Username: <username>
Email: <email>

Please go to https://ssp.dream.upd.edu.ph/?action=sendtoken to set your password. Also, note that the minimum password length is 14 characters.

Thanks!
'''

# Read from csv file
with open('accounts_info - accounts.csv', 'r') as open_file:
    for line in open_file:
        if line:
            tokens = line.split(',')
            name = tokens[0].strip()
            username = tokens[1].strip()
            receiver = tokens[2].strip()
            # print name, username, username, receiver
            msg = MIMEText(template.replace('<name>',
                name).replace('<username>',
                username).replace('<email>', receiver))
            msg['Subject'] = 'PHIL-LiDAR 1/2 account details'
            msg['From'] = sender
            msg['To'] = receiver
            print msg
            s = smtplib.SMTP(mail_server)
            s.sendmail(sender, [receiver], msg.as_string())
            s.quit()

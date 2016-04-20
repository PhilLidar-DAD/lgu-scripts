#!/usr/bin/env python

from docxtpl import DocxTemplate
from email import Encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
import jinja2
import json
import smtplib
import subprocess


_version = '0.03.4'
mail_server = 'mail.dream.upd.edu.ph'
sender = 'lipad@dream.upd.edu.ph'

template = '''
Dear <title> <name>,

The UP Disaster Risk and Exposure Assessment for Mitigation (DREAM) Program, started on December 29, 2011, is tasked to generate high-resolution, detailed, and up-to-date elevation maps for 18 critical river systems in the country. Using state-of-the-art technology, it has acquired, validated, and processed LiDAR datasets in order to produce flood hazards and flood inundation maps. 

DREAM's 3D data from airborne LiDAR surveys are currently used for the generation of flood hazard maps and for the establishment of water level forecasting systems to help our people and communities prepare for evacuation and appropriate response. DREAM's elevation datasets are however versatile enough to be used for other applications.

Acknowledging its beneficial effects, the government has expanded LiDAR area coverage from 18 critical river basins to 257 river basins throughout the country under the Phil LiDAR 1 Program. However, the UP DREAM Program itself is slated to have its project end on May 19, 2016. In view of this, we have organized a Sustainability Workshop on April 22, 2016. May we invite you to be actively involved in our event. Your presence and inputs will help us plan for the future of LiDAR usage in the country.

Ms. Marilou Supit and Ms. Denise Ann Suarez will coordinate with your office for your response. They can also be reached at (02) 981 8770 or fax (02)  981 8771, or  e-mail at info@dream.upd.edu.ph

Looking forward to your favorable response.
'''

data = json.load(open('data.json','r'))
# Read from csv file
for i in data:
    doc = DocxTemplate("invite.docx")
    context = { 'title' : i['title'], 'name' : i['name'] }
    jinja_env = jinja2.Environment()
    # jinja_env.filters['myfilter'] = myfilterfunc
    doc.render(context,jinja_env)
    filename = str(i['name']) + ".docx"
    doc.save(filename)

    out = subprocess.check_output(['/usr/bin/python3', '/usr/bin/unoconv', '-f', 'pdf', filename])

    invite_pdf = str(i['name']) + ".pdf"

    msg = MIMEMultipart()
    msg.attach(MIMEText(template.replace('<title>',i['title']).replace('<name>',i['name'])))
    msg['Subject'] = 'National Conference Invite Letter for FGD'
    msg['From'] = sender
    msg['To'] = ', '.join(i['emails'])

    for attachment in ['program.pdf', invite_pdf]:

        part = MIMEBase('application', "pdf")
        part.set_payload(open(attachment, "rb").read())
        Encoders.encode_base64(part)

        part.add_header('Content-Disposition', 'attachment; filename=' + attachment)

        msg.attach(part)

    # print msg
    s = smtplib.SMTP(mail_server)
    # s.sendmail(sender, [receiver], msg.as_string())
    s.sendmail(sender, ['klangga@gmail.com'], msg.as_string())
    s.quit()

    break
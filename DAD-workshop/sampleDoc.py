#!/usr/bin/env python

from docxtpl import DocxTemplate
import jinja2
import subprocess

doc = DocxTemplate("invite.docx")
context = { 'title' : "Lord Commander", 'name' : "John Snow" }
jinja_env = jinja2.Environment()
# jinja_env.filters['myfilter'] = myfilterfunc
doc.render(context,jinja_env)
filename = "JohnSnow.docx"
doc.save(filename)

#unoconv -f pdf invite.docx 

out = subprocess.check_output(['/usr/bin/python3', '/usr/bin/unoconv', '-f', 'pdf', 'invite.docx'])
print out
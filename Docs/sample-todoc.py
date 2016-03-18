from docxtpl import DocxTemplate
import jinja2

doc = DocxTemplate("TemplateLGULiPADAccountRegistration.docx")
context = { 'Municipality' : "Munishipariti" }
doc.render(context)
doc.save("generated_doc.docx")

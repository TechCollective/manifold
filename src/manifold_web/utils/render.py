from flask import render_template
from jinja2.exceptions import TemplateNotFound

def safe_render(template_name, **context):
    try:
        return render_template(template_name, **context)
    except TemplateNotFound:
        return f"""
        <html>
        <body>
            <h1>⚠️ Template Not Found: {template_name}</h1>
            <p>This is a fallback error renderer.</p>
        </body>
        </html>
        """

import os
import sys
import time

_tool = "check50"

# Add path to module for autodoc
sys.path.insert(0, os.path.abspath(f'../../{_tool}'))

# Include __init__ in autodoc
# Source: https://stackoverflow.com/questions/5599254/how-to-use-sphinxs-autodoc-to-document-a-classs-init-self-method
def skip(app, what, name, obj, would_skip, options):
    if name == "__init__":
        return False
    return would_skip

def setup(app):
    app.connect("autodoc-skip-member", skip)

extensions = ['sphinx.ext.autodoc']

html_css_files = ["https://cs50.readthedocs.io/_static/custom.css?" + str(round(time.time()))]
html_js_files = ["https://cs50.readthedocs.io/_static/custom.js?" + str(round(time.time()))]
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "display_version": False,
    "prev_next_buttons_location": False,
    "sticky_navigation": False
}
html_title = f'{_tool} Docs'

project = f'{_tool}'

import pathlib
import pkg_resources
import jinja2

TEMPLATES = pathlib.Path(pkg_resources.resource_filename("check50._renderer", "templates"))

def render(slug, result_json):
    with open(TEMPLATES / "results.html") as f:
        match_content = f.read()

    match_template = jinja2.Template(
        match_content, autoescape=jinja2.select_autoescape(enabled_extensions=("html",)))
    match_html = match_template.render(slug=slug, checks=result_json["results"], version=result_json["version"])

    dest = "temp_results.html"

    with open(dest, "w") as f:
        f.write(match_html)

    return pathlib.Path("temp_results.html").absolute()

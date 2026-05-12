from jinja2 import Environment, FileSystemLoader


def render_index_page(dates: list[str], template_dir: str = "templates") -> str:
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    tmpl = env.get_template("index.html")
    return tmpl.render(dates=sorted(dates, reverse=True))

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "content" / "resume.json"
VERSION_DATA_DIR = ROOT / "content" / "versions"
DOCS = ROOT / "docs"
PDF_NAME = "Rafael-Jimenez-CV.pdf"
PDF_PATH = DOCS / PDF_NAME
OUTPUT_PDF = ROOT / "output" / "pdf" / PDF_NAME

NAVY = HexColor("#071A2B")
NAVY_SOFT = HexColor("#153247")
CYAN = HexColor("#007D8A")
CYAN_BRIGHT = HexColor("#16C5D8")
CYAN_PALE = HexColor("#DFF7FA")
INK = HexColor("#142431")
MUTED = HexColor("#5F7180")
LINE = HexColor("#CFDBE2")
RAIL = HexColor("#F1F6F8")
WHITE = HexColor("#FFFFFF")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def icon(name: str) -> str:
    return f'<img class="icon" src="assets/icons/{esc(name)}.svg" alt="" aria-hidden="true">'


def render_technologies(items: Iterable[str]) -> str:
    return " · ".join(esc(item) for item in items)


def render_project(project: dict) -> str:
    bullets = "".join(f"<li>{esc(item)}</li>" for item in project["bullets"])
    return f"""
      <article class="project">
        <div class="project-head">
          <h3>{esc(project['name'])}</h3>
          <p class="date">{esc(project['dates'])}</p>
        </div>
        <p class="position">{esc(project['role'])} · {esc(project['company'])}</p>
        <ul>{bullets}</ul>
        <p class="team">{esc(project['team'])}</p>
        <p class="technologies"><strong>Tecnologías:</strong> {render_technologies(project['technologies'])}</p>
      </article>
    """


def render_job(job: dict) -> str:
    return f"""
      <article class="job">
        <div class="job-head">
          <h3>{esc(job['company'])}</h3>
          <p class="date">{esc(job['dates'])}</p>
        </div>
        <p class="position">{esc(job['role'])}</p>
        <p>{esc(job['summary'])}</p>
        <p class="technologies"><strong>Tecnologías:</strong> {render_technologies(job['technologies'])}</p>
      </article>
    """


def render_html(data: dict) -> str:
    person = data["person"]
    version_meta = ""
    if data["meta"].get("version"):
        version_meta = f'\n  <meta name="cv-version" content="{esc(data["meta"]["version"])}">'
    stack = "".join(f"<li>{esc(item)}</li>" for item in data["stack"])
    education = "".join(
        f"""
        <div class="rail-item">
          <dt>{esc(item['title'])}</dt>
          <dd>{esc(item['institution'])}<br>{esc(item['dates'])}</dd>
        </div>"""
        for item in data["education"]
    )
    certifications = "".join(
        f"""
        <div class="rail-item">
          <dt>{esc(item['title'])}</dt>
          <dd>{esc(item['status'])}</dd>
        </div>"""
        for item in data["certifications"]
    )
    languages = "".join(f"<li>{esc(item)}</li>" for item in data["languages"])

    return f"""<!doctype html>
<html lang="{esc(data['meta']['language'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(data['meta']['description'])}">{version_meta}
  <meta name="robots" content="noindex,nofollow,noarchive">
  <link rel="canonical" href="{esc(data['meta']['canonical'])}">
  <link rel="stylesheet" href="styles.css">
  <title>{esc(person['name'])} · {esc(person['title'])}</title>
</head>
<body>
  <a class="skip-link" href="#contenido">Saltar al contenido</a>
  <nav class="screen-toolbar" aria-label="Acciones del currículum">
    <a class="download-link" href="{esc(data['meta']['pdf_filename'])}" download>
      {icon('download')} Descargar PDF
    </a>
  </nav>

  <main class="cv" id="contenido">
    <article class="page" aria-label="Página 1 de 2 del currículum">
      <header class="hero">
        <p class="eyebrow">{esc(person['tagline'])}</p>
        <h1>{esc(person['name'])}</h1>
        <p class="role">{esc(person['title'])}</p>
        <ul class="contact-list" aria-label="Contacto">
          <li>{icon('map-pin')}<span>{esc(person['location'])}</span></li>
          <li><a href="mailto:{esc(person['email'])}">{icon('mail')}<span>{esc(person['email'])}</span></a></li>
          <li><a href="tel:{esc(person['phone_href'])}">{icon('phone')}<span>{esc(person['phone_display'])}</span></a></li>
          <li><a href="{esc(person['linkedin_href'])}">{icon('external-link')}<span>{esc(person['linkedin_display'])}</span></a></li>
        </ul>
      </header>

      <div class="page-grid">
        <div class="main-column">
          <section class="section" aria-labelledby="perfil">
            <h2 class="section-title" id="perfil">Perfil</h2>
            <p class="profile">{esc(data['profile'])}</p>
          </section>

          <section class="section" aria-labelledby="proyectos">
            <h2 class="section-title" id="proyectos">Experiencia por proyectos</h2>
            {render_project(data['projects'][0])}
            {render_project(data['projects'][1])}
          </section>

          <p class="availability">{esc(person['availability'])}</p>
        </div>

        <aside class="rail" aria-labelledby="stack">
          <p class="rail-number" aria-hidden="true">01</p>
          <h2 class="rail-title" id="stack">Stack principal</h2>
          <ul class="stack-list">{stack}</ul>
        </aside>
      </div>
      <footer class="page-footer">CV · página 1</footer>
    </article>

    <article class="page page--second" aria-label="Página 2 de 2 del currículum">
      <header class="page-masthead">
        <div>
          <p class="page-kicker">Experiencia · continuación</p>
          <h2>{esc(person['name'])}</h2>
        </div>
        <p class="page-role">{esc(person['title'])}</p>
      </header>

      <div class="page-grid">
        <div class="main-column">
          <section class="section" aria-labelledby="proyecto-sek">
            <h2 class="section-title" id="proyecto-sek">Proyecto destacado</h2>
            {render_project(data['projects'][2])}
          </section>

          <section class="section" aria-labelledby="experiencia-anterior">
            <h2 class="section-title" id="experiencia-anterior">Experiencia anterior</h2>
            <div class="jobs">
              {''.join(render_job(job) for job in data['earlier_experience'])}
            </div>
          </section>
        </div>

        <aside class="rail" aria-label="Formación, certificaciones e idiomas">
          <p class="rail-number" aria-hidden="true">02</p>
          <section class="rail-block" aria-labelledby="formacion">
            <h2 class="rail-title" id="formacion">Formación</h2>
            <dl class="rail-items">{education}</dl>
          </section>
          <section class="rail-block" aria-labelledby="certificaciones">
            <h2 class="rail-title" id="certificaciones">Seguridad</h2>
            <dl class="rail-items">{certifications}</dl>
          </section>
          <section class="rail-block" aria-labelledby="idiomas">
            <h2 class="rail-title" id="idiomas">Idiomas</h2>
            <ul class="compact-list">{languages}</ul>
          </section>
          <section class="rail-block" aria-labelledby="forma-trabajo">
            <h2 class="rail-title" id="forma-trabajo">Forma de trabajar</h2>
            <p class="work-style">{esc(data['work_style'])}</p>
          </section>
        </aside>
      </div>
      <footer class="page-footer">CV · página 2</footer>
    </article>
  </main>
</body>
</html>
"""


def register_fonts() -> dict[str, str]:
    font_dir = Path("C:/Windows/Fonts")
    candidates = {
        "Body": font_dir / "segoeui.ttf",
        "BodyBold": font_dir / "segoeuib.ttf",
        "Serif": font_dir / "georgia.ttf",
        "SerifBold": font_dir / "georgiab.ttf",
    }
    fallback = {
        "Body": "Helvetica",
        "BodyBold": "Helvetica-Bold",
        "Serif": "Times-Roman",
        "SerifBold": "Times-Bold",
    }
    for name, path in candidates.items():
        if not path.exists():
            continue
        pdfmetrics.registerFont(TTFont(name, str(path)))
        fallback[name] = name
    return fallback


def wrap_lines(text: str, font: str, size: float, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if pdfmetrics.stringWidth(candidate, font, size) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, font: str, size: float,
                 leading: float, color=INK) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    for line in wrap_lines(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_section_label(c: canvas.Canvas, label: str, x: float, y: float, fonts: dict[str, str]) -> float:
    c.setFillColor(CYAN)
    c.rect(x, y - 1.5, 21, 2.2, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont(fonts["BodyBold"], 7.7)
    c.drawString(x + 29, y - 3, label.upper())
    return y - 18


def draw_bullets(c: canvas.Canvas, bullets: Iterable[str], x: float, y: float, width: float,
                 fonts: dict[str, str], size: float = 8.4, leading: float = 11.2) -> float:
    for item in bullets:
        c.setFillColor(CYAN)
        c.circle(x + 2, y + 2, 1.35, fill=1, stroke=0)
        y = draw_wrapped(c, item, x + 10, y, width - 10, fonts["Body"], size, leading, HexColor("#354A57"))
        y -= 4
    return y


def draw_project_pdf(c: canvas.Canvas, project: dict, x: float, y: float, width: float,
                     fonts: dict[str, str], compact: bool = False) -> float:
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(x, y + 5, x + width, y + 5)
    y -= 9
    title_size = 12 if not compact else 11.5
    title_lines = wrap_lines(project["name"], fonts["SerifBold"], title_size, width - 82)
    c.setFillColor(NAVY)
    c.setFont(fonts["SerifBold"], title_size)
    title_y = y
    for line in title_lines:
        c.drawString(x + 13, title_y, line)
        title_y -= 14
    c.setFillColor(MUTED)
    c.setFont(fonts["BodyBold"], 6.8)
    c.drawRightString(x + width, y + 1, project["dates"].upper())
    c.setFillColor(CYAN)
    c.circle(x + 2.5, y + 3, 3, fill=0, stroke=1)
    y = min(title_y, y - 14)
    c.setFillColor(CYAN)
    c.setFont(fonts["BodyBold"], 8)
    c.drawString(x + 13, y, f"{project['role']} · {project['company']}")
    y -= 14
    y = draw_bullets(c, project["bullets"], x + 13, y, width - 13, fonts, 8.15 if compact else 8.35,
                     10.6 if compact else 11.0)
    c.setFillColor(MUTED)
    c.setFont(fonts["BodyBold"], 6.9)
    c.drawString(x + 13, y, project["team"])
    y -= 12
    technologies = "Tecnologías: " + " · ".join(project["technologies"])
    y = draw_wrapped(c, technologies, x + 13, y, width - 13, fonts["Body"], 6.9, 9, NAVY_SOFT)
    return y - 9


def draw_rail_title(c: canvas.Canvas, title: str, x: float, y: float, fonts: dict[str, str]) -> float:
    c.setFillColor(NAVY)
    c.setFont(fonts["BodyBold"], 7.2)
    c.drawString(x, y, title.upper())
    return y - 14


def draw_page_one(c: canvas.Canvas, data: dict, fonts: dict[str, str]) -> None:
    width, height = A4
    person = data["person"]
    hero_h = 159
    c.setFillColor(NAVY)
    c.rect(0, height - hero_h, width, hero_h, fill=1, stroke=0)
    c.setFillColor(CYAN_BRIGHT)
    c.rect(0, height - hero_h, 9, hero_h, fill=1, stroke=0)
    c.setFillColor(CYAN_BRIGHT)
    c.setFont(fonts["BodyBold"], 7.8)
    c.drawString(50, height - 41, person["tagline"].upper())
    c.setFillColor(WHITE)
    c.setFont(fonts["Serif"], 26)
    c.drawString(50, height - 75, person["name"])
    c.setFillColor(HexColor("#D8E6EB"))
    c.setFont(fonts["BodyBold"], 13)
    c.drawString(50, height - 101, person["title"])

    contacts = [
        (person["location"], None),
        (person["email"], f"mailto:{person['email']}"),
        (person["phone_display"], f"tel:{person['phone_href']}"),
        (person["linkedin_display"], person["linkedin_href"]),
    ]
    x = 50
    y = height - 133
    c.setFont(fonts["Body"], 7.8)
    for index, (label, url) in enumerate(contacts):
        if index:
            c.setFillColor(CYAN_BRIGHT)
            c.drawString(x, y, "·")
            x += 10
        c.setFillColor(HexColor("#E4EEF2"))
        c.drawString(x, y, label)
        text_width = pdfmetrics.stringWidth(label, fonts["Body"], 7.8)
        if url:
            c.linkURL(url, (x, y - 2, x + text_width, y + 8), relative=0)
        x += text_width + 9

    left = 50
    body_top = height - hero_h - 31
    main_w = 351
    gap = 18
    rail_x = left + main_w + gap
    rail_w = width - rail_x - 39
    rail_bottom = 42

    c.setFillColor(RAIL)
    c.rect(rail_x - 10, rail_bottom, rail_w + 10, body_top - rail_bottom + 7, fill=1, stroke=0)
    c.setStrokeColor(LINE)
    c.line(rail_x - 10, rail_bottom, rail_x - 10, body_top + 7)

    y = draw_section_label(c, "Perfil", left, body_top, fonts)
    y = draw_wrapped(c, data["profile"], left, y, main_w, fonts["Serif"], 11.4, 15.3, HexColor("#263B48"))
    y -= 18
    y = draw_section_label(c, "Experiencia por proyectos", left, y, fonts)
    y = draw_project_pdf(c, data["projects"][0], left, y, main_w, fonts)
    y = draw_project_pdf(c, data["projects"][1], left, y, main_w, fonts, compact=True)

    availability_lines = wrap_lines(person["availability"], fonts["BodyBold"], 7.5, main_w - 23)
    box_h = 17 + len(availability_lines) * 10
    c.setFillColor(CYAN_PALE)
    c.rect(left, y - box_h + 7, main_w, box_h, fill=1, stroke=0)
    c.setFillColor(CYAN_BRIGHT)
    c.rect(left, y - box_h + 7, 3.5, box_h, fill=1, stroke=0)
    draw_wrapped(c, person["availability"], left + 12, y - 6, main_w - 23, fonts["BodyBold"], 7.5, 10, NAVY_SOFT)

    c.setFillColor(CYAN)
    c.setFont(fonts["Serif"], 23)
    c.drawString(rail_x, body_top - 2, "01")
    ry = draw_rail_title(c, "Stack principal", rail_x, body_top - 36, fonts)
    for item in data["stack"]:
        c.setStrokeColor(LINE)
        c.line(rail_x, ry + 4, rail_x + rail_w - 8, ry + 4)
        c.setFillColor(NAVY_SOFT)
        c.setFont(fonts["BodyBold"], 8)
        c.drawString(rail_x, ry - 7, item)
        ry -= 22

    c.setFillColor(MUTED)
    c.setFont(fonts["BodyBold"], 6.3)
    c.drawRightString(width - 39, 24, "CV · PÁGINA 1")


def draw_page_two(c: canvas.Canvas, data: dict, fonts: dict[str, str]) -> None:
    width, height = A4
    person = data["person"]
    header_h = 88
    c.setFillColor(NAVY)
    c.rect(0, height - header_h, width, header_h, fill=1, stroke=0)
    c.setFillColor(CYAN_BRIGHT)
    c.rect(0, height - header_h, 9, header_h, fill=1, stroke=0)
    c.setFillColor(CYAN_BRIGHT)
    c.setFont(fonts["BodyBold"], 7.4)
    c.drawString(50, height - 32, "EXPERIENCIA · CONTINUACIÓN")
    c.setFillColor(WHITE)
    c.setFont(fonts["Serif"], 17)
    c.drawString(50, height - 59, person["name"])
    c.setFillColor(HexColor("#D8E6EB"))
    c.setFont(fonts["BodyBold"], 9.5)
    c.drawRightString(width - 39, height - 58, person["title"])

    left = 50
    body_top = height - header_h - 31
    main_w = 351
    gap = 18
    rail_x = left + main_w + gap
    rail_w = width - rail_x - 39
    rail_bottom = 42
    c.setFillColor(RAIL)
    c.rect(rail_x - 10, rail_bottom, rail_w + 10, body_top - rail_bottom + 7, fill=1, stroke=0)
    c.setStrokeColor(LINE)
    c.line(rail_x - 10, rail_bottom, rail_x - 10, body_top + 7)

    y = draw_section_label(c, "Proyecto destacado", left, body_top, fonts)
    y = draw_project_pdf(c, data["projects"][2], left, y, main_w, fonts, compact=True)
    y -= 3
    y = draw_section_label(c, "Experiencia anterior", left, y, fonts)
    for job in data["earlier_experience"]:
        c.setStrokeColor(LINE)
        c.setFillColor(WHITE)
        c.roundRect(left, y - 90, main_w, 88, 3, fill=1, stroke=1)
        c.setFillColor(CYAN)
        c.rect(left, y - 90, 3, 88, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont(fonts["SerifBold"], 10.5)
        c.drawString(left + 12, y - 17, job["company"])
        c.setFillColor(MUTED)
        c.setFont(fonts["BodyBold"], 6.6)
        c.drawRightString(left + main_w - 10, y - 16, job["dates"].upper())
        c.setFillColor(CYAN)
        c.setFont(fonts["BodyBold"], 7.5)
        c.drawString(left + 12, y - 33, job["role"])
        jy = draw_wrapped(c, job["summary"], left + 12, y - 49, main_w - 24, fonts["Body"], 7.6, 9.7, HexColor("#354A57"))
        tech = "Tecnologías: " + " · ".join(job["technologies"])
        draw_wrapped(c, tech, left + 12, jy - 4, main_w - 24, fonts["Body"], 6.5, 8.5, NAVY_SOFT)
        y -= 102

    c.setFillColor(CYAN)
    c.setFont(fonts["Serif"], 23)
    c.drawString(rail_x, body_top - 2, "02")
    ry = body_top - 38
    ry = draw_rail_title(c, "Formación", rail_x, ry, fonts)
    for item in data["education"]:
        ry = draw_wrapped(c, item["title"], rail_x, ry, rail_w - 8, fonts["BodyBold"], 7.5, 9.5, NAVY)
        ry = draw_wrapped(c, item["institution"], rail_x, ry - 2, rail_w - 8, fonts["Body"], 6.7, 8.5, MUTED)
        ry = draw_wrapped(c, item["dates"], rail_x, ry - 1, rail_w - 8, fonts["BodyBold"], 6.5, 8, MUTED)
        ry -= 10

    c.setStrokeColor(LINE)
    c.line(rail_x, ry, rail_x + rail_w - 8, ry)
    ry -= 18
    ry = draw_rail_title(c, "Seguridad", rail_x, ry, fonts)
    for item in data["certifications"]:
        ry = draw_wrapped(c, item["title"], rail_x, ry, rail_w - 8, fonts["BodyBold"], 7.4, 9.2, NAVY)
        ry = draw_wrapped(c, item["status"], rail_x, ry - 2, rail_w - 8, fonts["Body"], 6.5, 8.2, MUTED)
        ry -= 9

    c.setStrokeColor(LINE)
    c.line(rail_x, ry, rail_x + rail_w - 8, ry)
    ry -= 18
    ry = draw_rail_title(c, "Idiomas", rail_x, ry, fonts)
    for item in data["languages"]:
        ry = draw_wrapped(c, item, rail_x, ry, rail_w - 8, fonts["BodyBold"], 7.2, 9.2, NAVY_SOFT)
        ry -= 4

    c.setStrokeColor(LINE)
    c.line(rail_x, ry, rail_x + rail_w - 8, ry)
    ry -= 18
    ry = draw_rail_title(c, "Forma de trabajar", rail_x, ry, fonts)
    draw_wrapped(c, data["work_style"], rail_x, ry, rail_w - 8, fonts["Body"], 6.8, 9.2, HexColor("#314C59"))

    c.setFillColor(MUTED)
    c.setFont(fonts["BodyBold"], 6.3)
    c.drawRightString(width - 39, 24, "CV · PÁGINA 2")


def generate_pdf(data: dict, pdf_path: Path, fonts: dict[str, str]) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf_path), pagesize=A4, pageCompression=1)
    c.setTitle(f"{data['person']['name']} · {data['person']['title']}")
    c.setAuthor(data["person"]["name"])
    c.setSubject("Currículum profesional")
    c.setKeywords("C#, .NET, ASP.NET Core, SQL Server, Azure DevOps, Backend")
    draw_page_one(c, data, fonts)
    c.showPage()
    draw_page_two(c, data, fonts)
    c.showPage()
    c.save()

    reader = PdfReader(str(pdf_path))
    if len(reader.pages) != 2:
        raise RuntimeError(f"El PDF debe tener exactamente 2 páginas; se generaron {len(reader.pages)}")


def generate_site(data: dict, output_dir: Path, fonts: dict[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    markup = "\n".join(line.rstrip() for line in render_html(data).splitlines()) + "\n"
    (output_dir / "index.html").write_text(markup, encoding="utf-8", newline="\n")
    generate_pdf(data, output_dir / PDF_NAME, fonts)


def copy_shared_assets(output_dir: Path) -> None:
    shutil.copy2(DOCS / "styles.css", output_dir / "styles.css")
    shutil.copytree(DOCS / "assets", output_dir / "assets", dirs_exist_ok=True)


def main() -> None:
    with DATA_PATH.open("r", encoding="utf-8") as source:
        data = json.load(source)
    fonts = register_fonts()
    DOCS.mkdir(parents=True, exist_ok=True)
    generate_site(data, DOCS, fonts)
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PDF_PATH, OUTPUT_PDF)
    print(f"HTML: {DOCS / 'index.html'}")
    print(f"PDF:  {PDF_PATH}")
    print(f"PDF:  {OUTPUT_PDF}")

    for version_source in sorted(VERSION_DATA_DIR.glob("*.json")):
        with version_source.open("r", encoding="utf-8") as source:
            version_data = json.load(source)
        version_id = version_data["meta"].get("version")
        if version_id != version_source.stem:
            raise RuntimeError(f"La versión de {version_source.name} debe ser {version_source.stem}")
        version_output = DOCS / version_id
        if version_output.exists():
            print(f"VERSIÓN {version_id}: conservada sin cambios en {version_output}")
            continue
        layout = version_data["meta"].get("layout", "editorial")
        if layout != "editorial":
            raise RuntimeError(
                f"La versión {version_id} usa el layout {layout}; ejecuta su generador específico"
            )
        generate_site(version_data, version_output, fonts)
        copy_shared_assets(version_output)
        print(f"VERSIÓN {version_id}: {version_output}")


if __name__ == "__main__":
    main()

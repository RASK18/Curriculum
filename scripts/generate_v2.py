from __future__ import annotations

import html
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "content" / "versions" / "v2.json"
STYLE_PATH = ROOT / "layouts" / "v2" / "styles.css"
ASSET_SOURCE = ROOT / "assets" / "lucide"
FONT_SOURCE = ROOT / "assets" / "fonts" / "roboto-condensed"
OUTPUT_DIR = ROOT / "docs" / "v2"
PDF_NAME = "Rafael-Jimenez-CV.pdf"
V2_ICONS = (
    "briefcase-business",
    "clock-3",
    "cloud",
    "code-xml",
    "database",
    "download",
    "external-link",
    "graduation-cap",
    "house",
    "mail",
    "map-pin",
    "phone",
    "shield-check",
    "test-tube",
    "user-round",
    "workflow",
)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def icon(name: str, class_name: str = "icon") -> str:
    return (
        f'<img class="{esc(class_name)}" src="assets/icons/{esc(name)}.svg" '
        'alt="" aria-hidden="true">'
    )


def tech_line(items: Iterable[str]) -> str:
    return " · ".join(esc(item) for item in items)


def split_name(name: str) -> tuple[str, str]:
    first, *rest = name.split()
    return first, " ".join(rest)


def render_contact(person: dict) -> str:
    return f"""
      <ul class="contact-list" aria-label="Contacto">
        <li><span class="contact-item">{icon('map-pin')}<span>{esc(person['location'])}</span></span></li>
        <li><a href="mailto:{esc(person['email'])}">{icon('mail')}<span>{esc(person['email'])}</span></a></li>
        <li><a href="tel:{esc(person['phone_href'])}">{icon('phone')}<span>{esc(person['phone_display'])}</span></a></li>
        <li><a href="{esc(person['linkedin_href'])}">{icon('external-link')}<span>{esc(person['linkedin_display'])}</span></a></li>
      </ul>
    """


def render_project(project: dict, accent: str) -> str:
    bullets = "".join(f"<li>{esc(item)}</li>" for item in project["bullets"])
    return f"""
      <article class="project accent-{esc(accent)}">
        <div class="project-head">
          <div>
            <h3>{esc(project['name'])}</h3>
            <p class="position">{esc(project['role'])} · {esc(project['company'])}</p>
          </div>
          <p class="date-badge">{esc(project['dates'])}</p>
        </div>
        <ul>{bullets}</ul>
        <p class="tech-line"><strong>Tecnologías:</strong> {tech_line(project['technologies'])}</p>
      </article>
    """


def render_stack_groups(groups: Iterable[dict]) -> str:
    cards = []
    for group in groups:
        cards.append(
            f"""
            <article class="stack-group accent-{esc(group['accent'])}">
              <span class="stack-icon">{icon(group['icon'])}</span>
              <div>
                <h3>{esc(group['title'])}</h3>
                <p>{tech_line(group['items'])}</p>
              </div>
            </article>
            """
        )
    return "".join(cards)


def render_job(job: dict) -> str:
    return f"""
      <article class="job">
        <h3>{esc(job['company'])}</h3>
        <p class="job-date">{esc(job['dates'])}</p>
        <p class="job-role">{esc(job['role'])}</p>
        <p class="job-summary">{esc(job['summary'])}</p>
        <p class="job-tech"><strong>Tecnologías:</strong> {tech_line(job['technologies'])}</p>
      </article>
    """


def render_sidebar_page_one(data: dict) -> str:
    return f"""
      <aside class="sidebar" aria-label="Perfil y stack técnico">
        <div class="monogram-wrap" aria-hidden="true">
          <div class="monogram">
            <span class="monogram-letters">
              <span class="monogram-r">R</span><span class="monogram-j">J</span>
            </span>
          </div>
        </div>
        <section class="side-section" aria-labelledby="perfil-v2">
          <h2 class="side-heading" id="perfil-v2">{icon('user-round')}<span>Perfil</span></h2>
          <p class="profile">{esc(data['profile'])}</p>
        </section>
        <section class="side-section side-section--stack" aria-labelledby="stack-v2">
          <h2 class="side-heading" id="stack-v2">{icon('code-xml')}<span>Stack técnico</span></h2>
          <div class="stack-groups">{render_stack_groups(data['stack_groups'])}</div>
        </section>
        <section class="side-section side-section--work" aria-labelledby="trabajo-v2">
          <h2 class="side-heading" id="trabajo-v2">{icon('workflow')}<span>Forma de trabajar</span></h2>
          <p class="work-style">{esc(data['work_style'])}</p>
        </section>
      </aside>
    """


def render_html(data: dict) -> str:
    style_revision = hashlib.sha256(STYLE_PATH.read_bytes()).hexdigest()[:12]
    person = data["person"]
    first_name, surnames = split_name(person["name"])
    projects = data["projects"]
    jobs = "".join(render_job(job) for job in data["earlier_experience"])
    education = "".join(
        f"""
        <article class="education-card">
          <div>
            <h3>{esc(item['title'])}</h3>
            <p>{esc(item['institution'])}</p>
          </div>
          <span>{esc(item['dates'])}</span>
        </article>
        """
        for item in data["education"]
    )
    language_codes = ("ES", "EN")
    languages = "".join(
        f'<li><span class="lang-code" aria-hidden="true">{code}</span><strong>{esc(item)}</strong></li>'
        for code, item in zip(language_codes, data["languages"])
    )
    certifications = "".join(
        f"""
        <li>
          {icon('shield-check')}
          <strong>{esc(item['title'])}</strong>
          <span class="cert-year" aria-label="Obtenida en {esc(item['status'])}">{esc(item['status'])}</span>
        </li>
        """
        for item in data["certifications"]
    )
    return f"""<!doctype html>
<html lang="{esc(data['meta']['language'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(data['meta']['description'])}">
  <meta name="cv-version" content="{esc(data['meta']['version'])}">
  <meta name="cv-status" content="{esc(data['meta']['status'])}">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <link rel="canonical" href="{esc(data['meta']['canonical'])}">
  <link rel="icon" href="assets/icons/code-xml.svg" type="image/svg+xml">
  <link rel="stylesheet" href="styles.css?v={style_revision}">
  <title>{esc(person['name'])} · {esc(person['title'])}</title>
</head>
<body>
  <a class="skip-link" href="#contenido">Saltar al contenido</a>

  <main class="cv" id="contenido">
    <article class="page" aria-label="Currículum v2 de una página">
      <div class="upper-layout">
        <header class="main-header">
          <h1 class="name">{esc(first_name)}&nbsp;<span>{esc(surnames)}</span></h1>
          <p class="role">{esc(person['title'])}</p>
          {render_contact(person)}
          <p class="availability">{icon('house')}{esc(person['availability'])}</p>
          <nav class="screen-toolbar" aria-label="Acciones del currículum">
            <a class="toolbar-link" href="{esc(data['meta']['pdf_filename'])}" download>
              {icon('download')} Descargar PDF
            </a>
          </nav>
        </header>

        {render_sidebar_page_one(data)}

        <div class="main-content">
          <section aria-labelledby="experiencia-v2">
            <h2 class="section-banner" id="experiencia-v2">Experiencia profesional</h2>
            <div class="timeline">
              {render_project(projects[0], 'cyan')}
              {render_project(projects[1], 'orange')}
              {render_project(projects[2], 'purple')}
            </div>
          </section>

          <div class="lower-grid">
            <section class="compact-panel" aria-labelledby="experiencia-anterior-v2">
              <h2 class="lower-heading" id="experiencia-anterior-v2">{icon('clock-3')}Experiencia anterior</h2>
              <div class="jobs">{jobs}</div>
            </section>
            <section class="compact-panel compact-panel--education" aria-labelledby="formacion-v2">
              <h2 class="lower-heading" id="formacion-v2">{icon('graduation-cap')}Formación</h2>
              <div class="education-compact">{education}</div>
            </section>
          </div>
        </div>
      </div>

      <footer class="bottom-strip">
        <section aria-labelledby="idiomas-v2">
          <h2 class="strip-heading" id="idiomas-v2">Idiomas</h2>
          <ul class="language-strip">{languages}</ul>
        </section>
        <section aria-labelledby="certificaciones-v2">
          <h2 class="strip-heading" id="certificaciones-v2">Certificaciones</h2>
          <ul class="cert-strip">{certifications}</ul>
        </section>
      </footer>
    </article>
  </main>
</body>
</html>
"""


def find_chrome() -> Path:
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("Se necesita Google Chrome o Microsoft Edge para generar el PDF de v2")


def generate_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = find_chrome()
    profile_parent = ROOT / "tmp"
    profile_parent.mkdir(parents=True, exist_ok=True)
    profile_dir = Path(tempfile.mkdtemp(prefix="chrome-v2-", dir=profile_parent))
    command = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--disable-extensions",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=1500",
        f"--user-data-dir={profile_dir}",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)
    if result.returncode != 0 or not pdf_path.exists():
        raise RuntimeError(
            "No se pudo generar el PDF con el navegador.\n"
            f"Salida: {result.stdout}\nError: {result.stderr}"
        )
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) != 1:
        raise RuntimeError(f"El PDF de v2 debe tener 1 página; se generaron {len(reader.pages)}")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if data["meta"].get("version") != "v2" or data["meta"].get("layout") != "tech-panel":
        raise RuntimeError("content/versions/v2.json debe declarar version=v2 y layout=tech-panel")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    markup = "\n".join(line.rstrip() for line in render_html(data).splitlines()) + "\n"
    html_path = OUTPUT_DIR / "index.html"
    html_path.write_text(markup, encoding="utf-8", newline="\n")
    shutil.copy2(STYLE_PATH, OUTPUT_DIR / "styles.css")
    icon_output = OUTPUT_DIR / "assets" / "icons"
    shutil.rmtree(icon_output, ignore_errors=True)
    icon_output.mkdir(parents=True, exist_ok=True)
    for icon_name in V2_ICONS:
        shutil.copy2(ASSET_SOURCE / "icons" / f"{icon_name}.svg", icon_output / f"{icon_name}.svg")
    shutil.copy2(ASSET_SOURCE / "LUCIDE-LICENSE.txt", OUTPUT_DIR / "assets" / "LUCIDE-LICENSE.txt")
    shutil.copytree(FONT_SOURCE, OUTPUT_DIR / "assets" / "fonts" / "roboto-condensed", dirs_exist_ok=True)

    pdf_path = OUTPUT_DIR / PDF_NAME
    generate_pdf(html_path, pdf_path)

    print(f"HTML: {html_path}")
    print(f"PDF:  {pdf_path}")


if __name__ == "__main__":
    main()

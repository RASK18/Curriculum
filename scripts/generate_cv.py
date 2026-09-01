from __future__ import annotations

import html
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
CURRENT_PATH = ROOT / "content" / "current.json"
VERSION_DATA_DIR = ROOT / "content" / "versions"
STYLE_PATH = ROOT / "layouts" / "v1" / "styles.css"
ASSET_SOURCE = ROOT / "assets" / "lucide"
DOCS = ROOT / "docs"
PDF_NAME = "Rafael-Jimenez-CV.pdf"
V1_ICONS = ("download", "external-link", "mail", "map-pin", "phone")

def esc(value: str) -> str:
    return html.escape(value, quote=True)


def icon(name: str) -> str:
    return f'<img class="icon" src="assets/icons/{esc(name)}.svg" alt="" aria-hidden="true">'


def render_technologies(items: Iterable[str]) -> str:
    return " · ".join(esc(item) for item in items)


def render_stack_groups(groups: Iterable[dict]) -> str:
    return "".join(
        f"""
        <section class="stack-group">
          <h3>{esc(group['title'])}</h3>
          <p>{render_technologies(group['items'])}</p>
        </section>"""
        for group in groups
    )


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
    stack_groups = render_stack_groups(data["stack_groups"])
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
          <li class="contact-divider" aria-hidden="true">·</li>
          <li><a href="mailto:{esc(person['email'])}">{icon('mail')}<span>{esc(person['email'])}</span></a></li>
          <li class="contact-divider" aria-hidden="true">·</li>
          <li><a href="tel:{esc(person['phone_href'])}">{icon('phone')}<span>{esc(person['phone_display'])}</span></a></li>
          <li class="contact-divider" aria-hidden="true">·</li>
          <li><a href="{esc(person['linkedin_href'])}">{icon('external-link')}<span>{esc(person['linkedin_display'])}</span></a></li>
        </ul>
        <p class="availability">{esc(person['availability'])}</p>
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
        </div>

        <aside class="rail" aria-labelledby="stack">
          <p class="rail-number" aria-hidden="true">01</p>
          <h2 class="rail-title" id="stack">Stack por áreas</h2>
          <div class="stack-groups">{stack_groups}</div>
        </aside>
      </div>
      <footer class="page-footer">CV · página 1</footer>
    </article>

    <article class="page page--second" aria-label="Página 2 de 2 del currículum">
      <header class="page-masthead">
        <div>
          <p class="page-kicker">Trayectoria profesional</p>
          <p class="continuation-name">{esc(person['name'])}</p>
        </div>
        <p class="page-role">{esc(person['title'])}</p>
      </header>

      <div class="page-grid">
        <div class="main-column">
          <section class="section" aria-labelledby="proyecto-sek">
            <h2 class="section-title" id="proyecto-sek">Experiencia por proyectos · continuación</h2>
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


def render_redirect(version_id: str, data: dict) -> str:
    target = f"{version_id}/"
    return f"""<!doctype html>
<html lang="{esc(data['meta']['language'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <meta http-equiv="refresh" content="0; url={esc(target)}">
  <link rel="canonical" href="{esc(data['meta']['canonical'])}">
  <title>{esc(data['person']['name'])} · Currículum</title>
</head>
<body>
  <p>Redirigiendo al currículum actual. <a href="{esc(target)}">Continuar a {esc(version_id)}</a>.</p>
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
    raise RuntimeError("Se necesita Google Chrome o Microsoft Edge para generar el PDF")


def generate_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = find_chrome()
    profile_parent = ROOT / "tmp"
    profile_parent.mkdir(parents=True, exist_ok=True)
    profile_dir = Path(tempfile.mkdtemp(prefix="chrome-v1-", dir=profile_parent))
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
    if len(reader.pages) != 2:
        raise RuntimeError(f"El PDF debe tener exactamente 2 páginas; se generaron {len(reader.pages)}")


def generate_site(data: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    markup = "\n".join(line.rstrip() for line in render_html(data).splitlines()) + "\n"
    html_path = output_dir / "index.html"
    html_path.write_text(markup, encoding="utf-8", newline="\n")
    generate_pdf(html_path, output_dir / PDF_NAME)


def copy_shared_assets(output_dir: Path) -> None:
    shutil.copy2(STYLE_PATH, output_dir / "styles.css")
    icon_output = output_dir / "assets" / "icons"
    shutil.rmtree(icon_output, ignore_errors=True)
    icon_output.mkdir(parents=True, exist_ok=True)
    for icon_name in V1_ICONS:
        shutil.copy2(ASSET_SOURCE / "icons" / f"{icon_name}.svg", icon_output / f"{icon_name}.svg")
    shutil.copy2(ASSET_SOURCE / "LUCIDE-LICENSE.txt", output_dir / "assets" / "LUCIDE-LICENSE.txt")


def main() -> None:
    current_config = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
    current_version = current_config["version"]
    current_source = VERSION_DATA_DIR / f"{current_version}.json"
    if not current_source.exists():
        raise RuntimeError(f"La versión actual no existe: {current_version}")
    current_data = json.loads(current_source.read_text(encoding="utf-8"))

    DOCS.mkdir(parents=True, exist_ok=True)
    redirect_markup = "\n".join(
        line.rstrip() for line in render_redirect(current_version, current_data).splitlines()
    ) + "\n"
    (DOCS / "index.html").write_text(redirect_markup, encoding="utf-8", newline="\n")
    print(f"REDIRECCIÓN: {DOCS / 'index.html'} -> {current_version}/")

    for version_source in sorted(VERSION_DATA_DIR.glob("*.json")):
        with version_source.open("r", encoding="utf-8") as source:
            version_data = json.load(source)
        version_id = version_data["meta"].get("version")
        if version_id != version_source.stem:
            raise RuntimeError(f"La versión de {version_source.name} debe ser {version_source.stem}")
        version_output = DOCS / version_id
        layout = version_data["meta"].get("layout", "editorial")
        if layout != "editorial":
            print(f"VERSIÓN {version_id}: conservada; usa el generador del layout {layout}")
            continue
        copy_shared_assets(version_output)
        generate_site(version_data, version_output)
        print(f"VERSIÓN {version_id}: {version_output}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import unquote

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML_PATH = DOCS / "index.html"
CSS_PATH = DOCS / "styles.css"
PDF_PATH = DOCS / "Rafael-Jimenez-CV.pdf"
DATA_PATH = ROOT / "content" / "resume.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def relative_luminance(value: str) -> float:
    channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
              for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    high, low = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def html_text(markup: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def validate_html(data: dict) -> None:
    markup = HTML_PATH.read_text(encoding="utf-8")
    text = html_text(markup)
    assert_true('<html lang="es">' in markup, "Falta lang=es")
    assert_true('content="noindex,nofollow,noarchive"' in markup, "Falta la directiva robots")
    assert_true(f'href="{data["meta"]["canonical"]}"' in markup, "Canonical incorrecta")
    assert_true('href="Rafael-Jimenez-CV.pdf"' in markup, "El PDF no usa una ruta relativa")
    assert_true("<svg" not in markup.lower(), "El HTML no debe contener SVG dibujado manualmente")
    assert_true(not (DOCS / "CNAME").exists(), "El project site no debe incluir CNAME")

    expected = [
        data["person"]["name"],
        data["person"]["title"],
        data["person"]["availability"],
        data["person"]["email"],
        data["person"]["phone_display"],
        *(project["name"] for project in data["projects"]),
        *(item for item in data["stack"]),
    ]
    for value in expected:
        assert_true(value in text, f"Falta contenido esencial en HTML: {value}")

    for target in re.findall(r'(?:src|href)="([^"]+)"', markup):
        if target.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue
        local = DOCS / unquote(target)
        assert_true(local.exists(), f"Recurso relativo inexistente: {target}")

    for icon_name in ("download", "mail", "phone", "map-pin", "external-link"):
        assert_true((DOCS / "assets" / "icons" / f"{icon_name}.svg").exists(), f"Falta icono Lucide: {icon_name}")
    assert_true((DOCS / "assets" / "LUCIDE-LICENSE.txt").exists(), "Falta la licencia de Lucide")


def validate_css() -> None:
    styles = re.sub(r"\s+", " ", CSS_PATH.read_text(encoding="utf-8"))
    assert_true("@page { size: A4 portrait; margin: 0; }" in styles, "La impresión no está configurada como A4")
    assert_true("@media (max-width: 850px)" in styles, "Falta el flujo continuo para móvil/tablet")
    assert_true("@media (max-width: 520px)" in styles, "Falta el ajuste para móvil estrecho")
    assert_true("@media print" in styles, "Faltan estilos de impresión")
    assert_true("width: 210mm; height: 297mm; min-height: 297mm;" in styles,
                "Las hojas impresas no tienen dimensiones A4 exactas")
    assert_true(".skip-link, .screen-toolbar, .icon { display: none !important; }" in styles,
                "Los controles e iconos decorativos deben ocultarse al imprimir")


def validate_pdf(data: dict) -> None:
    reader = PdfReader(str(PDF_PATH))
    assert_true(len(reader.pages) == 2, "El PDF debe tener exactamente dos páginas")
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        assert_true(abs(width - 595.276) < 1 and abs(height - 841.89) < 1, "Una página no es A4")

    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    expected = [
        data["person"]["name"],
        data["person"]["title"],
        data["person"]["availability"],
        data["person"]["email"],
        data["person"]["phone_display"],
        *(project["name"] for project in data["projects"]),
        "CompTIA Security+ ce",
        "Certified Ethical Hacker (CEH)",
        "no vigente desde 2020",
        "no vigente desde 2021",
    ]
    normalized = re.sub(r"\s+", " ", extracted)
    for value in expected:
        assert_true(re.sub(r"\s+", " ", value) in normalized, f"Falta contenido esencial en PDF: {value}")

    links = []
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            action = annotation.get("/A")
            if action and action.get("/URI"):
                links.append(action.get("/URI"))
    assert_true(f"mailto:{data['person']['email']}" in links, "El email del PDF no es clicable")
    assert_true(f"tel:{data['person']['phone_href']}" in links, "El teléfono del PDF no es clicable")
    assert_true(data["person"]["linkedin_href"] in links, "LinkedIn del PDF no es clicable")


def validate_contrast() -> None:
    checks = [
        ("#142431", "#ffffff", 4.5, "texto principal"),
        ("#5f7180", "#ffffff", 4.5, "texto secundario"),
        ("#177c8a", "#ffffff", 4.5, "cargos en HTML"),
        ("#007d8a", "#ffffff", 4.5, "acentos con texto"),
        ("#16c5d8", "#071a2b", 4.5, "acentos sobre cabecera"),
        ("#294553", "#f1f6f8", 4.5, "texto de banda lateral"),
    ]
    for foreground, background, minimum, label in checks:
        ratio = contrast_ratio(foreground, background)
        assert_true(ratio >= minimum, f"Contraste insuficiente ({ratio:.2f}) en {label}")
        print(f"Contraste {label}: {ratio:.2f}:1")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    validate_html(data)
    validate_css()
    validate_pdf(data)
    validate_contrast()
    print("HTML: rutas, metadatos, contenido e iconos correctos")
    print("PDF: 2 páginas A4, texto seleccionable y 3 enlaces clicables")


if __name__ == "__main__":
    main()

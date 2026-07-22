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
VERSION_DATA_DIR = ROOT / "content" / "versions"
PDF_NAME = "Rafael-Jimenez-CV.pdf"


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


def validate_html(data: dict, html_path: Path) -> None:
    page_dir = html_path.parent
    markup = html_path.read_text(encoding="utf-8")
    text = html_text(markup)
    assert_true('<html lang="es">' in markup, "Falta lang=es")
    assert_true('content="noindex,nofollow,noarchive"' in markup, "Falta la directiva robots")
    assert_true(f'href="{data["meta"]["canonical"]}"' in markup, "Canonical incorrecta")
    assert_true('href="Rafael-Jimenez-CV.pdf"' in markup, "El PDF no usa una ruta relativa")
    assert_true("<svg" not in markup.lower(), "El HTML no debe contener SVG dibujado manualmente")
    if data["meta"].get("version"):
        assert_true(
            f'content="{data["meta"]["version"]}"' in markup,
            "Falta la versión del CV en los metadatos",
        )
    if data["meta"].get("status"):
        assert_true(
            f'<meta name="cv-status" content="{data["meta"]["status"]}">' in markup,
            "Falta el estado del CV en los metadatos",
        )

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
        local = page_dir / unquote(target)
        assert_true(local.exists(), f"Recurso relativo inexistente: {target}")

    for icon_name in ("download", "mail", "phone", "map-pin", "external-link"):
        assert_true((page_dir / "assets" / "icons" / f"{icon_name}.svg").exists(), f"Falta icono Lucide: {icon_name}")
    assert_true((page_dir / "assets" / "LUCIDE-LICENSE.txt").exists(), "Falta la licencia de Lucide")


def validate_css(css_path: Path = CSS_PATH, layout: str = "editorial") -> None:
    styles = re.sub(r"\s+", " ", css_path.read_text(encoding="utf-8"))
    assert_true("@page { size: A4 portrait; margin: 0; }" in styles, "La impresión no está configurada como A4")
    assert_true("(max-width: 850px)" in styles, "Falta el flujo continuo para móvil/tablet")
    assert_true("(max-width: 520px)" in styles, "Falta el ajuste para móvil estrecho")
    assert_true("@media print" in styles, "Faltan estilos de impresión")
    assert_true("width: 210mm" in styles and "height: 297mm" in styles and "min-height: 297mm" in styles,
                "Las hojas impresas no tienen dimensiones A4 exactas")
    assert_true(".skip-link" in styles and ".screen-toolbar" in styles and ".icon" in styles
                and "display: none !important" in styles,
                "Los controles e iconos decorativos deben ocultarse al imprimir")
    if layout == "tech-panel":
        for selector in (".monogram", ".sidebar", ".stack-groups", ".timeline", ".preview-badge"):
            assert_true(selector in styles, f"Falta el componente visual de v2: {selector}")


def validate_pdf(data: dict, pdf_path: Path) -> None:
    reader = PdfReader(str(pdf_path))
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


def validate_v2_contrast() -> None:
    checks = [
        ("#0c1830", "#ffffff", 4.5, "texto principal v2"),
        ("#526079", "#ffffff", 4.5, "texto secundario v2"),
        ("#00788a", "#ffffff", 4.5, "acento cian v2"),
        ("#6744ca", "#ffffff", 4.5, "acento morado v2"),
        ("#ad5700", "#ffffff", 4.5, "acento naranja v2"),
        ("#f7fbff", "#04142c", 4.5, "texto lateral v2"),
    ]
    for foreground, background, minimum, label in checks:
        ratio = contrast_ratio(foreground, background)
        assert_true(ratio >= minimum, f"Contraste insuficiente ({ratio:.2f}) en {label}")
        print(f"Contraste {label}: {ratio:.2f}:1")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert_true(not (DOCS / "CNAME").exists(), "El project site no debe incluir CNAME")
    validate_html(data, HTML_PATH)
    validate_css()
    validate_pdf(data, PDF_PATH)
    validate_contrast()
    print("HTML: rutas, metadatos, contenido e iconos correctos")
    print("PDF: 2 páginas A4, texto seleccionable y 3 enlaces clicables")

    for version_source in sorted(VERSION_DATA_DIR.glob("*.json")):
        version_data = json.loads(version_source.read_text(encoding="utf-8"))
        version_id = version_data["meta"].get("version")
        assert_true(version_id == version_source.stem, f"Versión inconsistente en {version_source.name}")
        version_dir = DOCS / version_id
        validate_html(version_data, version_dir / "index.html")
        validate_pdf(version_data, version_dir / PDF_NAME)
        layout = version_data["meta"].get("layout", "editorial")
        if layout == "editorial":
            assert_true((version_dir / "styles.css").read_bytes() == CSS_PATH.read_bytes(),
                        f"Los estilos de {version_id} no coinciden con la versión publicada")
        else:
            validate_css(version_dir / "styles.css", layout)
            if layout == "tech-panel":
                validate_v2_contrast()
        print(f"VERSIÓN {version_id}: HTML y PDF correctos")


if __name__ == "__main__":
    main()

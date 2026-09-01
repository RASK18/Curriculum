from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML_PATH = DOCS / "index.html"
CURRENT_PATH = ROOT / "content" / "current.json"
VERSION_DATA_DIR = ROOT / "content" / "versions"
V1_STYLE_SOURCE = ROOT / "layouts" / "v1" / "styles.css"
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


def validate_redirect(version_id: str, data: dict) -> None:
    markup = HTML_PATH.read_text(encoding="utf-8")
    target = f"{version_id}/"
    assert_true('<html lang="es">' in markup, "La redirección raíz no declara lang=es")
    assert_true(
        f'<meta http-equiv="refresh" content="0; url={target}">' in markup,
        "La redirección raíz no apunta a la versión actual",
    )
    assert_true(f'href="{target}"' in markup, "Falta el enlace alternativo a la versión actual")
    assert_true(
        f'href="{data["meta"]["canonical"]}"' in markup,
        "La redirección raíz no usa la canonical de la versión actual",
    )
    assert_true('content="noindex,nofollow,noarchive"' in markup, "Falta robots en la redirección")
    root_files = {item.name for item in DOCS.iterdir() if item.is_file()}
    assert_true(
        root_files == {".nojekyll", "index.html"},
        f"La raíz contiene archivos innecesarios: {sorted(root_files)}",
    )
    assert_true(not (DOCS / "assets").exists(), "La raíz no debe duplicar recursos de las versiones")


def validate_html(data: dict, html_path: Path, pdf_href: str = PDF_NAME) -> None:
    page_dir = html_path.parent
    markup = html_path.read_text(encoding="utf-8")
    text = html_text(markup)
    assert_true('<html lang="es">' in markup, "Falta lang=es")
    assert_true('content="noindex,nofollow,noarchive"' in markup, "Falta la directiva robots")
    assert_true(f'href="{data["meta"]["canonical"]}"' in markup, "Canonical incorrecta")
    assert_true(f'href="{pdf_href}"' in markup, "El enlace al PDF no es el esperado")
    assert_true("<svg" not in markup.lower(), "El HTML no debe contener SVG dibujado manualmente")
    toolbar_position = markup.find('<nav class="screen-toolbar"')
    cv_position = markup.find('<main class="cv"')
    assert_true(
        0 <= toolbar_position < cv_position,
        "El botón de descarga debe estar fuera de la hoja del currículum",
    )
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
        *(certification["title"] for certification in data["certifications"]),
        *(certification["status"] for certification in data["certifications"]),
    ]
    expected.extend(
        item
        for group in data.get("stack_groups", [])
        for item in group["items"]
    )
    for value in expected:
        assert_true(value in text, f"Falta contenido esencial en HTML: {value}")
    assert_true("no vigente" not in text.casefold(), "No debe mostrarse el estado de caducidad")

    for target in re.findall(r'(?:src|href)="([^"]+)"', markup):
        if target.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue
        local = page_dir / unquote(urlsplit(target).path)
        assert_true(local.exists(), f"Recurso relativo inexistente: {target}")

    for icon_name in ("download", "mail", "phone", "map-pin", "external-link"):
        assert_true((page_dir / "assets" / "icons" / f"{icon_name}.svg").exists(), f"Falta icono Lucide: {icon_name}")
    combined_assets_markup = markup + "\n" + (page_dir / "styles.css").read_text(encoding="utf-8")
    for icon_path in (page_dir / "assets" / "icons").glob("*.svg"):
        relative_icon = f"assets/icons/{icon_path.name}"
        assert_true(relative_icon in combined_assets_markup, f"Icono publicado sin uso: {relative_icon}")
    assert_true((page_dir / "assets" / "LUCIDE-LICENSE.txt").exists(), "Falta la licencia de Lucide")
    if data["meta"].get("layout") == "tech-panel":
        font_dir = page_dir / "assets" / "fonts" / "roboto-condensed"
        assert_true((font_dir / "RobotoCondensed-Variable.ttf").exists(), "Falta Roboto Condensed local")
        assert_true((font_dir / "OFL.txt").exists(), "Falta la licencia OFL de Roboto Condensed")


def validate_css(css_path: Path, layout: str = "editorial") -> None:
    styles = re.sub(r"\s+", " ", css_path.read_text(encoding="utf-8"))
    assert_true("@page { size: A4 portrait; margin: 0; }" in styles, "La impresión no está configurada como A4")
    assert_true("(max-width: 850px)" in styles, "Falta el flujo continuo para móvil/tablet")
    assert_true("(max-width: 520px)" in styles, "Falta el ajuste para móvil estrecho")
    assert_true("@media print" in styles, "Faltan estilos de impresión")
    assert_true("width: 210mm" in styles and "height: 297mm" in styles and "min-height: 297mm" in styles,
                "Las hojas impresas no tienen dimensiones A4 exactas")
    assert_true(".skip-link" in styles and ".screen-toolbar" in styles
                and "display: none !important" in styles,
                "Los controles de pantalla deben ocultarse al imprimir")
    if layout == "tech-panel":
        for selector in (".monogram", ".sidebar", ".stack-groups", ".timeline", ".bottom-strip"):
            assert_true(selector in styles, f"Falta el componente visual de v2: {selector}")


def validate_pdf(data: dict, pdf_path: Path) -> None:
    reader = PdfReader(str(pdf_path))
    assert_true(
        reader.trailer["/Root"].get("/StructTreeRoot") is not None,
        "El PDF debe conservar una estructura etiquetada para accesibilidad",
    )
    expected_pages = data["meta"].get("pages", 2)
    assert_true(
        len(reader.pages) == expected_pages,
        f"El PDF debe tener exactamente {expected_pages} página(s)",
    )
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
        *(certification["title"] for certification in data["certifications"]),
        *(certification["status"] for certification in data["certifications"]),
    ]
    normalized = re.sub(r"\s+", " ", extracted).casefold()
    assert_true("descargar pdf" not in normalized, "El control de descarga no debe aparecer dentro del PDF")
    for value in expected:
        expected_value = re.sub(r"\s+", " ", value).casefold()
        assert_true(expected_value in normalized, f"Falta contenido esencial en PDF: {value}")

    if data["meta"].get("layout", "editorial") == "editorial":
        page_one = re.sub(r"\s+", " ", reader.pages[0].extract_text() or "").casefold()
        page_two = re.sub(r"\s+", " ", reader.pages[1].extract_text() or "").casefold()
        page_one_anchors = [
            data["person"]["name"],
            data["person"]["availability"],
            "Perfil",
            data["projects"][0]["name"],
            data["projects"][1]["name"],
            "Stack por áreas",
        ]
        page_two_anchors = [
            "Trayectoria profesional",
            "Experiencia por proyectos",
            data["projects"][2]["name"],
            "Experiencia anterior",
            *(job["company"] for job in data["earlier_experience"]),
            "Formación",
            data["certifications"][0]["title"],
            "Idiomas",
        ]
        for page_text, anchors, page_number in (
            (page_one, page_one_anchors, 1),
            (page_two, page_two_anchors, 2),
        ):
            positions = []
            for value in anchors:
                expected_value = re.sub(r"\s+", " ", value).casefold()
                position = page_text.find(expected_value)
                assert_true(position >= 0, f"Falta un ancla de lectura en PDF (página {page_number}): {value}")
                positions.append(position)
            assert_true(
                positions == sorted(positions),
                f"El orden de lectura del PDF editorial no es coherente en la página {page_number}",
            )

    if data["meta"].get("layout") == "tech-panel":
        layout_text = "\n".join(
            page.extract_text(extraction_mode="layout") or "" for page in reader.pages
        )
        normalized_layout = re.sub(r"\s+", " ", layout_text).casefold()
        reading_anchors = [
            data["person"]["name"],
            data["person"]["availability"],
            *(project["name"] for project in data["projects"]),
            *(job["company"] for job in data["earlier_experience"]),
            data["education"][1]["institution"].split(" · ")[0],
            "Idiomas",
            "Certificaciones",
        ]
        anchor_positions = []
        for value in reading_anchors:
            expected_value = re.sub(r"\s+", " ", value).casefold()
            position = normalized_layout.find(expected_value)
            assert_true(position >= 0, f"Falta un ancla de lectura en PDF: {value}")
            anchor_positions.append(position)
        assert_true(
            anchor_positions == sorted(anchor_positions),
            "El orden geométrico de lectura del PDF v2 no es coherente",
        )

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
    current_config = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
    current_version = current_config["version"]
    current_source = VERSION_DATA_DIR / f"{current_version}.json"
    assert_true(current_source.exists(), f"La versión actual no existe: {current_version}")
    current_data = json.loads(current_source.read_text(encoding="utf-8"))
    assert_true(not (DOCS / "CNAME").exists(), "El project site no debe incluir CNAME")
    validate_redirect(current_version, current_data)
    output_pdfs = list((ROOT / "output" / "pdf").glob("*.pdf"))
    assert_true(not output_pdfs, "output/pdf no debe contener copias duplicadas")
    print(f"RAÍZ: redirección mínima a {current_version}/")

    for version_source in sorted(VERSION_DATA_DIR.glob("*.json")):
        version_data = json.loads(version_source.read_text(encoding="utf-8"))
        version_id = version_data["meta"].get("version")
        assert_true(version_id == version_source.stem, f"Versión inconsistente en {version_source.name}")
        version_dir = DOCS / version_id
        validate_html(version_data, version_dir / "index.html")
        validate_pdf(version_data, version_dir / PDF_NAME)
        layout = version_data["meta"].get("layout", "editorial")
        if layout == "editorial":
            validate_css(version_dir / "styles.css", layout)
            assert_true((version_dir / "styles.css").read_bytes() == V1_STYLE_SOURCE.read_bytes(),
                        f"Los estilos de {version_id} no coinciden con su fuente")
            validate_contrast()
        else:
            validate_css(version_dir / "styles.css", layout)
            if layout == "tech-panel":
                validate_v2_contrast()
        print(f"VERSIÓN {version_id}: HTML y PDF correctos")


if __name__ == "__main__":
    main()

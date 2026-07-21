# CV de Rafael Jiménez Aguirrebeña

CV estático en español, preparado para GitHub Pages y para impresión A4. El
HTML y el PDF se generan desde una única fuente estructurada:
[`content/resume.json`](content/resume.json).

## Generación

Requisitos: Python 3 con `reportlab` y `pypdf`.

```powershell
python scripts/generate_cv.py
```

El comando actualiza:

- `docs/index.html`
- `docs/Rafael-Jimenez-CV.pdf`
- `output/pdf/Rafael-Jimenez-CV.pdf`

Validación técnica:

```powershell
python scripts/validate_cv.py
```

## Revisión local

```powershell
python -m http.server 8765 --directory docs
```

Abrir `http://127.0.0.1:8765/`. La web usa rutas relativas y no necesita
framework, compilador frontend ni backend.

## Publicación

GitHub Pages se configura con la rama `main` y la carpeta `/docs`. El dominio
personalizado se hereda del repositorio de usuario `RASK18/RASK18.github.io`;
por ese motivo este repositorio no contiene un archivo `CNAME`.

## Licencias de terceros

Los iconos proceden sin modificaciones de `lucide-static` 1.25.0. Su aviso de
licencia se conserva en [`docs/assets/LUCIDE-LICENSE.txt`](docs/assets/LUCIDE-LICENSE.txt)
y en [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

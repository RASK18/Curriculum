# CV de Rafael Jiménez Aguirrebeña

CV estático en español, preparado para GitHub Pages y para impresión A4. La
versión actual se genera desde [`content/resume.json`](content/resume.json) y
cada versión histórica conserva su propia instantánea estructurada en
[`content/versions/`](content/versions/).

## Generación

Requisitos: Python 3 con `reportlab` y `pypdf`.

```powershell
python scripts/generate_cv.py
```

El comando actualiza:

- `docs/index.html`
- `docs/Rafael-Jimenez-CV.pdf`
- `docs/v1/index.html`
- `docs/v1/Rafael-Jimenez-CV.pdf`
- `output/pdf/Rafael-Jimenez-CV.pdf`

Validación técnica:

```powershell
python scripts/validate_cv.py
```

## Versiones

- `https://disboard.es/Curriculum/` contiene siempre la versión actual.
- `https://disboard.es/Curriculum/v1/` es una instantánea histórica e inmutable.

Para publicar una nueva versión se añade primero su fuente a
`content/versions/vN.json`. El campo `meta.version` debe coincidir con el nombre
del archivo; el generador se encarga de crear la carpeta correspondiente en
`docs/`. Si esa carpeta ya existe, no la sobrescribe: una versión publicada
permanece inmutable.

## Revisión local

```powershell
python -m http.server 8765 --directory docs
```

Abrir `http://127.0.0.1:8765/`. La web usa rutas relativas y no necesita
framework, compilador frontend ni backend.

## Publicación

El repositorio público es `RASK18/Curriculum`. GitHub Pages se configura con la
rama `main` y la carpeta `/docs`. El dominio personalizado se hereda del
repositorio de usuario `RASK18/RASK18.github.io`; por ese motivo este
repositorio no contiene un archivo `CNAME`.

## Licencias de terceros

Los iconos proceden sin modificaciones de `lucide-static` 1.25.0. Su aviso de
licencia se conserva en [`docs/assets/LUCIDE-LICENSE.txt`](docs/assets/LUCIDE-LICENSE.txt)
y en [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

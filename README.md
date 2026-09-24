# Nou Padel i Tenis Campos · Web pública

Web informativa del club, en castellano (`/`), catalán (`/ca/`) e inglés (`/en/`). Es una web
**estática**: `build.py` genera HTML a partir de los JSON de `content/` y GitHub Pages la publica.
No necesita servidor, base de datos ni Python en producción.

El panel de reservas del staff vive en otro repositorio,
[CamposClubManager](https://github.com/marcmorlaaa/CamposClubManager).

## Cambiar contenidos

Todo se edita en `content/` y se publica al hacer push a `main` (tarda uno o dos minutos):

| Fichero | Qué contiene |
| --- | --- |
| `site.json` | Contacto, enlaces, marcador, horario, tarifas y clases |
| `menu.json` | Carta de la cafetería |
| `announcements.json` | Tablón de anuncios (torneos, avisos…) |
| `collaborators.json` | Fichas de colaboradores, en el orden en que se muestran |
| `i18n.json` | Textos fijos de la interfaz en los tres idiomas |

Cualquier texto puede ser una cadena o `{"es": "…", "ca": "…", "en": "…"}`; si falta un idioma se usa
el castellano.

**Anuncios** (`announcements.json`): `title` es obligatorio en castellano. `event_date` es la fecha que
se muestra y `visible_until` el último día visible (si falta, se usa `event_date`; sin ninguna de las
dos, el anuncio sigue hasta que lo quites o pongas `"visible": false`). `link_kind` es `"signup"`
(botón «Inscríbete») o `"info"` («Más información»). Los enlaces de torneos de Sportelia se corrigen
solos a la vista pública. La web se regenera cada noche para retirar los caducados.

**Colaboradores** (`collaborators.json`): `name` y `specialty` obligatorios. Para la foto, deja una
imagen JPG/PNG/WebP (máx. ~2 MB, 4:3) en `static/images/collaborators/` y pon su ruta en `photo`,
por ejemplo `"images/collaborators/progame.jpg"`.

**Carta en PDF**: tras cambiar precios en `menu.json`, regenera el PDF (necesita Chromium o Chrome):

```powershell
python scripts/generate_menu_pdf.py
```

Si un dato está mal escrito (fecha, enlace, correo…), el build falla y no se publica nada: el error
aparece en la pestaña **Actions** de GitHub.

## En local

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python build.py
.venv\Scripts\python -m http.server 8000 -d dist
```

Web en <http://localhost:8000>. Tests: `.venv\Scripts\python -m unittest discover -s tests -v`.

## Publicación

GitHub Actions (`.github/workflows/pages.yml`) pasa los tests, genera `dist/` y lo publica en GitHub
Pages en cada push a `main`, cada noche y a mano desde **Actions → Publicar web → Run workflow**.

Dominio propio: pon el dominio en `"domain"` de `site.json` (se genera el fichero `CNAME`), configúralo
en **Settings → Pages** y apunta el DNS a GitHub Pages. El enlace «Acceso Staff» del pie aparece
cuando `"staff_url"` apunta al panel (por ejemplo `https://gestion.tu-dominio/login`).

La web sigue sin indexarse (`noindex` y `robots.txt`), igual que antes de separarla.

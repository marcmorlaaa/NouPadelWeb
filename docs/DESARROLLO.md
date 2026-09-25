# Desarrollo

La web es **estática**: `build.py` genera el HTML a partir de los JSON de `content/` y deja el
resultado en `dist/`. En producción no hace falta servidor, base de datos ni Python; GitHub Pages sirve
directamente esa carpeta.

Hay una página por idioma: castellano en `/`, catalán en `/ca/` e inglés en `/en/`. Todas las rutas
internas son relativas, así que la web funciona igual con dominio propio, bajo
`usuario.github.io/NouPadelWeb/` o abriendo `dist/` desde un servidor local.

El panel privado de reservas del staff es un proyecto aparte. La web solo enlaza con él desde el botón
**Acceso Staff** del pie y desde la dirección `/login`.

## Estructura

```
content/            Datos de la web (lo que se edita habitualmente)
  site.json           Contacto, enlaces, horario, tarifas, clases, dominio y enlace al panel
  menu.json           Carta de la cafetería
  announcements.json  Tablón de anuncios
  collaborators.json  Fichas de colaboradores
  i18n.json           Textos fijos de la interfaz en los tres idiomas
templates/index.html  Plantilla Jinja2 de la página (una para los tres idiomas)
static/             CSS, JS, fuentes, imágenes y carta en PDF (se copian tal cual a dist/static/)
build.py            Genera dist/ y, con --dev, la sirve en local
scripts/            generate_menu_pdf.py: regenera la carta en PDF desde menu.json
tests/              Tests del build (unittest)
.github/workflows/  Tests y publicación en GitHub Pages
```

Además de las páginas, el build escribe `robots.txt`, `sitemap.xml`, `CNAME`, `.nojekyll` y
`login/index.html` (una redirección al panel del staff, ver `staff_url` en
[CONTENIDOS.md](CONTENIDOS.md)).

## Arrancar en local

Hace falta Python 3.10 o superior.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build.py --dev
```

En Windows, cambia `.venv/bin/` por `.venv\Scripts\`.

Abre <http://localhost:8000>. El modo `--dev` genera la web y la sirve en el puerto 8000, con
**Acceso Staff** apuntando al panel local (`http://localhost/login`). Tras editar algo, para el
servidor con Ctrl+C y vuelve a lanzarlo.

Otras opciones:

```bash
.venv/bin/python build.py                                             # solo generar dist/
.venv/bin/python build.py --dev --staff-url http://localhost:5000/login  # panel en otro puerto
.venv/bin/python -m unittest discover -s tests -v                     # tests
```

`dist/` no se versiona.

## Publicación

El workflow `.github/workflows/pages.yml` se ejecuta en cada push a `main`, cada noche (para retirar los
anuncios caducados) y a mano desde **Actions → Publicar web → Run workflow**. Pasa los tests, genera
`dist/` y lo publica en GitHub Pages, siempre que la variable del repositorio `PAGES_ENABLED` valga
`true`.

Cómo se montó todo desde cero (GitHub Pages, dominio en IONOS, HTTPS y Google) está en
[DESPLIEGUE.md](DESPLIEGUE.md).

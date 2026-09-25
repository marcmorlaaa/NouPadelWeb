# Nou Padel i Tenis Campos · Web pública

Web informativa del club **Nou Padel i Tenis Campos** (Campos, Mallorca): horarios, tarifas, clases,
carta de la cafetería, tablón de anuncios, colaboradores y contacto, en castellano (`/`),
catalán (`/ca/`) e inglés (`/en/`).

Es una web **estática**: `build.py` genera el HTML a partir de los JSON de `content/`. No necesita
servidor, base de datos ni Python en producción; basta con servir la carpeta `dist/`.

El panel privado de reservas del staff es otro proyecto:
[CamposClubManager](https://github.com/marcmorlaaa/CamposClubManager). La web solo enlaza con él desde
el botón **Acceso Staff** del pie.

> **Estado:** repositorio privado y **todavía sin publicar**. Ver [Publicación](#publicación).

## Estructura

```
content/            Datos de la web (lo que se edita habitualmente)
  site.json           Contacto, enlaces, marcador, horario, tarifas, clases, dominio y enlace al panel
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

## Desarrollo local

Requisitos: Python 3.10 o superior.

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python build.py --dev
```

Abre <http://localhost:8000>. El modo `--dev` genera la web y la sirve en el puerto 8000; **Acceso
Staff** apunta al panel local, `http://localhost/login`, que es donde lo levanta CamposClubManager
con `docker compose -f docker-compose.local.yml up`. Los dos proyectos pueden estar arrancados a la vez.

Tras editar algo, para el servidor (Ctrl+C) y vuelve a lanzar `build.py --dev`.

Otras opciones:

```powershell
.venv\Scripts\python build.py                                        # solo generar dist/, con los datos de site.json
.venv\Scripts\python build.py --dev --staff-url http://localhost:5000/login   # panel en otro puerto
.venv\Scripts\python -m unittest discover -s tests -v                # tests
```

`dist/` no se versiona.

## Cambiar contenidos

Todo se edita en `content/`. Cualquier texto puede ser una cadena o `{"es": "…", "ca": "…", "en": "…"}`;
si falta un idioma se usa el castellano.

Si un dato está mal escrito (fecha, enlace, correo, teléfono, foto inexistente…), el build falla con un
mensaje que dice qué fichero y qué entrada revisar, y no se publica nada.

### Anuncios (`announcements.json`)

```json
{
  "title": {"es": "Torneo de otoño", "ca": "Torneig de tardor", "en": "Autumn tournament"},
  "body": {"es": "Del 15 al 18 de octubre.\nCategorías de 2.ª a 5.ª."},
  "link": "https://torneos.sportelia.es/#/tournaments-details/XXXX/public",
  "link_kind": "signup",
  "event_date": "2026-10-15",
  "visible_until": "2026-10-18",
  "visible": true
}
```

- `title` es obligatorio en castellano; `body` admite saltos de línea (`\n`).
- `event_date` (AAAA-MM-DD) es la fecha que se muestra; `visible_until` es el último día visible. Si
  falta `visible_until` se usa `event_date`; sin ninguna, el anuncio sigue hasta que lo borres o pongas
  `"visible": false`.
- `link_kind`: `"signup"` muestra «Inscríbete» y `"info"` «Más información». Los enlaces de Sportelia se
  corrigen solos a su vista pública.
- Se ordenan por fecha; los que no tienen fecha van al final. Si no hay ninguno visible, la sección no
  aparece.
- Los caducados se retiran al generar la web y el navegador también oculta los que caducan entre dos
  builds. Con la publicación activa, la web se regenera cada noche.

### Colaboradores (`collaborators.json`)

Se muestran en el orden del fichero. `name` y `specialty` son obligatorios; el resto (`description`,
`prices`, `availability`, `phone`, `email`, `website`, `instagram`) es opcional. `"visible": false` oculta
la ficha sin borrarla.

Para la foto, deja una imagen JPG, PNG o WebP (4:3, máx. ~2 MB) en `static/images/collaborators/` y
pon su ruta relativa a `static/` en `photo`, por ejemplo `"images/collaborators/progame.jpg"`. Sin foto
se muestra la inicial del nombre.

### Horario, tarifas y contacto (`site.json`)

- `schedule`: franjas con `days`, `hours` y `weekdays` (1 = lunes … 7 = domingo) para marcar el día de hoy.
- `rates` y `classes`: precios con coma decimal (`"24,00"`); un precio vacío muestra «Consultar».
- `playtomic`: si está, «Reservar pista» abre Playtomic; si no, baja a contacto.
- `staff_url`: enlace de **Acceso Staff** en producción (por ejemplo `https://gestion.tu-dominio/login`).
  Vacío, el enlace no aparece. En local lo sustituye `--dev`.
- `domain`: dominio propio (`noupadeliteniscampos.com`, sin `https://` ni barras). Genera `CNAME` y
  `sitemap.xml`, y activa las URLs absolutas de los metadatos: `canonical`, `hreflang` con `x-default`,
  Open Graph y el JSON-LD del club. Los enlaces internos siguen siendo relativos.
- `indexable`: `false` deja la web cerrada a buscadores (`noindex` en cada página y `Disallow: /` en
  `robots.txt`); `true` quita el `noindex` y `robots.txt` apunta al sitemap. Requiere `domain`.
- `latitude` y `longitude`: coordenadas de la entrada del club para el JSON-LD.
- `share_image`: imagen al compartir el enlace, relativa a `static/`, de 1200×630 (`images/og.jpg`).

### Carta (`menu.json` y PDF)

La carta de la web sale de `menu.json`. El PDF descargable (solo en castellano) está versionado en
`static/documents/carta.pdf`; tras cambiar precios, regenéralo (necesita Chromium o Google Chrome):

```powershell
.venv\Scripts\python scripts/generate_menu_pdf.py
```

### Textos de la interfaz (`i18n.json`)

Cada idioma debe tener todas las claves; un test lo comprueba.

## Publicación

El workflow `.github/workflows/pages.yml` se ejecuta en cada push a `main`, cada noche y a mano
(**Actions → Publicar web → Run workflow**): pasa los tests y genera `dist/`. **Solo publica** en
GitHub Pages si la variable del repositorio `PAGES_ENABLED` vale `true` (ya lo vale: la web está publicada en
<https://noupadeliteniscampos.com/>, con HTTPS de GitHub).

El paso a paso completo (GitHub Pages, DNS en IONOS, HTTPS y Google Search Console), con los problemas
que salieron y cómo se resolvieron, está en [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md). El plan de SEO,
con lo hecho y lo pendiente, en [`docs/PLAN_SEO_Y_PUBLICACION.md`](docs/PLAN_SEO_Y_PUBLICACION.md).

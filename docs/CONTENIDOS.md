# Cambiar contenidos

Todo se edita en `content/`. Cualquier texto puede ser una cadena o `{"es": "…", "ca": "…", "en": "…"}`;
si falta un idioma se usa el castellano.

Si un dato está mal escrito (fecha, enlace, correo, teléfono, foto inexistente…), el build falla con un
mensaje que dice qué fichero y qué entrada revisar, y no se publica nada.

Después de cualquier cambio, genera la web en local para revisarla (ver [DESARROLLO.md](DESARROLLO.md))
y haz push a `main`: se publica sola en un par de minutos.

## Anuncios (`announcements.json`)

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
- Los caducados se retiran al generar la web, y el navegador también oculta los que caducan entre dos
  builds. La web se regenera cada noche.

## Colaboradores (`collaborators.json`)

Se muestran en el orden del fichero. `name` y `specialty` son obligatorios; el resto (`description`,
`prices`, `availability`, `phone`, `email`, `website`, `instagram`) es opcional. `"visible": false` oculta
la ficha sin borrarla.

Para la foto, deja una imagen JPG, PNG o WebP (4:3, máx. ~2 MB) en `static/images/collaborators/` y
pon su ruta relativa a `static/` en `photo`, por ejemplo `"images/collaborators/progame.jpg"`. Sin foto
se muestra la inicial del nombre.

## Horario, tarifas y contacto (`site.json`)

- `schedule`: franjas con `days`, `hours` y `weekdays` (1 = lunes … 7 = domingo) para marcar el día de hoy.
- `rates` y `classes`: precios con coma decimal (`"24,00"`); un precio vacío muestra «Consultar».
- `playtomic`: si está, «Reservar pista» abre Playtomic; si no, baja a contacto.
- `staff_url`: dirección del login del panel del staff. Se usa en el botón **Acceso Staff** del pie y
  en la página `/login`, que redirige ahí. Vacío, no aparece ninguna de las dos. En local lo sustituye
  `--dev`.
- `domain`: dominio propio (`noupadeliteniscampos.com`, sin `https://` ni barras). Genera `CNAME` y
  `sitemap.xml`, y activa las URLs absolutas de los metadatos: `canonical`, `hreflang` con `x-default`,
  Open Graph y el JSON-LD del club. Los enlaces internos siguen siendo relativos.
- `indexable`: `false` deja la web cerrada a buscadores (`noindex` en cada página y `Disallow: /` en
  `robots.txt`); `true` quita el `noindex` y `robots.txt` apunta al sitemap. Requiere `domain`.
- `latitude` y `longitude`: coordenadas de la entrada del club para el JSON-LD.
- `share_image`: imagen al compartir el enlace, relativa a `static/`, de 1200×630 (`images/og.jpg`).

## Carta (`menu.json` y PDF)

La carta de la web sale de `menu.json`. El PDF descargable (solo en castellano) está versionado en
`static/documents/carta.pdf`; tras cambiar precios hay que regenerarlo (necesita Chromium o Google
Chrome):

```bash
.venv/bin/python scripts/generate_menu_pdf.py
```

## Textos de la interfaz (`i18n.json`)

Cada idioma debe tener todas las claves; un test lo comprueba.

# AGENTS.md

Guía para agentes que trabajen en este repositorio.

## Qué es

Web pública estática de **Nou Padel i Tenis Campos**, separada del panel de reservas
(`CamposClubManager`, otro repo). Todos los textos visibles y comentarios van en **castellano**.

- `build.py` — carga `content/*.json`, valida anuncios y colaboradores (un error lanza `ContentError`
  y el build no escribe nada) y renderiza `templates/index.html` con Jinja2 una vez por idioma:
  `dist/index.html`, `dist/ca/index.html`, `dist/en/index.html`. Copia `static/` a `dist/static/`
  y escribe `robots.txt`, `.nojekyll` y `CNAME` (si `site.json` tiene `domain`).
- Todas las URLs son **relativas** (`root` = `''` o `'../'`, `lang_paths` para el selector de idioma)
  para que la web funcione bajo `usuario.github.io/NouPadelWeb/` y con dominio propio. No añadas rutas
  que empiecen por `/`; un test lo comprueba.
- `localize()` convierte `{"es", "ca", "en"}` en el texto del idioma con reserva en castellano; se
  aplica a `site.json`, `menu.json`, `collaborators.json` y a título/cuerpo de los anuncios.
  `i18n.json` debe tener todas las claves en todos los idiomas (test).
- SEO: `site.json` → `domain` activa `canonical`, `hreflang` (+ `x-default`), Open Graph, JSON-LD
  `SportsActivityLocation` y `sitemap.xml`, todos con URLs absolutas (la única excepción a la regla de
  rutas relativas, y solo en metadatos). `indexable: false` pone `noindex` y `Disallow: /`; `true` exige
  `domain`. `validate_site()` valida dominio, coordenadas y `share_image`. Plan: `docs/PLAN_SEO_Y_PUBLICACION.md`; despliegue: `docs/DESPLIEGUE.md`.
- Documentación: el `README.md` es solo la presentación pública (qué es y licencias); todo lo técnico va en
  `docs/` (índice en `docs/README.md`: `DESARROLLO.md`, `CONTENIDOS.md`, `DESPLIEGUE.md`, plan SEO).
- Anuncios: se ocultan en el build los que tienen `visible: false` o cuyo último día
  (`visible_until` o `event_date`) ya pasó, con la fecha de Europe/Madrid. Además `public.js` retira en
  el navegador los que caducan entre builds (`data-last-day`), y el workflow regenera cada noche.
- Diseño «Marcador»: `static/css/public.css` y `static/js/public.js`, sin dependencias, sin CDN;
  fuentes propias en `static/fonts/` (OFL). La carta funciona sin JavaScript.
- `scripts/generate_menu_pdf.py` genera el `static/documents/carta.pdf` versionado desde `menu.json`
  (solo castellano, necesita Chromium local).
- «Acceso Staff» enlaza a `site.json` → `staff_url` (vacío = sin enlace). `build(staff_url=…)` /
  `--staff-url` lo sustituyen; `--dev` usa `LOCAL_STAFF_URL` (el panel local de CamposClubManager).
  El mismo enlace genera `dist/login/index.html`, una redirección «meta refresh» (Pages no admite
  redirecciones de servidor): `noupadeliteniscampos.com/login` lleva al panel en `staff.noupadeliteniscampos.com`.

## Comandos

```powershell
.venv\Scripts\python build.py                                # genera dist/
.venv\Scripts\python -m unittest discover -s tests -v        # tests (unittest, sin dependencias extra)
.venv\Scripts\python build.py --dev                          # genera y sirve en :8000, Acceso Staff → http://localhost/login
```

`dist/` no se versiona: lo genera y publica `.github/workflows/pages.yml` (push a `main`, cron nocturno
y ejecución manual). El despliegue a Pages solo se ejecuta si la variable del repo
`PAGES_ENABLED` es `true` (ya lo es: publicada en `https://noupadeliteniscampos.com/`; DNS en IONOS, `www` redirige al dominio).

# Plan de SEO y publicación

Dominio elegido: **`noupadeliteniscampos.com`** (sin `www` como principal; `www` redirige a él).

URLs finales:

| Idioma | URL |
|---|---|
| Castellano (principal y `x-default`) | `https://noupadeliteniscampos.com/` |
| Catalán | `https://noupadeliteniscampos.com/ca/` |
| Inglés | `https://noupadeliteniscampos.com/en/` |

Leyenda: 🧑 lo hace una persona (cuentas, pagos, DNS) · 🤖 cambio en el repositorio.

---

## Fase 0 · Preparativos

- [x] 🧑 Dominio `noupadeliteniscampos.com` comprado en **IONOS**. Pendiente: comprobar que está a nombre
      del club (no de una persona que pueda irse) y que la renovación automática está activada.
- [ ] 🧑 Opcional: registrar también `noupadeliteniscampos.es` y redirigirlo al `.com`.
- [x] 🧑 El repositorio pasa a **público** (GitHub Pages gratis; no guarda secretos).
- [ ] 🧑 Decidir la URL de «Acceso Staff» en producción. Propuesta: `https://gestion.noupadeliteniscampos.com/login`
      (depende de dónde se despliegue CamposClubManager). Mientras no exista, `staff_url` se queda vacío.
- [ ] 🧑 Hacer fotos reales: pistas de pádel, pistas de tenis, cafetería y tienda. Se necesita al menos una
      horizontal buena para la portada y para compartir (se recorta a 1200×630).

## Fase 1 · SEO técnico en el build 🤖 ✅

Todo se genera desde `site.json`, sin romper la regla de «solo URLs relativas» para enlaces internos:
las URLs absolutas solo se usan en metadatos y solo si `domain` está relleno.

- [x] Nuevo campo `site.json` → `"indexable": false`. Controla a la vez:
  - `<meta name="robots">`: `noindex, nofollow` si es `false`, se quita si es `true`.
  - `robots.txt`: `Disallow: /` si es `false`; si es `true`, `Allow: /` + `Sitemap: https://{domain}/sitemap.xml`.
  - Si `indexable` es `true` y `domain` está vacío, el build falla con `ContentError`.
- [x] `<link rel="canonical">` absoluto en cada idioma.
- [x] `hreflang` con URLs absolutas (Google no acepta las relativas) y `x-default` apuntando al castellano.
      Sin dominio se deja como ahora.
- [x] `sitemap.xml` con las 3 URLs y sus alternativas `xhtml:link` de idioma. Sin `lastmod`: el build
      nocturno lo cambiaría cada día aunque no cambie nada, y Google deja de fiarse de él.
- [x] Open Graph y Twitter Card: `og:title`, `og:description`, `og:url`, `og:image` (absoluta),
      `og:locale` (`es_ES`, `ca_ES`, `en_GB`) y `og:locale:alternate`, `twitter:card=summary_large_image`.
- [x] Imagen para compartir: `static/images/og.jpg` (1200×630), de momento una composición provisional
      con el logo. Cuando haya foto, sustituir el fichero (o cambiar `share_image`).
- [x] JSON-LD `SportsActivityLocation` generado desde `site.json` en cada idioma: nombre, logo, dirección
      (`PostalAddress`), `geo`, teléfono, email, `openingHoursSpecification` desde `schedule`, `hasMap`,
      `sameAs` (Instagram y Playtomic) y `url`. Sin `priceRange` (es opcional).
- [x] Añadir `"latitude"` y `"longitude"` a `site.json` (sacadas de Google Maps, sobre la entrada del club).
- [x] Tests: `noindex` y `Disallow` con `indexable: false`; canonical, hreflang absoluto, sitemap y JSON-LD
      válido con `indexable: true`; error si falta el dominio. Adaptar `tests/test_build.py:49-50`.
- [x] Actualizar README y AGENTS.md.

En esta fase se deja **`indexable: false`**, así que se puede subir a `main` sin que nada cambie en buscadores.

## Fase 2 · Contenido 🤖 + 🧑

- [ ] Poner la foto de portada en `static/images/` y rellenar `hero_image` y `hero_image_alt` en `site.json`
      (alt descriptivo, por ejemplo «Pistas de pádel cubiertas de Nou Padel i Tenis Campos»).
- [ ] Comprimir las imágenes (WebP/AVIF, menos de ~200 KB) y ponerles `width` y `height`.
- [x] Revisar `meta_description` y `hero_description` en los tres idiomas: que salgan «pádel», «Campos»,
      «Mallorca» y, de forma natural, la zona cercana (Colònia de Sant Jordi, Ses Salines, Santanyí, Llucmajor).
- [ ] Comprobar que nombre, dirección y teléfono son **exactamente iguales** en la web, en Google Business
      Profile, en Playtomic y en Instagram.

## Fase 3 · Publicar en GitHub Pages (con `indexable: false`) 🧑

Primero se publica cerrada a buscadores para comprobar que todo funciona con el dominio.

1. [ ] **Verificar el dominio en GitHub** (evita que otra persona lo secuestre):
       perfil → **Settings → Pages → Add a domain** → `noupadeliteniscampos.com`. GitHub da un registro TXT
       `_github-pages-challenge-marcmorlaaa` que hay que crear en el DNS del registrador y luego pulsar **Verify**.
2. [ ] En el repositorio: **Settings → Pages → Source: GitHub Actions**.
3. [ ] **Settings → Secrets and variables → Actions → Variables** → crear `PAGES_ENABLED` = `true`.
4. [x] 🤖 En `site.json`: `"domain": "noupadeliteniscampos.com"` (falta `staff_url` cuando exista).
       Ojo: publicando con GitHub Actions, GitHub **ignora** el fichero `CNAME`; el dominio se configura en el
       paso 6. El campo `domain` sirve para las URLs absolutas de la fase 1.
5. [ ] Registros DNS en IONOS (**Dominios y SSL → el dominio → DNS**). Antes, borrar los registros `A`/`AAAA`
       de `@` y el `CNAME`/`A` de `www` que IONOS crea por defecto (apuntan a su página de aparcamiento):

       | Tipo | Nombre | Valor |
       |---|---|---|
       | A | `@` | `185.199.108.153` |
       | A | `@` | `185.199.109.153` |
       | A | `@` | `185.199.110.153` |
       | A | `@` | `185.199.111.153` |
       | AAAA | `@` | `2606:50c0:8000::153` |
       | AAAA | `@` | `2606:50c0:8001::153` |
       | AAAA | `@` | `2606:50c0:8002::153` |
       | AAAA | `@` | `2606:50c0:8003::153` |
       | CNAME | `www` | `marcmorlaaa.github.io` |

       Si el DNS está en Cloudflare, dejar estos registros **sin proxy** (nube gris), al menos hasta que
       GitHub emita el certificado.
6. [ ] En el repositorio: **Settings → Pages → Custom domain** → `noupadeliteniscampos.com` → **Save**.
       Esperar a que el DNS check salga en verde (de minutos a unas horas).
7. [ ] Marcar **Enforce HTTPS** cuando GitHub lo permita (tarda hasta ~1 h en emitir el certificado).
8. [ ] Comprobar:
   - `https://noupadeliteniscampos.com/`, `/ca/` y `/en/` cargan con estilos, fuentes y logo.
   - `http://` y `https://www.` redirigen a `https://noupadeliteniscampos.com/`.
   - La carta PDF se descarga, y funcionan el selector de idioma, Playtomic, WhatsApp y el mapa.
   - En Actions, la ejecución nocturna también publica.

## Fase 4 · Abrir a buscadores 🤖

- [ ] `site.json` → `"indexable": true`. Push a `main`.
- [ ] Comprobar en producción: no hay `noindex` en el HTML, `robots.txt` apunta al sitemap y
      `https://noupadeliteniscampos.com/sitemap.xml` se abre bien.

## Fase 5 · Alta en buscadores 🧑

1. [ ] **Google Search Console** → añadir propiedad de tipo **Dominio** `noupadeliteniscampos.com`
       (se verifica con otro registro TXT en el DNS).
2. [ ] **Sitemaps** → enviar `https://noupadeliteniscampos.com/sitemap.xml`.
3. [ ] **Inspección de URLs** → pedir la indexación de `/`, `/ca/` y `/en/`.
4. [ ] **Bing Webmaster Tools** → «Importar desde Google Search Console» (también cubre DuckDuckGo y Ecosia).
5. [ ] Validar:
   - [Prueba de resultados enriquecidos](https://search.google.com/test/rich-results): el JSON-LD sin errores.
   - [PageSpeed Insights](https://pagespeed.web.dev/): móvil y escritorio en verde.
   - Vista previa de compartir: pegar el enlace en WhatsApp y comprobar la foto y el título.

## Fase 6 · SEO local (lo que más pesa para «pádel Campos») 🧑

- [ ] **Google Business Profile**: reclamar o crear la ficha del club.
  - Categoría principal «Club de pádel» y secundarias «Pista de tenis» y «Cafetería».
  - Web `https://noupadeliteniscampos.com/`, mismo teléfono y horario que la web, y botón de reserva a Playtomic.
  - Subir fotos y publicar novedades (torneos, clases) de vez en cuando.
  - Pedir reseñas a los clientes (un QR en recepción ayuda) y contestarlas todas.
- [ ] Poner el enlace a la web en la bio de Instagram, en la ficha de Playtomic y en el grupo de WhatsApp.
- [ ] Pedir enlaces a la web: ProGame Tennis Academy, colaboradores, Ajuntament de Campos (directorio de
      entidades o instalaciones deportivas), federación balear de pádel si hay torneos, prensa local.
- [ ] Apple Maps (Apple Business Connect) y Bing Places con los mismos datos.

## Fase 7 · Mantenimiento

- [ ] Revisar Search Console una vez al mes: errores de indexación y búsquedas por las que aparece la web.
- [ ] Mantener horario y tarifas al día en `site.json` **y** en Google Business Profile a la vez.
- [ ] Renovar el dominio (automático) y tener localizado quién gestiona la cuenta del registrador.
- [ ] Más adelante, si interesa posicionar búsquedas concretas («clases de pádel niños Campos»,
      «torneo pádel Mallorca»), crear páginas propias para ellas en lugar de secciones de la portada.

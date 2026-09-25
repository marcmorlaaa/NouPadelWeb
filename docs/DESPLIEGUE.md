# Despliegue paso a paso: GitHub Pages + dominio en IONOS + Google

Cómo se publicó `https://noupadeliteniscampos.com/` el 25 de septiembre de 2026, para poder repetirlo
(otro dominio, otro repositorio o si hay que rehacerlo). El plan general de SEO está en
[`PLAN_SEO_Y_PUBLICACION.md`](PLAN_SEO_Y_PUBLICACION.md).

Resumen de piezas:

| Pieza | Dónde | Qué hace |
|---|---|---|
| Código y build | GitHub, repo `marcmorlaaa/NouPadelWeb` (público) | `.github/workflows/pages.yml` genera `dist/` y lo publica |
| Hosting y HTTPS | GitHub Pages | Sirve la web y emite el certificado (gratis, se renueva solo) |
| Dominio y DNS | IONOS | Apunta `noupadeliteniscampos.com` y `www` a GitHub Pages |
| Buscadores | Google Search Console (+ Bing) | Verifica el dominio, recibe el sitemap e indexa |

Leyenda: 🧑 web de un proveedor · 💻 terminal o repositorio.

---

## 1. Preparar el repositorio 💻

1. En `content/site.json`:

   ```json
   "domain": "noupadeliteniscampos.com",
   "indexable": false,
   ```

   `domain` va sin `https://` ni barras. Con `indexable: false` la web se publica con `noindex` y
   `robots.txt` bloqueando todo: así se puede probar sin que Google la vea a medio hacer.
2. Tests y build en local, y push a `main`:

   ```bash
   .venv/bin/python -m unittest discover -s tests
   .venv/bin/python build.py
   git push origin main
   ```

## 2. Activar GitHub Pages 💻

GitHub Pages gratis solo publica desde repositorios **públicos** (en privado hace falta GitHub Pro).
El repositorio no guarda secretos, pero al hacerlo público se ve todo el historial, incluido el email
de los commits.

Con `gh` (o lo mismo en la web del repositorio):

```bash
# Repositorio público                       (Settings → General → Danger Zone → Change visibility)
gh repo edit --visibility public --accept-visibility-change-consequences
# Pages publicado desde GitHub Actions       (Settings → Pages → Source: GitHub Actions)
gh api -X POST repos/marcmorlaaa/NouPadelWeb/pages -f build_type=workflow
# Variable que deja al workflow desplegar     (Settings → Secrets and variables → Actions → Variables)
gh variable set PAGES_ENABLED --body true
# Lanzar el workflow y esperar a que termine
gh workflow run pages.yml --ref main
gh run watch "$(gh run list --workflow pages.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
```

La web queda en `https://marcmorlaaa.github.io/NouPadelWeb/`. Comprobar que cargan `/`, `/ca/`, `/en/`,
los estilos y la carta PDF **antes** de tocar el dominio.

## 3. Verificar el dominio en GitHub 🧑

Evita que otra cuenta de GitHub pueda usar el dominio.

1. GitHub → foto de perfil → **Settings → Pages → Add a domain** → `noupadeliteniscampos.com`.
2. GitHub muestra «Create a TXT record» con un nombre y un valor («use this code for the value»).
3. En IONOS: **Dominios & SSL** → `noupadeliteniscampos.com` → pestaña **DNS** → **Añadir registro** → **TXT**:
   - **Nombre de host:** solo `_github-pages-challenge-marcmorlaaa`. **Sin** `.noupadeliteniscampos.com`:
     IONOS lo añade solo y, si se escribe entero, queda duplicado y la verificación falla.
   - **Valor:** el código de GitHub, tal cual.
   - **TTL:** el de por defecto.
4. Comprobar que ya se ve (en minutos):

   ```bash
   dig +short TXT _github-pages-challenge-marcmorlaaa.noupadeliteniscampos.com @8.8.8.8
   ```

5. Volver a GitHub y pulsar **Verify**.

## 4. Apuntar el DNS de IONOS a GitHub Pages 🧑

En la misma pestaña **DNS** de IONOS:

1. **Borrar** el registro `A` (`217.160.0.95`) y el `AAAA` (`2001:8d8:…`) de `@`. Son la página de
   aparcamiento de IONOS (la que responde «404 nginx»).
2. **Crear** en `@`:

   | Tipo | Host | Valor |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |

3. **No crear el CNAME de `www`.** En IONOS, `www` hereda solo los registros de `@`; al intentar añadir el
   CNAME avisa de que se desactivarán los registros de `www`. No hace falta: con los `A`/`AAAA` heredados,
   GitHub ya redirige `www` al dominio principal.
4. **No tocar** el TXT de SPF de IONOS (`v=spf1 include:_spf-eu.ionos.com ~all`) ni los TXT de verificación.
5. **No contratar ni configurar ningún SSL en IONOS** (Dominios & SSL → Certificados). Ninguna de sus
   opciones («mi página web en IONOS» o «mi servidor») sirve para GitHub Pages: el certificado lo pone GitHub.
6. Comprobar en los servidores de IONOS y en uno público:

   ```bash
   dig +short A noupadeliteniscampos.com @ns1047.ui-dns.de
   dig +short A www.noupadeliteniscampos.com @8.8.8.8
   ```

   Ambos deben devolver las cuatro IPs `185.199.10x.153`.

## 5. Conectar el dominio y activar HTTPS 💻

Solo cuando el DNS ya apunte a GitHub: en cuanto se pone el dominio, `github.io` redirige a él, y si aún
no resuelve la web deja de verse.

```bash
# Settings → Pages → Custom domain → noupadeliteniscampos.com → Save
gh api -X PUT repos/marcmorlaaa/NouPadelWeb/pages -f cname=noupadeliteniscampos.com
# Esperar al certificado (minutos, hasta ~1 h): repetir hasta que diga "approved"
gh api repos/marcmorlaaa/NouPadelWeb/pages --jq '.https_certificate.state'
# Settings → Pages → Enforce HTTPS
gh api -X PUT repos/marcmorlaaa/NouPadelWeb/pages -F https_enforced=true
```

Nota: publicando con GitHub Actions, GitHub ignora el fichero `CNAME` de `dist/`; el dominio se configura
solo en este paso.

Comprobaciones:

- `https://noupadeliteniscampos.com/`, `/ca/` y `/en/` cargan con estilos, fuentes y logo.
- `http://…`, `https://www.…` y `https://marcmorlaaa.github.io/NouPadelWeb/` redirigen a
  `https://noupadeliteniscampos.com/`.
- Se descarga la carta PDF y funcionan el selector de idioma, Playtomic, WhatsApp y el mapa.

## 6. Abrir la web a buscadores 💻

1. En `content/site.json`: `"indexable": true`. Tests y push a `main`.
2. Cuando termine el workflow, comprobar en producción:

   ```bash
   curl -s https://noupadeliteniscampos.com/robots.txt         # Allow: / y la línea Sitemap
   curl -s https://noupadeliteniscampos.com/ | grep -c noindex  # 0
   ```

## 7. Google Search Console 🧑

1. https://search.google.com/search-console → **Añadir propiedad** → tipo **Dominio** →
   `noupadeliteniscampos.com`. (No «Prefijo de la URL»: la de dominio cubre `www`, `http` y `https`.)
2. En «Instrucciones para» Google detecta **1and1.com** (el nombre antiguo de IONOS) → **Iniciar
   verificación** → entrar en IONOS y autorizar. Google crea el TXT solo. No cerrar la pestaña hasta que
   diga «Propiedad verificada».
   Si falla: elegir «Cualquier proveedor de DNS», copiar `google-site-verification=…` y crearlo como TXT
   con host `@` en IONOS.
3. Menú izquierdo → **Indexación → Sitemaps** → en «Añadir un sitemap» escribir `sitemap.xml` → **Enviar**.
   Al principio puede salir «No se ha podido obtener»; en horas pasa a «Correcto» con 3 páginas.
4. Barra de arriba (**Inspeccionar cualquier URL**) → pegar `https://noupadeliteniscampos.com/` →
   «La URL no está en Google» (normal) → **Solicitar indexación**. Repetir con `/ca/` y `/en/`.
5. Opcional: https://www.bing.com/webmasters → **Importar desde Google Search Console** (Bing,
   DuckDuckGo y Ecosia).
6. Para saber si ya está indexada: buscar en Google `site:noupadeliteniscampos.com` (días, a veces 1–2 semanas).

---

## Problemas que salieron

| Síntoma | Causa | Solución |
|---|---|---|
| El navegador dice que el dominio no tiene SSL | El DNS aún apuntaba a la página de aparcamiento de IONOS | Cambiar el DNS (paso 4); GitHub emite el certificado solo. No comprar SSL en IONOS |
| «404 nginx» al abrir el dominio, en el PC y en el móvil por wifi | El DNS de la red local tenía guardada la IP antigua de IONOS (TTL 3600 s = hasta 1 h) | Esperar a que caduque, o probar con el móvil en datos. Comprobar con `dig noupadeliteniscampos.com` (la 2.ª columna es el tiempo que le queda) frente a `dig … @8.8.8.8` |
| IONOS avisa al crear el CNAME de `www` de que desactivará registros | `www` ya hereda los `A`/`AAAA` de `@` | No crear el CNAME |
| Search Console: «La URL no está en Google» | Google aún no la ha visitado | Solicitar indexación y esperar |

Para probar la web saltándose la caché DNS local:

```bash
curl -s --resolve noupadeliteniscampos.com:443:185.199.108.153 -o /dev/null -w '%{http_code}\n' https://noupadeliteniscampos.com/
```

## Mantenimiento

- El certificado HTTPS lo renueva GitHub solo (el primero caduca el 24/12/2026 y se renueva antes).
- El dominio se renueva en IONOS: tener activada la renovación automática y saber quién tiene la cuenta.
- Cada push a `main` y cada noche (23:05 UTC) el workflow vuelve a publicar. Para pararlo sin borrar nada:
  `gh variable set PAGES_ENABLED --body false`.

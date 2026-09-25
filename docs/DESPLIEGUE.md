# Cómo publicar la web

Estos son los pasos que seguí para poner la web en marcha con GitHub Pages y un dominio comprado en
IONOS. Si algún día hay que rehacerlo, cambiar de dominio o montarlo en otra cuenta, debería bastar con
seguirlos en orden.

Lo que necesitas antes de empezar:

- Una cuenta de GitHub con este repositorio.
- El dominio comprado (aquí, `noupadeliteniscampos.com` en IONOS) y acceso a su panel.
- Una cuenta de Google para Search Console.
- Python instalado para generar la web en tu ordenador y comprobar que todo va bien.

Si usas otro dominio, cambia `noupadeliteniscampos.com` por el tuyo en todo lo que sigue.

## Paso 1. Preparar el repositorio

Abre `content/site.json` y pon el dominio, sin `https://` ni barras:

```json
"domain": "noupadeliteniscampos.com",
"indexable": false,
```

Deja `indexable` en `false` de momento. Así la web se publica pero los buscadores no la indexan
todavía, y puedes probarla con calma.

Comprueba que todo funciona en local y sube los cambios:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python build.py
git push origin main
```

## Paso 2. Activar GitHub Pages

Con la cuenta gratuita de GitHub, Pages solo funciona si el repositorio es público. Antes de hacerlo
público, asegúrate de que no hay contraseñas ni datos privados en ningún commit: al cambiarlo se ve
todo el historial.

En la página del repositorio en GitHub:

1. Ve a **Settings → General**, baja hasta el final y en **Change visibility** elige **Public**.
2. Ve a **Settings → Pages** y en **Source** elige **GitHub Actions**.
3. Ve a **Settings → Secrets and variables → Actions**, pestaña **Variables**, y crea una variable
   llamada `PAGES_ENABLED` con el valor `true`. Sin ella el workflow pasa los tests pero no publica.
4. Ve a **Actions**, elige **Publicar web** y pulsa **Run workflow**.

Cuando termine (menos de un minuto), la web estará en `https://marcmorlaaa.github.io/NouPadelWeb/`.
Ábrela y revisa que cargan las tres versiones (`/`, `/ca/` y `/en/`), los estilos y la carta en PDF.
No sigas hasta que esto funcione.

## Paso 3. Verificar el dominio en GitHub

Esto sirve para que ninguna otra cuenta de GitHub pueda usar tu dominio.

1. En GitHub, haz clic en tu foto de perfil y ve a **Settings → Pages** (los ajustes de tu cuenta, no
   los del repositorio).
2. Pulsa **Add a domain** y escribe `noupadeliteniscampos.com`.
3. GitHub te da un registro TXT con un nombre y un valor. Déjalo abierto.
4. En IONOS entra en **Dominios & SSL**, elige el dominio y abre la pestaña **DNS**. Pulsa **Añadir
   registro** y elige **TXT**:
   - En el nombre de host pon solo `_github-pages-challenge-marcmorlaaa`. IONOS añade el dominio
     detrás por su cuenta; si lo escribes entero queda repetido y la verificación falla.
   - En el valor pega el código de GitHub tal cual.
5. Espera unos minutos, vuelve a GitHub y pulsa **Verify**.

Si no se verifica a la primera, espera un poco más. Puedes comprobar si el registro ya se ve con:

```bash
dig +short TXT _github-pages-challenge-marcmorlaaa.noupadeliteniscampos.com @8.8.8.8
```

## Paso 4. Apuntar el dominio a GitHub

Sigue en la pestaña **DNS** de IONOS.

Primero borra el registro A que apunta a `217.160.0.95` y el AAAA que empieza por `2001:8d8:`. Son de
la página de aparcamiento que IONOS pone por defecto (la que muestra «404 nginx»).

Después crea estos registros, todos con el host `@`:

```
A      185.199.108.153
A      185.199.109.153
A      185.199.110.153
A      185.199.111.153
AAAA   2606:50c0:8000::153
AAAA   2606:50c0:8001::153
AAAA   2606:50c0:8002::153
AAAA   2606:50c0:8003::153
```

Algunas cosas que conviene saber:

- La guía de GitHub dice que crees un CNAME para `www`. En IONOS no hace falta: `www` ya usa los
  mismos registros que el dominio principal, y si intentas crear el CNAME te avisa de que desactivará
  otros registros. Déjalo como está; GitHub redirige `www` al dominio principal él solo.
- No borres el registro TXT que empieza por `v=spf1`, es del correo de IONOS.
- No contrates ni configures ningún certificado SSL en IONOS. El certificado lo pone GitHub gratis en
  el paso siguiente.

Para comprobar que los cambios ya están activos:

```bash
dig +short A noupadeliteniscampos.com @8.8.8.8
```

Tiene que devolver las cuatro direcciones que empiezan por `185.199.`. Si en tu ordenador la web sigue
saliendo como antes, lee el apartado de problemas del final.

## Paso 5. Conectar el dominio y activar HTTPS

Haz esto solo cuando el paso anterior ya funcione. En cuanto pongas el dominio, la dirección de
`github.io` redirige a él, y si el DNS aún no está listo la web deja de verse.

1. En el repositorio, ve a **Settings → Pages**.
2. En **Custom domain** escribe `noupadeliteniscampos.com` y pulsa **Save**.
3. GitHub comprueba el DNS («DNS check in progress»). Si tarda, recarga la página de vez en cuando.
4. Cuando salga en verde, marca **Enforce HTTPS**. Si la casilla está gris, GitHub todavía está
   emitiendo el certificado; puede tardar hasta una hora.

Un detalle: al publicar con GitHub Actions, GitHub no hace caso del fichero `CNAME` que genera el
build. El dominio solo cuenta si lo pones en este paso.

Comprueba que:

- `https://noupadeliteniscampos.com/`, `/ca/` y `/en/` se ven bien.
- `http://noupadeliteniscampos.com` y `https://www.noupadeliteniscampos.com` te llevan a
  `https://noupadeliteniscampos.com/`.
- La carta en PDF se descarga y funcionan el selector de idioma y los enlaces a Playtomic, WhatsApp y
  el mapa.

## Paso 6. Abrir la web a los buscadores

Cambia en `content/site.json`:

```json
"indexable": true,
```

Pasa los tests, haz push y espera a que termine el workflow. Luego comprueba que `robots.txt` ya
permite la entrada y que las páginas no llevan `noindex`:

```bash
curl -s https://noupadeliteniscampos.com/robots.txt
curl -s https://noupadeliteniscampos.com/ | grep -c noindex
```

El primero debe mostrar `Allow: /` y la línea del sitemap. El segundo debe dar `0`.

## Paso 7. Dar de alta la web en Google

1. Entra en [Google Search Console](https://search.google.com/search-console) y pulsa **Añadir
   propiedad**. Elige el tipo **Dominio** (no «Prefijo de la URL») y escribe
   `noupadeliteniscampos.com`.
2. Google detecta que el dominio está en IONOS (lo llama por su nombre antiguo, 1and1.com). Pulsa
   **Iniciar verificación**, entra con tu cuenta de IONOS y autoriza. No cierres la pestaña hasta que
   ponga «Propiedad verificada».

   Si eso falla, elige «Cualquier proveedor de DNS», copia el texto `google-site-verification=…` y
   créalo en IONOS como registro TXT con host `@`.
3. En el menú de la izquierda ve a **Sitemaps**, escribe `sitemap.xml` y pulsa **Enviar**. Es normal
   que al principio diga «No se ha podido obtener»; en unas horas cambia a «Correcto».
4. En la barra de arriba pega `https://noupadeliteniscampos.com/`. Dirá que la URL no está en Google,
   que es normal. Pulsa **Solicitar indexación**. Repite con `/ca/` y `/en/`.
5. Si quieres aparecer también en Bing, DuckDuckGo y Ecosia, entra en
   [Bing Webmaster Tools](https://www.bing.com/webmasters) e importa la web desde Search Console.

Para saber si Google ya la tiene, busca `site:noupadeliteniscampos.com`. Puede tardar desde unos días
hasta un par de semanas.

## Paso 8. Enlazar el panel del staff (opcional)

El botón **Acceso Staff** del pie y la dirección `noupadeliteniscampos.com/login` llevan al panel de
reservas, que está alojado en otro servidor. Para que funcionen:

1. En IONOS crea un registro A con el host `staff` que apunte a la IP del servidor del panel.
2. En ese servidor, configura el subdominio `staff.noupadeliteniscampos.com` con su certificado HTTPS.
   Esto se explica en la documentación del panel.
3. En `content/site.json` pon `"staff_url": "https://staff.noupadeliteniscampos.com/login"` y haz push.

GitHub Pages no permite redirecciones de servidor, así que el build genera una página `login/index.html`
que redirige al panel en cuanto se abre.

## Problemas que me encontré

**El navegador dice que la web no es segura o que no tiene certificado.** El DNS todavía apuntaba a la
página de aparcamiento de IONOS. Cuando el paso 4 está bien hecho, GitHub emite el certificado solo.
No hace falta comprar nada en IONOS.

**En mi ordenador sale «404 nginx», pero en el móvil con datos la web va bien.** Tu ordenador (o el
router de casa) tiene guardada la dirección antigua y tarda hasta una hora en olvidarla. Puedes esperar
o probar desde el móvil sin wifi. Para comprobarlo, compara lo que responde tu red con lo que responde
Google:

```bash
dig +short noupadeliteniscampos.com
dig +short noupadeliteniscampos.com @8.8.8.8
```

Si el segundo da las direcciones de GitHub y el primero no, es solo cuestión de esperar.

**IONOS avisa de que va a desactivar registros al crear el CNAME de `www`.** No lo crees; no hace falta
(ver paso 4).

**Search Console dice «La URL no está en Google».** Es normal al principio. Solicita la indexación y
espera.

## Mantenimiento

- GitHub renueva el certificado HTTPS solo.
- El dominio se renueva en IONOS. Ten activada la renovación automática y apunta quién tiene acceso a
  esa cuenta.
- La web se vuelve a publicar con cada push a `main` y cada noche. Si necesitas parar las
  publicaciones sin borrar nada, cambia la variable `PAGES_ENABLED` a `false`.

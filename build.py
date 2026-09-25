"""Genera la web estática en dist/ a partir de content/, templates/ y static/.

Uso: python build.py [--out dist] [--staff-url URL]
     python build.py --dev     genera y sirve la web en http://localhost:8000, con «Acceso Staff»
                               apuntando al panel local (CamposClubManager en http://localhost/login)
Cada idioma queda en su carpeta (/, /ca/, /en/) y todas las rutas son relativas, así que la web
funciona igual en GitHub Pages (con o sin dominio propio) que abriendo dist/ desde un servidor local.
Cualquier dato mal escrito en content/ hace fallar el build: mejor no publicar que publicar algo roto.
"""
import argparse
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / 'content'
STATIC_DIR = ROOT / 'static'
# Idiomas de la web: el castellano es el de reserva para cualquier texto sin traducir.
LANGUAGES = {'es': 'Español', 'ca': 'Català', 'en': 'English'}
DEFAULT_LANGUAGE = 'es'
LINK_KINDS = ('info', 'signup')
# Versión de los assets en las URLs (?v=…): cambia en cada build y evita cachés viejas tras publicar.
ASSET_VERSION = datetime.now().strftime('%Y%m%d%H%M')
# Panel de reservas en desarrollo: docker-compose.local.yml de CamposClubManager lo sirve en el puerto 80.
LOCAL_STAFF_URL = 'http://localhost/login'
DEV_PORT = 8000
# Metadatos para buscadores y redes sociales (ver seo_context).
OG_LOCALES = {'es': 'es_ES', 'ca': 'ca_ES', 'en': 'en_GB'}
SHARE_IMAGE_SIZE = (1200, 630)
SCHEMA_DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')


class ContentError(ValueError):
    """Dato de content/ que no se puede publicar."""


def load_data(name):
    with (CONTENT_DIR / name).open(encoding='utf-8') as source:
        return json.load(source)


def localize(value, lang):
    """Sustituye cada {"es": …, "ca": …, "en": …} por el texto del idioma, o el castellano si falta."""
    if isinstance(value, dict):
        if DEFAULT_LANGUAGE in value and set(value) <= set(LANGUAGES):
            return value.get(lang) or value[DEFAULT_LANGUAGE]
        return {key: localize(item, lang) for key, item in value.items()}
    if isinstance(value, list):
        return [localize(item, lang) for item in value]
    return value


def interface_texts(lang):
    texts = load_data('i18n.json')
    return {**texts[DEFAULT_LANGUAGE], **texts.get(lang, {})}


def today():
    """Fecha de hoy en Mallorca: el build de GitHub corre en UTC."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo('Europe/Madrid')).date()
    except Exception:
        return date.today()


# Fechas de los anuncios sin depender de los «locales» instalados en la máquina.
WEEKDAYS = {
    'es': ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'),
    'ca': ('dilluns', 'dimarts', 'dimecres', 'dijous', 'divendres', 'dissabte', 'diumenge'),
    'en': ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
}
MONTHS = {
    'es': ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'),
    'ca': ('gener', 'febrer', 'març', 'abril', 'maig', 'juny', 'juliol', 'agost', 'setembre', 'octubre', 'novembre', 'desembre'),
    'en': ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'),
}
SHORT_MONTHS = {
    'es': ('ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'),
    'ca': ('gen', 'febr', 'març', 'abr', 'maig', 'juny', 'jul', 'ag', 'set', 'oct', 'nov', 'des'),
    'en': ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'),
}


def long_date(value, lang):
    weekday, month = WEEKDAYS[lang][value.weekday()], MONTHS[lang][value.month - 1]
    if lang == 'en':
        return f'{weekday} {value.day} {month}'
    if lang == 'ca':
        return f"{weekday} {value.day} {'d’' if month[0] in 'aeiou' else 'de '}{month}".capitalize()
    return f'{weekday} {value.day} de {month}'.capitalize()


def external_url(value):
    """Solo se publican enlaces web absolutos, nunca esquemas ejecutables."""
    try:
        parsed = urlsplit(value)
        return bool(parsed.scheme in ('https', 'http') and parsed.hostname
                    and not parsed.username and not parsed.password
                    and not re.search(r'[\s\\]', value))
    except ValueError:
        return False


def normalize_announcement_url(value):
    """Asegura que los enlaces de torneos en Sportelia apunten a la vista pública."""
    value = (value or '').strip()
    match = re.match(r'^(https?://torneos\.sportelia\.es/#/tournaments-details/[^/\s]+)/?$', value)
    return f'{match.group(1)}/public' if match else value


def parse_date(value, where):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ContentError(f'{where}: la fecha «{value}» debe tener el formato AAAA-MM-DD.')


def check_link(value, where):
    if value and not external_url(value):
        raise ContentError(f'{where}: el enlace «{value}» debe empezar por https:// o http:// y tener un dominio válido.')


def validate_announcements(rows):
    """Comprueba announcements.json entero: un error en un anuncio oculto también para el build."""
    for number, row in enumerate(rows, 1):
        where = f'announcements.json, anuncio {number}'
        title = row.get('title')
        if not (title.get(DEFAULT_LANGUAGE) if isinstance(title, dict) else title):
            raise ContentError(f'{where}: falta el título en castellano.')
        check_link(row.get('link', ''), where)
        if row.get('link_kind', 'info') not in LINK_KINDS:
            raise ContentError(f'{where}: «link_kind» debe ser «info» o «signup».')
        event, until = parse_date(row.get('event_date'), where), parse_date(row.get('visible_until'), where)
        if event and until and until < event:
            raise ContentError(f'{where}: «visible_until» no puede ser anterior a «event_date».')


def visible_announcements(rows, lang, on_date):
    """Anuncios visibles que no han caducado, en el orden en que se muestran y con los textos del idioma.

    El último día visible es visible_until, o event_date si no hay; sin ninguna de las dos, sigue hasta ocultarlo.
    public.js vuelve a ocultar en el navegador los que caduquen entre dos builds.
    """
    shown = []
    for row in rows:
        event, until = parse_date(row.get('event_date'), ''), parse_date(row.get('visible_until'), '')
        last_day = until or event
        if not row.get('visible', True) or (last_day and last_day < on_date):
            continue
        shown.append((event is None, event or date.min, row, event, last_day))
    shown.sort(key=lambda item: item[:2])
    announcements = []
    for _, _, row, event, last_day in shown:
        texts = localize({'title': row['title'], 'body': row.get('body', '')}, lang)
        announcements.append({
            'title': texts['title'], 'body': texts['body'],
            'link': normalize_announcement_url(row.get('link', '')), 'link_kind': row.get('link_kind', 'info'),
            'last_day': last_day.isoformat() if last_day else '',
            'event': {'iso': event.isoformat(), 'day': event.day, 'month': SHORT_MONTHS[lang][event.month - 1],
                      'long': long_date(event, lang)} if event else None,
        })
    return announcements


def validate_collaborators(rows):
    for number, row in enumerate(rows, 1):
        where = f'collaborators.json, colaborador {number}'
        if not row.get('name') or not row.get('specialty'):
            raise ContentError(f'{where}: indica «name» y «specialty».')
        for key in ('website', 'instagram'):
            check_link(row.get(key, ''), where)
        if row.get('email') and not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', row['email']):
            raise ContentError(f'{where}: el correo «{row["email"]}» no es válido.')
        if row.get('phone') and not re.fullmatch(r'\+?[0-9 ()\-]{6,40}', row['phone']):
            raise ContentError(f'{where}: el teléfono «{row["phone"]}» no es válido.')
        photo = row.get('photo', '')
        if photo and (not (STATIC_DIR / photo).is_file() or '..' in Path(photo).parts):
            raise ContentError(f'{where}: no existe la foto static/{photo}.')


def visible_collaborators(rows, lang):
    """Colaboradores marcados como visibles, en el orden del JSON; sus textos también se pueden traducir."""
    return [localize(row, lang) for row in rows if row.get('visible', True)]


def validate_site(site):
    """Datos de site.json que usan los metadatos de buscadores: dominio, indexación, coordenadas e imagen."""
    domain = site.get('domain', '').strip()
    if domain and not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}', domain):
        raise ContentError(f'site.json: «domain» debe ser solo el dominio en minúsculas, sin https:// ni barras («{domain}»).')
    if site.get('indexable') and not domain:
        raise ContentError('site.json: con «indexable»: true hace falta «domain» (las URLs de buscadores son absolutas).')
    for key, limit in (('latitude', 90), ('longitude', 180)):
        value = site.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or abs(value) > limit):
            raise ContentError(f'site.json: «{key}» debe ser un número entre -{limit} y {limit}.')
    image = site.get('share_image', '')
    if image and (not (STATIC_DIR / image).is_file() or '..' in Path(image).parts):
        raise ContentError(f'site.json: no existe la imagen para compartir static/{image}.')


def page_urls(domain):
    """URL absoluta de cada idioma con dominio propio; sin dominio no hay URLs absolutas."""
    if not domain:
        return {}
    return {code: f'https://{domain}/' + ('' if code == DEFAULT_LANGUAGE else code + '/') for code in LANGUAGES}


def opening_hours(schedule):
    """«08:00 – 12:00 · 16:30 – 23:00» → una franja de schema.org por tramo; «Cerrado» no genera ninguna."""
    specs = []
    for row in schedule:
        days = [SCHEMA_DAYS[day - 1] for day in row.get('weekdays', []) if 1 <= day <= 7]
        for opens, closes in re.findall(r'(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})', str(row.get('hours', ''))):
            if days:
                specs.append({'@type': 'OpeningHoursSpecification', 'dayOfWeek': days, 'opens': opens, 'closes': closes})
    return specs


def structured_data(site, ui, urls, lang):
    """JSON-LD del club para Google: los mismos datos que se ven en la página."""
    street, _, rest = site.get('address', '').partition(' · ')
    town = re.match(r'(\d{5})\s+([^,]+)', rest.strip())
    phones = [phone['number'] for phone in site.get('phones', []) if phone.get('number')]
    base = urls[DEFAULT_LANGUAGE]
    data = {
        '@context': 'https://schema.org', '@type': 'SportsActivityLocation', '@id': base + '#club',
        'name': site['name'], 'description': ui['meta_description'], 'url': urls[lang],
        'logo': base + 'static/images/logo-noupadel-transparent.png',
        'image': base + 'static/' + site['share_image'] if site.get('share_image') else '',
        # Los teléfonos del club son españoles: se publican con prefijo internacional.
        'telephone': (phones[0] if phones[0].startswith('+') else '+34 ' + phones[0]) if phones else '',
        'email': site.get('email', ''),
        # Región y país fijos: el club está en Mallorca.
        'address': {'@type': 'PostalAddress', 'streetAddress': street.strip(),
                    'postalCode': town.group(1) if town else '', 'addressLocality': town.group(2).strip() if town else '',
                    'addressRegion': 'Illes Balears', 'addressCountry': 'ES'} if street else '',
        'geo': {'@type': 'GeoCoordinates', 'latitude': site['latitude'], 'longitude': site['longitude']}
        if site.get('latitude') is not None and site.get('longitude') is not None else '',
        'hasMap': site.get('maps', ''),
        'openingHoursSpecification': opening_hours(site.get('schedule', [])),
        'sameAs': [site[key] for key in ('instagram', 'playtomic') if site.get(key)],
    }
    data = {key: value for key, value in data.items() if value}
    # «<» escapado: el JSON va dentro de <script> y ningún texto puede cerrarlo.
    return Markup(json.dumps(data, ensure_ascii=False, indent=2).replace('<', '\\u003c'))


def seo_context(site, ui, lang):
    """canonical, hreflang, Open Graph y JSON-LD. Sin «domain» solo queda lo que no necesita URLs absolutas."""
    urls = page_urls(site.get('domain', '').strip())
    image = urls[DEFAULT_LANGUAGE] + 'static/' + site['share_image'] if urls and site.get('share_image') else ''
    return {
        'indexable': bool(site.get('indexable')), 'urls': urls, 'canonical': urls.get(lang, ''),
        'x_default': urls.get(DEFAULT_LANGUAGE, ''), 'image': image, 'image_size': SHARE_IMAGE_SIZE,
        'locale': OG_LOCALES[lang], 'alternate_locales': [OG_LOCALES[code] for code in LANGUAGES if code != lang],
        'json_ld': structured_data(site, ui, urls, lang) if urls else '',
    }


def sitemap(domain):
    """Las tres páginas con sus versiones en otros idiomas. Sin «lastmod»: el build nocturno lo cambiaría
    cada día aunque nada cambie, y Google deja de fiarse de él."""
    urls = page_urls(domain)
    links = ''.join(f'    <xhtml:link rel="alternate" hreflang="{code}" href="{url}"/>\n' for code, url in urls.items())
    links += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{urls[DEFAULT_LANGUAGE]}"/>\n'
    entries = ''.join(f'  <url>\n    <loc>{url}</loc>\n{links}  </url>\n' for url in urls.values())
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            f'{entries}</urlset>\n')


def robots_txt(site):
    domain = site.get('domain', '').strip()
    if not site.get('indexable'):
        return 'User-agent: *\nDisallow: /\n'
    return f'User-agent: *\nAllow: /\n\nSitemap: https://{domain}/sitemap.xml\n'


def login_redirect(url):
    """Página /login/: GitHub Pages no permite redirecciones de servidor, así que redirige con
    «meta refresh» al panel de reservas (y deja un enlace por si el navegador no lo sigue)."""
    url = escape(url)
    return ('<!DOCTYPE html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="robots" content="noindex">\n'
            f'<meta http-equiv="refresh" content="0; url={url}">\n'
            '<title>Acceso Staff</title>\n</head>\n<body>\n'
            f'<p><a href="{url}">Ir al panel de reservas</a></p>\n</body>\n</html>\n')


def phone_href(value):
    return 'tel:' + re.sub(r'[^+0-9]', '', value)


def short_price(value):
    """«24,00» → «24», «4,50» se queda igual: las cifras grandes del diseño no llevan céntimos a cero."""
    return value[:-3] if value.endswith(',00') else value


def environment():
    env = Environment(loader=FileSystemLoader(ROOT / 'templates'), autoescape=select_autoescape(['html']))
    env.filters['phone_href'] = phone_href
    env.filters['short_price'] = short_price
    return env


def page_context(lang, on_date, staff_url=None):
    site = localize(load_data('site.json'), lang)
    if staff_url is not None:
        site['staff_url'] = staff_url
    for key in ('playtomic', 'whatsapp', 'instagram', 'maps', 'staff_url'):
        if not external_url(site.get(key, '')):
            site[key] = ''
    for key in ('url', 'rent_url'):
        if site.get('tennis') and not external_url(site['tennis'].get(key, '')):
            site['tennis'][key] = ''
    # «root» lleva de la página del idioma a la raíz de la web: '' en /, '../' en /ca/ y /en/.
    root = '' if lang == DEFAULT_LANGUAGE else '../'
    ui = interface_texts(lang)
    return {
        'site': site, 'menu': localize(load_data('menu.json'), lang),
        'collaborators': visible_collaborators(load_data('collaborators.json'), lang),
        'announcements': visible_announcements(load_data('announcements.json'), lang, on_date),
        'lang': lang, 'languages': LANGUAGES, 'ui': ui, 'root': root,
        'seo': seo_context(site, ui, lang),
        'lang_paths': {code: (root + ('' if code == DEFAULT_LANGUAGE else code + '/')) or './' for code in LANGUAGES},
        'asset_version': ASSET_VERSION,
    }


def build(out_dir, on_date=None, staff_url=None):
    """staff_url sustituye al de site.json (p. ej. el panel local en desarrollo)."""
    out_dir = Path(out_dir)
    on_date = on_date or today()
    validate_announcements(load_data('announcements.json'))
    validate_collaborators(load_data('collaborators.json'))
    site = load_data('site.json')
    validate_site(site)
    template = environment().get_template('index.html')
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(STATIC_DIR, out_dir / 'static', ignore=shutil.ignore_patterns('.gitkeep'))
    for lang in LANGUAGES:
        page_dir = out_dir if lang == DEFAULT_LANGUAGE else out_dir / lang
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / 'index.html').write_text(template.render(page_context(lang, on_date, staff_url)), encoding='utf-8')
    # Con «indexable»: false la web queda cerrada a buscadores (robots.txt y «noindex» en cada página).
    (out_dir / 'robots.txt').write_text(robots_txt(site), encoding='utf-8')
    # GitHub Pages: sin procesado Jekyll, y con dominio propio si site.json tiene «domain».
    (out_dir / '.nojekyll').write_text('', encoding='utf-8')
    # /login/ lleva al panel (el mismo enlace que «Acceso Staff»); sin panel configurado no existe.
    login_url = staff_url if staff_url is not None else site.get('staff_url', '')
    if external_url(login_url):
        (out_dir / 'login').mkdir()
        (out_dir / 'login' / 'index.html').write_text(login_redirect(login_url), encoding='utf-8')
    domain = site.get('domain', '').strip()
    if domain:
        (out_dir / 'CNAME').write_text(domain + '\n', encoding='utf-8')
        (out_dir / 'sitemap.xml').write_text(sitemap(domain), encoding='utf-8')
    return out_dir


def serve(out_dir, port=DEV_PORT):
    """Servidor local de desarrollo (solo en este equipo); Ctrl+C para pararlo."""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    handler = partial(SimpleHTTPRequestHandler, directory=str(out_dir))
    with ThreadingHTTPServer(('127.0.0.1', port), handler) as server:
        print(f'Web en http://localhost:{port}/ · Ctrl+C para parar', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', default=ROOT / 'dist', type=Path, help='carpeta de salida (por defecto dist/)')
    parser.add_argument('--staff-url', help='enlace de «Acceso Staff»; sustituye al de site.json')
    parser.add_argument('--dev', action='store_true',
                        help=f'desarrollo local: «Acceso Staff» a {LOCAL_STAFF_URL} y servidor en el puerto {DEV_PORT}')
    args = parser.parse_args()
    staff_url = args.staff_url or (LOCAL_STAFF_URL if args.dev else None)
    try:
        print(f'Web generada en {build(args.out, staff_url=staff_url)}', flush=True)
    except ContentError as error:
        raise SystemExit(f'Error en content/: {error}')
    if staff_url and not external_url(staff_url):
        print(f'Aviso: «{staff_url}» no es un enlace http(s) válido; el pie se queda sin «Acceso Staff».')
    if args.dev:
        serve(args.out)

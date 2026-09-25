import json
import re
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

import build
from build import LANGUAGES, ContentError, load_data, localize

TODAY = date(2026, 9, 24)


class BuildTests(unittest.TestCase):
    """Genera la web en una carpeta temporal y comprueba el HTML resultante."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / 'dist'
        self.overrides = {}

    def tearDown(self):
        self.tmp.cleanup()

    def render(self, lang='es', **overrides):
        """Build con content/ real, salvo los ficheros que se sustituyen (p. ej. site={…})."""
        self.overrides.update({f'{name}.json': value for name, value in overrides.items()})
        original = build.load_data
        with patch('build.load_data', side_effect=lambda name: self.overrides.get(name, original(name))):
            build.build(self.out, on_date=TODAY)
        page = self.out / ('' if lang == 'es' else lang) / 'index.html'
        return page.read_text(encoding='utf-8')

    def test_pages_assets_and_relative_urls(self):
        html = self.render()
        for text in ['Pádel y tenis en Campos', 'WhatsApp', 'Playtomic', 'Clases de pádel', 'Llama a Antonia',
                     'ProGame Tennis Academy', '613 09 64 75', 'noupadeliteniscampos@gmail.com', 'Camí Vell de Ciutat, 31']:
            self.assertIn(text, html)
        for path in ['ca/index.html', 'en/index.html', 'robots.txt', '.nojekyll', 'static/css/public.css',
                     'static/js/public.js', 'static/documents/carta.pdf']:
            self.assertTrue((self.out / path).is_file(), path)
        self.assertTrue((self.out / 'static/fonts/public-sans-latin.woff2').read_bytes().startswith(b'wOF2'))
        self.assertIn('href="static/css/public.css?v=', html)
        self.assertIn('href="../static/css/public.css?v=', (self.out / 'ca/index.html').read_text(encoding='utf-8'))
        self.assertIn('href="static/documents/carta.pdf" download="Carta-Nou-Padel-i-Tenis-Campos.pdf"', html)
        # Sin rutas absolutas: la web funciona también bajo usuario.github.io/NouPadelWeb/.
        self.assertNotRegex(html, r'(href|src)="/(?!/)')
        # Sin dominio no hay CNAME, sitemap ni URLs absolutas en los metadatos.
        html = self.render(site={**load_data('site.json'), 'domain': '', 'indexable': False})
        self.assertFalse((self.out / 'CNAME').exists())
        self.assertFalse((self.out / 'sitemap.xml').exists())
        self.assertNotIn('rel="canonical"', html)
        self.assertNotIn('application/ld+json', html)
        self.assertNotIn('og:image', html)
        self.assertIn('<link rel="alternate" hreflang="ca" href="ca/">', html)
        self.assertIn('Disallow: /', (self.out / 'robots.txt').read_text())
        self.assertIn('noindex', html)

    def test_languages(self):
        expected = {'es': ('Pádel y tenis en Campos', 'Reservar pista', 'Pernil dolç', './'),
                    'ca': ('Pàdel i tennis a Campos', 'Reserva pista', 'Jamón york', './'),
                    'en': ('Padel and tennis in Campos', 'Book a court', 'Jamón york', './')}
        self.render()
        for lang, (title, book, other_language_dish, _) in expected.items():
            with self.subTest(lang=lang):
                html = (self.out / ('' if lang == 'es' else lang) / 'index.html').read_text(encoding='utf-8')
                self.assertIn(f'<html lang="{lang}">', html)
                self.assertIn(title, html)
                self.assertIn(book, html)
                self.assertNotIn(other_language_dish, html)
                current = './' if lang == 'es' else '../' + lang + '/'
                self.assertIn(f'href="{current}" hreflang="{lang}" lang="{lang}" aria-label="{LANGUAGES[lang]}" aria-current="true"', html)
        ca = (self.out / 'ca/index.html').read_text(encoding='utf-8')
        self.assertIn('href="../" hreflang="es"', ca)
        self.assertIn('href="../en/" hreflang="en"', ca)
        self.assertIn('href="ca/" hreflang="ca"', (self.out / 'index.html').read_text(encoding='utf-8'))
        self.assertIn('Cooked ham', (self.out / 'en/index.html').read_text(encoding='utf-8'))

    def test_every_language_has_every_text(self):
        texts = load_data('i18n.json')
        self.assertEqual(set(texts), set(LANGUAGES))
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                self.assertEqual(set(texts[lang]), set(texts['es']))
                self.assertTrue(all(value.strip() for value in texts[lang].values()))

    def test_localize_falls_back_to_spanish(self):
        data = {'name': {'es': 'Tenis', 'ca': 'Tennis'}, 'phone': {'label': 'Recepción', 'number': '1'}, 'list': [{'es': 'Hola', 'en': ''}]}
        self.assertEqual(localize(data, 'ca'), {'name': 'Tennis', 'phone': {'label': 'Recepción', 'number': '1'}, 'list': ['Hola']})
        self.assertEqual(localize(data, 'en')['name'], 'Tenis')

    def test_menu_transcription(self):
        menu = localize(load_data('menu.json'), 'es')
        self.assertEqual(len(menu), 9)
        items = {item['name']: item for category in menu for item in category['items']}
        self.assertEqual(len(items), 42)
        self.assertEqual(items['Jamón york']['half'], '3,00')
        self.assertEqual(items['Tabla de jamón ibérico']['half'], '8,00')
        self.assertEqual(items['Chuletón (500 g)']['price'], '25,00')
        self.assertEqual(items['Volea']['price'], '20,00')
        self.assertIn('Mínimo 3 personas', items['Volea']['description'])

    def test_configured_contact_and_external_links(self):
        site = load_data('site.json')
        site.update(phones=[{'label': 'Recepción', 'number': '+34 600 000 001'}],
                    email='club@example.com', instagram='https://example.com/instagram',
                    playtomic='https://example.com/playtomic', staff_url='https://gestion.example.com/login',
                    whatsapp='https://wa.me/34600000001', maps='https://example.com/maps', domain='www.example.com')
        html = self.render(site=site)
        for url in ['tel:+34600000001', 'mailto:club@example.com', site['instagram'], site['playtomic'],
                    site['whatsapp'], site['maps'], site['staff_url']]:
            self.assertIn('href="' + url + '"', html)
        self.assertIn('Acceso Staff', html)
        self.assertEqual((self.out / 'CNAME').read_text(), 'www.example.com\n')
        site.update(maps='javascript:alert(1)', staff_url='')
        html = self.render(site=site)
        self.assertNotIn('javascript:alert(1)', html)
        # Un enlace no válido se descarta y desaparece el botón «Cómo llegar»; sin panel, no hay «Acceso Staff».
        self.assertNotIn('Cómo llegar', html)
        self.assertNotIn('Acceso Staff', html)
        self.assertNotIn('<iframe', html)
        self.assertNotIn('<form', html)

    def test_staff_url_override_for_local_development(self):
        site = {**load_data('site.json'), 'staff_url': 'https://gestion.example.com/login'}
        self.overrides['site.json'] = site
        original = build.load_data
        with patch('build.load_data', side_effect=lambda name: self.overrides.get(name, original(name))):
            build.build(self.out, on_date=TODAY, staff_url=build.LOCAL_STAFF_URL)
        for page in ['index.html', 'ca/index.html', 'en/index.html']:
            html = (self.out / page).read_text(encoding='utf-8')
            self.assertIn(f'<a class="footer-staff" href="{build.LOCAL_STAFF_URL}">', html)
            self.assertNotIn('gestion.example.com', html)
        # Sin sustituto se usa el de site.json.
        self.assertIn('href="https://gestion.example.com/login"', self.render())

    def test_schedule_and_rates(self):
        site = load_data('site.json')
        site.update(schedule=[{'days': 'Lunes a viernes', 'hours': '08:00 – 23:30'}],
                    rates=[{'name': 'Pádel', 'items': [{'name': 'Pista · 90 min', 'detail': 'Hasta 4 jugadores', 'price': '28,00'},
                                                       {'name': 'Bono', 'price': ''}]}])
        html = self.render(site=site)
        for text in ['href="#tarifas"', 'Lunes a viernes', '08:00 – 23:30', 'Pista · 90 min', 'Hasta 4 jugadores', '28 €', 'Consultar']:
            self.assertIn(text, html)
        site.update(schedule=[], rates=[])
        html = self.render(site=site)
        self.assertIn('Horario próximamente', html)
        self.assertIn('Tarifas próximamente', html)

    def test_booking_classes_and_menu(self):
        site = load_data('site.json')
        site.update(playtomic='', classes=[{'name': 'Particular · 60 min', 'price': '35,00'}])
        html = self.render(site=site)
        # Sin Playtomic, «Reservar pista» lleva a contacto en lugar de a un enlace vacío.
        self.assertIn('<a class="button button-accent" href="#contacto">Reservar pista</a>', html)
        self.assertIn('data-weekdays="1 2 3 4 5"', html)
        self.assertIn('Particular · 60 min', html)
        self.assertIn('35 €', html)
        # La carta funciona sin JavaScript: una categoría plegable por bloque, con precio mínimo.
        self.assertEqual(html.count('<details class="menu-category"'), 9)
        self.assertIn('desde 2,50 €', html)
        site.update(playtomic='https://example.com/playtomic')
        html = self.render(site=site)
        self.assertIn('href="https://example.com/playtomic" target="_blank" rel="noopener noreferrer">Reservar pista', html)
        # Las flechas solo acompañan a enlaces que abren otra pestaña.
        self.assertEqual(html.count('↗'), html.count('(abre en otra pestaña)'))

    def test_classes_contact_and_tennis(self):
        site = load_data('site.json')
        site.update(classes_contact={'name': 'Antonia', 'number': ''})
        html = self.render(site=site)
        # Sin teléfono de Antonia, el botón lleva a contacto y su fila avisa de que llegará.
        self.assertIn('<a class="button" href="#contacto">Pedir información</a>', html)
        self.assertIn('<dt>Clases de pádel · Antonia</dt>', html)
        site.update(classes_contact={'name': 'Antonia', 'number': '600 11 22 33'},
                    tennis={'name': 'ProGame Tennis Academy', 'url': 'javascript:alert(1)', 'rent_url': 'https://example.com/tenis'})
        html = self.render(site=site)
        self.assertIn('href="tel:600112233">Llamar a Antonia · 600 11 22 33</a>', html)
        self.assertIn('href="https://example.com/tenis"', html)
        self.assertNotIn('javascript:alert(1)', html)
        self.assertNotIn('¿Buscas clases de tenis?', html)

    def announcement(self, **overrides):
        values = {'title': {'es': 'Torneo de otoño', 'ca': 'Torneig de tardor'}, 'body': 'Categorías de 1.ª a 5.ª',
                  'event_date': '2026-10-04', 'link': 'https://example.com/torneo', 'link_kind': 'signup', 'visible': True}
        values.update(overrides)
        return values

    def test_announcements_board(self):
        rows = [
            self.announcement(),
            self.announcement(title='Sin fecha', event_date='', link='', link_kind='info'),
            self.announcement(title='Antes', event_date='2026-09-30', link_kind='info'),
            self.announcement(title='Oculto', visible=False),
            self.announcement(title='Caducado', event_date='2026-09-23'),
            self.announcement(title='Sigue hasta el domingo', event_date='2026-09-20', visible_until='2026-09-27'),
            self.announcement(title='Sportelia', event_date='2026-10-10',
                              link='https://torneos.sportelia.es/#/tournaments-details/-abc123'),
        ]
        html = self.render(announcements=rows)
        self.assertIn('id="anuncios"', html)
        for text in ['Torneo de otoño', 'Sin fecha', 'Sigue hasta el domingo', 'Domingo 4 de octubre', 'Inscríbete',
                     'https://torneos.sportelia.es/#/tournaments-details/-abc123/public', 'data-last-day="2026-09-27"']:
            self.assertIn(text, html)
        self.assertNotIn('Oculto', html)
        self.assertNotIn('Caducado', html)
        # Ordenados por fecha; los que no tienen fecha, al final.
        self.assertLess(html.index('Sigue hasta el domingo'), html.index('Antes'))
        self.assertLess(html.index('Antes'), html.index('Torneo de otoño'))
        self.assertLess(html.index('Torneo de otoño'), html.index('Sin fecha'))
        ca = (self.out / 'ca/index.html').read_text(encoding='utf-8')
        self.assertIn('Torneig de tardor', ca)
        self.assertIn('Diumenge 4 d’octubre', ca)
        self.assertIn('Sin fecha', ca)  # sin traducción, en castellano
        self.assertNotIn('id="anuncios"', self.render(announcements=[self.announcement(visible=False)]))

    def test_invalid_content_stops_the_build(self):
        bad_announcements = [{'title': ''}, self.announcement(link='javascript:alert(1)'),
                             self.announcement(link_kind='otro'), self.announcement(event_date='15/10/2026'),
                             self.announcement(event_date='2026-10-10', visible_until='2026-10-01'),
                             self.announcement(visible=False, link='ftp://example.com')]
        for row in bad_announcements:
            with self.subTest(announcement=row):
                with self.assertRaises(ContentError):
                    self.render(announcements=[row])
        person = load_data('collaborators.json')[0]
        for overrides in [{'website': 'javascript:alert(1)'}, {'instagram': 'https://'}, {'email': 'correo-invalido'},
                          {'phone': 'llámame'}, {'name': ''}, {'photo': 'images/collaborators/no-existe.jpg'},
                          {'photo': '../build.py'}]:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ContentError):
                    self.render(announcements=[], collaborators=[{**person, **overrides}])
        self.assertFalse((self.out / 'index.html').exists())

    def test_collaborators_escaped_ordered_and_hidden(self):
        person = load_data('collaborators.json')[0]
        rows = [{**person, 'name': 'Primero', 'photo': 'images/logo-noupadel.jpg'},
                {**person, 'name': '<script>alert(1)</script>', 'photo': ''},
                {**person, 'name': 'Invisible', 'visible': False},
                {**person, 'name': 'Traducido', 'specialty': {'es': 'Fisioterapia', 'en': 'Physiotherapy'}}]
        html = self.render(collaborators=rows)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertLess(html.index('Primero'), html.index('&lt;script&gt;'))
        self.assertIn('src="static/images/logo-noupadel.jpg" alt="Primero"', html)
        self.assertIn('<div class="collaborator-placeholder" aria-hidden="true">&lt;</div>', html)
        self.assertNotIn('Invisible', html)
        self.assertIn('Physiotherapy', (self.out / 'en/index.html').read_text(encoding='utf-8'))
        self.assertIn('src="../static/images/logo-noupadel.jpg"', (self.out / 'en/index.html').read_text(encoding='utf-8'))
        self.assertIn('Aún no hay colaboradores', self.render(collaborators=[]))

    def test_closed_to_search_engines_until_indexable(self):
        site = {**load_data('site.json'), 'domain': 'noupadeliteniscampos.com', 'indexable': False}
        html = self.render(site=site)
        self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
        self.assertEqual((self.out / 'robots.txt').read_text(), 'User-agent: *\nDisallow: /\n')
        # Con dominio ya van los metadatos absolutos, aunque los buscadores no entren todavía.
        self.assertIn('<link rel="canonical" href="https://noupadeliteniscampos.com/">', html)

    def test_indexable_site_metadata(self):
        site = {**load_data('site.json'), 'domain': 'noupadeliteniscampos.com', 'indexable': True}
        html = self.render(site=site)
        base = 'https://noupadeliteniscampos.com/'
        self.assertNotIn('noindex', html)
        self.assertEqual((self.out / 'robots.txt').read_text(), f'User-agent: *\nAllow: /\n\nSitemap: {base}sitemap.xml\n')
        for lang, path in [('es', ''), ('ca', 'ca/'), ('en', 'en/')]:
            with self.subTest(lang=lang):
                page = (self.out / path / 'index.html').read_text(encoding='utf-8')
                self.assertIn(f'<link rel="canonical" href="{base}{path}">', page)
                self.assertIn(f'<meta property="og:url" content="{base}{path}">', page)
                self.assertIn(f'<meta property="og:locale" content="{build.OG_LOCALES[lang]}">', page)
                for code, other in [('es', ''), ('ca', 'ca/'), ('en', 'en/'), ('x-default', '')]:
                    self.assertIn(f'<link rel="alternate" hreflang="{code}" href="{base}{other}">', page)
        self.assertIn(f'<meta property="og:image" content="{base}static/images/og.jpg">', html)
        self.assertTrue((self.out / 'static/images/og.jpg').is_file())
        # Sitemap: las tres páginas, cada una con sus alternativas de idioma.
        sitemap = ElementTree.parse(self.out / 'sitemap.xml').getroot()
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
        self.assertEqual([loc.text for loc in sitemap.findall('s:url/s:loc', ns)], [base, base + 'ca/', base + 'en/'])
        self.assertEqual(len(sitemap.findall('s:url/x:link', ns)), 12)
        # JSON-LD válido y con los datos de la página.
        data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(data['@type'], 'SportsActivityLocation')
        self.assertEqual(data['name'], 'Nou Padel i Tenis Campos')
        self.assertEqual(data['telephone'], '+34 613 09 64 75')
        self.assertEqual(data['address']['postalCode'], '07630')
        self.assertEqual(data['address']['addressLocality'], 'Campos')
        self.assertEqual(data['geo'], {'@type': 'GeoCoordinates', 'latitude': 39.437107, 'longitude': 3.004353})
        self.assertIn('https://www.instagram.com/noupadeliteniscampos/', data['sameAs'])
        hours = [(spec['dayOfWeek'], spec['opens'], spec['closes']) for spec in data['openingHoursSpecification']]
        self.assertIn((['Saturday'], '17:30', '23:00'), hours)
        self.assertEqual(len(hours), 4)  # dos tramos entre semana, dos el sábado; el domingo cierra
        en = (self.out / 'en/index.html').read_text(encoding='utf-8')
        self.assertIn(f'"url": "{base}en/"', en)

    def test_structured_data_cannot_close_the_script(self):
        site = {**load_data('site.json'), 'name': 'Club</script><script>alert(1)</script>'}
        html = self.render(site=site)
        self.assertNotIn('<script>alert(1)', html)
        self.assertIn('\\u003c/script>', html)

    def test_invalid_site_settings_stop_the_build(self):
        for overrides in [{'domain': '', 'indexable': True}, {'domain': 'https://noupadeliteniscampos.com/'},
                          {'domain': 'Noupadel.com'}, {'latitude': 'norte'}, {'longitude': 200},
                          {'share_image': 'images/no-existe.jpg'}]:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ContentError):
                    self.render(site={**load_data('site.json'), **overrides})
        self.assertFalse((self.out / 'index.html').exists())

    def test_content_files_are_valid(self):
        build.validate_announcements(load_data('announcements.json'))
        build.validate_collaborators(load_data('collaborators.json'))
        build.validate_site(load_data('site.json'))
        for name in ['site.json', 'menu.json', 'i18n.json', 'collaborators.json', 'announcements.json']:
            json.loads((build.CONTENT_DIR / name).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()

"""Genera la carta descargable desde los mismos datos que la web.

Ejecutar en un equipo con Python 3 y Chromium: python scripts/generate_menu_pdf.py
El PDF resultante se incluye en el repositorio; GitHub Pages solo lo sirve.
"""
import json
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def spanish(value):
    """La carta en PDF va en castellano: de cada {"es", "ca", "en"} se queda con "es"."""
    if isinstance(value, dict):
        if 'es' in value and set(value) <= {'es', 'ca', 'en'}:
            return value['es']
        return {key: spanish(item) for key, item in value.items()}
    if isinstance(value, list):
        return [spanish(item) for item in value]
    return value


def generate():
    # «chrome» cubre Windows con la carpeta de Chrome en el PATH.
    browser = (shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
               or shutil.which('chrome'))
    if not browser:
        raise SystemExit('Instala Chromium o Google Chrome para generar la carta.')
    site = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
    menu = spanish(json.loads((ROOT / 'content/menu.json').read_text(encoding='utf-8')))
    sections = []
    for category in menu:
        rows = []
        for item in category['items']:
            description = f'<small>{escape(item["description"])}</small>' if item.get('description') else ''
            half = f'<td>{escape(item["half"])} €</td>' if item.get('half') else '<td>—</td>'
            rows.append(f'<tr><th scope="row">{escape(item["name"])}{description}</th>'
                        f'<td>{escape(item["price"])} €</td>{half if category.get("half") else ""}</tr>')
        columns = '<thead><tr><td></td><th>Entero / ración</th><th>½</th></tr></thead>' if category.get('half') else ''
        note = f'<p class="note">{escape(category["note"])}</p>' if category.get('note') else ''
        sections.append(f'<section><h2>{escape(category["name"])}</h2><table>{columns}'
                        f'<tbody>{"".join(rows)}</tbody></table>{note}</section>')

    logo = (ROOT / 'static/images/logo-noupadel-transparent.png').as_uri()
    document = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Carta · {escape(site['name'])}</title>
<style>
@page {{ size: A4; margin: 13mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 9pt Arial, sans-serif; color: #173e32; background: #fff; }}
header {{ display: flex; align-items: center; gap: 15px; border-bottom: 2px solid #173e32; padding-bottom: 14px; margin-bottom: 20px; }}
header img {{ width: 68px; height: 68px; }}
header p {{ font-size: 9pt; margin: 0 0 6px; }}
h1 {{ font: 32pt Georgia, serif; margin: 0; }}
header > span {{ margin-left: auto; font-size: 8pt; }}
main {{ columns: 2; column-gap: 28px; }}
section {{ break-inside: avoid; margin: 0 0 18px; }}
h2 {{ margin: 0 0 6px; padding-bottom: 6px; border-bottom: 1px solid #bdc9b1; font: 16pt Georgia, serif; }}
table {{ width: 100%; border-collapse: collapse; font-size: 8pt; }}
td, th {{ padding: 4px 0; text-align: right; vertical-align: top; font-weight: normal; }}
tbody th {{ text-align: left; padding-right: 7px; }}
tbody td {{ white-space: nowrap; padding-left: 9px; }}
tbody tr {{ border-bottom: 1px solid #edf0e7; }}
thead th {{ font-size: 6pt; color: #667068; }}
small {{ display: block; color: #667068; font-size: 7pt; margin-top: 2px; }}
.note {{ font-size: 7pt; margin: 8px 0 0; }}
footer {{ border-top: 1px solid #bdc9b1; padding-top: 10px; margin-top: 10px; font-size: 7pt; color: #667068; }}
</style></head><body>
<header><img src="{logo}" alt=""><div><p>{escape(site['name'])}</p><h1>La carta</h1></div><span>Campos · Mallorca</span></header>
<main>{''.join(sections)}</main>
<footer>Para información sobre alérgenos, consulta con nuestro personal. Precios en euros.</footer>
</body></html>'''
    destination = ROOT / 'static/documents/carta.pdf'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='noupadel-carta-') as temporary:
        source = Path(temporary) / 'carta.html'
        source.write_text(document, encoding='utf-8')
        subprocess.run([browser, '--headless', '--no-sandbox', '--disable-gpu',
                        f'--user-data-dir={temporary}/browser', '--no-pdf-header-footer',
                        f'--print-to-pdf={destination}', source.as_uri()], check=True, timeout=60)
    print(f'Carta generada: {destination}')


if __name__ == '__main__':
    generate()

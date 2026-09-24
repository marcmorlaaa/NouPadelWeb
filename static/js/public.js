// Marca el horario de hoy (1 = lunes … 7 = domingo, como en site.json). Sin JavaScript no se marca nada
// y el marcador muestra la primera franja del horario tal cual.
// Los textos («Hoy», «Abierto hoy»…) llegan en atributos data-* desde la plantilla, ya traducidos.
const todayIndex = new Date().getDay() || 7;
const hoursList = document.querySelector('.hours-list');
const todaySlot = hoursList && hoursList.querySelector(`[data-weekdays~="${todayIndex}"]`);
if (todaySlot) {
    todaySlot.classList.add('is-today');
    todaySlot.querySelector('dt').dataset.today = hoursList.dataset.todayLabel;
    const scoreHours = document.querySelector('.score-hours');
    const scoreToday = document.querySelector('.scoreboard-today');
    if (scoreHours) {
        const parts = Array.from(todaySlot.querySelectorAll('dd span')).map((s) => s.textContent.trim()).filter(Boolean);
        const hoursText = (parts.length > 0 ? parts.join(' · ') : todaySlot.querySelector('dd').textContent.trim()).replace(/\s*–\s*/g, '–');
        const isClosed = /^(cerrado|tancat|closed)$/i.test(hoursText);
        scoreHours.querySelector('dt').textContent = isClosed && scoreHours.dataset.todayLabel
            ? scoreHours.dataset.todayLabel
            : scoreHours.dataset.openLabel;
        const dd = scoreHours.querySelector('dd');
        if (parts.length > 1) {
            dd.replaceChildren(...parts.map((p) => {
                const span = document.createElement('span');
                span.textContent = p.replace(/\s*–\s*/g, '–');
                return span;
            }));
        } else {
            dd.textContent = hoursText;
        }
    }
    if (scoreToday) {
        const dayName = new Date().toLocaleDateString(document.documentElement.lang, { weekday: 'long' });
        scoreToday.textContent = `${scoreToday.dataset.label}, ${dayName}`;
        scoreToday.hidden = false;
    }
}

// Al cambiar de idioma se mantiene la sección en la que estaba el visitante.
document.querySelectorAll('.lang-switch a').forEach((link) => {
    link.addEventListener('click', () => { link.hash = window.location.hash; });
});

// Sin JavaScript la navegación queda siempre visible. Hasta 1160px se pliega tras el botón Menú.
// La carta no necesita JavaScript: cada categoría es un <details>.
const header = document.querySelector('.site-header');
const navToggle = document.querySelector('.nav-toggle');
if (header && navToggle) {
    const setNavOpen = (open) => {
        header.classList.toggle('nav-open', open);
        navToggle.setAttribute('aria-expanded', String(open));
    };
    document.documentElement.classList.add('js-nav');
    navToggle.hidden = false;
    navToggle.addEventListener('click', () => setNavOpen(!header.classList.contains('nav-open')));
    header.querySelector('.site-nav').addEventListener('click', (event) => {
        if (event.target.closest('a')) setNavOpen(false);
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && header.classList.contains('nav-open')) {
            setNavOpen(false);
            navToggle.focus();
        }
    });
    window.matchMedia('(min-width: 1161px)').addEventListener('change', (event) => {
        if (event.matches) setNavOpen(false);
    });
}

// La web se genera una vez al día: si un anuncio caduca entre dos builds, se oculta ya en el navegador.
// data-last-day es el último día visible (AAAA-MM-DD); sin JavaScript se ve lo que había en el último build.
const localToday = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
document.querySelectorAll('.news-item[data-last-day]').forEach((item) => {
    if (item.dataset.lastDay < localToday) item.remove();
});
const newsSection = document.querySelector('#anuncios');
if (newsSection && !newsSection.querySelector('.news-item')) newsSection.remove();

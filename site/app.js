import { viewModel, jerusalemDate, TIMEZONE } from './view.js';

export const STRINGS = {
  he: {
    dir: 'rtl', locale: 'he-IL', toggle: 'English', brand: 'יש משחק? · בלומפילד',
    yesGame: 'יש משחק', yesEvent: 'יש אירוע', no: 'אין משחק',
    next: 'האירוע הבא', noNext: 'אין אירועים מאושרים בקרוב',
    today: 'היום', tomorrow: 'מחר',
    stale: 'שימו לב: הנתונים לא עודכנו יותר מיומיים — ייתכן שהם לא מעודכנים.',
    updated: 'עודכן', sources: 'מקורות', subscribe: 'הוספה ליומן (iCal)',
    loadError: 'לא ניתן לטעון את הנתונים.',
    tentative: 'משוער', prevMonth: 'החודש הקודם', nextMonth: 'החודש הבא',
    football: '⚽', concert: '🎵', other: '•',
  },
  en: {
    dir: 'ltr', locale: 'en-GB', toggle: 'עברית', brand: 'Game on? · Bloomfield',
    yesGame: "There's a game", yesEvent: "There's an event", no: 'No game',
    next: 'Next event', noNext: 'No confirmed events coming up',
    today: 'Today', tomorrow: 'Tomorrow',
    stale: 'Heads up: data has not been refreshed for over two days and may be out of date.',
    updated: 'Updated', sources: 'Sources', subscribe: 'Add to calendar (iCal)',
    loadError: 'Could not load the data.',
    tentative: 'Tentative', prevMonth: 'Previous month', nextMonth: 'Next month',
    football: '⚽', concert: '🎵', other: '•',
  },
};

const LANG_KEY = 'yesh-mischak.lang';
const $ = (id) => document.getElementById(id);

function loadLang() {
  try { return localStorage.getItem(LANG_KEY) === 'en' ? 'en' : 'he'; } catch { return 'he'; }
}
function saveLang(lang) {
  try { localStorage.setItem(LANG_KEY, lang); } catch { /* private mode: not remembered */ }
}

export const state = { lang: loadLang(), data: null, month: jerusalemDate(new Date()).slice(0, 7) };
export const t = (key) => STRINGS[state.lang][key];

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => (k === 'class' ? (node.className = v) : node.setAttribute(k, v)));
  node.append(...children.filter((c) => c !== null && c !== undefined));
  return node;
}

export const eventLine = (e) => [e.time ? `${e.time} · ` : '', el('bdi', {}, e.title)];

function relativeText({ type, weekday, date }) {
  const locale = t('locale');
  if (type === 'today') return t('today');
  if (type === 'tomorrow') return t('tomorrow');
  if (type === 'weekday') {
    // 2026-10-04 is a Sunday; offset gives the requested weekday.
    return new Date(Date.UTC(2026, 9, 4 + weekday, 12)).toLocaleDateString(locale, { weekday: 'long', timeZone: 'UTC' });
  }
  return new Date(`${date}T12:00:00Z`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC' });
}

function renderChrome() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = t('dir');
  document.title = t('brand');
  $('lang').textContent = t('toggle');
  document.querySelectorAll('[data-i18n]').forEach((n) => (n.textContent = t(n.dataset.i18n)));
}

function renderAnswer(vm) {
  const today = $('today');
  today.className = `today ${vm.today.busy ? 'yes' : 'no'}`;
  const answer = vm.today.busy ? (vm.today.isGame ? t('yesGame') : t('yesEvent')) : t('no');
  today.replaceChildren(
    el('p', { class: 'answer' }, answer),
    ...(vm.today.busy ? [el('ul', {}, ...vm.today.events.map((e) => el('li', {}, ...eventLine(e))))] : []),
  );

  const next = $('next');
  next.replaceChildren(
    el('div', { class: 'label' }, t('next')),
    vm.next
      ? el('div', { class: 'what' }, `${t(vm.next.event.kind)} ${relativeText(vm.next.relative)} · `, ...eventLine(vm.next.event))
      : el('div', { class: 'what' }, t('noNext')),
  );

  $('stale').hidden = !vm.stale;
  $('stale').textContent = t('stale');
}

function renderFooter(data) {
  const when = new Date(data.generated_at).toLocaleString(t('locale'), {
    timeZone: TIMEZONE, dateStyle: 'medium', timeStyle: 'short',
  });
  $('updated').textContent = `${t('updated')}: ${when}`;
  $('sources').replaceChildren(
    `${t('sources')}: `,
    ...data.sources.flatMap((s, i) => [i ? ' · ' : '', el('a', { href: s.url, rel: 'noopener' }, el('bdi', {}, s.name))]),
  );
}

function shiftMonth(month, delta) {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(Date.UTC(y, m - 1 + delta, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
}

function monthDays(month) {
  const [y, m] = month.split('-').map(Number);
  const first = new Date(Date.UTC(y, m - 1, 1));
  const count = new Date(Date.UTC(y, m, 0)).getUTCDate();
  const blanks = first.getUTCDay(); // weeks start on Sunday
  const days = Array.from({ length: count }, (_, i) => `${month}-${String(i + 1).padStart(2, '0')}`);
  return { blanks, days };
}

export function renderCalendar() {
  const locale = t('locale');
  const [y, m] = state.month.split('-').map(Number);
  const title = new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString(locale, { month: 'long', year: 'numeric', timeZone: 'UTC' });
  const today = jerusalemDate(new Date());
  const byDay = Map.groupBy(state.data.events, (e) => e.date);

  const nav = el('div', { class: 'cal-nav' },
    el('button', { type: 'button', 'aria-label': t('prevMonth'), 'data-shift': '-1' }, state.lang === 'he' ? '→' : '←'),
    el('h2', {}, title),
    el('button', { type: 'button', 'aria-label': t('nextMonth'), 'data-shift': '1' }, state.lang === 'he' ? '←' : '→'),
  );

  const weekdayNames = Array.from({ length: 7 }, (_, i) =>
    new Date(Date.UTC(2026, 9, 4 + i, 12)).toLocaleDateString(locale, { weekday: 'short', timeZone: 'UTC' }));
  const { blanks, days } = monthDays(state.month);

  const grid = el('ol', { class: 'cal-grid' },
    ...weekdayNames.map((n) => el('li', { class: 'cal-head', 'aria-hidden': 'true' }, n)),
    ...Array.from({ length: blanks }, () => el('li', { class: 'cal-blank', 'aria-hidden': 'true' })),
    ...days.map((date) => {
      const events = byDay.get(date) ?? [];
      const classes = ['cal-day'];
      if (date === today) classes.push('is-today');
      if (date < today) classes.push('is-past');
      if (events.some((e) => e.status === 'confirmed')) classes.push('has-confirmed');
      else if (events.length) classes.push('has-tentative');
      return el('li', { class: classes.join(' ') },
        el('span', { class: 'cal-num' }, String(Number(date.slice(8)))),
        ...events.map((e) => el('div', { class: `cal-event ${e.status}` },
          `${t(e.kind)} `, ...eventLine(e), e.status === 'tentative' ? el('span', { class: 'cal-tag' }, t('tentative')) : null)),
      );
    }),
  );

  const section = document.getElementById('calendar');
  section.replaceChildren(nav, grid);
  section.querySelectorAll('[data-shift]').forEach((b) =>
    b.addEventListener('click', () => {
      state.month = shiftMonth(state.month, Number(b.dataset.shift));
      renderCalendar();
    }));
}

export function render() {
  renderChrome();
  if (!state.data) return;
  renderAnswer(viewModel(state.data, new Date()));
  renderFooter(state.data);
  renderCalendar();
}

$('lang').addEventListener('click', () => {
  state.lang = state.lang === 'he' ? 'en' : 'he';
  saveLang(state.lang);
  render();
});

render();
try {
  const response = await fetch('events.json', { cache: 'no-cache' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  state.data = await response.json();
  render();
} catch (error) {
  $('today').replaceChildren(el('p', { class: 'warning' }, t('loadError')));
  console.error(error);
}

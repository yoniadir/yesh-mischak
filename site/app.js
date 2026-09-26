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

export const eventLine = (e) => `${e.time ? e.time + ' · ' : ''}${e.title}`;

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
    vm.today.busy ? el('ul', {}, ...vm.today.events.map((e) => el('li', {}, eventLine(e)))) : null,
  );

  const next = $('next');
  next.replaceChildren(
    el('div', { class: 'label' }, t('next')),
    vm.next
      ? el('div', { class: 'what' }, `${t(vm.next.event.kind)} ${relativeText(vm.next.relative)} · ${eventLine(vm.next.event)}`)
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
    ...data.sources.flatMap((s, i) => [i ? ' · ' : '', el('a', { href: s.url, rel: 'noopener' }, s.name)]),
  );
}

// Task 9 replaces this with the month calendar.
export function renderCalendar() {}

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

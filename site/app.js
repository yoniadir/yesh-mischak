import { viewModel, jerusalemDate, TIMEZONE, dayIndicators, defaultSelection } from './view.js';

export const STRINGS = {
  he: {
    dir: 'rtl', locale: 'he-IL', brand: 'יש משחק? · בלומפילד',
    yesGame: 'יש משחק', yesEvent: 'יש אירוע', no: 'אין משחק',
    next: 'האירוע הבא', noNext: 'אין אירועים מאושרים בקרוב',
    today: 'היום', tomorrow: 'מחר',
    stale: 'שימו לב: הנתונים לא עודכנו יותר מיומיים — ייתכן שהם לא מעודכנים.',
    updated: 'עודכן', sources: 'מקורות', subscribe: 'הוספה ליומן (iCal)',
    loadError: 'לא ניתן לטעון את הנתונים.',
    tentative: 'משוער', prevMonth: 'החודש הקודם', nextMonth: 'החודש הבא',
    football: '⚽', concert: '🎵', other: '•',
    noEventsDay: 'אין אירועים ביום זה', noEventsMonth: 'אין אירועים החודש',
    confirmedCount: (n) => (n === 1 ? 'אירוע מאושר אחד' : `${n} אירועים מאושרים`),
    likelyCount: (n) => (n === 1 ? 'אירוע משוער אחד' : `${n} אירועים משוערים`),
  },
  en: {
    dir: 'ltr', locale: 'en-GB', brand: 'Game on? · Bloomfield',
    yesGame: "There's a game", yesEvent: "There's an event", no: 'No game',
    next: 'Next event', noNext: 'No confirmed events coming up',
    today: 'Today', tomorrow: 'Tomorrow',
    stale: 'Heads up: data has not been refreshed for over two days and may be out of date.',
    updated: 'Updated', sources: 'Sources', subscribe: 'Add to calendar (iCal)',
    loadError: 'Could not load the data.',
    tentative: 'Likely', prevMonth: 'Previous month', nextMonth: 'Next month',
    football: '⚽', concert: '🎵', other: '•',
    noEventsDay: 'No events', noEventsMonth: 'No events this month',
    confirmedCount: (n) => (n === 1 ? '1 confirmed event' : `${n} confirmed events`),
    likelyCount: (n) => (n === 1 ? '1 likely event' : `${n} likely events`),
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

export const state = { lang: loadLang(), data: null, month: jerusalemDate(new Date()).slice(0, 7), selected: null };
export const t = (key) => STRINGS[state.lang][key];

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => (k === 'class' ? (node.className = v) : node.setAttribute(k, v)));
  node.append(...children.filter((c) => c !== null && c !== undefined));
  return node;
}

const fullDate = (date) => new Date(`${date}T12:00:00Z`).toLocaleDateString(t('locale'), {
  weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC',
});

export function eventRow(e, { showStatus = false, lead = null } = {}) {
  const sub = [lead, e.time].filter(Boolean).join(' · ');
  return el('li', { class: 'row' },
    el('span', { class: 'tile', 'aria-hidden': 'true' }, t(e.kind)),
    el('span', { class: 'row-main' },
      el('span', { class: 'row-title' }, el('bdi', {}, e.title)),
      sub ? el('span', { class: 'row-sub' }, sub) : null),
    showStatus && e.status === 'tentative' ? el('span', { class: 'pill' }, t('tentative')) : null);
}

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
  document.querySelectorAll('#lang [data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang)));
  document.querySelectorAll('[data-i18n]').forEach((n) => (n.textContent = t(n.dataset.i18n)));
}

function renderAnswer(vm) {
  const stadium = $('stadium');
  stadium.hidden = false;
  stadium.dataset.lights = vm.today.busy ? 'on' : 'off';
  const today = $('today');
  today.className = `today ${vm.today.busy ? 'yes' : 'no'}`;
  const answer = vm.today.busy ? (vm.today.isGame ? t('yesGame') : t('yesEvent')) : t('no');
  today.replaceChildren(
    el('p', { class: 'answer' }, answer),
    ...(vm.today.busy ? [el('ul', { class: 'group' }, ...vm.today.events.map((e) => eventRow(e)))] : []),
  );

  const next = $('next');
  next.replaceChildren(
    el('h2', { class: 'section-title' }, t('next')),
    el('ul', { class: 'group' },
      vm.next
        ? eventRow(vm.next.event, { lead: relativeText(vm.next.relative) })
        : el('li', { class: 'row row-plain' }, t('noNext'))),
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

function groupByDate(events) {
  const byDay = new Map();
  for (const e of events) {
    const list = byDay.get(e.date);
    if (list) list.push(e);
    else byDay.set(e.date, [e]);
  }
  return byDay;
}

export function renderCalendar(focusSelector) {
  const locale = t('locale');
  const [y, m] = state.month.split('-').map(Number);
  const title = new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString(locale, { month: 'long', year: 'numeric', timeZone: 'UTC' });
  const today = jerusalemDate(new Date());
  const byDay = groupByDate(state.data.events);
  const chev = (dir) => el('span', { class: `chev ${dir}`, 'aria-hidden': 'true' });

  const nav = el('div', { class: 'cal-nav' },
    el('h2', {}, title),
    state.month !== today.slice(0, 7) || state.selected !== today
      ? el('button', { type: 'button', class: 'text-btn', 'data-today': '' }, t('today')) : null,
    el('button', { type: 'button', class: 'icon-btn', 'aria-label': t('prevMonth'), 'data-shift': '-1' }, chev('pt-start')),
    el('button', { type: 'button', class: 'icon-btn', 'aria-label': t('nextMonth'), 'data-shift': '1' }, chev('pt-end')),
  );

  const weekdayNames = Array.from({ length: 7 }, (_, i) =>
    new Date(Date.UTC(2026, 9, 4 + i, 12)).toLocaleDateString(locale, { weekday: 'short', timeZone: 'UTC' }));
  const { blanks, days } = monthDays(state.month);

  const grid = el('ol', { class: 'cal-grid', 'aria-label': title },
    ...weekdayNames.map((n) => el('li', { class: 'cal-head', 'aria-hidden': 'true' }, n)),
    ...Array.from({ length: blanks }, () => el('li', { class: 'cal-blank', 'aria-hidden': 'true' })),
    ...days.map((date) => {
      const events = byDay.get(date) ?? [];
      const { confirmed, tentative } = dayIndicators(events);
      const classes = ['cal-day'];
      if (date === today) classes.push('is-today');
      if (date < today) classes.push('is-past');
      const confirmedCount = events.filter((e) => e.status === 'confirmed').length;
      const likelyCount = events.length - confirmedCount;
      const label = [
        fullDate(date),
        date === today ? t('today') : null,
        confirmedCount ? t('confirmedCount')(confirmedCount) : null,
        likelyCount ? t('likelyCount')(likelyCount) : null,
      ].filter(Boolean).join(', ');
      return el('li', {},
        el('button', {
          type: 'button', class: classes.join(' '), 'data-date': date, 'aria-label': label,
          'aria-pressed': String(date === state.selected), ...(date === today ? { 'aria-current': 'date' } : {}),
        },
        el('span', { class: 'cal-num', 'aria-hidden': 'true' }, String(Number(date.slice(8)))),
        el('span', { class: 'cal-dots', 'aria-hidden': 'true' },
          confirmed ? el('i', { class: 'dot confirmed' }) : null,
          tentative ? el('i', { class: 'dot tentative' }) : null)));
    }),
  );

  const selectedEvents = state.selected ? byDay.get(state.selected) ?? [] : [];
  const detail = el('div', { class: 'cal-detail', 'aria-live': 'polite' },
    state.selected ? el('h3', {}, fullDate(state.selected)) : null,
    selectedEvents.length
      ? el('ul', { class: 'list' }, ...selectedEvents.map((e) => eventRow(e, { showStatus: true })))
      : el('p', { class: 'cal-empty' }, state.selected ? t('noEventsDay') : t('noEventsMonth')));

  $('calendar').replaceChildren(el('div', { class: 'group cal-card' }, nav, grid, detail));
  if (focusSelector) $('calendar').querySelector(focusSelector)?.focus();
}

$('calendar').addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button || !state.data) return;
  const today = jerusalemDate(new Date());
  if (button.dataset.date) {
    state.selected = button.dataset.date;
    renderCalendar(`[data-date="${state.selected}"]`);
  } else if (button.dataset.shift) {
    state.month = shiftMonth(state.month, Number(button.dataset.shift));
    state.selected = defaultSelection(state.data.events, state.month, today);
    renderCalendar(`[data-shift="${button.dataset.shift}"]`);
  } else if (button.hasAttribute('data-today')) {
    state.month = today.slice(0, 7);
    state.selected = today;
    renderCalendar(`[data-date="${today}"]`);
  }
});

export function render() {
  renderChrome();
  if (!state.data) return;
  renderAnswer(viewModel(state.data, new Date()));
  renderFooter(state.data);
  try {
    renderCalendar();
  } catch (error) {
    console.error(error);
  }
}

document.querySelectorAll('#lang [data-lang]').forEach((b) => b.addEventListener('click', () => {
  if (state.lang === b.dataset.lang) return;
  state.lang = b.dataset.lang;
  saveLang(state.lang);
  render();
}));

async function load() {
  try {
    const response = await fetch('events.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    if (state.selected === null) state.selected = defaultSelection(state.data.events, state.month, jerusalemDate(new Date()));
    render();
  } catch (error) {
    console.error(error);
    // Keep showing existing data (the staleness warning covers it); only
    // report a load error when we have nothing at all to show.
    if (!state.data) {
      $('today').replaceChildren(el('p', { class: 'banner' }, t('loadError')));
    }
  }
}

render();
load();

// A backgrounded tab can be resumed by the OS on a later day without
// reloading, which would otherwise keep showing a stale "today" answer.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') load();
});
window.addEventListener('pageshow', (event) => {
  if (event.persisted) load();
});

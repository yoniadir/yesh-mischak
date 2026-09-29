export const TIMEZONE = 'Asia/Jerusalem';
const STALE_AFTER_MS = 2 * 24 * 60 * 60 * 1000;

const dateFormat = new Intl.DateTimeFormat('en-CA', {
  timeZone: TIMEZONE, year: 'numeric', month: '2-digit', day: '2-digit',
});
const timeFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: TIMEZONE, hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

export const jerusalemDate = (now) => dateFormat.format(now);
export const jerusalemTime = (now) => timeFormat.format(now);

const dayNumber = (isoDate) => Date.parse(`${isoDate}T00:00:00Z`) / 86_400_000;

function relativeDay(today, date) {
  const days = dayNumber(date) - dayNumber(today);
  if (days === 0) return { type: 'today' };
  if (days === 1) return { type: 'tomorrow' };
  if (days < 7) return { type: 'weekday', weekday: new Date(`${date}T12:00:00Z`).getUTCDay() };
  return { type: 'date', date };
}

export function viewModel(data, now) {
  const today = jerusalemDate(now);
  const clock = jerusalemTime(now);
  const confirmed = data.events.filter((e) => e.status === 'confirmed');
  const todays = confirmed.filter((e) => e.date === today);
  const next = confirmed.find(
    (e) => e.date > today || (e.date === today && e.time !== null && e.time > clock),
  ) ?? null;
  return {
    today: { busy: todays.length > 0, isGame: todays.some((e) => e.kind === 'football'), events: todays },
    next: next && { event: next, relative: relativeDay(today, next.date) },
    stale: now.getTime() - Date.parse(data.generated_at) > STALE_AFTER_MS,
    generatedAt: data.generated_at,
  };
}

export function dayIndicators(events) {
  const confirmed = events.some((e) => e.status === 'confirmed');
  return { confirmed, tentative: !confirmed && events.some((e) => e.status === 'tentative') };
}

export function defaultSelection(events, month, today) {
  if (today.startsWith(month)) return today;
  const dates = events.filter((e) => e.date.startsWith(month)).map((e) => e.date).sort();
  return dates[0] ?? null;
}

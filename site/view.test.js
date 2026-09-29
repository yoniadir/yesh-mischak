import { test } from 'node:test';
import assert from 'node:assert/strict';
import { viewModel, dayIndicators, defaultSelection } from './view.js';

const ev = (date, time, extra = {}) => ({
  id: `t:${date}:${time}`, date, time, title: `event ${date} ${time}`,
  kind: 'football', status: 'confirmed', source: 'sportpalace', url: null, ...extra,
});
const doc = (events, generated_at = '2026-10-09T06:00:00+03:00') =>
  ({ version: 1, generated_at, timezone: 'Asia/Jerusalem', sources: [], events });
const at = (iso) => new Date(iso);

test('confirmed event today answers yes', () => {
  const vm = viewModel(doc([ev('2026-10-10', '19:30')]), at('2026-10-10T10:00:00+03:00'));
  assert.equal(vm.today.busy, true);
  assert.equal(vm.today.isGame, true);
});

test('tentative event today does not answer yes', () => {
  const vm = viewModel(doc([ev('2026-10-10', '19:30', { status: 'tentative' })]), at('2026-10-10T10:00:00+03:00'));
  assert.equal(vm.today.busy, false);
});

test('concert today is an event, not a game', () => {
  const vm = viewModel(doc([ev('2026-10-10', '21:00', { kind: 'concert' })]), at('2026-10-10T10:00:00+03:00'));
  assert.equal(vm.today.busy, true);
  assert.equal(vm.today.isGame, false);
});

test('earlier event still answers yes late in the evening', () => {
  const vm = viewModel(doc([ev('2026-10-10', '15:45')]), at('2026-10-10T23:30:00+03:00'));
  assert.equal(vm.today.busy, true);
});

test('next event tomorrow is described as tomorrow', () => {
  const vm = viewModel(doc([ev('2026-10-10', '15:45')]), at('2026-10-09T23:00:00+03:00'));
  assert.equal(vm.today.busy, false);
  assert.equal(vm.next.event.date, '2026-10-10');
  assert.deepEqual(vm.next.relative, { type: 'tomorrow' });
});

test('next event 2-6 days out is described by weekday', () => {
  // Tue 2026-10-06 -> Sat 2026-10-10
  const vm = viewModel(doc([ev('2026-10-10', '19:30')]), at('2026-10-06T12:00:00+03:00'));
  assert.deepEqual(vm.next.relative, { type: 'weekday', weekday: 6 });
});

test('next event a week or more out is described by date', () => {
  const vm = viewModel(doc([ev('2026-10-17', '18:45')]), at('2026-10-10T12:00:00+03:00'));
  assert.deepEqual(vm.next.relative, { type: 'date', date: '2026-10-17' });
});

test('next event is shown even when there is an event today', () => {
  const data = doc([ev('2026-10-10', '19:30'), ev('2026-10-17', '18:45')]);
  const before = viewModel(data, at('2026-10-10T10:00:00+03:00'));
  assert.equal(before.next.event.date, '2026-10-10');
  assert.deepEqual(before.next.relative, { type: 'today' });
  const after = viewModel(data, at('2026-10-10T21:00:00+03:00'));
  assert.equal(after.today.busy, true);
  assert.equal(after.next.event.date, '2026-10-17');
});

test('tentative events are never the next event', () => {
  const data = doc([ev('2026-10-11', '19:00', { status: 'tentative' }), ev('2026-10-17', '18:45')]);
  const vm = viewModel(data, at('2026-10-10T12:00:00+03:00'));
  assert.equal(vm.next.event.date, '2026-10-17');
});

test('data older than two days is stale, recent data is not', () => {
  const now = at('2026-09-26T07:00:00+03:00');
  assert.equal(viewModel(doc([], '2026-09-24T06:00:00+03:00'), now).stale, true);
  assert.equal(viewModel(doc([], '2026-09-25T06:00:00+03:00'), now).stale, false);
});

test('today is the Jerusalem day, not the device day', () => {
  // 21:30Z on Oct 9 = 00:30 Oct 10 in Jerusalem = 11:30 Oct 9 in Honolulu
  const now = at('2026-10-09T21:30:00Z');
  assert.equal(viewModel(doc([ev('2026-10-10', '19:30')]), now).today.busy, true);
  assert.equal(viewModel(doc([ev('2026-10-09', '18:00')]), now).today.busy, false);
});

test('empty event list is coherent', () => {
  const vm = viewModel(doc([]), at('2026-10-10T12:00:00+03:00'));
  assert.deepEqual(vm.today, { busy: false, isGame: false, events: [] });
  assert.equal(vm.next, null);
  assert.equal(vm.stale, false);
});

test('dayIndicators: confirmed wins over tentative', () => {
  assert.deepEqual(dayIndicators([]), { confirmed: false, tentative: false });
  assert.deepEqual(dayIndicators([ev('2026-10-10', '19:30')]), { confirmed: true, tentative: false });
  assert.deepEqual(dayIndicators([ev('2026-10-10', null, { status: 'tentative' })]), { confirmed: false, tentative: true });
  assert.deepEqual(
    dayIndicators([ev('2026-10-10', null, { status: 'tentative' }), ev('2026-10-10', '19:30')]),
    { confirmed: true, tentative: false },
  );
});

test('defaultSelection: today when the visible month is the current month', () => {
  assert.equal(defaultSelection([], '2026-10', '2026-10-10'), '2026-10-10');
  assert.equal(defaultSelection([ev('2026-10-20', '19:30')], '2026-10', '2026-10-10'), '2026-10-10');
});

test('defaultSelection: first event day of another month, in date order', () => {
  const events = [ev('2026-11-20', '19:30'), ev('2026-11-05', null, { status: 'tentative' }), ev('2026-12-01', '19:30')];
  assert.equal(defaultSelection(events, '2026-11', '2026-10-10'), '2026-11-05');
});

test('defaultSelection: nothing selected in an empty other month', () => {
  assert.equal(defaultSelection([ev('2026-12-01', '19:30')], '2026-11', '2026-10-10'), null);
});

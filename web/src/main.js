import '@fontsource/barlow/400.css';
import '@fontsource/barlow/500.css';
import '@fontsource/barlow/600.css';
import '@fontsource/barlow/700.css';
import '@fontsource/barlow-condensed/600.css';
import '@fontsource/barlow-condensed/700.css';
import './styles.css';
import { gsap } from 'gsap';
import { createCity } from './city.js';

const $ = (id) => document.getElementById(id);
const num = new Intl.NumberFormat('en-PH');
const day = (iso) => new Date(`${iso.slice(0, 10)}T00:00:00Z`);
const dmy = (iso, year = false) => day(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', ...(year && { year: 'numeric' }), timeZone: 'UTC' });
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

async function load(name) {
  const res = await fetch(`data/${name}`);
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
}

function fatal(html) {
  $('fatal').innerHTML = html;
  $('fatal').hidden = false;
}

async function main() {
  let data;
  try {
    const [meta, forecast, resident, daytime, plans, shapes] = await Promise.all(
      ['meta.json', 'forecast.json', 'index_resident.json', 'index_daytime.json', 'plans.json', 'barangays.geojson'].map(load));
    data = { meta, forecast, index: { resident, daytime }, plans, shapes };
  } catch (err) {
    fatal(`<p>No dashboard data yet (${err.message}).<br>Run <code>python -m f2f.run</code>, then <code>python -m f2f.export</code>.</p>`);
    return;
  }
  const { meta } = data;
  const weeks = [...new Set(data.forecast.map((r) => r.issue_date))].sort();
  const state = { mode: 'resident', week: Math.min(3, weeks.length - 1), uptake: String(meta.uptake_default), decided: null };
  const names = Object.fromEntries(data.index.resident.map((r) => [r.psgc10, r.name]));

  // static header facts
  $('run-id').textContent = meta.run_id;
  $('chip-cases').querySelector('span').textContent = `Cases through ${dmy(meta.cases_through, true)} (PIDSR)`;
  $('gate-note').textContent = `Gate impaired since ${dmy(meta.gate.start, true)} · ${meta.gate.barangays.map((id) => names[id]).join(', ')}`;
  $('fc-src').textContent = meta.forecast_synthetic ? 'synthetic forecast · model pending (#7)' : `model ${data.forecast[0].model}`;
  $('fc-src').classList.toggle('syn', meta.forecast_synthetic);
  $('rain-src').innerHTML = `weekly rain, mm · solid = observed by the issue date · <span class="syn">${meta.rain_synthetic ? 'illustrative until CHIRPS (#3)' : 'CHIRPS'}</span>`;
  $('uptake').innerHTML = Object.keys(data.plans.resident).map((u) => `<option value="${u}">${Math.round(u * 100)}%</option>`).join('');
  $('uptake').value = state.uptake;
  $('scrub').max = weeks.length - 1;
  $('ticks').innerHTML = weeks.map((w) => `<span>${dmy(w)}</span>`).join('');

  let city = null;
  try {
    city = createCity($('city'), $('labels'), data.shapes, { onSelect: renderTable });
  } catch {
    $('stage-note').textContent = 'The 3D view needs WebGL. Every barangay is still in the table and the stock plan.';
    $('stage-note').hidden = false;
  }

  const rows = () => data.index[state.mode];

  function renderMode(intro = false) {
    city?.setIndex(rows(), { intro });
    $('map-src').textContent = state.mode === 'daytime'
      ? `stack height = priority · daytime scenario: residents × ${meta.daytime.factor} + ${num.format(meta.daytime.inflow)} port workers`
      : 'stack height = priority score · residents (POPCEN 2024)';
    renderTable(city?.selected);
    renderStock();
  }

  function renderTable(sel = null) {
    const act = rows().filter((r) => r.tier === 'act_now').sort((a, b) => a.rank - b.rank);
    const body = $('act-rows');
    body.innerHTML = act.map((r) => {
      const left = ((r.rank_p05 - 1) / 18) * 100, width = ((r.rank_p95 - r.rank_p05 + 1) / 18) * 100;
      const band = r.rank_p05 === r.rank_p95
        ? '<div class="band"><u class="pending"></u><span class="syn">pending</span></div>'
        : `<div class="band"><u><i style="left:${left}%;width:${width}%"></i></u>${r.rank_p05}–${r.rank_p95}</div>`;
      return `<tr tabindex="0" data-id="${r.psgc10}" aria-selected="${r.psgc10 === sel}">
        <td class="rk">${r.rank}</td><td>${r.name}</td><td class="sc">${r.score.toFixed(2)}</td><td>${band}</td></tr>`;
    }).join('');
    body.classList.toggle('has-sel', Boolean(sel) && act.some((r) => r.psgc10 === sel));
  }
  $('act-rows').addEventListener('click', (e) => { const tr = e.target.closest('tr'); if (tr) city?.select(tr.dataset.id); });
  $('act-rows').addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    e.preventDefault();
    city?.select(e.target.closest('tr').dataset.id);
  });

  function renderWeek() {
    const issue = weeks[state.week];
    $('cur-date').textContent = dmy(issue, true);
    $('scrub').value = state.week;
    $('scrub').style.setProperty('--pct', `${(state.week / (weeks.length - 1)) * 100}%`);
    const rainThrough = new Date(day(issue) - 864e5).toISOString();
    $('chip-rain').querySelector('span').textContent = `Rain through ${dmy(rainThrough, true)}${meta.rain_synthetic ? ' · illustrative' : ''}`;
    $('chip-rain').classList.toggle('syn-chip', meta.rain_synthetic);

    const now = data.forecast.filter((r) => r.issue_date === issue).sort((a, b) => a.h - b.h);
    $('weeks').innerHTML = now.map((r) => {
      const hist = data.forecast.filter((x) => x.h === r.h && x.issue_date <= issue).sort((a, b) => a.issue_date.localeCompare(b.issue_date));
      const tag = r.alert === 'warning' ? '<span class="tag">WARNING</span>' : r.alert === 'watch' ? '<span class="tag watch">WATCH</span>' : `<span>${dmy(r.target_week)}</span>`;
      return `<div class="${r.alert}"><div class="wl">Week +${r.h}${tag}</div>
        <span class="big${meta.forecast_synthetic ? ' syn' : ''}">${Math.round(r.p_elevated * 100)}%</span>
        <div class="hist" aria-hidden="true">${hist.map((x) => `<i style="height:${Math.max(3, x.p_elevated * 22)}px"></i>`).join('')}</div></div>`;
    }).join('');
    $('fc-foot').textContent = `Elevated = 3 or more reported cases in the week · watch at ${meta.alerts.watch_rain_lag2_mm} mm, warning at ${meta.alerts.warning_rain_lag2_mm} mm of rain two weeks back · as of ${dmy(issue, true)}`;

    // the priority index is standing; it switches on for the city only while a forecast week is on alert
    const onAlert = now.some((r) => r.alert !== 'none');
    city?.setAlert(onAlert);
    $('replay').classList.toggle('standby', !onAlert);
    $('standby-key').hidden = onAlert;
    $('act-src').textContent = onAlert
      ? 'priority index · rank bands pending (#11)'
      : 'standby · no forecast week on watch or warning';

    renderRain(issue);
    const observed = weeks.filter((w) => w < issue).map((w) => meta.rain_weekly_mm[w.slice(0, 10)] ?? 0);
    const recent = observed.slice(-2).reduce((s, x) => s + x, 0);
    city?.setWater(Math.min(1, recent / 400)); // shortcut: water depth is a rain proxy until the flood log (#4) gives real depths
  }

  function renderRain(issue) {
    const svg = $('bars');
    const w = svg.clientWidth || 600, h = 92, n = weeks.length, slot = w / n, max = 340;
    const y = (mm) => h - (mm / max) * (h - 16);
    const bars = weeks.map((wk, i) => {
      const mm = meta.rain_weekly_mm[wk.slice(0, 10)] ?? 0, x = i * slot + 4, bw = slot - 8;
      if (wk >= issue) return `<rect x="${x}" y="${h - 14}" width="${bw}" height="14" fill="none" stroke="#1f4fbf" stroke-dasharray="4 3"/><text x="${x + bw / 2}" y="${h - 18}" text-anchor="middle" class="t mute">not yet</text>`;
      return `<rect x="${x}" y="${y(mm)}" width="${bw}" height="${h - y(mm)}" fill="#1f4fbf"/><text x="${x + bw / 2}" y="${y(mm) - 4}" text-anchor="middle" class="t">${mm}</text>`;
    }).join('');
    const line = (mm, label, cls) => `<line x1="0" x2="${w}" y1="${y(mm)}" y2="${y(mm)}" class="${cls}"/><text x="${w}" y="${y(mm) - 4}" text-anchor="end" class="t ${cls}">${label}</text>`;
    const cut = weeks.indexOf(issue) * slot;
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    svg.innerHTML = `${bars}${line(meta.alerts.watch_rain_lag2_mm, `watch ${meta.alerts.watch_rain_lag2_mm} mm`, 'watchl')}${line(meta.alerts.warning_rain_lag2_mm, `warning ${meta.alerts.warning_rain_lag2_mm} mm`, 'warnl')}<line x1="0" x2="${w}" y1="${h}" y2="${h}" class="base"/><line x1="${cut}" x2="${cut}" y1="0" y2="${h + 6}" class="nowl"/>`;
  }
  new ResizeObserver(() => renderRain(weeks[state.week])).observe($('bars'));

  function renderStock() {
    const plan = data.plans[state.mode][state.uptake];
    const unmet = plan.total_need - plan.total_alloc;
    $('onhand').textContent = num.format(plan.stock_on_hand);
    $('need').textContent = num.format(plan.total_need);
    $('unmet').textContent = num.format(unmet);
    const ratio = unmet / plan.stock_on_hand;
    $('spill').style.width = `${Math.min(64, 34 * ratio)}%`;
    $('spill').classList.toggle('cut', 34 * ratio > 64); // drawn truncated, so it carries a break mark
    $('stock-src').textContent = `${dmy(plan.issue_date)} plan · ${state.mode === 'daytime' ? 'daytime scenario' : 'residents'} · f2f.planner`;
    $('spill-x').textContent = ratio > 1.9 ? `unmet is ${ratio.toFixed(1)}× what is on hand` : `unmet ${num.format(unmet)}`;
    if (state.decided?.plan !== plan.plan_id) resetDecision();
  }

  function resetDecision() {
    state.decided = null;
    $('decide').innerHTML = `<button class="btn pri" id="approve" type="button">Approve plan</button><button class="btn" id="reject" type="button">Reject</button><span class="src">Nothing is dispatched from here.</span>`;
  }
  $('decide').addEventListener('click', (e) => {
    const action = e.target.id === 'approve' ? 'approved' : e.target.id === 'reject' ? 'rejected' : null;
    if (!action) return;
    const plan = data.plans[state.mode][state.uptake];
    state.decided = { plan: plan.plan_id, action };
    $('decide').innerHTML = `<span class="stamp ${action}">${action}</span><span class="src">Plan ${plan.plan_id} · template only, not written to the audit log until #16 wires the local endpoint.</span>`;
    if (!reduce) gsap.from('#decide .stamp', { scale: 1.6, opacity: 0, rotate: -8, duration: 0.5, ease: 'expo.out' });
  });

  // replay controls
  let player = null;
  const go = (i) => { state.week = Math.max(0, Math.min(weeks.length - 1, i)); renderWeek(); };
  $('scrub').addEventListener('input', (e) => go(Number(e.target.value)));
  $('prev').addEventListener('click', () => go(state.week - 1));
  $('next').addEventListener('click', () => go(state.week + 1));
  $('play').addEventListener('click', () => {
    if (player) { player.kill(); player = null; $('play').textContent = 'Play'; return; }
    if (state.week === weeks.length - 1) go(0);
    $('play').textContent = 'Pause';
    player = gsap.timeline({ onComplete: () => { player = null; $('play').textContent = 'Play'; } });
    for (let i = state.week + 1; i < weeks.length; i++) player.call(go, [i], `+=${reduce ? 0.8 : 1.6}`);
  });

  document.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', () => {
    state.mode = b.dataset.mode;
    document.querySelectorAll('.seg button').forEach((x) => x.setAttribute('aria-checked', String(x === b)));
    renderMode();
  }));
  $('uptake').addEventListener('change', (e) => { state.uptake = e.target.value; renderStock(); });

  renderMode(true);
  renderWeek();
}

main();

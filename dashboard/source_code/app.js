// SupeRR Selector Dashboard App — Final Revision with Left Sidebar & Full Features
const DATA_DIR = './data/';

// State Management
const state = {
  coverage: null,
  top10: null,
  batters: [],
  bowlers: [],
  nearMisses: null,
  watchlist: null,
  evidence: null,
  timeline: null,
  robustness: null,
  baselines: [],
  paceSpin: [],
  pressureByOver: [],
  model: null,
  glossary: [],
  features: [],
  limitations: [],

  // Full tables state (Batters & Bowlers separate)
  battersPage: 1,
  bowlersPage: 1,
  pageSize: 15,
  battersFilter: { search: '', verdict: 'all', minPBalls: 200, minIPL: 0, sortCol: 'rank', sortAsc: true },
  bowlersFilter: { search: '', verdict: 'all', type: 'all', minPBalls: 200, minIPL: 0, sortCol: 'rank', sortAsc: true },

  // Detail inspection
  inspectedBatterId: 1699, // Suryakumar Yadav default
  inspectedBowlerId: 7825, // Jasprit Bumrah default

  // Comparison State
  compare: {
    mode: 'bat',   // 'bat' | 'bowl'
    p1Id: null,    // nothing is pre-selected: the comparison appears only after two players are chosen
    p2Id: null
  },

  // What-If Challenge State
  challengeType: 'bat',
  challengeWeights: { rae: 40, dae: 20, delta: 20, cons: 20 },

  bootType: 'bat',
  heatmapType: 'bat',

  // Charts
  radarChartInstance: null,
  timelineChartInstance: null,
  bootstrapChartInstance: null,
  pressureOverChartInstance: null
};

const GLOSSARY_MAP = {
  'score': 'Pressure Score',
  'rae': 'Runs Above Expected (RAE / 100)',
  'dae': 'Dismissals / Wickets vs Expected (DAE / 100)',
  'delta': 'Delta (Lift under pressure)',
  'cons': 'Consistency',
  'reliab': 'Reliability (shrinkage)',
  'verdict': 'Stability verdict',
  'boot_top10_pct': 'Bootstrap Top-10 %',
  'p_balls': 'High-pressure ball'
};

function formatNum(val, dec = 1) {
  if (val === null || val === undefined || isNaN(val)) return 'n/a';
  return Number(val).toFixed(dec);
}

function renderVerdictChip(verdict) {
  if (!verdict) return '<span class="chip">n/a</span>';
  const vLower = String(verdict).toLowerCase();
  let chipClass = 'chip-stable';
  if (vLower === 'moderate') chipClass = 'chip-moderate';
  if (vLower === 'borderline') chipClass = 'chip-borderline';
  return `<span class="chip ${chipClass}">${verdict}</span>`;
}

// Data Fetching
async function loadAllData() {
  try {
    const fetchJson = async (filename) => {
      // Bundled copy (data/data_bundle.js) lets the dashboard open by double-click (file://) as well as from a server
      if (window.SUPERR_DATA && window.SUPERR_DATA[filename] !== undefined) return window.SUPERR_DATA[filename];
      const res = await fetch(`${DATA_DIR}${filename}`);
      if (!res.ok) throw new Error(`Could not load ${filename}: ${res.statusText}`);
      return await res.json();
    };

    const [
      coverage, top10, batters, bowlers, nearMisses, watchlist,
      evidence, timeline, robustness, baselines, paceSpin,
      pressureByOver, model, glossary, features, limitations
    ] = await Promise.all([
      fetchJson('coverage.json'),
      fetchJson('top10.json'),
      fetchJson('batters.json'),
      fetchJson('bowlers.json'),
      fetchJson('near_misses.json'),
      fetchJson('eligibility_watchlist.json'),
      fetchJson('evidence.json'),
      fetchJson('timeline.json'),
      fetchJson('robustness.json'),
      fetchJson('baselines.json'),
      fetchJson('pace_spin_league.json'),
      fetchJson('pressure_by_over.json'),
      fetchJson('model.json'),
      fetchJson('glossary.json'),
      fetchJson('features.json'),
      fetchJson('limitations.json')
    ]);

    state.coverage = coverage;
    state.top10 = top10;
    state.batters = batters;
    state.bowlers = bowlers;
    state.nearMisses = nearMisses;
    state.watchlist = watchlist;
    state.evidence = evidence;
    state.timeline = timeline;
    state.robustness = robustness;
    state.baselines = baselines;
    state.paceSpin = paceSpin;
    state.pressureByOver = pressureByOver;
    state.model = model;
    state.glossary = glossary;
    state.features = features;
    state.limitations = limitations;

    initUI();
  } catch (err) {
    console.error('Fatal initialization error:', err);
    document.body.innerHTML = `<div style="padding:40px;color:red;font-family:sans-serif;">
      <h2>Data Loading Error</h2>
      <p>${err.message}</p>
    </div>`;
  }
}

function initUI() {
  // defaults come from the data (official rank 1), never from hard-coded ids
  state.inspectedBatterId = (state.batters.find(p => p.rank === 1) || state.batters[0]).player_id;
  state.inspectedBowlerId = (state.bowlers.find(p => p.rank === 1) || state.bowlers[0]).player_id;
  setupSidebarAndScrollspy();
  renderCoverageStrip();
  renderExecutiveSummary();
  renderTop10Tables();
  renderAllBattersTable();
  renderAllBowlersTable();
  initPlayerComparison();
  renderPressureSection();
  initRobustnessAndWhatIf();
  renderMethodology();
  renderNearMissesAndWatchlist();
  initGlossaryModal();
  renderInspectedBatter(state.inspectedBatterId);
  renderInspectedBowler(state.inspectedBowlerId);
  restoreInitialRoute();
}

// ==========================================================================
// 1. SIDEBAR NAVIGATION & SCROLLSPY
// ==========================================================================
// One router for every navigation path: sidebar links, topic buttons, in-page jumps, browser back/forward and refresh.
const NAV = { lockUntil: 0, current: null, ready: false };
const COMPARE_ALIASES = { 'sub-batter-comparison': 'bat', 'sub-bowler-comparison': 'bowl' };

function navElement(id) {
  if (id === 'sub-bowler-comparison') return document.getElementById('sub-batter-comparison'); // same tool, bowler mode
  return document.getElementById(id);
}

function navHeaderOffset() {
  const bar = document.querySelector('.top-bar-mobile');
  const h = bar && getComputedStyle(bar).display !== 'none' ? bar.offsetHeight : 0;
  return h + 16;
}

function setActiveNav(id, fromClick) {
  let link = document.querySelector(`.nav-sub-link[href="#${id}"]`);
  let parent = link ? link.closest('.nav-topic') : document.querySelector(`.nav-topic[data-topic="${id}"]`);
  if (!link && parent) link = parent.querySelector('.nav-sub-link');
  if (!parent) return;
  document.querySelectorAll('.nav-sub-link').forEach(l => {
    const on = l === link;
    l.classList.toggle('active', on);
    if (on) l.setAttribute('aria-current', 'location'); else l.removeAttribute('aria-current');
  });
  document.querySelectorAll('.nav-topic').forEach(t => {
    const isParent = t === parent;
    t.classList.toggle('active', isParent);
    if (isParent) {
      if (fromClick) delete t.dataset.userClosed;
      if (!t.dataset.userClosed) t.classList.add('expanded');
    } else {
      t.classList.remove('expanded');
      delete t.dataset.userClosed;
    }
    const btn = t.querySelector('.nav-topic-btn');
    if (btn) btn.setAttribute('aria-expanded', t.classList.contains('expanded') ? 'true' : 'false');
  });
  if (link && link.scrollIntoView) link.scrollIntoView({ block: 'nearest' });
}

function navigateTo(id, opts = {}) {
  const { push = true, smooth = true } = opts;
  if (!id) return false;
  if (COMPARE_ALIASES[id] && typeof setCompareMode === 'function') setCompareMode(COMPARE_ALIASES[id]);
  const el = navElement(id);
  if (!el) return false;
  const y = Math.max(0, el.getBoundingClientRect().top + window.scrollY - navHeaderOffset());
  NAV.current = id;
  lockSpyUntilScrollSettles();
  window.scrollTo({ top: y, behavior: smooth ? 'smooth' : 'instant' });
  setActiveNav(id, true);
  if (location.hash !== '#' + id) { if (push) history.pushState(null, '', '#' + id); else history.replaceState(null, '', '#' + id); }
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar && window.innerWidth <= 1024) sidebar.classList.remove('open');
  return true;
}
window.navigateTo = navigateTo;

// While a programmatic scroll is running the scroll-spy must stay quiet, otherwise it would highlight (and write to the
// address bar) every section the page passes on the way. The lock is released once the scroll position stops changing.
function lockSpyUntilScrollSettles() {
  NAV.lockUntil = Date.now() + 6000;
  const token = (NAV.lockToken = (NAV.lockToken || 0) + 1);
  let last = window.scrollY, still = 0;
  const tick = () => {
    if (token !== NAV.lockToken) return;
    if (Math.abs(window.scrollY - last) < 1) still++; else still = 0;
    last = window.scrollY;
    if (still >= 3) { NAV.lockUntil = 0; return; }
    setTimeout(tick, 70);
  };
  setTimeout(tick, 70);
}

function restoreInitialRoute() {
  NAV.ready = true;
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  const id = decodeURIComponent(location.hash.replace(/^#/, ''));
  if (!id || !navElement(id)) { updateScrollSpy(true); return; }
  // charts and tables change the page height while they render, so settle the position more than once
  const go = () => navigateTo(id, { push: false, smooth: false });
  go(); requestAnimationFrame(go); setTimeout(go, 350); setTimeout(go, 900);
}

function updateScrollSpy(force) {
  if (!NAV.ready || (!force && Date.now() < NAV.lockUntil)) return;
  const line = navHeaderOffset() + 70;
  let currentId = null, bestTop = -Infinity;
  const seen = new Set();
  const consider = (el, id) => {
    if (!el || seen.has(el)) return;
    seen.add(el);
    const top = el.getBoundingClientRect().top;
    if (top <= line && top >= bestTop) { bestTop = top; currentId = id; }
  };
  // a topic's own header counts as its first subtopic, so the highlight moves as soon as the topic starts
  document.querySelectorAll('.nav-topic').forEach(t => {
    const first = t.querySelector('.nav-sub-link');
    if (first) consider(document.getElementById(t.dataset.topic), first.getAttribute('href').slice(1));
  });
  document.querySelectorAll('.nav-sub-link').forEach(l => { const id = l.getAttribute('href').slice(1); consider(navElement(id), id); });
  if (!currentId) { const first = document.querySelector('.nav-sub-link'); currentId = first ? first.getAttribute('href').slice(1) : null; }
  if (currentId === 'sub-batter-comparison' && state.compare.mode === 'bowl') currentId = 'sub-bowler-comparison';
  if (!currentId || currentId === NAV.current) return;
  NAV.current = currentId;
  setActiveNav(currentId, false);
  if (location.hash !== '#' + currentId) history.replaceState(null, '', '#' + currentId); // keeps the place on refresh
}

function setupSidebarAndScrollspy() {
  const sidebar = document.getElementById('app-sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle-btn');
  if (toggleBtn) {
    toggleBtn.setAttribute('aria-controls', 'app-sidebar');
    toggleBtn.addEventListener('click', (e) => { e.stopPropagation(); sidebar.classList.toggle('open'); });
  }
  // tap outside the open sidebar closes it on small screens
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 1024 && sidebar.classList.contains('open') && !sidebar.contains(e.target)) sidebar.classList.remove('open');
  });

  // Main topics: open the topic and go to it; clicking an already open topic collapses it
  document.querySelectorAll('.nav-topic-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const topic = btn.closest('.nav-topic');
      if (topic.classList.contains('expanded')) {
        topic.classList.remove('expanded');
        if (topic.classList.contains('active')) topic.dataset.userClosed = '1';
        btn.setAttribute('aria-expanded', 'false');
        return;
      }
      navigateTo(topic.dataset.topic);
    });
  });

  // Subtopics and any other in-page link (href="#...") go through the router
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;
    const id = decodeURIComponent(a.getAttribute('href').slice(1));
    if (!id || !navElement(id)) return;
    e.preventDefault();
    navigateTo(id);
  });

  // Back / forward
  window.addEventListener('popstate', () => {
    const id = decodeURIComponent(location.hash.replace(/^#/, ''));
    if (id) navigateTo(id, { push: false, smooth: false });
    else { window.scrollTo({ top: 0, behavior: 'instant' }); NAV.lockUntil = 0; updateScrollSpy(true); }
  });

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; updateScrollSpy(false); });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
}


// ==========================================================================
// 2. COVERAGE & EXECUTIVE SUMMARY
// ==========================================================================
function renderCoverageStrip() {
  const cov = state.coverage;
  if (!cov) return;
  document.getElementById('coverage-strip').innerHTML = `
    <div class="cov-item">Audited Matches: <span class="cov-val">${cov.matches_in_pressure_model.toLocaleString()}</span> (${cov.ipl_matches} IPL · ${cov.t20i_matches} T20I)</div>
    <div class="cov-item">Total Balls: <span class="cov-val">${cov.deliveries_in_pressure_model.toLocaleString()}</span></div>
    <div class="cov-item">High-Pressure Deliveries: <span class="cov-val">${cov.high_pressure_deliveries.toLocaleString()}</span></div>
    <div class="cov-item">Threshold PI: <span class="cov-val">Inn 1: ${cov.pressure_threshold_PI_inn1.toFixed(1)} · Inn 2: ${cov.pressure_threshold_PI_inn2.toFixed(1)}</span></div>
    <div class="cov-item">Eligible (200b / 15m): <span class="cov-val">69 Batters · 69 Bowlers</span></div>
    <div class="cov-item">Horizon: <span class="cov-val">${cov.date_min} to ${cov.date_max}</span></div>
  `;
}

function renderExecutiveSummary() {
  const batStable = state.top10.bat.filter(p => p.verdict === 'Stable').length;
  const batMod = state.top10.bat.filter(p => p.verdict === 'Moderate').length;
  const batBord = state.top10.bat.filter(p => p.verdict === 'Borderline').length;

  const bowlStable = state.top10.bowl.filter(p => p.verdict === 'Stable').length;
  const bowlMod = state.top10.bowl.filter(p => p.verdict === 'Moderate').length;
  const bowlBord = state.top10.bowl.filter(p => p.verdict === 'Borderline').length;

  document.getElementById('headline-selected').innerHTML = `
    <strong>Batting Leaders:</strong> Suryakumar Yadav (74.6), Heinrich Klaasen (73.7), Prabhsimran Singh (73.1).<br>
    <strong>Bowling Leaders:</strong> Jasprit Bumrah (78.4), Krunal Pandya (73.0), Sunil Narine (72.6).<br>
    All cleared the strict 200 pressure-ball & 15-match minimum eligibility gate.
  `;

  document.getElementById('headline-evidence').innerHTML = `
    Derived from <strong>47,038 high-pressure balls</strong> across 818 matches. Scored against 24 empirical context cells across Runs vs Expected (40%), Wickets vs Expected (20%), Individual Lift (20%), and Innings Consistency (20%).
  `;

  document.getElementById('headline-robustness').innerHTML = `
    <strong>Batters:</strong> ${batStable} Stable, ${batMod} Moderate, ${batBord} Borderline.<br>
    <strong>Bowlers:</strong> ${bowlStable} Stable, ${bowlMod} Moderate, ${bowlBord} Borderline.<br>
    Verified across 24 alternative specification scenarios and 1,000 bootstrap resamples.
  `;
}

// ==========================================================================
// 3. TOP 10 TABLES & INSPECTION
// ==========================================================================
// Photographs are used only for the top three batters and bowlers. Only ids listed here have a supplied photo file;
// any other player (or a missing file) gets an initials badge instead, so no broken image can appear.
const PLAYER_PHOTOS = { 1699: true, 4260: true, 7216: true, 2933: true, 4219: true, 781: true };
function renderTop3Cards() {
  [['bat', 'top3-batters-cards', 'inspectBatter'], ['bowl', 'top3-bowlers-cards', 'inspectBowler']].forEach(([k, boxId, fn]) => {
    const box = document.getElementById(boxId);
    if (!box) return;
    box.innerHTML = state.top10[k].slice(0, 3).map(p => {
      const initials = p.name.split(' ').slice(0, 2).map(w => w[0]).join('');
      const pic = PLAYER_PHOTOS[p.player_id]
        ? `<img class="top3-photo" src="assets/player_photos/${p.player_id}.jpg" alt="${p.name}" loading="lazy">`
        : `<span class="top3-photo top3-initials" aria-hidden="true">${initials}</span>`;
      return `<button type="button" class="top3-card" onclick="window.${fn}(${p.player_id})" title="Open ${p.name}'s pressure profile">
        ${pic}
        <span class="top3-text">
          <span class="top3-rank">#${p.rank}</span>
          <span class="top3-name">${p.name}</span>
          <span class="top3-meta"><strong>${formatNum(p.score, 1)}</strong> score ${renderVerdictChip(p.verdict)}</span>
        </span>
      </button>`;
    }).join('');
  });
}

function renderTop10Tables() {
  renderTop3Cards();
  const batTbody = document.querySelector('#top10-batters-table tbody');
  const bowlTbody = document.querySelector('#top10-bowlers-table tbody');

  const fullTopBat = state.top10.bat.map(p => {
    const full = state.batters.find(b => b.player_id === p.player_id) || {};
    return { ...p, p_sr: full.p_sr, np_sr: full.np_sr };
  });

  const fullTopBowl = state.top10.bowl.map(p => {
    const full = state.bowlers.find(b => b.player_id === p.player_id) || {};
    return { ...p, p_econ: full.p_econ, np_econ: full.np_econ };
  });

  batTbody.innerHTML = fullTopBat.map(p => `
    <tr class="clickable-row" onclick="window.inspectBatter(${p.player_id})">
      <td><strong>#${p.rank}</strong></td>
      <td><strong>${p.name}</strong></td>
      <td><strong style="color:var(--rr-pink);font-size:1rem;">${formatNum(p.score, 1)}</strong></td>
      <td>${renderVerdictChip(p.verdict)}</td>
      <td>${p.p_balls}</td>
      <td><strong>${formatNum(p.p_sr, 1)}</strong></td>
      <td>${formatNum(p.np_sr, 1)}</td>
      <td>${formatNum(p.boot_top10_pct, 1)}%</td>
      <td><button class="btn btn-outline-rr btn-sm">Inspect</button></td>
    </tr>
  `).join('');

  bowlTbody.innerHTML = fullTopBowl.map(p => `
    <tr class="clickable-row" onclick="window.inspectBowler(${p.player_id})">
      <td><strong>#${p.rank}</strong></td>
      <td><strong>${p.name}</strong></td>
      <td><strong style="color:var(--rr-royal-blue);font-size:1rem;">${formatNum(p.score, 1)}</strong></td>
      <td>${renderVerdictChip(p.verdict)}</td>
      <td>${p.p_balls}</td>
      <td><strong>${formatNum(p.p_econ, 2)}</strong></td>
      <td>${formatNum(p.np_econ, 2)}</td>
      <td>${formatNum(p.boot_top10_pct, 1)}%</td>
      <td><button class="btn btn-outline-rr btn-sm">Inspect</button></td>
    </tr>
  `).join('');
}

// ==========================================================================
// 4. FULL 69 BATTERS & 69 BOWLERS TABLES (WITH SEARCH, SORT & PAGINATION)
// ==========================================================================
function renderAllBattersTable() {
  const f = state.battersFilter;
  let filtered = state.batters.filter(p => {
    if (f.search && !p.name.toLowerCase().includes(f.search.toLowerCase())) return false;
    if (f.verdict !== 'all' && p.verdict !== f.verdict) return false;
    if (p.p_balls < f.minPBalls) return false;
    if ((p.ipl_pct || 0) < f.minIPL) return false;
    return true;
  });

  filtered.sort((a, b) => {
    const valA = a[f.sortCol];
    const valB = b[f.sortCol];
    if (typeof valA === 'string') return f.sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    return f.sortAsc ? (valA - valB) : (valB - valA);
  });

  const totalPages = Math.ceil(filtered.length / state.pageSize) || 1;
  state.battersPage = Math.min(state.battersPage, totalPages);
  const startIdx = (state.battersPage - 1) * state.pageSize;
  const pageItems = filtered.slice(startIdx, startIdx + state.pageSize);

  const tbody = document.querySelector('#all-batters-table tbody');
  tbody.innerHTML = pageItems.map(p => `
    <tr>
      <td><strong>#${p.rank}</strong></td>
      <td><strong>${p.name}</strong></td>
      <td>${p.p_balls}</td>
      <td>${p.p_matches}</td>
      <td><strong>${formatNum(p.p_sr, 1)}</strong></td>
      <td>${formatNum(p.np_sr, 1)}</td>
      <td>${formatNum(p.rae, 2)}</td>
      <td>${formatNum(p.cons, 1)}%</td>
      <td><strong style="color:var(--rr-pink);">${formatNum(p.score, 1)}</strong></td>
      <td>${renderVerdictChip(p.verdict)}</td>
      <td><button class="btn btn-outline-rr btn-sm" onclick="window.inspectBatter(${p.player_id})">Inspect</button></td>
    </tr>
  `).join('');

  // Pagination bar
  const pBar = document.getElementById('batters-pagination');
  pBar.innerHTML = `
    <span>Showing ${startIdx + 1}–${Math.min(startIdx + state.pageSize, filtered.length)} of ${filtered.length} eligible batters</span>
    <div class="pagination-controls">
      <button class="btn btn-secondary btn-sm" ${state.battersPage === 1 ? 'disabled' : ''} onclick="window.changeBatterPage(-1)">&larr; Prev</button>
      <span>Page ${state.battersPage} of ${totalPages}</span>
      <button class="btn btn-secondary btn-sm" ${state.battersPage === totalPages ? 'disabled' : ''} onclick="window.changeBatterPage(1)">Next &rarr;</button>
    </div>
  `;

  // Attach filter inputs
  const searchInput = document.getElementById('batter-table-search');
  const verdictSelect = document.getElementById('batter-table-verdict');
  const pballsSlider = document.getElementById('batter-slider-pballs');
  const pballsVal = document.getElementById('batter-val-pballs');
  const iplSlider = document.getElementById('batter-slider-ipl');
  const iplVal = document.getElementById('batter-val-ipl');

  searchInput.oninput = (e) => { f.search = e.target.value; state.battersPage = 1; renderAllBattersTable(); };
  verdictSelect.onchange = (e) => { f.verdict = e.target.value; state.battersPage = 1; renderAllBattersTable(); };
  pballsSlider.oninput = (e) => { f.minPBalls = parseInt(e.target.value, 10); pballsVal.textContent = f.minPBalls; state.battersPage = 1; renderAllBattersTable(); };
  iplSlider.oninput = (e) => { f.minIPL = parseInt(e.target.value, 10); iplVal.textContent = `${f.minIPL}%`; state.battersPage = 1; renderAllBattersTable(); };

  // Sorting
  document.querySelectorAll('#all-batters-table th[data-col]').forEach(th => {
    th.style.cursor = 'pointer';
    th.onclick = (e) => {
      if (e.target.classList.contains('info-btn')) return;
      const col = th.dataset.col;
      if (f.sortCol === col) f.sortAsc = !f.sortAsc;
      else { f.sortCol = col; f.sortAsc = true; }
      renderAllBattersTable();
    };
  });
}

function renderAllBowlersTable() {
  const f = state.bowlersFilter;
  let filtered = state.bowlers.filter(p => {
    if (f.search && !p.name.toLowerCase().includes(f.search.toLowerCase())) return false;
    if (f.verdict !== 'all' && p.verdict !== f.verdict) return false;
    if (f.type !== 'all' && p.bowl_type !== f.type) return false;
    if (p.p_balls < f.minPBalls) return false;
    if ((p.ipl_pct || 0) < f.minIPL) return false;
    return true;
  });

  filtered.sort((a, b) => {
    const valA = a[f.sortCol];
    const valB = b[f.sortCol];
    if (typeof valA === 'string') return f.sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    return f.sortAsc ? (valA - valB) : (valB - valA);
  });

  const totalPages = Math.ceil(filtered.length / state.pageSize) || 1;
  state.bowlersPage = Math.min(state.bowlersPage, totalPages);
  const startIdx = (state.bowlersPage - 1) * state.pageSize;
  const pageItems = filtered.slice(startIdx, startIdx + state.pageSize);

  const tbody = document.querySelector('#all-bowlers-table tbody');
  tbody.innerHTML = pageItems.map(p => `
    <tr>
      <td><strong>#${p.rank}</strong></td>
      <td><strong>${p.name}</strong></td>
      <td>${p.p_balls}</td>
      <td>${p.p_matches}</td>
      <td><strong>${formatNum(p.p_econ, 2)}</strong></td>
      <td>${formatNum(p.np_econ, 2)}</td>
      <td>${formatNum(p.rae, 2)}</td>
      <td>${formatNum(p.dae, 2)}</td>
      <td>${formatNum(p.cons, 1)}%</td>
      <td><strong style="color:var(--rr-royal-blue);">${formatNum(p.score, 1)}</strong></td>
      <td>${renderVerdictChip(p.verdict)}</td>
      <td><button class="btn btn-outline-rr btn-sm" onclick="window.inspectBowler(${p.player_id})">Inspect</button></td>
    </tr>
  `).join('');

  const pBar = document.getElementById('bowlers-pagination');
  pBar.innerHTML = `
    <span>Showing ${startIdx + 1}–${Math.min(startIdx + state.pageSize, filtered.length)} of ${filtered.length} eligible bowlers</span>
    <div class="pagination-controls">
      <button class="btn btn-secondary btn-sm" ${state.bowlersPage === 1 ? 'disabled' : ''} onclick="window.changeBowlerPage(-1)">&larr; Prev</button>
      <span>Page ${state.bowlersPage} of ${totalPages}</span>
      <button class="btn btn-secondary btn-sm" ${state.bowlersPage === totalPages ? 'disabled' : ''} onclick="window.changeBowlerPage(1)">Next &rarr;</button>
    </div>
  `;

  // Attach filter inputs
  const searchInput = document.getElementById('bowler-table-search');
  const verdictSelect = document.getElementById('bowler-table-verdict');
  const typeSelect = document.getElementById('bowler-table-type');
  const pballsSlider = document.getElementById('bowler-slider-pballs');
  const pballsVal = document.getElementById('bowler-val-pballs');
  const iplSlider = document.getElementById('bowler-slider-ipl');
  const iplVal = document.getElementById('bowler-val-ipl');

  searchInput.oninput = (e) => { f.search = e.target.value; state.bowlersPage = 1; renderAllBowlersTable(); };
  verdictSelect.onchange = (e) => { f.verdict = e.target.value; state.bowlersPage = 1; renderAllBowlersTable(); };
  typeSelect.onchange = (e) => { f.type = e.target.value; state.bowlersPage = 1; renderAllBowlersTable(); };
  pballsSlider.oninput = (e) => { f.minPBalls = parseInt(e.target.value, 10); pballsVal.textContent = f.minPBalls; state.bowlersPage = 1; renderAllBowlersTable(); };
  iplSlider.oninput = (e) => { f.minIPL = parseInt(e.target.value, 10); iplVal.textContent = `${f.minIPL}%`; state.bowlersPage = 1; renderAllBowlersTable(); };

  document.querySelectorAll('#all-bowlers-table th[data-col]').forEach(th => {
    th.style.cursor = 'pointer';
    th.onclick = (e) => {
      if (e.target.classList.contains('info-btn')) return;
      const col = th.dataset.col;
      if (f.sortCol === col) f.sortAsc = !f.sortAsc;
      else { f.sortCol = col; f.sortAsc = true; }
      renderAllBowlersTable();
    };
  });
}

window.changeBatterPage = (delta) => { state.battersPage += delta; renderAllBattersTable(); };
window.changeBowlerPage = (delta) => { state.bowlersPage += delta; renderAllBowlersTable(); };

// ==========================================================================
// 5. BATTER & BOWLER SUBTOPIC DETAIL RENDERING
// ==========================================================================
window.inspectBatter = function(pid) {
  state.inspectedBatterId = pid;
  renderInspectedBatter(pid);
  navigateTo('sub-batter-pressure-vs-normal');
};

window.inspectBowler = function(pid) {
  state.inspectedBowlerId = pid;
  renderInspectedBowler(pid);
  navigateTo('sub-bowler-pressure-vs-normal');
};

function renderInspectedBatter(pid) {
  const p = state.batters.find(b => b.player_id === pid) || state.batters[0];
  if (!p) return;

  // Pressure vs Normal
  document.getElementById('batter-player-detail-box').innerHTML = `
    <div class="card" style="border-left:4px solid var(--rr-pink);">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:14px;">
        <div>
          <h4 style="font-size:1.4rem;font-weight:800;color:var(--rr-navy);">${p.name} (#${p.rank} Batter)</h4>
          <span style="font-size:0.85rem;color:var(--text-muted);">${p.p_balls} high-pressure balls across ${p.p_matches} matches</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <span class="chip chip-stable" style="font-size:1rem;padding:6px 14px;">Score: ${formatNum(p.score, 1)}</span>
          ${renderVerdictChip(p.verdict)}
        </div>
      </div>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr><th>Metric</th><th>Pressure Level</th><th>Normal Level</th><th>Differential (Delta / Lift)</th></tr>
          </thead>
          <tbody>
            <tr><td>Strike Rate</td><td><strong>${formatNum(p.p_sr, 1)}</strong></td><td>${formatNum(p.np_sr, 1)}</td><td><strong style="color:var(--rr-pink);">${p.p_sr >= p.np_sr ? '+' : ''}${formatNum(p.p_sr - p.np_sr, 1)}</strong></td></tr>
            <tr><td>Runs Above Expected / 100 (RAE)</td><td><strong>${formatNum(p.rae, 2)}</strong></td><td>${formatNum(p.np_rae, 2)}</td><td>Z-score: ${formatNum(p.z_rae, 2)}</td></tr>
            <tr><td>Dismissals vs Expected / 100 (DAE)</td><td><strong>${formatNum(p.dae, 2)}</strong></td><td>-</td><td>Z-score: ${formatNum(p.z_dae, 2)}</td></tr>
            <tr><td>Boundary % / Dot Ball %</td><td><strong>${formatNum(p.p_bnd_pct, 1)}%</strong></td><td>${formatNum(p.p_dot_pct, 1)}% (Dot)</td><td>Clutch Contribution: ${formatNum(p.clutch_pct, 1)}%</td></tr>
          </tbody>
        </table>
      </div>
      ${p.justification ? `<div class="justification-box" style="margin-top:16px;"><strong>Selection Justification:</strong> ${p.justification}</div>` : ''}
    </div>
  `;

  // Score breakdown
  const cRae = Math.max(0, p.contrib_rae || 0);
  const cDae = Math.max(0, p.contrib_dae || 0);
  const cDelta = Math.max(0, p.contrib_delta || 0);
  const cCons = Math.max(0, p.contrib_cons || 0);
  const totalC = (cRae + cDae + cDelta + cCons) || 1;
  const pRae = ((cRae / totalC) * 100).toFixed(1);
  const pDae = ((cDae / totalC) * 100).toFixed(1);
  const pDelta = ((cDelta / totalC) * 100).toFixed(1);
  const pCons = ((cCons / totalC) * 100).toFixed(1);

  document.getElementById('batter-score-breakdown-container').innerHTML = `
    <div class="card">
      <h4 style="font-size:1.05rem;font-weight:700;color:var(--rr-navy);margin-bottom:8px;">${p.name}: Component Contribution to Score</h4>
      <div class="breakdown-bar">
        <div class="bar-segment bg-rae" style="width:${pRae}%;">${pRae > 8 ? `RAE ${pRae}%` : ''}</div>
        <div class="bar-segment bg-dae" style="width:${pDae}%;">${pDae > 8 ? `DAE ${pDae}%` : ''}</div>
        <div class="bar-segment bg-delta" style="width:${pDelta}%;">${pDelta > 8 ? `Delta ${pDelta}%` : ''}</div>
        <div class="bar-segment bg-cons" style="width:${pCons}%;">${pCons > 8 ? `Cons ${pCons}%` : ''}</div>
      </div>
      <div class="breakdown-legend">
        <span class="legend-item"><span class="legend-color bg-rae"></span> Runs vs Exp (${formatNum(cRae, 1)} pts / ${pRae}%)</span>
        <span class="legend-item"><span class="legend-color bg-dae"></span> Dismissals vs Exp (${formatNum(cDae, 1)} pts / ${pDae}%)</span>
        <span class="legend-item"><span class="legend-color bg-delta"></span> Lift / Delta (${formatNum(cDelta, 1)} pts / ${pDelta}%)</span>
        <span class="legend-item"><span class="legend-color bg-cons"></span> Consistency (${formatNum(cCons, 1)} pts / ${pCons}%)</span>
      </div>
    </div>
  `;

  // Splits
  document.getElementById('batter-splits-container').innerHTML = `
    <div class="card">
      <div class="table-responsive">
        <table class="table">
          <thead><tr><th>Match Situation</th><th>Pressure Balls</th><th>Output vs Expected</th><th>Strike Rate</th></tr></thead>
          <tbody>
            <tr><td>1st Innings (Setting Target)</td><td>${p.inn1_balls || 0}</td><td style="color:${(p.inn1_vs_exp || 0) >= 0 ? '#15803D' : '#B91C1C'};font-weight:700;">${formatNum(p.inn1_vs_exp, 1)}</td><td><strong>${formatNum(p.inn1_rate, 1)}</strong></td></tr>
            <tr><td>2nd Innings (Chasing Target)</td><td>${p.inn2_balls || 0}</td><td style="color:${(p.inn2_vs_exp || 0) >= 0 ? '#15803D' : '#B91C1C'};font-weight:700;">${formatNum(p.inn2_vs_exp, 1)}</td><td><strong>${formatNum(p.inn2_rate, 1)}</strong></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;

  // Pace vs Spin
  const paceLow = (p.vs_pace_balls || 0) < 60;
  const spinLow = (p.vs_spin_balls || 0) < 60;
  document.getElementById('batter-pacespin-container').innerHTML = `
    <div class="card">
      <div class="table-responsive">
        <table class="table">
          <thead><tr><th>Discipline</th><th>Pressure Deliveries</th><th>Strike Rate</th><th>Dismissals</th><th>Sample Reliability</th></tr></thead>
          <tbody>
            <tr><td>vs Pace Under Pressure</td><td>${p.vs_pace_balls || 0}</td><td><strong>${formatNum(p.vs_pace_sr, 1)}</strong></td><td>${p.vs_pace_outs || 0}</td><td>${paceLow ? '<span class="chip chip-borderline">Low sample (&lt;60b)</span>' : '<span class="chip chip-stable">Sufficient Sample</span>'}</td></tr>
            <tr><td>vs Spin Under Pressure</td><td>${p.vs_spin_balls || 0}</td><td><strong>${formatNum(p.vs_spin_sr, 1)}</strong></td><td>${p.vs_spin_outs || 0}</td><td>${spinLow ? '<span class="chip chip-borderline">Low sample (&lt;60b)</span>' : '<span class="chip chip-stable">Sufficient Sample</span>'}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderInspectedBowler(pid) {
  const p = state.bowlers.find(b => b.player_id === pid) || state.bowlers[0];
  if (!p) return;

  document.getElementById('bowler-player-detail-box').innerHTML = `
    <div class="card" style="border-left:4px solid var(--rr-royal-blue);">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:14px;">
        <div>
          <h4 style="font-size:1.4rem;font-weight:800;color:var(--rr-navy);">${p.name} (#${p.rank} Bowler)</h4>
          <span style="font-size:0.85rem;color:var(--text-muted);">${p.p_balls} high-pressure balls across ${p.p_matches} matches · ${p.bowl_type} (${p.bowl_style})</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <span class="chip chip-stable" style="font-size:1rem;padding:6px 14px;background:#E0F2FE;color:var(--rr-royal-blue);">Score: ${formatNum(p.score, 1)}</span>
          ${renderVerdictChip(p.verdict)}
        </div>
      </div>
      <div class="table-responsive">
        <table class="table">
          <thead><tr><th>Metric</th><th>Pressure Level</th><th>Normal Level</th><th>Differential (Delta / Lift)</th></tr></thead>
          <tbody>
            <tr><td>Economy Rate</td><td><strong>${formatNum(p.p_econ, 2)}</strong></td><td>${formatNum(p.np_econ, 2)}</td><td><strong style="color:var(--rr-royal-blue);">${p.p_econ <= p.np_econ ? '-' : '+'}${formatNum(Math.abs(p.p_econ - p.np_econ), 2)}</strong></td></tr>
            <tr><td>Runs Saved vs Expected / 100 (RAE)</td><td><strong>${formatNum(p.rae, 2)}</strong></td><td>-</td><td>Z-score: ${formatNum(p.z_rae, 2)}</td></tr>
            <tr><td>Wickets Above Expected / 100 (DAE)</td><td><strong>${formatNum(p.dae, 2)}</strong></td><td>-</td><td>Z-score: ${formatNum(p.z_dae, 2)}</td></tr>
            <tr><td>Consistency %</td><td><strong>${formatNum(p.cons, 1)}%</strong></td><td>-</td><td>Z-score: ${formatNum(p.z_cons, 2)}</td></tr>
          </tbody>
        </table>
      </div>
      ${p.justification ? `<div class="justification-box" style="margin-top:16px;"><strong>Selection Justification:</strong> ${p.justification}</div>` : ''}
    </div>
  `;

  const cRae = Math.max(0, p.contrib_rae || 0);
  const cDae = Math.max(0, p.contrib_dae || 0);
  const cDelta = Math.max(0, p.contrib_delta || 0);
  const cCons = Math.max(0, p.contrib_cons || 0);
  const totalC = (cRae + cDae + cDelta + cCons) || 1;
  const pRae = ((cRae / totalC) * 100).toFixed(1);
  const pDae = ((cDae / totalC) * 100).toFixed(1);
  const pDelta = ((cDelta / totalC) * 100).toFixed(1);
  const pCons = ((cCons / totalC) * 100).toFixed(1);

  document.getElementById('bowler-score-breakdown-container').innerHTML = `
    <div class="card">
      <h4 style="font-size:1.05rem;font-weight:700;color:var(--rr-navy);margin-bottom:8px;">${p.name}: Component Contribution to Score</h4>
      <div class="breakdown-bar">
        <div class="bar-segment bg-rae" style="width:${pRae}%;">${pRae > 8 ? `RAE ${pRae}%` : ''}</div>
        <div class="bar-segment bg-dae" style="width:${pDae}%;">${pDae > 8 ? `DAE ${pDae}%` : ''}</div>
        <div class="bar-segment bg-delta" style="width:${pDelta}%;">${pDelta > 8 ? `Delta ${pDelta}%` : ''}</div>
        <div class="bar-segment bg-cons" style="width:${pCons}%;">${pCons > 8 ? `Cons ${pCons}%` : ''}</div>
      </div>
      <div class="breakdown-legend">
        <span class="legend-item"><span class="legend-color bg-rae"></span> Runs Saved vs Exp (${formatNum(cRae, 1)} pts / ${pRae}%)</span>
        <span class="legend-item"><span class="legend-color bg-dae"></span> Wickets vs Exp (${formatNum(cDae, 1)} pts / ${pDae}%)</span>
        <span class="legend-item"><span class="legend-color bg-delta"></span> Lift / Delta (${formatNum(cDelta, 1)} pts / ${pDelta}%)</span>
        <span class="legend-item"><span class="legend-color bg-cons"></span> Consistency (${formatNum(cCons, 1)} pts / ${pCons}%)</span>
      </div>
    </div>
  `;

  document.getElementById('bowler-splits-container').innerHTML = `
    <div class="card">
      <div class="table-responsive">
        <table class="table">
          <thead><tr><th>Match Situation</th><th>Pressure Balls</th><th>Output vs Expected</th><th>Economy</th></tr></thead>
          <tbody>
            <tr><td>1st Innings (Defending Par)</td><td>${p.inn1_balls || 0}</td><td style="color:${(p.inn1_vs_exp || 0) >= 0 ? '#15803D' : '#B91C1C'};font-weight:700;">${formatNum(p.inn1_vs_exp, 1)}</td><td><strong>${formatNum(p.inn1_rate, 2)}</strong></td></tr>
            <tr><td>2nd Innings (Defending Target)</td><td>${p.inn2_balls || 0}</td><td style="color:${(p.inn2_vs_exp || 0) >= 0 ? '#15803D' : '#B91C1C'};font-weight:700;">${formatNum(p.inn2_vs_exp, 1)}</td><td><strong>${formatNum(p.inn2_rate, 2)}</strong></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// ==========================================================================
// 6. INTERACTIVE PLAYER COMPARISON TOOL (COMPACT SELECTORS + LARGE ARENA)
// ==========================================================================
const compareCombos = {};

function compareList() { return state.compare.mode === 'bat' ? state.batters : state.bowlers; }
function comparePlayer(id) { return id == null ? null : compareList().find(p => p.player_id === id) || null; }

// Searchable dropdown: type to filter, arrow keys + Enter, click to choose, x to clear.
function createCombo(rootId, slot) {
  const root = document.getElementById(rootId);
  const input = root.querySelector('.combo-input');
  const list = root.querySelector('.combo-list');
  const clearBtn = root.querySelector('.combo-clear');
  const other = slot === 'p1Id' ? 'p2Id' : 'p1Id';
  let items = [], idx = -1, typed = false;

  const label = () => { const p = comparePlayer(state.compare[slot]); return p ? `#${p.rank} ${p.name}` : ''; };
  const sync = () => { input.value = label(); clearBtn.hidden = state.compare[slot] == null; };
  const render = () => {
    const q = typed ? input.value.trim().toLowerCase() : '';
    items = compareList().filter(p => p.player_id !== state.compare[other] && (!q || p.name.toLowerCase().includes(q) || String(p.rank) === q.replace('#', '')));
    list.innerHTML = items.length
      ? items.map((p, i) => `<li role="option" id="${rootId}-opt-${i}" data-id="${p.player_id}" class="${i === idx ? 'hl' : ''}${p.player_id === state.compare[slot] ? ' sel' : ''}" aria-selected="${p.player_id === state.compare[slot]}"><span>#${p.rank} ${p.name}</span><span class="combo-meta">${formatNum(p.score, 1)}</span></li>`).join('')
      : '<li class="combo-none">No matching player</li>';
    if (idx >= 0) { input.setAttribute('aria-activedescendant', `${rootId}-opt-${idx}`); const li = list.children[idx]; if (li && li.scrollIntoView) li.scrollIntoView({ block: 'nearest' }); }
    else input.removeAttribute('aria-activedescendant');
  };
  const open = () => { render(); list.hidden = false; input.setAttribute('aria-expanded', 'true'); };
  const close = () => { list.hidden = true; idx = -1; typed = false; input.setAttribute('aria-expanded', 'false'); };
  const choose = (id) => {
    state.compare[slot] = id;
    close(); sync();
    Object.values(compareCombos).forEach(c => c.sync());
    renderComparisonArena();
  };

  input.addEventListener('focus', () => { typed = false; idx = -1; input.select(); open(); });
  input.addEventListener('click', () => { if (list.hidden) open(); });
  input.addEventListener('input', () => { typed = true; idx = -1; open(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); if (list.hidden) open(); idx = Math.min(items.length - 1, idx + 1); render(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); idx = Math.max(0, idx - 1); render(); }
    else if (e.key === 'Enter') { e.preventDefault(); const pick = items[idx >= 0 ? idx : (typed && items.length ? 0 : -1)]; if (pick) { choose(pick.player_id); input.blur(); } }
    else if (e.key === 'Escape') { close(); sync(); input.blur(); }
  });
  input.addEventListener('blur', () => { setTimeout(() => { close(); sync(); }, 120); });
  list.addEventListener('mousedown', (e) => {
    const li = e.target.closest('li[data-id]');
    if (!li) return;
    e.preventDefault();
    choose(parseInt(li.dataset.id, 10));
    input.blur();
  });
  clearBtn.addEventListener('click', () => choose(null));
  return { sync, close };
}

function setCompareMode(mode) {
  if (mode !== 'bat' && mode !== 'bowl') return;
  const changed = state.compare.mode !== mode;
  state.compare.mode = mode;
  if (changed) { state.compare.p1Id = null; state.compare.p2Id = null; } // batters and bowlers are never mixed
  const bat = document.getElementById('compare-mode-bat'), bowl = document.getElementById('compare-mode-bowl');
  if (bat && bowl) {
    bat.classList.toggle('active', mode === 'bat'); bowl.classList.toggle('active', mode === 'bowl');
    bat.setAttribute('aria-selected', mode === 'bat'); bowl.setAttribute('aria-selected', mode === 'bowl');
  }
  const noun = mode === 'bat' ? 'batter' : 'bowler';
  ['p1', 'p2'].forEach((k, i) => {
    const inp = document.getElementById(`compare-${k}-input`);
    if (inp) inp.placeholder = `Search a ${noun}...`;
    const h = document.getElementById(`compare-${k}-heading`);
    if (h) h.textContent = `${mode === 'bat' ? 'Batter' : 'Bowler'} ${i + 1}`;
  });
  Object.values(compareCombos).forEach(c => { c.close(); c.sync(); });
  renderComparisonArena();
}
window.setCompareMode = setCompareMode;

function initPlayerComparison() {
  compareCombos.p1 = createCombo('combo-p1', 'p1Id');
  compareCombos.p2 = createCombo('combo-p2', 'p2Id');
  const go = (mode) => {
    setCompareMode(mode);
    const id = mode === 'bat' ? 'sub-batter-comparison' : 'sub-bowler-comparison';
    NAV.current = id; setActiveNav(id, true);
    if (location.hash !== '#' + id) history.replaceState(null, '', '#' + id);
  };
  document.getElementById('compare-mode-bat').addEventListener('click', () => go('bat'));
  document.getElementById('compare-mode-bowl').addEventListener('click', () => go('bowl'));
  document.getElementById('reset-comparison-btn').addEventListener('click', () => {
    state.compare.p1Id = null; state.compare.p2Id = null;
    Object.values(compareCombos).forEach(c => { c.close(); c.sync(); });
    renderComparisonArena();
  });
  setCompareMode(state.compare.mode);
}

function renderComparisonArena() {
  const isBat = state.compare.mode === 'bat';
  const noun = isBat ? 'batter' : 'bowler';
  const p1 = comparePlayer(state.compare.p1Id), p2 = comparePlayer(state.compare.p2Id);

  [['p1', p1], ['p2', p2]].forEach(([k, p]) => {
    document.getElementById(`${k}-summary-name`).textContent = p ? `#${p.rank} ${p.name}` : 'No player selected';
    document.getElementById(`${k}-summary-badge`).innerHTML = p ? renderVerdictChip(p.verdict) : '';
  });

  const empty = document.getElementById('compare-empty-state');
  const body = document.getElementById('compare-results-body');
  if (!p1 || !p2) {
    ['radarChartInstance', 'compareBarChartInstance'].forEach(k => { if (state[k]) { state[k].destroy(); state[k] = null; } });
    body.hidden = true; empty.hidden = false;
    empty.textContent = !p1 && !p2 ? `Select two ${noun}s above to see the head-to-head comparison.`
      : `Now select ${!p1 ? `${isBat ? 'Batter' : 'Bowler'} 1` : `${isBat ? 'Batter' : 'Bowler'} 2`} to complete the comparison.`;
    return;
  }
  empty.hidden = true; body.hidden = false;

  const rate = p => isBat ? p.p_sr : p.p_econ, nrate = p => isBat ? p.np_sr : p.np_econ, rd = isBat ? 1 : 2;
  const outLabel = isBat ? 'Runs above expected / 100' : 'Runs saved vs expected / 100';
  document.getElementById('compare-title').textContent = `${p1.name} vs ${p2.name} (${isBat ? 'Batters' : 'Bowlers'})`;

  const kpi = (lab, a, b) => `
    <div class="compare-kpi-cell">
      <div class="compare-kpi-label">${lab}</div>
      <div class="compare-kpi-values"><span class="val-p1">${a}</span><span style="font-size:0.8rem;color:var(--text-muted);">vs</span><span class="val-p2">${b}</span></div>
    </div>`;
  document.getElementById('compare-kpi-row').innerHTML =
    kpi('Official Pressure Score', formatNum(p1.score, 1), formatNum(p2.score, 1)) +
    kpi(isBat ? 'Pressure Strike Rate' : 'Pressure Economy', formatNum(rate(p1), rd), formatNum(rate(p2), rd)) +
    kpi(outLabel, formatNum(p1.rae, 1), formatNum(p2.rae, 1)) +
    kpi('Consistency', `${formatNum(p1.cons, 1)}%`, `${formatNum(p2.cons, 1)}%`);

  const C1 = '#E60693', C2 = '#0077D8';
  const radarCanvas = document.getElementById('compareRadarChart');
  if (state.radarChartInstance) state.radarChartInstance.destroy();
  const pcs = p => [p.pc_output, p.pc_wickets, p.pc_lift, p.pc_consistency, p.pc_boundary, p.pc_dot].map(v => v == null ? 0 : v);
  state.radarChartInstance = new Chart(radarCanvas, {
    type: 'radar',
    data: {
      labels: ['Output', 'Wickets', 'Lift', 'Consistency', 'Boundary %', 'Dot ball %'],
      datasets: [
        { label: p1.name, data: pcs(p1), borderColor: C1, backgroundColor: 'rgba(230, 6, 147, 0.2)', borderWidth: 2.5, pointRadius: 4 },
        { label: p2.name, data: pcs(p2), borderColor: C2, backgroundColor: 'rgba(0, 119, 216, 0.2)', borderWidth: 2.5, pointRadius: 4 }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { r: { min: 0, max: 100, ticks: { stepSize: 20 } } } }
  });

  const barCanvas = document.getElementById('compareBarChart');
  if (state.compareBarChartInstance) state.compareBarChartInstance.destroy();
  const bars = p => [p.rae, p.delta, p.inn1_vs_exp, p.inn2_vs_exp].map(v => v == null ? null : +(+v).toFixed(1));
  state.compareBarChartInstance = new Chart(barCanvas, {
    type: 'bar',
    data: {
      labels: [isBat ? 'Runs above expected' : 'Runs saved', 'Lift vs own normal', '1st innings vs expected', 'Chase vs expected'],
      datasets: [
        { label: p1.name, data: bars(p1), backgroundColor: C1, borderRadius: 4 },
        { label: p2.name, data: bars(p2), backgroundColor: C2, borderRadius: 4 }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { title: { display: true, text: 'per 100 pressure balls' } } } }
  });

  const table = document.getElementById('compare-metrics-table');
  table.querySelector('thead').innerHTML = `<tr><th>Metric</th><th style="color:var(--rr-pink);">#${p1.rank} ${p1.name}</th><th style="color:var(--rr-royal-blue);">#${p2.rank} ${p2.name}</th></tr>`;
  const na = v => (v == null || Number.isNaN(v)) ? 'n/a' : v;
  const rows = [
    ['Official rank', `#${p1.rank}`, `#${p2.rank}`],
    ['Pressure Score', formatNum(p1.score, 1), formatNum(p2.score, 1)],
    ['Stability verdict', renderVerdictChip(p1.verdict), renderVerdictChip(p2.verdict)],
    ['Pressure balls', na(p1.p_balls), na(p2.p_balls)],
    ['Matches with pressure balls', na(p1.p_matches), na(p2.p_matches)],
    [isBat ? 'Pressure strike rate' : 'Pressure economy', formatNum(rate(p1), rd), formatNum(rate(p2), rd)],
    [isBat ? 'Normal strike rate' : 'Normal economy', formatNum(nrate(p1), rd), formatNum(nrate(p2), rd)],
    [isBat ? 'Dismissals under pressure' : 'Wickets under pressure', na(isBat ? p1.p_outs : p1.p_wk), na(isBat ? p2.p_outs : p2.p_wk)],
    [outLabel, formatNum(p1.rae, 1), formatNum(p2.rae, 1)],
    ['Wickets vs expected / 100', formatNum(p1.dae, 2), formatNum(p2.dae, 2)],
    ['Lift vs own normal level', formatNum(p1.delta, 1), formatNum(p2.delta, 1)],
    ['Consistency', `${formatNum(p1.cons, 1)}%`, `${formatNum(p2.cons, 1)}%`],
    ['1st innings vs expected / 100', formatNum(p1.inn1_vs_exp, 1), formatNum(p2.inn1_vs_exp, 1)],
    ['Chase vs expected / 100', formatNum(p1.inn2_vs_exp, 1), formatNum(p2.inn2_vs_exp, 1)],
    ['IPL share of pressure balls', `${formatNum(p1.ipl_pct, 1)}%`, `${formatNum(p2.ipl_pct, 1)}%`],
    ['Scenarios in top 10', `${na(p1.scen_top10)} / ${na(p1.scen_total)}`, `${na(p2.scen_top10)} / ${na(p2.scen_total)}`],
    ['Bootstrap top-10 %', `${formatNum(p1.boot_top10_pct, 1)}%`, `${formatNum(p2.boot_top10_pct, 1)}%`]
  ];
  table.querySelector('tbody').innerHTML = rows.map(r => `<tr><td><strong>${r[0]}</strong></td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join('');

  const hi = p1.score >= p2.score ? p1 : p2, lo = hi === p1 ? p2 : p1;
  const gap = Math.abs(p1.score - p2.score).toFixed(1);
  const more = p1.p_balls >= p2.p_balls ? p1 : p2, less = more === p1 ? p2 : p1;
  const steadier = p1.cons >= p2.cons ? p1 : p2, other = steadier === p1 ? p2 : p1;
  document.getElementById('compare-insights-text').innerHTML =
    `<strong>Summary:</strong> ${hi.name} has the higher official Pressure Score, by ${gap} points (rank #${hi.rank} against #${lo.rank}). ` +
    `${more.name} has the larger sample (${more.p_balls} pressure balls against ${less.p_balls}). ` +
    `${steadier.name} is the more consistent (${formatNum(steadier.cons, 1)}% against ${formatNum(other.cons, 1)}%). ` +
    `Verdicts: ${p1.name} is ${p1.verdict}, ${p2.name} is ${p2.verdict}.`;
}


// ==========================================================================
// 7. PRESSURE SECTION CHARTS
// ==========================================================================
function renderPressureSection() {
  const pOverCanvas = document.getElementById('pressureByOverChart');
  if (pOverCanvas && state.pressureByOver) {
    const overs = state.pressureByOver.map(r => `Over ${r.overid}`);
    const inn1 = state.pressureByOver.map(r => (r.inn1_share * 100).toFixed(1));
    const inn2 = state.pressureByOver.map(r => (r.inn2_share * 100).toFixed(1));

    state.pressureOverChartInstance = new Chart(pOverCanvas, {
      type: 'bar',
      data: {
        labels: overs,
        datasets: [
          { label: '1st Innings High-Pressure Share %', data: inn1, backgroundColor: '#0077D8' },
          { label: 'Chase High-Pressure Share %', data: inn2, backgroundColor: '#E60693' }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { title: { display: true, text: '% of deliveries classified high pressure' }, min: 0, max: 100 } }
      }
    });
  }

  // Pace vs Spin League table
  document.querySelector('#pace-spin-table tbody').innerHTML = state.paceSpin.map(r => `
    <tr>
      <td><strong>${r.pace_or_spin}</strong></td>
      <td><span class="chip ${r.HP ? 'chip-borderline' : 'chip-stable'}">${r.HP ? 'High Pressure' : 'Normal'}</span></td>
      <td>${r.balls.toLocaleString()}</td>
      <td>${r.runs.toLocaleString()}</td>
      <td>${r.wk.toLocaleString()}</td>
      <td><strong>${formatNum(r.econ, 2)}</strong></td>
      <td>${formatNum(r.balls_per_wkt, 1)}</td>
    </tr>
  `).join('');

  // Splits display
  document.getElementById('topic-splits-display-box').innerHTML = `
    <div class="card">
      <p class="card-intro">
        In first innings, pressure accumulates as the match nears completion (death overs 16–20 account for 78% of all 1st innings high-pressure balls). 
        In chases, pressure can strike at any phase depending on target run rate escalation and quick wicket clusters.
      </p>
    </div>
  `;

  // Timeline chart (default: Suryakumar Yadav)
  renderPressureResponseTimeline(state.inspectedBatterId, 'bat');
}

function renderPressureResponseTimeline(pid, type) {
  const list = type === 'bat' ? state.timeline.bat : state.timeline.bowl;
  const player = (type === 'bat' ? state.batters : state.bowlers).find(p => p.player_id === pid) || state.batters[0];
  const playerRows = list.filter(r => r.player_id === pid);

  const bands = ['0-20', '20-40', '40-60', '60-80', '80-100'];
  const playerRates = [];
  const leagueRates = [];
  const lowSampleBands = [];

  bands.forEach(b => {
    const row = playerRows.find(r => r.band === b);
    if (row) {
      playerRates.push(row.rate);
      leagueRates.push(row.league_rate);
      if (row.balls < 30) lowSampleBands.push(`${b} (${row.balls}b)`);
    } else {
      playerRates.push(null);
      leagueRates.push(null);
      lowSampleBands.push(`${b} (0b)`);
    }
  });

  const warnElem = document.getElementById('timeline-low-sample-warning');
  if (warnElem) {
    warnElem.innerHTML = lowSampleBands.length > 0 
      ? `<strong>Note:</strong> Low sample (&lt;30 balls) in bands: ${lowSampleBands.join(', ')} for ${player.name}.`
      : '';
  }

  const ctx = document.getElementById('playerTimelineChart');
  if (!ctx) return;
  if (state.timelineChartInstance) state.timelineChartInstance.destroy();

  state.timelineChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: bands,
      datasets: [
        {
          label: `${player.name} (${type === 'bat' ? 'Strike Rate' : 'Economy'})`,
          data: playerRates,
          borderColor: '#E60693',
          backgroundColor: '#E60693',
          tension: 0.25,
          borderWidth: 3,
          pointRadius: 5
        },
        {
          label: `League Benchmark (${type === 'bat' ? 'Strike Rate' : 'Economy'})`,
          data: leagueRates,
          borderColor: '#0077D8',
          backgroundColor: '#0077D8',
          borderDash: [5, 5],
          tension: 0.25,
          borderWidth: 2,
          pointRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { title: { display: true, text: type === 'bat' ? 'Strike Rate' : 'Economy Rate' } },
        x: { title: { display: true, text: 'Pressure Index (PI) Band' } }
      }
    }
  });
}

// ==========================================================================
// 8. ROBUSTNESS & WHAT-IF RECALIBRATION
// ==========================================================================
function initRobustnessAndWhatIf() {
  const sRae = document.getElementById('weight-rae');
  const sDae = document.getElementById('weight-dae');
  const sDelta = document.getElementById('weight-delta');
  const sCons = document.getElementById('weight-cons');

  const vRae = document.getElementById('val-rae');
  const vDae = document.getElementById('val-dae');
  const vDelta = document.getElementById('val-delta');
  const vCons = document.getElementById('val-cons');

  const updateSliders = () => {
    state.challengeWeights.rae = parseInt(sRae.value, 10);
    state.challengeWeights.dae = parseInt(sDae.value, 10);
    state.challengeWeights.delta = parseInt(sDelta.value, 10);
    state.challengeWeights.cons = parseInt(sCons.value, 10);

    vRae.textContent = state.challengeWeights.rae;
    vDae.textContent = state.challengeWeights.dae;
    vDelta.textContent = state.challengeWeights.delta;
    vCons.textContent = state.challengeWeights.cons;

    const total = state.challengeWeights.rae + state.challengeWeights.dae + state.challengeWeights.delta + state.challengeWeights.cons;
    const totalElem = document.getElementById('total-weight-display');
    const warnElem = document.getElementById('weight-warning');
    totalElem.textContent = `${total}%`;

    if (total === 100) {
      totalElem.className = 'weight-valid';
      warnElem.style.display = 'none';
    } else {
      totalElem.className = 'rank-down';
      warnElem.style.display = 'inline';
    }

    renderWhatIfTable();
  };

  [sRae, sDae, sDelta, sCons].forEach(s => s.addEventListener('input', updateSliders));

  document.getElementById('reset-weights-btn').onclick = () => {
    sRae.value = 40; sDae.value = 20; sDelta.value = 20; sCons.value = 20;
    updateSliders();
  };

  document.getElementById('challenge-type-bat').onclick = (e) => {
    state.challengeType = 'bat';
    e.target.classList.add('active');
    document.getElementById('challenge-type-bowl').classList.remove('active');
    renderWhatIfTable();
  };

  document.getElementById('challenge-type-bowl').onclick = (e) => {
    state.challengeType = 'bowl';
    e.target.classList.add('active');
    document.getElementById('challenge-type-bat').classList.remove('active');
    renderWhatIfTable();
  };

  renderWhatIfTable();
  initBootstrapChart();
  initHeatmap();
}

function renderWhatIfTable() {
  const isBat = state.challengeType === 'bat';
  const list = isBat ? state.batters : state.bowlers;

  const w1 = state.challengeWeights.rae / 100;
  const w2 = state.challengeWeights.dae / 100;
  const w3 = state.challengeWeights.delta / 100;
  const w4 = state.challengeWeights.cons / 100;

  const computed = list.map(p => {
    const whatIfScore = 50.0 + 15.0 * (w1 * p.z_rae + w2 * p.z_dae + w3 * p.z_delta + w4 * p.z_cons);
    return {
      player: p,
      officialRank: p.rank,
      officialScore: p.score,
      whatIfScore: whatIfScore
    };
  });

  computed.sort((a, b) => b.whatIfScore - a.whatIfScore);
  computed.forEach((item, index) => {
    item.whatIfRank = index + 1;
    item.rankDelta = item.officialRank - item.whatIfRank;
  });

  computed.sort((a, b) => a.officialRank - b.officialRank);

  document.querySelector('#whatif-table tbody').innerHTML = computed.slice(0, 25).map(item => {
    let deltaDisplay = `<span class="rank-same">-</span>`;
    if (item.rankDelta > 0) deltaDisplay = `<span class="rank-up">&uarr; +${item.rankDelta}</span>`;
    if (item.rankDelta < 0) deltaDisplay = `<span class="rank-down">&darr; ${item.rankDelta}</span>`;

    return `
      <tr>
        <td><strong>#${item.officialRank}</strong></td>
        <td><strong>${item.player.name}</strong></td>
        <td>${formatNum(item.officialScore, 1)}</td>
        <td><strong>${formatNum(item.whatIfScore, 1)}</strong></td>
        <td><strong>#${item.whatIfRank}</strong></td>
        <td>${deltaDisplay}</td>
      </tr>
    `;
  }).join('');
}

function initBootstrapChart() {
  const batBtn = document.getElementById('boot-type-bat');
  const bowlBtn = document.getElementById('boot-type-bowl');

  batBtn.onclick = () => {
    state.bootType = 'bat';
    batBtn.classList.add('active');
    bowlBtn.classList.remove('active');
    renderBootstrapChart();
  };

  bowlBtn.onclick = () => {
    state.bootType = 'bowl';
    bowlBtn.classList.add('active');
    batBtn.classList.remove('active');
    renderBootstrapChart();
  };

  renderBootstrapChart();
}

function renderBootstrapChart() {
  const isBat = state.bootType === 'bat';
  const list = (isBat ? state.batters : state.bowlers).slice(0, 15);
  const labels = list.map(p => `#${p.rank} ${p.name}`);
  const top10Pcts = list.map(p => p.boot_top10_pct || 0);

  const ctx = document.getElementById('bootstrapChart');
  if (!ctx) return;
  if (state.bootstrapChartInstance) state.bootstrapChartInstance.destroy();

  state.bootstrapChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Bootstrap Top-10 %',
          data: top10Pcts,
          backgroundColor: list.map(p => p.verdict === 'Stable' ? '#15803D' : (p.verdict === 'Moderate' ? '#B45309' : '#B91C1C')),
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100, title: { display: true, text: 'Bootstrap Top-10 Retention %' } },
        x: { ticks: { maxRotation: 45, minRotation: 45 } }
      }
    }
  });
}

function initHeatmap() {
  const batBtn = document.getElementById('heatmap-type-bat');
  const bowlBtn = document.getElementById('heatmap-type-bowl');

  batBtn.onclick = () => {
    state.heatmapType = 'bat';
    batBtn.classList.add('active');
    bowlBtn.classList.remove('active');
    renderHeatmap();
  };

  bowlBtn.onclick = () => {
    state.heatmapType = 'bowl';
    bowlBtn.classList.add('active');
    batBtn.classList.remove('active');
    renderHeatmap();
  };

  renderHeatmap();
}

function renderHeatmap() {
  const container = document.getElementById('heatmap-container');
  const isBat = state.heatmapType === 'bat';
  const robData = isBat ? state.robustness.bat : state.robustness.bowl;

  if (!robData || !robData.scenarios || !robData.rows) {
    container.innerHTML = '<p>Robustness data not available.</p>';
    return;
  }

  const scenarios = robData.scenarios;
  const rows = robData.rows;

  let html = `
    <table class="table heatmap-table">
      <thead>
        <tr>
          <th class="player-col">Official Rank & Player</th>
          ${scenarios.map(s => `<th>${s.name || s.id || s}</th>`).join('')}
        </tr>
      </thead>
      <tbody>
  `;

  rows.forEach((r, idx) => {
    const rankVal = r.rank || (idx + 1);
    html += `
      <tr>
        <td class="player-col">#${rankVal} ${r.name}</td>
        ${scenarios.map(s => {
          const sKey = typeof s === 'string' ? s : (s.name || s.id);
          const val = r[sKey];
          if (val === null || val === undefined) {
            return `<td class="cell-ineligible" title="Not eligible in this scenario">n/a</td>`;
          }
          let cls = 'cell-top10';
          if (val > 10 && val <= 20) cls = 'cell-11-20';
          if (val > 20) cls = 'cell-worse';
          return `<td class="${cls}">${val}</td>`;
        }).join('')}
      </tr>
    `;
  });

  html += '</tbody></table>';
  container.innerHTML = html;
}

// ==========================================================================
// 9. METHODOLOGY & DIAGNOSTICS
// ==========================================================================
function renderMethodology() {
  // 24 Context Baselines
  document.querySelector('#baselines-table tbody').innerHTML = state.baselines.map(r => `
    <tr>
      <td>Innings ${r.innings}</td>
      <td>${r.phase}</td>
      <td><span class="chip ${r.high_pressure ? 'chip-borderline' : 'chip-stable'}">${r.high_pressure ? 'Yes' : 'No'}</span></td>
      <td>${formatNum(r.e_runs, 3)}</td>
      <td>${formatNum(r.e_out, 4)}</td>
      <td>${(r.bat_balls || 0).toLocaleString()}</td>
      <td>${formatNum(r.e_conc, 3)}</td>
      <td>${formatNum(r.e_wk, 4)}</td>
      <td>${(r.bowl_balls || 0).toLocaleString()}</td>
    </tr>
  `).join('');

  // Feature Register
  document.querySelector('#features-table tbody').innerHTML = state.features.map(f => `
    <tr>
      <td><strong>${f.name}</strong></td>
      <td><span class="chip ${f.status === 'Core' ? 'chip-stable' : 'chip-moderate'}">${f.status}</span></td>
      <td style="white-space:normal;font-size:0.85rem;max-width:240px;">${f.purpose}</td>
      <td style="white-space:normal;font-size:0.82rem;font-family:monospace;max-width:220px;">${f.calculation}</td>
      <td>${f.source_columns}</td>
      <td style="white-space:normal;font-size:0.82rem;max-width:200px;color:#64748B;">${f.limitation}</td>
    </tr>
  `).join('');

  // Diagnostics
  const m = state.model;
  if (m) {
    const diag = m.diagnostics || {};
    document.getElementById('diagnostics-summary').innerHTML = `
      <div class="diag-card">
        <h4>Cross-Validated Win Probability AUC</h4>
        <ul class="diag-list">
          <li><span>1st Innings Model (CV-AUC):</span> <strong>${formatNum(m.wp_cv_auc?.inn1 || state.coverage?.auc_inn1_cv, 3)}</strong></li>
          <li><span>Chase Model (CV-AUC):</span> <strong>${formatNum(m.wp_cv_auc?.inn2 || state.coverage?.auc_inn2_cv, 3)}</strong></li>
          <li><span>High-Pressure Cutoff Inn 1:</span> <strong>Top 25% (PI &gt; ${formatNum(m.pressure_thresholds?.inn1, 1)})</strong></li>
          <li><span>High-Pressure Cutoff Inn 2:</span> <strong>Top 25% (PI &gt; ${formatNum(m.pressure_thresholds?.inn2, 1)})</strong></li>
        </ul>
      </div>
      <div class="diag-card">
        <h4>Component Weights & Effective Variance</h4>
        <ul class="diag-list">
          <li><span>RAE (Runs vs Expected):</span> <strong>40% nominal | ${formatNum(diag.effective_variance_share?.rae, 1)}% effective</strong></li>
          <li><span>DAE (Wickets vs Expected):</span> <strong>20% nominal | ${formatNum(diag.effective_variance_share?.dae, 1)}% effective</strong></li>
          <li><span>Delta (Pressure Lift):</span> <strong>20% nominal | ${formatNum(diag.effective_variance_share?.delta, 1)}% effective</strong></li>
          <li><span>Consistency:</span> <strong>20% nominal | ${formatNum(diag.effective_variance_share?.cons, 1)}% effective</strong></li>
        </ul>
      </div>
      <div class="diag-card">
        <h4>Split-Half Reliability Diagnostics</h4>
        <ul class="diag-list">
          <li><span>Batting Split-Half Correlation:</span> <strong>${formatNum(diag.split_half_correlation?.bat, 2)} (Weakly repeatable)</strong></li>
          <li><span>Bowling Split-Half Correlation:</span> <strong>${formatNum(diag.split_half_correlation?.bowl, 2)} (Moderate)</strong></li>
          <li><span>Component Cross-Correlations:</span> <strong>All |r| &lt; 0.25 (Orthogonal)</strong></li>
          <li><span>Par Run Rate Innings 1:</span> <strong>${formatNum(m.par_run_rate?.inn1, 2)} runs/over</strong></li>
        </ul>
      </div>
    `;
  }

  // Limitations
  document.getElementById('limitations-container').innerHTML = state.limitations.map(text => `<li>${text}</li>`).join('');
}

// ==========================================================================
// 10. NEAR MISSES & WATCHLIST
// ==========================================================================
function renderNearMissesAndWatchlist() {
  document.querySelector('#near-miss-batters-table tbody').innerHTML = state.nearMisses.bat.map(p => `
    <tr>
      <td><strong>#${p.rank}</strong></td>
      <td><strong>${p.name}</strong></td>
      <td>${formatNum(p.score, 1)}</td>
      <td>${renderVerdictChip(p.verdict)}</td>
      <td style="white-space:normal;font-size:0.85rem;max-width:320px;">${p.near_miss_reason || 'n/a'}</td>
    </tr>
  `).join('');

  document.querySelector('#near-miss-bowlers-table tbody').innerHTML = state.nearMisses.bowl.map(p => `
    <tr>
      <td><strong>#${p.rank}</strong></td>
      <td><strong>${p.name}</strong></td>
      <td>${formatNum(p.score, 1)}</td>
      <td>${renderVerdictChip(p.verdict)}</td>
      <td style="white-space:normal;font-size:0.85rem;max-width:320px;">${p.near_miss_reason || 'n/a'}</td>
    </tr>
  `).join('');

  const batWatch = state.watchlist.bat.map(p => ({ ...p, discipline: 'Batter' }));
  const bowlWatch = state.watchlist.bowl.map(p => ({ ...p, discipline: 'Bowler' }));
  document.querySelector('#watchlist-table tbody').innerHTML = [...batWatch, ...bowlWatch].map(p => `
    <tr>
      <td><span class="chip ${p.discipline === 'Batter' ? 'chip-moderate' : 'chip-stable'}">${p.discipline}</span></td>
      <td><strong>${p.name}</strong></td>
      <td>${p.p_balls} (Excluded &lt; 200b)</td>
      <td>${p.p_matches}</td>
      <td>${formatNum(p.rae, 2)}</td>
      <td>${formatNum(p.dae, 2)}</td>
      <td>${formatNum(p.delta, 2)}</td>
      <td>${formatNum(p.cons, 1)}%</td>
      <td><strong style="color:var(--rr-pink);">#${p.rank_if_150_12}</strong></td>
    </tr>
  `).join('');
}

// ==========================================================================
// 11. GLOSSARY MODAL
// ==========================================================================
function initGlossaryModal() {
  const modal = document.getElementById('glossary-modal');
  const closeBtn = document.getElementById('modal-close-btn');

  const closeModal = () => { modal.style.display = 'none'; };
  closeBtn.onclick = closeModal;
  modal.onclick = (e) => { if (e.target === modal) closeModal(); };
  window.onkeydown = (e) => { if (e.key === 'Escape' && modal.style.display !== 'none') closeModal(); };

  document.body.addEventListener('click', (e) => {
    const btn = e.target.closest('.info-btn');
    if (!btn) return;
    const metricKey = btn.dataset.metric;
    openGlossary(metricKey);
  });
}

function openGlossary(metricKey) {
  const modal = document.getElementById('glossary-modal');
  const mappedTitle = GLOSSARY_MAP[metricKey] || metricKey;

  let entry = state.glossary.find(g => 
    g.metric.toLowerCase() === mappedTitle.toLowerCase() ||
    g.metric.toLowerCase().includes(metricKey.toLowerCase())
  );

  if (!entry) entry = state.glossary[0];

  document.getElementById('modal-metric-name').textContent = entry.metric;
  document.getElementById('modal-def').textContent = entry.definition || 'n/a';
  document.getElementById('modal-formula').textContent = entry.formula || 'n/a';
  document.getElementById('modal-source').textContent = entry.source_columns || 'n/a';
  document.getElementById('modal-sample').textContent = entry.sample || 'n/a';
  document.getElementById('modal-limitation').textContent = entry.limitation || 'n/a';

  modal.style.display = 'flex';
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', loadAllData); else loadAllData();

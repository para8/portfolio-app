import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

// ── Auth state ────────────────────────────────────────────────────────────────
let _supabase = null;
let _session = null;

// ── State ─────────────────────────────────────────────────────────────────────
const state = {
  positions: null,    // full GET /positions response
  transactions: [],
  tickers: [],
  prices: {},
  pricesDetail: [],
  brokers: [],
  categories: [],
  sectors: [],
  fxRate: 86,
  txnTickerFilter: null,
};

let activeView = 'positions';
let txnDaysFilter = '';
let pieChart = null;
let expandedGroups = new Set();

// ── Helpers ───────────────────────────────────────────────────────────────────
const displayName = (t) => t?.short_name || t?.name || '';

// ── Inline add category/sector ────────────────────────────────────────────────
const COLOR_PALETTE = ['#facc15','#93c5fd','#d8b4fe','#fdba74','#fbbf24','#a5f3fc','#6ee7b7','#f87171','#34d399','#60a5fa'];

function pickAutoColor(type) {
  const used = (type === 'category' ? state.categories : state.sectors).map(x => x.color);
  return COLOR_PALETTE.find(c => !used.includes(c)) ?? COLOR_PALETTE[used.length % COLOR_PALETTE.length];
}

function refreshAllSelectsOfType(type, newId) {
  const items = type === 'category' ? state.categories : state.sectors;
  const selector = type === 'category'
    ? '#new-ticker-category, .resolve-category'
    : '#new-ticker-sector, .resolve-sector';
  document.querySelectorAll(selector).forEach(sel => {
    sel.innerHTML = items.map(x =>
      `<option value="${x.id}" ${x.id === newId ? 'selected' : ''}>${x.name}</option>`
    ).join('');
  });
}

function attachSelectAdd(selectEl, type) {
  if (!selectEl || selectEl.dataset.addAttached) return;
  selectEl.dataset.addAttached = '1';

  // Wrap select + "+" button
  const wrap = document.createElement('div');
  wrap.className = 'select-add-wrap';
  selectEl.parentNode.insertBefore(wrap, selectEl);
  wrap.appendChild(selectEl);

  const plusBtn = document.createElement('button');
  plusBtn.type = 'button';
  plusBtn.className = 'btn-add-opt';
  plusBtn.title = `Add new ${type}`;
  plusBtn.textContent = '+';
  wrap.appendChild(plusBtn);

  // Inline form (hidden by default)
  const inline = document.createElement('div');
  inline.className = 'add-opt-inline';
  inline.innerHTML = `
    <input type="text" class="add-opt-input" placeholder="New ${type} name">
    <span class="add-opt-error"></span>
    <button type="button" class="add-opt-submit" disabled>Add</button>
  `;
  wrap.parentNode.insertBefore(inline, wrap.nextSibling);

  const input = inline.querySelector('.add-opt-input');
  const error = inline.querySelector('.add-opt-error');
  const submitBtn = inline.querySelector('.add-opt-submit');

  plusBtn.addEventListener('click', () => {
    const open = inline.classList.toggle('open');
    if (open) { input.value = ''; error.textContent = ''; submitBtn.disabled = true; input.focus(); }
  });

  input.addEventListener('input', () => {
    const val = input.value.trim();
    const items = type === 'category' ? state.categories : state.sectors;
    const exists = items.some(x => x.name.toLowerCase() === val.toLowerCase());
    if (!val) {
      error.textContent = ''; submitBtn.disabled = true;
    } else if (exists) {
      error.textContent = 'Already exists'; submitBtn.disabled = true;
    } else {
      error.textContent = ''; submitBtn.disabled = false;
    }
  });

  submitBtn.addEventListener('click', async () => {
    const name = input.value.trim();
    if (!name) return;
    const color = pickAutoColor(type);
    try {
      submitBtn.disabled = true;
      const created = await api('POST', `/${type === 'category' ? 'categories' : 'sectors'}`, { name, color });
      if (type === 'category') {
        state.categories = await api('GET', '/categories');
      } else {
        state.sectors = await api('GET', '/sectors');
      }
      refreshAllSelectsOfType(type, created.id);
      inline.classList.remove('open');
    } catch (err) {
      error.textContent = err.message || 'Error saving';
      submitBtn.disabled = false;
    }
  });
}

// ── Formatting ─────────────────────────────────────────────────────────────────
const inr = v => v == null ? '—' : '₹' + Math.round(Math.abs(v)).toLocaleString('en-IN');
const inrK = v => {
  if (v == null) return '—';
  const a = Math.abs(v);
  if (a >= 1e7) return '₹' + (a / 1e7).toFixed(2) + ' Cr';
  if (a >= 1e5) return '₹' + (a / 1e5).toFixed(1) + 'L';
  return '₹' + Math.round(a).toLocaleString('en-IN');
};
const pct = v => v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(1) + '%';
const f4 = v => +parseFloat(v).toFixed(4);

// ── Import state ──────────────────────────────────────────────────────────────
let importParseResult = null;

// ── API helpers ───────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const headers = { 'Content-Type': 'application/json' };
  if (_session?.access_token) {
    headers['Authorization'] = 'Bearer ' + _session.access_token;
  }
  const opts = { method, headers };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch('/api/v1' + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function apiUpload(path, formData) {
  const headers = {};
  if (_session?.access_token) headers['Authorization'] = 'Bearer ' + _session.access_token;
  const res = await fetch('/api/v1' + path, { method: 'POST', headers, body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const msg = Array.isArray(detail)
      ? detail.map(e => e.msg || JSON.stringify(e)).join('; ')
      : (detail || res.statusText);
    throw new Error(msg);
  }
  return res.json();
}

function showToast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  el.style.display = 'block';
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.style.display = 'none'; }, 3000);
}

// ── Auth screen helpers ────────────────────────────────────────────────────────
function showAuthScreen() {
  document.getElementById('auth-screen').style.display = '';
  document.getElementById('app-screen').style.display = 'none';
}

function showApp() {
  document.getElementById('auth-screen').style.display = 'none';
  document.getElementById('app-screen').style.display = '';
}

function setAuthMsg(id, msg, isError = false) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = 'auth-msg ' + (isError ? 'auth-msg-error' : 'auth-msg-ok');
}

// ── Auth boot ─────────────────────────────────────────────────────────────────
async function bootAuth() {
  // Fetch Supabase public config from backend
  let cfg;
  try {
    cfg = await fetch('/api/v1/auth-config').then(r => r.json());
  } catch (e) {
    console.error('Failed to fetch auth-config', e);
    showAuthScreen();
    setAuthMsg('login-msg', 'Could not connect to server. Try refreshing.', true);
    return;
  }

  _supabase = createClient(cfg.supabase_url, cfg.supabase_anon_key);

  // Check for an existing session
  const { data: { session } } = await _supabase.auth.getSession();
  if (session) {
    _session = session;
    showApp();
    init();
  } else {
    showAuthScreen();
  }

  // React to future auth state changes (login, logout, token refresh)
  _supabase.auth.onAuthStateChange(async (event, session) => {
    const prevSession = _session;
    _session = session;
    if (session && !prevSession) {
      // Just logged in — load app
      showApp();
      // Reset state so we don't show stale data from another user
      Object.assign(state, {
        positions: null, transactions: [], tickers: [], prices: {},
        pricesDetail: [], brokers: [], categories: [], sectors: [],
        fxRate: 86, txnTickerFilter: null,
      });
      expandedGroups = new Set();
      init();
    } else if (!session && prevSession) {
      // Logged out — show auth screen
      showAuthScreen();
    }
  });

  setupAuthForms();
}

// ── Auth form handlers ────────────────────────────────────────────────────────
function setupAuthForms() {
  // Tab switching
  document.querySelectorAll('.auth-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const isLogin = tab.dataset.authTab === 'login';
      document.getElementById('auth-form-login').style.display = isLogin ? '' : 'none';
      document.getElementById('auth-form-signup').style.display = isLogin ? 'none' : '';
    });
  });

  // Login
  document.getElementById('btn-login').addEventListener('click', async () => {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    if (!email || !password) {
      setAuthMsg('login-msg', 'Email and password are required.', true);
      return;
    }
    const btn = document.getElementById('btn-login');
    btn.disabled = true;
    btn.textContent = 'Signing in…';
    setAuthMsg('login-msg', '');

    const { error } = await _supabase.auth.signInWithPassword({ email, password });
    btn.disabled = false;
    btn.textContent = 'Sign in';

    if (error) {
      setAuthMsg('login-msg', error.message, true);
    }
    // On success, onAuthStateChange fires and shows the app
  });

  // Enter key on login form
  ['login-email', 'login-password'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') document.getElementById('btn-login').click();
    });
  });

  // Signup
  document.getElementById('btn-signup').addEventListener('click', async () => {
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    if (!email || !password) {
      setAuthMsg('signup-msg', 'Email and password are required.', true);
      return;
    }
    if (password.length < 6) {
      setAuthMsg('signup-msg', 'Password must be at least 6 characters.', true);
      return;
    }
    const btn = document.getElementById('btn-signup');
    btn.disabled = true;
    btn.textContent = 'Creating account…';
    setAuthMsg('signup-msg', '');

    const { error } = await _supabase.auth.signUp({ email, password });
    btn.disabled = false;
    btn.textContent = 'Create account';

    if (error) {
      setAuthMsg('signup-msg', error.message, true);
    } else {
      setAuthMsg('signup-msg',
        '✓ Check your email for a confirmation link before signing in.', false);
      document.getElementById('signup-email').value = '';
      document.getElementById('signup-password').value = '';
    }
  });

  // Enter key on signup form
  ['signup-email', 'signup-password'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') document.getElementById('btn-signup').click();
    });
  });

  // Logout
  document.getElementById('btn-logout').addEventListener('click', async () => {
    await _supabase.auth.signOut();
    // onAuthStateChange handles the UI transition
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  // Wire up all UI event handlers immediately — no dependency on data
  setupNav();
  setupFxInput();
  setupTransactionFilters();
  setupAddForm();

  // Read stored FX rate
  try {
    const cfg = await api('GET', '/config/fx_rate_usd_inr');
    state.fxRate = parseFloat(cfg.value) || 86;
    document.getElementById('fx-rate').value = state.fxRate;
  } catch (_) {}

  // Fetch all data — wrapped so a failure doesn't leave UI dead
  try {
    await Promise.all([
      fetchPositions(),
      api('GET', '/transactions').then(d => { state.transactions = d; }),
      api('GET', '/tickers').then(d => { state.tickers = d; }),
      api('GET', '/prices').then(d => { state.prices = d; }),
      api('GET', '/prices/detail').then(d => { state.pricesDetail = d; }),
      api('GET', '/brokers').then(d => { state.brokers = d; }),
      api('GET', '/categories').then(d => { state.categories = d; }),
      api('GET', '/sectors').then(d => { state.sectors = d; }),
    ]);
  } catch (err) {
    console.error('Data load error:', err);
  }

  renderAll();
}

async function fetchPositions(fxOverride) {
  const url = fxOverride != null ? `/positions?fx_rate=${fxOverride}` : '/positions';
  state.positions = await api('GET', url);
  if (state.positions) state.fxRate = state.positions.fx_rate;
}

function renderAll() {
  renderPositions();
  renderInsights();
  renderTransactions();
  renderPrices();
  renderAddForm();
}

// ── Navigation ─────────────────────────────────────────────────────────────────
function setupNav() {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', () => {
      const view = el.dataset.view;
      if (view) showView(view);
    });
  });
}

function showView(view, tickerFilter) {
  activeView = view;
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('view-' + view)?.classList.add('active');
  document.querySelector(`.nav-item[data-view="${view}"]`)?.classList.add('active');
  if (view === 'transactions' && tickerFilter) {
    state.txnTickerFilter = tickerFilter;
    renderTransactions();
  }
}

// ── FX rate ───────────────────────────────────────────────────────────────────
function setupFxInput() {
  const input = document.getElementById('fx-rate');
  let debounce;

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    debounce = setTimeout(async () => {
      const v = parseFloat(input.value);
      if (!v || v <= 0) return;
      await fetchPositions(v);
      renderPositions();
      renderInsights();
      document.getElementById('fx-note').textContent = 'updated ' + new Date().toLocaleTimeString();
    }, 400);
  });

  input.addEventListener('blur', async () => {
    const v = parseFloat(input.value);
    if (!v || v <= 0) return;
    await api('PUT', '/config/fx_rate_usd_inr', { value: String(v) }).catch(() => {});
  });
}

// ── Positions ─────────────────────────────────────────────────────────────────
function renderPositions() {
  const p = state.positions;
  if (!p) return;

  const s = p.summary;

  // Summary strip
  document.getElementById('s-inv').textContent = inrK(s.total_invested_inr);
  document.getElementById('s-val').textContent = inrK(s.total_value_inr);
  document.getElementById('s-val-sub').textContent = `${s.priced_count}/${s.total_count} instruments priced`;

  const pnlEl = document.getElementById('s-pnl');
  if (s.total_pnl_inr != null) {
    pnlEl.textContent = (s.total_pnl_inr >= 0 ? '+' : '-') + inrK(Math.abs(s.total_pnl_inr));
    pnlEl.className = 'stat-value ' + (s.total_pnl_inr >= 0 ? 'pos' : 'neg');
    document.getElementById('s-pnl-sub').textContent = pct(s.total_pnl_pct);
  } else {
    pnlEl.textContent = '—';
    pnlEl.className = 'stat-value';
  }

  document.getElementById('s-fx').textContent = s.usd_exposure_pct != null ? s.usd_exposure_pct.toFixed(1) + '%' : '—';
  document.getElementById('s-fx-sub').textContent = `@ ₹${state.fxRate}`;

  const totalPos = p.by_category.reduce((s, g) => s + g.positions.length, 0);
  document.getElementById('pos-sub').textContent =
    `${state.transactions.length} transactions · ${totalPos} positions · ${p.by_category.length} categories`;

  // Table
  const tbody = document.getElementById('pos-tbody');
  tbody.innerHTML = '';

  for (const group of p.by_category) {
    const isExpanded = expandedGroups.has(group.category);
    const multiPos = group.positions.length > 1;
    const portPct = group.weight_pct;

    // Build category pill style
    const catColor = group.color;
    const pillStyle = `background:${catColor}18;color:${catColor};border-color:${catColor}40`;

    // Group row
    const tr = document.createElement('tr');
    tr.className = 'group-row' + (isExpanded ? ' expanded' : '');
    tr.innerHTML = `
      <td>
        <div class="group-name-cell">
          <div class="group-label">
            ${multiPos ? `<span class="expand-icon">▶</span>` : '<span style="width:10px;display:inline-block"></span>'}
            <span class="group-name">${group.category}</span>
          </div>
          <div class="group-meta">
            ${multiPos ? `<span class="count-pill">${group.positions.length} positions</span>` : `<span style="font-size:12px;color:var(--muted)">${group.positions[0] ? displayName(group.positions[0]) : ''}</span>`}
            <div class="weight-bar-wrap"><div class="weight-bar" style="width:${Math.min((portPct || 0) * 2.5, 100)}%"></div></div>
          </div>
        </div>
      </td>
      <td><span class="cat-pill" style="${pillStyle}">${group.category}</span></td>
      <td class="num">${portPct != null ? portPct.toFixed(1) + '%' : '—'}</td>
      <td class="num">${inrK(group.invested_inr)}</td>
      <td class="num">${group.value_inr != null ? inrK(group.value_inr) : '<span style="color:var(--muted)">—</span>'}</td>
      <td class="num">${renderPnlCell(group.pnl_inr, group.pnl_pct)}</td>
      <td class="num">
        ${!multiPos && group.positions[0] ? `<span style="font-family:var(--mono);font-size:12px;color:var(--muted2)">${group.positions[0].currency === 'USD' ? '$' : '₹'}${group.positions[0].avg_buy_price.toFixed(2)}</span>` : '<span style="color:var(--muted)">—</span>'}
      </td>
      <td class="num">
        ${!multiPos && group.positions[0] ? `<span style="font-family:var(--mono);font-size:12px;color:var(--muted2)">${f4(group.positions[0].held_units)}</span>` : '<span style="color:var(--muted)">—</span>'}
      </td>
    `;

    if (multiPos) {
      tr.addEventListener('click', () => {
        if (expandedGroups.has(group.category)) expandedGroups.delete(group.category);
        else expandedGroups.add(group.category);
        renderPositions();
      });
    } else if (group.positions[0]) {
      tr.addEventListener('click', () => showView('transactions', group.positions[0].ticker_id));
    }

    tbody.appendChild(tr);

    // Sub-rows when expanded
    if (isExpanded && multiPos) {
      for (const pos of group.positions) {
        const sub = document.createElement('tr');
        sub.className = 'sub-row';
        sub.innerHTML = `
          <td colspan="2">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:11px;color:var(--muted2)">${displayName(pos)}</span>
            </div>
          </td>
          <td class="num" style="color:var(--muted);font-size:10px">${pos.weight_pct != null ? pos.weight_pct.toFixed(1) + '%' : '—'}</td>
          <td class="num">${inrK(pos.invested_inr)}</td>
          <td class="num">${pos.value_inr != null ? inrK(pos.value_inr) : '<span style="color:var(--muted)">—</span>'}</td>
          <td class="num">${renderPnlCell(pos.pnl_inr, pos.pnl_pct)}</td>
          <td class="num"><span style="font-family:var(--mono);font-size:12px;color:var(--muted2)">${pos.currency === 'USD' ? '$' : '₹'}${pos.avg_buy_price.toFixed(2)}</span></td>
          <td class="num"><span style="font-family:var(--mono);font-size:12px;color:var(--muted2)">${f4(pos.held_units)}</span></td>
        `;
        sub.addEventListener('click', () => showView('transactions', pos.ticker_id));
        tbody.appendChild(sub);
      }
    }
  }

  // Allocation bars
  buildAllocBars(p);
}

function renderPnlCell(pnlInr, pnlPct) {
  if (pnlInr == null) return '<span style="color:var(--muted);font-size:11px">no price</span>';
  const cls = pnlInr >= 0 ? 'pos' : 'neg';
  return `<div class="pnl-cell">
    <div class="pnl-amt ${cls}">${pnlInr >= 0 ? '+' : '-'}${inrK(Math.abs(pnlInr))}</div>
    <div class="pnl-pct ${cls}">${pct(pnlPct)}</div>
  </div>`;
}

function buildAllocBars(p) {
  // By category
  const catEl = document.getElementById('alloc-cat');
  catEl.innerHTML = '';
  for (const g of p.by_category) {
    const pv = g.weight_pct ?? 0;
    catEl.innerHTML += `
      <div class="alloc-row">
        <div class="alloc-label">${g.category}</div>
        <div class="alloc-bar-wrap"><div class="alloc-bar" style="width:${pv.toFixed(1)}%;background:${g.color}"></div></div>
        <div class="alloc-pct" style="color:${g.color}">${pv.toFixed(1)}%</div>
      </div>`;
  }

  // By sector — aggregate from positions
  const sectorMap = {};
  for (const g of p.by_category) {
    for (const pos of g.positions) {
      const sec = pos.sector || 'Others';
      if (!sectorMap[sec]) sectorMap[sec] = { value: 0, invested: 0 };
      sectorMap[sec].value += pos.value_inr ?? pos.invested_inr ?? 0;
      sectorMap[sec].invested += pos.invested_inr ?? 0;
    }
  }
  const totalVal = Object.values(sectorMap).reduce((s, v) => s + v.value, 0);
  const sectorEl = document.getElementById('alloc-sector');
  sectorEl.innerHTML = '';
  const sectorColors = {};
  for (const s of state.sectors) sectorColors[s.name] = s.color;

  for (const [name, vals] of Object.entries(sectorMap).sort((a, b) => b[1].value - a[1].value)) {
    const pv = totalVal > 0 ? (vals.value / totalVal * 100) : 0;
    const col = sectorColors[name] || '#9a9aa3';
    sectorEl.innerHTML += `
      <div class="alloc-row">
        <div class="alloc-label">${name}</div>
        <div class="alloc-bar-wrap"><div class="alloc-bar" style="width:${pv.toFixed(1)}%;background:${col}"></div></div>
        <div class="alloc-pct" style="color:${col}">${pv.toFixed(1)}%</div>
      </div>`;
  }
}

// ── Insights ───────────────────────────────────────────────────────────────────
function renderInsights() {
  if (!state.positions) return;
  buildPieChart();
  buildSectorBars();
}

function buildPieChart() {
  const p = state.positions;
  const entries = p.by_category.map(g => ({
    label: g.category,
    color: g.color,
    val: g.value_inr ?? g.invested_inr ?? 0,
  })).sort((a, b) => b.val - a.val);

  const total = entries.reduce((s, e) => s + e.val, 0);

  if (pieChart) { pieChart.destroy(); pieChart = null; }

  const canvas = document.getElementById('alloc-pie');
  pieChart = new Chart(canvas.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: entries.map(e => e.label),
      datasets: [{
        data: entries.map(e => e.val),
        backgroundColor: entries.map(e => e.color + 'bb'),
        borderColor: entries.map(e => e.color),
        borderWidth: 1.5,
        hoverBackgroundColor: entries.map(e => e.color),
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: false,
      cutout: '60%',
      animation: { duration: 500 },
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      onHover: (event, elements) => {
        canvas.style.cursor = elements.length ? 'pointer' : 'default';
        if (elements.length) {
          const i = elements[0].index;
          setPieCenter(entries[i], total);
          document.querySelectorAll('.pie-legend-item').forEach((el, j) =>
            el.classList.toggle('active', i === j));
        } else {
          resetPieCenter(total);
          document.querySelectorAll('.pie-legend-item').forEach(el => el.classList.remove('active'));
        }
      },
    },
  });

  resetPieCenter(total);

  // Legend
  const legendEl = document.getElementById('pie-legend');
  legendEl.innerHTML = entries.map((e, i) => {
    const pv = total > 0 ? (e.val / total * 100) : 0;
    return `
      <div class="pie-legend-item" data-idx="${i}">
        <div class="pie-legend-dot" style="background:${e.color}"></div>
        <div class="pie-legend-name">${e.label}</div>
        <div class="pie-legend-right">
          <div class="pie-legend-pct" style="color:${e.color}">${pv.toFixed(1)}%</div>
          <div class="pie-legend-val">${inrK(e.val)}</div>
        </div>
      </div>`;
  }).join('');

  legendEl.querySelectorAll('.pie-legend-item').forEach((el, i) => {
    el.addEventListener('mouseenter', () => {
      setPieCenter(entries[i], total);
      el.classList.add('active');
    });
    el.addEventListener('mouseleave', () => {
      resetPieCenter(total);
      el.classList.remove('active');
    });
  });
}

function setPieCenter(entry, total) {
  const pv = total > 0 ? (entry.val / total * 100) : 0;
  document.getElementById('apc-label').textContent = entry.label;
  document.getElementById('apc-pct').textContent = pv.toFixed(1) + '%';
  document.getElementById('apc-pct').style.color = entry.color;
  document.getElementById('apc-val').textContent = inrK(entry.val);
}

function resetPieCenter(total) {
  document.getElementById('apc-label').textContent = 'total value';
  document.getElementById('apc-pct').textContent = '100%';
  document.getElementById('apc-pct').style.color = 'var(--accent)';
  document.getElementById('apc-val').textContent = inrK(total);
}

function buildSectorBars() {
  const p = state.positions;
  const sectorMap = {};
  for (const g of p.by_category) {
    for (const pos of g.positions) {
      const sec = pos.sector || 'Others';
      if (!sectorMap[sec]) sectorMap[sec] = { value: 0 };
      sectorMap[sec].value += pos.value_inr ?? pos.invested_inr ?? 0;
    }
  }

  const sectorColors = {};
  for (const s of state.sectors) sectorColors[s.name] = s.color;

  const totalVal = Object.values(sectorMap).reduce((s, v) => s + v.value, 0);
  const el = document.getElementById('sector-bars');
  el.innerHTML = '';

  for (const [name, vals] of Object.entries(sectorMap).sort((a, b) => b[1].value - a[1].value)) {
    const pv = totalVal > 0 ? (vals.value / totalVal * 100) : 0;
    const col = sectorColors[name] || '#9a9aa3';
    el.innerHTML += `
      <div class="sector-row">
        <div class="sector-name">${name}</div>
        <div class="sector-bar-wrap"><div class="sector-bar" style="width:${pv.toFixed(1)}%;background:${col}"></div></div>
        <div class="sector-pct">${pv.toFixed(1)}%</div>
        <div class="sector-val">${inrK(vals.value)}</div>
      </div>`;
  }
}

// ── Transactions ───────────────────────────────────────────────────────────────
function setupTransactionFilters() {
  const brokerSel = document.getElementById('txn-broker-filter');
  const typeSel = document.getElementById('txn-type-filter');
  const daysBtns = document.querySelectorAll('.filter-btn[data-days]');

  brokerSel.addEventListener('change', renderTransactions);
  typeSel.addEventListener('change', renderTransactions);
  daysBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      daysBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      txnDaysFilter = btn.dataset.days;
      renderTransactions();
    });
  });
}

function renderTransactions() {
  // Populate broker dropdown
  const brokerSel = document.getElementById('txn-broker-filter');
  const selectedBroker = brokerSel.value;
  if (brokerSel.options.length <= 1) {
    for (const b of state.brokers) {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = b.name;
      brokerSel.appendChild(opt);
    }
  }
  brokerSel.value = selectedBroker;

  const brokerFilter = parseInt(brokerSel.value) || null;
  const typeFilter = document.getElementById('txn-type-filter').value;
  const days = txnDaysFilter ? parseInt(txnDaysFilter) : null;

  let txns = state.transactions;

  if (state.txnTickerFilter) {
    txns = txns.filter(t => t.ticker_id === state.txnTickerFilter);
  }
  if (brokerFilter) txns = txns.filter(t => t.broker_id === brokerFilter);
  if (typeFilter) txns = txns.filter(t => t.type === typeFilter);
  if (days) {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    txns = txns.filter(t => new Date(t.date) >= cutoff);
  }

  const filterTicker = state.txnTickerFilter
    ? state.tickers.find(tk => tk.id === state.txnTickerFilter) : null;
  document.getElementById('txn-sub').textContent =
    `${txns.length} transactions${filterTicker ? ' · filtered by ' + displayName(filterTicker) : ''}`;

  const tbody = document.getElementById('txn-tbody');
  tbody.innerHTML = '';

  for (const t of txns) {
    const tr = document.createElement('tr');
    const ticker = state.tickers.find(tk => tk.id === t.ticker_id);
    const cur = ticker?.currency || 'INR';
    const sym = cur === 'USD' ? '$' : '₹';
    tr.innerHTML = `
      <td style="font-family:var(--mono);font-size:12px;color:var(--muted2)">${t.date}</td>
      <td>
        <span style="font-size:12px;color:var(--muted2)">${t.ticker_name || displayName(ticker)}</span>
      </td>
      <td><span class="txn-type type-${t.type}">${t.type}</span></td>
      <td class="num">${f4(t.units)}</td>
      <td class="num">${sym}${t.price.toFixed(2)}</td>
      <td class="num">${sym}${Math.round(t.amount).toLocaleString('en-IN')}</td>
      <td><span class="broker-pill">${t.broker_name || '—'}</span></td>
      <td><button class="delete-btn" data-id="${t.id}" title="Delete">✕</button></td>
    `;
    tbody.appendChild(tr);
  }

  tbody.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!confirm('Delete this transaction?')) return;
      try {
        await api('DELETE', `/transactions/${btn.dataset.id}`);
        state.transactions = state.transactions.filter(t => t.id !== parseInt(btn.dataset.id));
        await fetchPositions();
        renderAll();
        showToast('Transaction deleted');
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      }
    });
  });
}

// ── Prices ─────────────────────────────────────────────────────────────────────
function renderPrices() {
  const tbody = document.getElementById('prices-tbody');
  tbody.innerHTML = '';

  // Sort by updated_at ASC (stalest first), nulls first
  const sorted = [...state.pricesDetail].sort((a, b) => {
    if (!a.updated_at) return -1;
    if (!b.updated_at) return 1;
    return a.updated_at.localeCompare(b.updated_at);
  });

  for (const p of sorted) {
    const ticker = state.tickers.find(t => t.id === p.ticker_id);
    const cur = ticker?.currency || 'INR';
    const sym = cur === 'USD' ? '$' : '₹';
    const isStale = !p.updated_at;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-size:12px;color:var(--muted2)">${displayName(ticker) || '—'}</td>
      <td style="font-family:var(--mono);font-size:11px;color:var(--muted)">${cur}</td>
      <td class="num">
        ${sym}<input class="price-input${isStale ? ' price-stale' : ''}"
          type="number" step="any" value="${p.price}"
          data-ticker-id="${p.ticker_id}" data-orig="${p.price}">
      </td>
      <td style="font-family:var(--mono);font-size:11px;color:var(--muted)">
        ${p.updated_at ? new Date(p.updated_at).toLocaleString() : '<span style="color:var(--red)">never</span>'}
      </td>
    `;
    tbody.appendChild(tr);
  }

  tbody.querySelectorAll('.price-input').forEach(input => {
    input.addEventListener('blur', async () => {
      const v = parseFloat(input.value);
      if (!v || v <= 0 || v === parseFloat(input.dataset.orig)) return;
      try {
        await api('PUT', `/prices/${input.dataset.tickerId}`, { price: v });
        input.dataset.orig = v;
        input.classList.remove('price-stale');
        // Refresh positions
        await fetchPositions();
        await api('GET', '/prices').then(d => { state.prices = d; });
        await api('GET', '/prices/detail').then(d => { state.pricesDetail = d; });
        renderPositions();
        renderInsights();
        const updatedTicker = state.tickers.find(t => t.id === parseInt(input.dataset.tickerId));
        showToast(`Price updated: ${displayName(updatedTicker)}`);
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      }
    });
  });
}

// ── Add Form ───────────────────────────────────────────────────────────────────
function renderAddForm() {
  // Populate category dropdown
  const catSel = document.getElementById('new-ticker-category');
  catSel.innerHTML = '';
  for (const c of state.categories) {
    catSel.innerHTML += `<option value="${c.id}">${c.name}</option>`;
  }
  attachSelectAdd(catSel, 'category');

  // Populate sector dropdown
  const secSel = document.getElementById('new-ticker-sector');
  secSel.innerHTML = '';
  for (const s of state.sectors) {
    secSel.innerHTML += `<option value="${s.id}">${s.name}</option>`;
  }
  attachSelectAdd(secSel, 'sector');

  // Populate ticker dropdown for transaction
  const tkSel = document.getElementById('new-txn-ticker');
  tkSel.innerHTML = '';
  for (const t of [...state.tickers].sort((a, b) => displayName(a).localeCompare(displayName(b)))) {
    tkSel.innerHTML += `<option value="${t.id}" data-currency="${t.currency}">${displayName(t)}</option>`;
  }

  // Populate broker dropdown for transaction
  const brSel = document.getElementById('new-txn-broker');
  brSel.innerHTML = '';
  for (const b of state.brokers) {
    brSel.innerHTML += `<option value="${b.id}">${b.name}</option>`;
  }

  // Set today's date
  document.getElementById('new-txn-date').value = new Date().toISOString().slice(0, 10);

  // Sync currency display
  function syncCurrency() {
    const opt = tkSel.options[tkSel.selectedIndex];
    document.getElementById('new-txn-currency').value = opt?.dataset.currency || '';
    updatePreview();
  }
  tkSel.addEventListener('change', syncCurrency);
  syncCurrency();

  // Live preview
  function updatePreview() {
    const units = parseFloat(document.getElementById('new-txn-units').value) || 0;
    const price = parseFloat(document.getElementById('new-txn-price').value) || 0;
    const amount = units * price;
    const opt = tkSel.options[tkSel.selectedIndex];
    const cur = opt?.dataset.currency || 'INR';
    const sym = cur === 'USD' ? '$' : '₹';

    document.getElementById('prev-amount').textContent = amount > 0 ? `${sym}${amount.toFixed(2)}` : '—';
    document.getElementById('prev-currency').textContent = cur;
    document.getElementById('prev-inr').textContent =
      amount > 0 ? inrK(cur === 'USD' ? amount * state.fxRate : amount) : '—';
  }

  document.getElementById('new-txn-units').addEventListener('input', updatePreview);
  document.getElementById('new-txn-price').addEventListener('input', updatePreview);

}

function setupAddForm() {
  // Tab switching
  document.querySelectorAll('.add-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.add-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const isTxn = tab.dataset.tab === 'transaction';
      document.getElementById('add-ticker-form').style.display = tab.dataset.tab === 'ticker' ? '' : 'none';
      document.getElementById('add-txn-form').style.display = isTxn ? '' : 'none';
      document.getElementById('import-upload-card').style.display = isTxn ? '' : 'none';
      document.getElementById('import-review-card').style.display = 'none';
      document.getElementById('import-divider').style.display = isTxn ? '' : 'none';
    });
  });

  // Add ticker
  document.getElementById('btn-add-ticker').addEventListener('click', async () => {
    const name = document.getElementById('new-ticker-name').value.trim();
    const short_name = document.getElementById('new-ticker-display-name').value.trim() || null;
    const currency = document.getElementById('new-ticker-currency').value;
    const category_id = parseInt(document.getElementById('new-ticker-category').value);
    const sector_id = parseInt(document.getElementById('new-ticker-sector').value);

    if (!name) return showToast('Name is required', 'error');

    try {
      await api('POST', '/tickers', { name, short_name, currency, category_id, sector_id });
      state.tickers = await api('GET', '/tickers');
      renderAddForm();
      showToast(`Ticker "${name}" added`);
      document.getElementById('new-ticker-name').value = '';
      document.getElementById('new-ticker-display-name').value = '';
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  });

  // Add transaction
  document.getElementById('btn-add-txn').addEventListener('click', async () => {
    const ticker_id = parseInt(document.getElementById('new-txn-ticker').value);
    const type = document.getElementById('new-txn-type').value;
    const date = document.getElementById('new-txn-date').value;
    const units = parseFloat(document.getElementById('new-txn-units').value);
    const price = parseFloat(document.getElementById('new-txn-price').value);
    const broker_id = parseInt(document.getElementById('new-txn-broker').value);

    if (!ticker_id || !date || !units || !price) return showToast('All fields required', 'error');

    try {
      await api('POST', '/transactions', { ticker_id, type, date, units, price, broker_id });
      const [txns] = await Promise.all([
        api('GET', '/transactions'),
        fetchPositions(),
      ]);
      state.transactions = txns;
      renderAll();
      const txnTicker = state.tickers.find(t => t.id === ticker_id);
      showToast(`Transaction added: ${type} ${units} ${displayName(txnTicker)}`);
      document.getElementById('new-txn-units').value = '';
      document.getElementById('new-txn-price').value = '';
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  });

  setupImportSection();
}

// ── Import flow ───────────────────────────────────────────────────────────────
function setupImportSection() {
  // Parse file
  document.getElementById('btn-parse-file').onclick = async () => {
    const fileInput = document.getElementById('import-file');
    const currency = document.getElementById('import-currency').value;
    if (!fileInput.files.length) return showToast('Please select a file', 'error');

    const btn = document.getElementById('btn-parse-file');
    btn.disabled = true;
    btn.textContent = 'Parsing…';
    try {
      const fd = new FormData();
      fd.append('file', fileInput.files[0]);
      fd.append('currency', currency);
      importParseResult = await apiUpload('/import/parse', fd);
      renderImportReview(importParseResult, currency);
    } catch (err) {
      showToast('Parse error: ' + err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Parse file';
    }
  };

  // Back button
  document.getElementById('btn-import-back').onclick = () => {
    document.getElementById('import-review-card').style.display = 'none';
    document.getElementById('import-upload-card').style.display = '';
  };
}

function renderImportReview(result, currency) {
  const total = result.transactions.length;
  const dupes = result.transactions.filter(t => t.status === 'duplicate').length;
  const newCount = total - dupes;
  const newFunds = result.unresolved_funds.length;

  // Summary banner
  document.getElementById('import-summary-banner').innerHTML =
    `<strong>${total}</strong> transactions found &nbsp;·&nbsp; ` +
    `<strong>${dupes}</strong> duplicates &nbsp;·&nbsp; ` +
    `<strong>${newFunds}</strong> new fund${newFunds !== 1 ? 's' : ''}`;

  // Unresolved fund panels
  const unresolvedEl = document.getElementById('import-unresolved');
  unresolvedEl.innerHTML = '';
  for (const fundName of result.unresolved_funds) {
    const panel = document.createElement('div');
    panel.className = 'import-unresolved-panel';
    panel.dataset.fund = fundName;
    const catOptions = state.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    const secOptions = state.sectors.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
    panel.innerHTML = `
      <div class="fund-name">⚠ Unresolved: <strong>${fundName}</strong></div>
      <div class="form-grid">
        <div class="form-group">
          <label>Short name <span style="opacity:.5">(optional)</span></label>
          <input type="text" class="resolve-display-name" placeholder="Abbreviated name">
        </div>
        <div class="form-group">
          <label>Category <span style="color:var(--red)">*</span></label>
          <select class="resolve-category">${catOptions}</select>
        </div>
        <div class="form-group">
          <label>Sector <span style="color:var(--red)">*</span></label>
          <select class="resolve-sector">${secOptions}</select>
        </div>
      </div>`;
    panel.querySelectorAll('input, select').forEach(el => el.addEventListener('input', updateImportConfirmBtn));
    unresolvedEl.appendChild(panel);
    attachSelectAdd(panel.querySelector('.resolve-category'), 'category');
    attachSelectAdd(panel.querySelector('.resolve-sector'), 'sector');
  }

  // Transaction table
  const tbody = document.getElementById('import-txn-tbody');
  tbody.innerHTML = '';
  result.transactions.forEach((t, i) => {
    const isDupe = t.status === 'duplicate';
    const tr = document.createElement('tr');
    if (isDupe) tr.classList.add('is-duplicate');
    tr.innerHTML = `
      <td><input type="checkbox" data-idx="${i}" ${isDupe ? '' : 'checked'} ${isDupe ? 'disabled' : ''}></td>
      <td style="font-family:var(--mono);font-size:11px">${t.date}</td>
      <td style="font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${t.name}">${t.name}</td>
      <td><span class="txn-type type-${t.type}">${t.type}</span></td>
      <td class="num" style="font-family:var(--mono);font-size:11px">${t.units.toFixed(3)}</td>
      <td class="num" style="font-family:var(--mono);font-size:11px">${t.price.toFixed(3)}</td>
      <td class="num" style="font-family:var(--mono);font-size:11px">${Math.round(t.amount).toLocaleString('en-IN')}</td>
      <td style="font-size:11px;color:var(--muted)">${t.currency}</td>
      <td><span class="status-${t.status}">${t.status}</span></td>`;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('input[type=checkbox]').forEach(cb =>
    cb.addEventListener('change', updateImportConfirmBtn)
  );

  // Show review, hide upload
  document.getElementById('import-upload-card').style.display = 'none';
  document.getElementById('import-review-card').style.display = '';
  updateImportConfirmBtn();

  // Confirm handler (set fresh each render)
  const confirmBtn = document.getElementById('btn-import-confirm');
  confirmBtn.onclick = async () => {
    const checkedBoxes = [...tbody.querySelectorAll('input[type=checkbox]:checked')];
    const checkedTxns = checkedBoxes.map(cb => {
      const t = result.transactions[parseInt(cb.dataset.idx)];
      return { fund_name: t.name, date: t.date, type: t.type, units: t.units, price: t.price, amount: t.amount };
    });

    const newTickers = [...unresolvedEl.querySelectorAll('.import-unresolved-panel')].map(panel => ({
      name: panel.dataset.fund,
      short_name: panel.querySelector('.resolve-display-name').value.trim() || null,
      category_id: parseInt(panel.querySelector('.resolve-category').value),
      sector_id: parseInt(panel.querySelector('.resolve-sector').value),
    }));

    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Importing…';
    try {
      const res = await api('POST', '/import/confirm', {
        currency,
        new_tickers: newTickers,
        transactions: checkedTxns,
      });
      showToast(`${res.imported} imported · ${res.skipped} skipped`);
      // Refresh data and reset to upload view
      const [txns] = await Promise.all([api('GET', '/transactions'), fetchPositions()]);
      state.transactions = txns;
      if (activeView === 'transactions') renderTransactions();
      state.tickers = await api('GET', '/tickers');
      importParseResult = null;
      document.getElementById('import-review-card').style.display = 'none';
      document.getElementById('import-upload-card').style.display = '';
      document.getElementById('import-file').value = '';
    } catch (err) {
      showToast('Import error: ' + err.message, 'error');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.textContent = updateImportConfirmBtn() || 'Import transactions';
    }
  };
}

function updateImportConfirmBtn() {
  const tbody = document.getElementById('import-txn-tbody');
  const unresolvedEl = document.getElementById('import-unresolved');
  if (!tbody) return;

  const checkedCount = tbody.querySelectorAll('input[type=checkbox]:checked').length;

  // Check all unresolved panels have a category selected
  const panels = [...unresolvedEl.querySelectorAll('.import-unresolved-panel')];
  const allResolved = panels.every(panel =>
    panel.querySelector('.resolve-category').value
  );

  const btn = document.getElementById('btn-import-confirm');
  if (!btn) return;
  btn.disabled = checkedCount === 0 || !allResolved;
  btn.textContent = `Import ${checkedCount} transaction${checkedCount !== 1 ? 's' : ''}`;
  return btn.textContent;
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', bootAuth);

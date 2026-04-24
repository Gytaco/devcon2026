#!/usr/bin/env python3
"""
transform.py
Converts report.html → index.html:
  • Autodesk light theme (white/blue brand palette)
  • AUTODESK | DevCon 2026 nav branding
  • Replaces the broken 78-column matrix with 4 JS-built aggregate tables
  • Pagefind full-text search integration
  • Improved per-video search (all card text, not just title)
  • Hash-based deep linking (#video-ID auto-opens card)
"""
import re, os, sys, html as html_lib
# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE  = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(HERE, "report.html")
DEST  = os.path.join(HERE, "index.html")

# ─────────────────────────────────────────────────────────────────────────────
NEW_CSS = """<style>
  :root {
    --bg:#FAFBFD; --surface:#FFFFFF; --surface2:#EEF2F7; --border:#DDE3EC;
    --text:#1F2937; --muted:#6B7280;
    --primary:#1858A8; --accent:#0070C0;
    --green:#007A33; --yellow:#B45309; --orange:#E56000;
    --red:#C0392B; --purple:#7B2FBE; --pink:#BE185D;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,"Segoe UI",Arial,sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.6}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline;color:var(--primary)}
  h2{font-size:1.2rem;font-weight:700}
  h3{font-size:1rem;font-weight:600;color:var(--primary);margin-bottom:8px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{background:var(--surface2);padding:8px 12px;text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border)}
  td{padding:8px 12px;border-bottom:1px solid var(--border);vertical-align:top}
  tr:hover td{background:#F0F5FF}

  /* Chips */
  .chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;margin:2px}
  .chip-theme  {background:#EBF2FF;color:#1858A8}
  .chip-client {background:#E6F7F2;color:#006B5B}
  .chip-product{background:#FFF0E6;color:#C04A00}
  .chip-ai     {background:#F3EFFE;color:#6B21A8}
  .chip-demo   {background:#FFFBEB;color:#92400E;border:1px solid #FCD34D}
  .chip-slides {background:#EBF2FF;color:#1858A8;border:1px solid #BFDBFE}
  .chip-code   {background:#ECFDF5;color:#065F46;border:1px solid #6EE7B7}
  .chip-ui     {background:#FFF7ED;color:#9A3412;border:1px solid #FED7AA}
  .chip-data   {background:#F3EFFE;color:#6B21A8;border:1px solid #E9D5FF}
  .chip-diagram{background:#FDF2F8;color:#9D174D;border:1px solid #FBCFE8}

  /* Nav */
  #nav{position:sticky;top:0;z-index:100;background:#FFFFFF;border-bottom:1px solid var(--border);box-shadow:0 1px 4px rgba(0,0,0,.06);display:flex;align-items:center;padding:0 24px;gap:0}
  .brand{display:flex;align-items:center;margin-right:28px;padding:14px 0;white-space:nowrap;gap:0}
  .brand-adesk{font-weight:800;font-size:.95rem;letter-spacing:.06em;color:#1F2937}
  .brand-sep{color:var(--primary);font-weight:300;font-size:1.3rem;margin:0 9px;line-height:1}
  .brand-event{font-size:.85rem;font-weight:600;color:var(--primary)}
  .tab-btn{padding:14px 18px;cursor:pointer;border:none;background:none;color:var(--muted);font-size:14px;font-weight:500;border-bottom:3px solid transparent;transition:all .15s}
  .tab-btn:hover{color:var(--text)}
  .tab-btn.active{color:var(--primary);border-bottom-color:var(--primary);font-weight:600}
  .nav-search-btn{margin-left:auto;cursor:pointer;padding:6px 14px;border:1px solid var(--border);border-radius:6px;font-size:13px;color:var(--muted);background:var(--surface2);transition:all .15s;white-space:nowrap;user-select:none}
  .nav-search-btn:hover{border-color:var(--primary);color:var(--primary)}
  #nav .meta{font-size:12px;color:var(--muted);margin-left:16px;white-space:nowrap}

  /* Pagefind overlay */
  #pf-overlay{position:fixed;inset:0;background:rgba(15,23,42,.55);z-index:999;display:flex;align-items:flex-start;justify-content:center;padding-top:72px}
  #pf-box{background:#FFF;border-radius:12px;padding:24px;width:100%;max-width:640px;box-shadow:0 24px 64px rgba(0,0,0,.18);position:relative}
  #pf-close{position:absolute;top:10px;right:14px;cursor:pointer;font-size:20px;color:var(--muted);background:none;border:none;line-height:1;padding:4px}
  #pf-close:hover{color:var(--text)}
  #pf-note{font-size:11px;color:#9CA3AF;margin-top:10px;text-align:center}
  #pf-note a{color:#9CA3AF}
  #pf-note code{background:#F3F4F6;padding:1px 5px;border-radius:3px;font-size:10px}

  /* Tab panels */
  .tab-panel{display:none}
  .tab-panel.active{display:block}

  /* Layout */
  .container{max-width:1400px;margin:0 auto;padding:24px}
  .section{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
  .section-title{font-size:1.05rem;font-weight:700;margin-bottom:16px;color:var(--text);display:flex;align-items:center;gap:8px}

  /* Executive summary */
  #exec-summary p{color:var(--muted);line-height:1.8}

  /* Stats */
  .stats{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px}
  .stat-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px 22px;flex:1;min-width:120px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
  .stat-num{font-size:2rem;font-weight:800;color:var(--primary);line-height:1}
  .stat-label{font-size:12px;color:var(--muted);margin-top:4px;font-weight:500}

  /* Aggregate tables */
  .agg-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:20px}
  .agg-card{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:16px}
  .agg-card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
  .agg-card-title{font-size:.95rem;font-weight:700;color:var(--text)}
  .count-badge{background:var(--primary);color:#FFF;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px}
  .agg-filter{width:100%;padding:6px 10px;margin-bottom:10px;border:1px solid var(--border);border-radius:6px;font-size:13px;color:var(--text);background:var(--surface)}
  .agg-filter:focus{outline:none;border-color:var(--primary)}
  .agg-table{width:100%;border-collapse:collapse;font-size:13px}
  .agg-table th{background:var(--surface2);padding:6px 10px;text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border);white-space:nowrap;user-select:none}
  .agg-table td{padding:6px 10px;border-bottom:1px solid var(--border);vertical-align:top}
  .agg-table tbody tr:hover td{background:#EEF5FF}
  .sort-arrow{font-size:10px;color:var(--muted);margin-left:2px}
  .agg-name{cursor:pointer;color:var(--accent);font-weight:500}
  .agg-name:hover{text-decoration:underline;color:var(--primary)}

  /* Per-video */
  .video-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;margin-bottom:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)}
  .video-header{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer;background:var(--surface);border-bottom:1px solid transparent;transition:background .15s}
  .video-header:hover{background:#F5F8FF}
  .video-header.open{border-bottom-color:var(--border);background:#F5F8FF}
  .video-header .arrow{color:var(--muted);font-size:12px;margin-left:auto;transition:transform .2s}
  .video-header.open .arrow{transform:rotate(90deg)}
  .video-date{font-size:12px;color:var(--muted);white-space:nowrap}
  .video-body{display:none;padding:20px}
  .video-body.open{display:block}
  .video-summary{color:var(--muted);margin-bottom:16px;line-height:1.7}

  /* Demo timestamps */
  .demo-list{list-style:none}
  .demo-list li{padding:6px 0;border-bottom:1px solid var(--border);display:flex;gap:12px;align-items:flex-start}
  .demo-list li:last-child{border-bottom:none}
  .ts-link{font-family:monospace;font-size:12px;color:var(--yellow);white-space:nowrap;font-weight:600}
  .demo-desc{color:var(--muted)}

  /* Frames */
  .frames-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:8px}
  .frame-card{background:var(--surface2);border:1px solid var(--border);border-radius:6px;overflow:hidden}
  .frame-card img{width:100%;height:160px;object-fit:cover;display:block}
  .frame-info{padding:10px 12px}
  .frame-ts{font-size:11px;font-family:monospace;margin-bottom:4px;color:var(--muted)}
  .frame-desc{font-size:12px;color:var(--muted);margin:4px 0;line-height:1.5}
  .frame-products{font-size:11px;color:var(--orange);font-weight:600}

  /* Transcript */
  .transcript-toggle{display:flex;align-items:center;gap:8px;cursor:pointer;color:var(--muted);font-size:13px;padding:8px 0;user-select:none}
  .transcript-toggle:hover{color:var(--text)}
  .transcript-body{max-height:400px;overflow-y:auto;padding:12px;background:var(--surface2);border-radius:6px;margin-top:8px;font-size:13px;line-height:1.7;display:none;border:1px solid var(--border)}
  .transcript-body.open{display:block}
  .seg{padding:3px 0}
  .seg.demo-highlight{background:rgba(180,83,9,.07);border-left:3px solid var(--yellow);padding-left:6px;border-radius:2px}
  .seg-ts{font-family:monospace;font-size:11px;margin-right:6px;color:var(--yellow);font-weight:600}

  /* Sidebar */
  #pv-layout{display:flex;gap:20px}
  #pv-sidebar{width:220px;flex-shrink:0;position:sticky;top:65px;align-self:flex-start;max-height:calc(100vh - 90px);overflow-y:auto;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px}
  #pv-sidebar a{display:block;padding:5px 8px;border-radius:4px;font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  #pv-sidebar a:hover{background:#EEF2FF;color:var(--primary);text-decoration:none}
  #pv-content{flex:1;min-width:0}

  /* Search */
  .search-wrap{position:relative;margin-bottom:8px}
  .search-box{width:100%;padding:9px 12px 9px 36px;background:var(--surface);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:13px}
  .search-box:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(24,88,168,.1)}
  .search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:14px;pointer-events:none}
  .search-meta{font-size:12px;color:var(--muted);margin-bottom:14px}

  /* Badges */
  .badge{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
  .badge-api    {background:var(--orange)}
  .badge-product{background:var(--primary)}
  .badge-llm    {background:var(--purple)}
  .badge-rag    {background:var(--pink)}
  .badge-ml     {background:var(--green)}
  .badge-agent  {background:var(--yellow)}
  .badge-other  {background:var(--muted)}

  /* Hide old matrix */
  .matrix-wrapper{display:none!important}

  @media(max-width:768px){
    #pv-layout{flex-direction:column}
    #pv-sidebar{width:100%;position:static}
    .frames-grid{grid-template-columns:1fr}
    .stats{flex-direction:column}
    .agg-grid{grid-template-columns:1fr}
  }
</style>"""

# ─────────────────────────────────────────────────────────────────────────────
NEW_NAV = """<!-- NAV -->
<nav id="nav">
  <div class="brand">
    <span class="brand-adesk">AUTODESK</span>
    <span class="brand-sep">|</span>
    <span class="brand-event">DevCon 2026</span>
  </div>
  <button class="tab-btn active" onclick="switchTab('combined')">Summaries</button>
  <button class="tab-btn" onclick="switchTab('perVideo')">Session Explorer</button>
  <div class="nav-search-btn" onclick="togglePagefindSearch()">&#128269;&nbsp; Search all content</div>
  <div class="meta">78 sessions &nbsp;&middot;&nbsp; April 2026</div>
</nav>

<!-- Pagefind full-text search overlay -->
<div id="pf-overlay" style="display:none">
  <div id="pf-box">
    <button id="pf-close" onclick="togglePagefindSearch()" title="Close (Esc)">&#x2715;</button>
    <div id="pf-search"></div>
    <p id="pf-note">
      Powered by <a href="https://pagefind.app" target="_blank">Pagefind</a> &nbsp;&middot;&nbsp;
      Build index: <code>npx pagefind --site .</code>
    </p>
  </div>
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
AGG_SECTION = """
  <!-- Aggregate Intelligence Tables -->
  <div class="section" id="agg-section">
    <div class="section-title">&#128202; Session Intelligence &mdash; Full Breakdown</div>
    <p style="color:var(--muted);margin-bottom:20px;font-size:13px;line-height:1.7">
      Every topic, product, client, and AI technology that appeared across all 78 DevCon 2026 sessions, ranked by frequency.
      <strong>Click any item name</strong> to jump to matching sessions in the Session Explorer.
    </p>
    <div class="agg-grid">

      <div class="agg-card">
        <div class="agg-card-header">
          <span class="agg-card-title">&#127991;&nbsp; Topics &amp; Themes</span>
          <span class="count-badge" id="count-themes">&#8230;</span>
        </div>
        <div id="agg-themes"><p style="color:var(--muted);font-size:12px;padding:8px 0">Building&hellip;</p></div>
      </div>

      <div class="agg-card">
        <div class="agg-card-header">
          <span class="agg-card-title">&#128295;&nbsp; Autodesk Products &amp; APIs</span>
          <span class="count-badge" id="count-products">&#8230;</span>
        </div>
        <div id="agg-products"><p style="color:var(--muted);font-size:12px;padding:8px 0">Building&hellip;</p></div>
      </div>

      <div class="agg-card">
        <div class="agg-card-header">
          <span class="agg-card-title">&#127970;&nbsp; Clients &amp; Partners</span>
          <span class="count-badge" id="count-clients">&#8230;</span>
        </div>
        <div id="agg-clients"><p style="color:var(--muted);font-size:12px;padding:8px 0">Building&hellip;</p></div>
      </div>

      <div class="agg-card">
        <div class="agg-card-header">
          <span class="agg-card-title">&#129302;&nbsp; AI Technologies</span>
          <span class="count-badge" id="count-ai">&#8230;</span>
        </div>
        <div id="agg-ai"><p style="color:var(--muted);font-size:12px;padding:8px 0">Building&hellip;</p></div>
      </div>

    </div>
  </div>
"""

# ─────────────────────────────────────────────────────────────────────────────
NEW_EXEC_SUMMARY_P = """DevCon 2026 brought together <strong>78 sessions</strong> from Autodesk partners, clients, and the developer community — showcasing real-world applications of AI, automation, and data across AEC and manufacturing. Sessions range from hands-on MCP server workshops to enterprise-scale deployments at organisations including Sweco, Bosch, Deutsche Bahn, and BCA Singapore. AI agents, LLMs, and the Autodesk Platform Services (APS) ecosystem feature prominently, with partners demonstrating measurable productivity gains across BIM automation, sustainability reporting, construction safety, and digital twin integration. Use the <strong>Session Intelligence</strong> tables below to identify which clients attended, which Autodesk products are gaining developer momentum, and which business problems are being solved through the APS ecosystem. Open any session to read its summary and watch key demo moments directly on YouTube."""

OLD_EXEC_SUMMARY_P = "Across the analyzed videos, there is a strong focus on integrating AI technologies in architecture, engineering, and construction workflows to enhance automation, sustainability, and data management. Key themes include the utilization of digital twins for real-time data integration, improving sustainability in construction, and automating project management tasks. Companies like Sweco and Bosch are prominent, showcasing their collaborative efforts with Autodesk products such as APS, Revit, and Fusion. AI technologies like GPT and AI agents are consistently employed to support decision-making, process automation, and increased efficiency in design and construction workflows."

# ─────────────────────────────────────────────────────────────────────────────
NEW_JS = """<script>
// ── Tab switching ─────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}

// ── Card open/close ───────────────────────────────────────────────────────
function toggleCard(id) {
  document.getElementById('hdr-'  + id).classList.toggle('open');
  document.getElementById('body-' + id).classList.toggle('open');
}

// ── Open card by ID and scroll to it (used from aggregate tables) ─────────
function openAndScrollTo(id) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-perVideo').classList.add('active');
  document.querySelectorAll('.tab-btn')[1].classList.add('active');
  setTimeout(function() {
    var card = document.getElementById('video-' + id);
    if (!card) return;
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
    var hdr  = document.getElementById('hdr-'  + id);
    var body = document.getElementById('body-' + id);
    if (hdr && body && !body.classList.contains('open')) {
      hdr.classList.add('open');
      body.classList.add('open');
    }
  }, 50);
  return false;
}

// ── Transcript toggle ─────────────────────────────────────────────────────
function toggleTranscript(id) {
  var body  = document.getElementById('tr-' + id);
  var arrow = document.getElementById('tr-arrow-' + id);
  body.classList.toggle('open');
  arrow.textContent = body.classList.contains('open') ? '▼' : '▶';
}

// ── Video search — searches ALL text in each card ─────────────────────────
var _totalCards = 0;
function filterVideos(query) {
  var q = (query || '').toLowerCase().trim();
  var visible = 0;
  document.querySelectorAll('#pv-content .video-card').forEach(function(card) {
    var show = !q || card.textContent.toLowerCase().includes(q);
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  document.querySelectorAll('#pv-sidebar a').forEach(function(a) {
    var href = a.getAttribute('href') || '';
    if (href.startsWith('#video-')) {
      var c = document.getElementById('video-' + href.slice(7));
      a.style.display = (c && c.style.display === 'none') ? 'none' : '';
    }
  });
  var meta = document.getElementById('search-count');
  if (meta) {
    meta.textContent = q
      ? visible + ' of ' + _totalCards + ' sessions match'
      : _totalCards + ' sessions';
  }
}

// ── Aggregate table: filter-and-navigate ─────────────────────────────────
// IMPORTANT: called via element.dataset.filter to avoid HTML attribute quoting issues
function filterAndGo(query) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-perVideo').classList.add('active');
  document.querySelectorAll('.tab-btn')[1].classList.add('active');
  var box = document.getElementById('video-search');
  if (box) { box.value = query; filterVideos(query); }
  setTimeout(function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (box) box.focus();
  }, 80);
}

// ── Aggregate table: per-table text filter ────────────────────────────────
function filterAggTable(input) {
  var q = input.value.toLowerCase().trim();
  var tbl = input.parentElement.querySelector('.agg-table');
  if (!tbl) return;
  tbl.querySelectorAll('tbody tr').forEach(function(row) {
    row.style.display = (!q || row.textContent.toLowerCase().includes(q)) ? '' : 'none';
  });
}

// ── Aggregate table: column sort ──────────────────────────────────────────
function sortAggTable(th, colIdx) {
  var tbl   = th.closest('table');
  var tbody = tbl.querySelector('tbody');
  var rows  = Array.from(tbody.querySelectorAll('tr'));
  var prevCol = parseInt(tbl.dataset.sortCol || '-1');
  var prevDir = tbl.dataset.sortDir || 'desc';
  var dir = (prevCol === colIdx && prevDir === 'desc') ? 'asc' : 'desc';
  tbl.dataset.sortDir = dir;
  tbl.dataset.sortCol = colIdx;
  rows.sort(function(a, b) {
    var av = (a.cells[colIdx] || {}).textContent.trim();
    var bv = (b.cells[colIdx] || {}).textContent.trim();
    var an = parseFloat(av), bn = parseFloat(bv);
    var cmp = (!isNaN(an) && !isNaN(bn)) ? (an - bn) : av.localeCompare(bv);
    return dir === 'asc' ? cmp : -cmp;
  });
  tbl.querySelectorAll('.sort-arrow').forEach(s => s.textContent = '↕');
  var arr = th.querySelector('.sort-arrow');
  if (arr) arr.textContent = dir === 'asc' ? '▲' : '▼';
  rows.forEach(r => tbody.appendChild(r));
}

// ── Pagefind overlay ──────────────────────────────────────────────────────
var _pfInit = false;
function togglePagefindSearch() {
  var ov = document.getElementById('pf-overlay');
  var show = ov.style.display === 'none' || !ov.style.display;
  ov.style.display = show ? 'flex' : 'none';
  if (show && !_pfInit && window.PagefindUI) {
    // Derive bundlePath relative to this page so it works on GitHub Pages
    // subdirectories (e.g. /repo-name/pagefind/) as well as at root.
    var bundlePath = window.location.pathname.replace(/[^/]*$/, '') + 'pagefind/';
    new PagefindUI({
      element: '#pf-search',
      showSubResults: true,
      excerptLength: 20,
      highlightParam: 'highlight',
      bundlePath: bundlePath
    });
    _pfInit = true;
  }
  if (show) {
    setTimeout(function() {
      var inp = document.querySelector('#pf-search input');
      if (inp) inp.focus();
    }, 120);
  }
}

// ── Keyboard shortcuts ─────────────────────────────────────────────────────
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var ov = document.getElementById('pf-overlay');
    if (ov && ov.style.display !== 'none') { ov.style.display = 'none'; return; }
    var box = document.getElementById('video-search');
    if (box && box.value) { box.value = ''; filterVideos(''); return; }
  }
  if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
    e.preventDefault();
    var box = document.getElementById('video-search');
    if (box) {
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-perVideo').classList.add('active');
      document.querySelectorAll('.tab-btn')[1].classList.add('active');
      box.focus();
    }
  }
});

// ── Chip normalisation ────────────────────────────────────────────────────
// Runs at page-load and rewrites verbose AI-generated chip text into clean
// canonical group names so the aggregate tables are actually readable and
// clicking a row correctly filters sessions in the Session Explorer.
function normalizeTheme(raw) {
  var t = raw.toLowerCase();
  if (/\bmcp\b|model context protocol/.test(t))                                    return 'MCP & APS Integration';
  if (/digital twin|facility manag|intelligent operat/.test(t))                    return 'Digital Twins & Facility Management';
  if (/sustainab|carbon|climate|green build|digital product passport/.test(t))     return 'Sustainability & Carbon';
  if (/bim.*qualit|bim.*compli|bim.*automat|automat.*bim|deterministic ai.*bim|bim.*qa/.test(t)) return 'BIM Quality & Compliance Automation';
  if (/interoperab|data exchange|granular data/.test(t))                           return 'Data Interoperability & Exchange';
  if (/data.*integrat|integrat.*data|data management|data.*access|lifecycle data|data.*pipeline|data.*quality|data.*model|data.*process/.test(t)) return 'Data Management & Integration';
  if (/ai agent|agentic|llm.driven|generative ai|human.ai/.test(t))               return 'AI Agents & LLMs';
  if (/design automat|automat.*design|computational design|facade|automat.*architectural|automat.*revit|revit.*automat/.test(t)) return 'Design & Workflow Automation';
  if (/\bbim\b|building information model/.test(t))                               return 'BIM & Design';
  if (/construction.*workflow|automat.*construction|construction.*automat|project deliver|site safety|safety.*notif|rework/.test(t)) return 'Construction Workflows & Automation';
  if (/project manag|enterprise.*project|project lifecycle/.test(t))              return 'Project & Enterprise Management';
  if (/\bapi\b|\bapis\b|autodesk platform service|aps.*business|aps.*subscript|api.*capacit|securing api|oauth/.test(t)) return 'APS & API Development';
  if (/urban planning|geobim|gis.*bim|bim.*gis|infrastructure design|dam project/.test(t)) return 'Urban Planning & Infrastructure';
  if (/manufactur|plm|mes |erp|fusion.*automat|fabricat/.test(t))                 return 'Manufacturing & PLM';
  if (/visual|render|xr |walkthrough|experiential/.test(t))                       return 'Visualization & Simulation';
  if (/cloud.based|cloud.*workflow|platform.*evolution|scalab|backend|architecture transit/.test(t)) return 'Cloud & Platform Scalability';
  if (/securit|authoriz/.test(t))                                                 return 'Security & Authentication';
  if (/knowledge.*graph|knowledge.*manag|knowledge evolut/.test(t))               return 'Knowledge Management';
  if (/ai.*integrat|integrat.*ai|ai.*transform|ai.*workflow|workflow.*ai|ai.*aec|aec.*ai|ai.driven|ai.powered|ai.assisted|ai.enhanced|ai.based|ai.*automat|automat.*ai|ai renais|ai in |ai and /.test(t)) return 'AI Integration in AEC';
  if (/automat|digital transform|workflow|integrat/.test(t))                      return 'Automation & Digital Transformation';
  return raw.length > 55 ? 'AEC Innovation' : raw;
}

function normalizeProduct(raw) {
  var t = raw.toLowerCase().trim();
  if (/\baps\b|autodesk platform service|platform service/.test(t))   return 'APS';
  if (/\bacc\b|autodesk construction cloud|acc docs/.test(t))          return 'ACC';
  if (/\bforma\b|autodesk forma|forma.*build|forma construct/.test(t)) return 'Forma';
  if (/\bfusion\b/.test(t))                                            return 'Fusion';
  if (/\brevit\b/.test(t))                                             return 'Revit';
  if (/viewer sdk|aps viewer|\bviewer\b/.test(t))                      return 'Viewer SDK';
  if (/model derivative/.test(t))                                      return 'Model Derivative API';
  if (/aec data model/.test(t))                                        return 'AEC Data Model API';
  if (/\btandem\b/.test(t))                                            return 'Tandem';
  if (/navisworks/.test(t))                                            return 'Navisworks';
  if (/civil 3d/.test(t))                                              return 'Civil 3D';
  if (/\bautocad\b/.test(t))                                           return 'AutoCAD';
  if (/design automation api/.test(t))                                 return 'Design Automation API';
  if (/data management api/.test(t))                                   return 'Data Management API';
  if (/\bforge\b/.test(t))                                             return 'Forge';
  if (/autodesk assistant/.test(t))                                    return 'Autodesk Assistant';
  if (/app store/.test(t))                                             return 'Autodesk App Store';
  if (/bim 360/.test(t))                                               return 'BIM 360';
  if (/model context protocol|\bmcp\b/.test(t))                        return 'MCP Server';
  if (/\binventor\b/.test(t))                                          return 'Inventor';
  if (/\bdynamo\b/.test(t))                                            return 'Dynamo';
  if (/infraworks/.test(t))                                            return 'InfraWorks';
  if (/\bgraphql\b/.test(t))                                           return 'GraphQL';
  if (/workshop xr/.test(t))                                           return 'Workshop XR';
  return raw;
}

function normalizeAI(raw) {
  var t = raw.toLowerCase().trim();
  if (/\bclaude\b|clawed|claude cod/.test(t))                          return 'Claude (Anthropic)';
  if (/chatgpt|chat gpt/.test(t))                                      return 'ChatGPT';
  if (/\bgpt\b/.test(t))                                               return 'GPT / ChatGPT';
  if (/copilot studio/.test(t))                                        return 'Microsoft Copilot Studio';
  if (/\bcopilot\b|co-pilot|github copilot/.test(t))                  return 'Microsoft Copilot';
  if (/ai coding agent|ai client|agentic system|onboarding co-pilot/.test(t)) return 'AI Agents';
  if (/\bai agent/.test(t))                                            return 'AI Agents';
  if (/large language model|llm/.test(t))                              return 'LLMs (General)';
  if (/azure openai|azure ai foundry/.test(t))                        return 'Azure OpenAI';
  if (/amazon bedrock|bedrock knowledge/.test(t))                      return 'Amazon Bedrock';
  if (/openai whisper|whisper/.test(t))                                return 'OpenAI Whisper';
  if (/\bopenai\b/.test(t))                                            return 'OpenAI';
  if (/\brag\b/.test(t))                                               return 'RAG';
  if (/machine learning|reinforcement learning/.test(t))               return 'Machine Learning';
  if (/generative ai|generative design/.test(t))                       return 'Generative AI';
  if (/autodesk assistant/.test(t))                                    return 'Autodesk Assistant';
  if (/victor ai/.test(t))                                             return 'Victor AI';
  if (/\biot\b/.test(t))                                               return 'IoT';
  if (/roberta|facebook ai/.test(t))                                   return 'RoBERTa';
  if (/pinecone/.test(t))                                              return 'Pinecone';
  if (/\bgemini\b/.test(t))                                            return 'Google Gemini';
  return raw;
}

function normalizeClient(raw) {
  var t = raw.toLowerCase().trim();
  // discard clearly bad AI extraction artefacts
  if (/^(partners or customers|basics|atlantis|valley|brazil|fash|swiss|suez|others?|n[/]a)$/.test(t)) return '';
  if (/sweco|swecco/.test(t))                                          return 'Sweco';
  if (/bca singapore|building and construction authority/.test(t))     return 'BCA Singapore';
  if (/deutsche bahn/.test(t))                                         return 'Deutsche Bahn';
  if (/\bbosch\b/.test(t))                                             return 'Bosch';
  if (/\baws\b|amazon web services/.test(t))                           return 'AWS';
  if (/\baecom\b/.test(t))                                             return 'AECOM';
  if (/\bwsp\b/.test(t))                                               return 'WSP';
  if (/arcadis/.test(t))                                               return 'Arcadis';
  if (/\besri\b/.test(t))                                              return 'Esri';
  if (/skanska/.test(t))                                               return 'Skanska';
  if (/parsons/.test(t))                                               return 'Parsons';
  if (/microsoft/.test(t))                                             return 'Microsoft';
  if (/novo nordisk|novo nordus/.test(t))                              return 'Novo Nordisk';
  return raw;
}

// ── Build aggregate tables from chip data already in the DOM ─────────────
function _esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function _trunc(s, n) { return s.length > n ? s.slice(0, n) + '…' : s; }

function buildAggregateTables() {
  // Step 1: rewrite chip text in the DOM to canonical names.
  // This ensures filterVideos() matches correctly when a row is clicked.
  var chipNorm = [
    ['#pv-content .video-card .chip-theme',   normalizeTheme],
    ['#pv-content .video-card .chip-product', normalizeProduct],
    ['#pv-content .video-card .chip-ai',      normalizeAI],
    ['#pv-content .video-card .chip-client',  normalizeClient]
  ];
  chipNorm.forEach(function(pair) {
    document.querySelectorAll(pair[0]).forEach(function(el) {
      var n = pair[1](el.textContent.trim());
      if (n) { el.textContent = n; }
      else   { el.style.display = 'none'; } // hide invalid/noise chips
    });
  });

  // Step 2: collect from the now-normalised DOM (dedup per video per key)
  var themeMap = {}, prodMap = {}, clientMap = {}, aiMap = {};
  document.querySelectorAll('#pv-content .video-card').forEach(function(card) {
    var vid   = card.id.replace('video-', '');
    var title = card.dataset.title || vid;
    function collect(sel, map) {
      var seen = {};
      card.querySelectorAll(sel).forEach(function(el) {
        if (el.style.display === 'none') return;
        var k = el.textContent.trim();
        if (!k || seen[k]) return;
        seen[k] = true;
        if (!map[k]) map[k] = [];
        map[k].push({ id: vid, title: title });
      });
    }
    collect('.chip-theme',   themeMap);
    collect('.chip-product', prodMap);
    collect('.chip-client',  clientMap);
    collect('.chip-ai',      aiMap);
  });

  renderAggTable('agg-themes',   themeMap,  'Topic / Theme',         'theme');
  renderAggTable('agg-products', prodMap,   'Product / API',         'product');
  renderAggTable('agg-clients',  clientMap, 'Client / Organisation', 'client');
  renderAggTable('agg-ai',       aiMap,     'AI Technology',         'ai');

  [['count-themes', themeMap],['count-products', prodMap],
   ['count-clients', clientMap],['count-ai', aiMap]].forEach(function(pair) {
    var el = document.getElementById(pair[0]);
    if (el) el.textContent = Object.keys(pair[1]).length;
  });

  // Update top stat cards with real counts
  function setStat(id, val) { var e = document.getElementById(id); if (e) e.textContent = val; }
  setStat('stat-sessions', _totalCards);
  setStat('stat-themes',   Object.keys(themeMap).length);
  setStat('stat-clients',  Object.keys(clientMap).length);
  setStat('stat-products', Object.keys(prodMap).length);
  setStat('stat-ai',       Object.keys(aiMap).length);
}

function renderAggTable(cid, map, colName, chipType) {
  var container = document.getElementById(cid);
  if (!container) return;
  var entries = Object.entries(map).sort(function(a, b) { return b[1].length - a[1].length; });
  var h = '<input class="agg-filter" placeholder="Filter ' + _esc(colName.toLowerCase()) + 's&hellip;" oninput="filterAggTable(this)">';
  h += '<div style="overflow-x:auto"><table class="agg-table" data-sort-dir="desc" data-sort-col="1">';
  h += '<thead><tr>';
  h += '<th onclick="sortAggTable(this,0)" style="cursor:pointer;min-width:160px">' + _esc(colName) + ' <span class="sort-arrow">&#8597;</span></th>';
  h += '<th onclick="sortAggTable(this,1)" style="cursor:pointer;text-align:center;width:78px">Sessions <span class="sort-arrow">&#9660;</span></th>';
  h += '<th>Sample sessions (click to explore)</th>';
  h += '</tr></thead><tbody>';
  entries.forEach(function(entry) {
    var name   = entry[0];
    var videos = entry[1];
    // Use data-filter attribute to avoid HTML attribute quoting issues with
    // JSON.stringify which produces double-quoted strings inside onclick="..."
    var chips  = videos.slice(0, 5).map(function(v) {
      return '<a href="#" class="chip chip-' + chipType + '" style="font-size:10px"'
           + ' data-filter="' + _esc(name) + '"'
           + ' onclick="filterAndGo(this.dataset.filter);return false">'
           + _esc(_trunc(v.title, 30)) + '</a>';
    }).join('');
    if (videos.length > 5) chips += '<span class="chip" style="background:#EEF2F7;color:#6B7280;font-size:10px">+' + (videos.length - 5) + ' more</span>';
    h += '<tr>';
    h += '<td><span class="agg-name" data-filter="' + _esc(name) + '" onclick="filterAndGo(this.dataset.filter)">' + _esc(name) + '</span></td>';
    h += '<td style="text-align:center;font-weight:700;color:var(--primary)">' + videos.length + '</td>';
    h += '<td>' + chips + '</td>';
    h += '</tr>';
  });
  h += '</tbody></table></div>';
  container.innerHTML = h;
}

// ── On load: build tables, handle hash deep-link ─────────────────────────
window.addEventListener('load', function() {
  // Remove the old Cross-Video Themes section (the broken matrix)
  var mw = document.querySelector('.matrix-wrapper');
  if (mw) {
    var sec = mw.closest('.section');
    if (sec) sec.remove();
  }

  // Count total cards for search counter
  _totalCards = document.querySelectorAll('#pv-content .video-card').length;
  var meta = document.getElementById('search-count');
  if (meta) meta.textContent = _totalCards + ' sessions';

  // Build aggregate tables (normalises chip text first, then aggregates)
  buildAggregateTables();

  // Hash-based deep linking: index.html#video-XYZ
  var hash = window.location.hash;
  if (hash && hash.startsWith('#video-')) {
    openAndScrollTo(hash.slice(7));
  }
});
</script>"""

# ─────────────────────────────────────────────────────────────────────────────
def main():
    print(f"Reading {SRC} …")
    with open(SRC, "r", encoding="utf-8") as f:
        html = f.read()
    total_lines = html.count("\n")
    print(f"  {len(html):,} bytes  |  {total_lines:,} lines")

    # 1 ── Replace <style> block ──────────────────────────────────────────────
    html, n = re.subn(r"<style>.*?</style>", NEW_CSS, html, count=1, flags=re.DOTALL)
    print(f"  ✓ CSS replaced ({n})")

    # 2 ── Add Pagefind to <head> ─────────────────────────────────────────────
    pf_head = ('<link href="pagefind/pagefind-ui.css" rel="stylesheet">\n'
               '<script src="pagefind/pagefind-ui.js"></script>')
    if "pagefind/pagefind-ui.js" not in html:
        html = html.replace("</head>", pf_head + "\n</head>", 1)
        print("  ✓ Pagefind head tags inserted")

    # 3 ── Replace nav (<!-- NAV --> … </nav>) ────────────────────────────────
    html, n = re.subn(r"<!-- NAV -->.*?</nav>", NEW_NAV, html, count=1, flags=re.DOTALL)
    print(f"  ✓ Nav replaced ({n})")

    # 4 ── Update page title ──────────────────────────────────────────────────
    html = html.replace(
        "<title>YouTube Channel Analysis Report</title>",
        "<title>Autodesk DevCon 2026 — Summaries</title>",
        1,
    )
    print("  ✓ Page title updated")

    # 5a ── Replace hardcoded stats section with dynamic IDs ─────────────────
    OLD_STATS = """  <!-- Stats -->
  <div class="stats">
    <div class="stat-card">
      <div class="stat-num">78</div>
      <div class="stat-label">Videos analysed</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">5</div>
      <div class="stat-label">Shared themes</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">14</div>
      <div class="stat-label">Clients identified</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">3</div>
      <div class="stat-label">Autodesk products/APIs</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">3</div>
      <div class="stat-label">AI technologies</div>
    </div>
  </div>"""
    NEW_STATS = """  <!-- Stats -->
  <div class="stats">
    <div class="stat-card">
      <div class="stat-num" id="stat-sessions">78</div>
      <div class="stat-label">Sessions</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="stat-themes">&mdash;</div>
      <div class="stat-label">Unique topics</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="stat-clients">&mdash;</div>
      <div class="stat-label">Clients &amp; partners</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="stat-products">&mdash;</div>
      <div class="stat-label">Autodesk products</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="stat-ai">&mdash;</div>
      <div class="stat-label">AI technologies</div>
    </div>
  </div>"""
    if OLD_STATS in html:
        html = html.replace(OLD_STATS, NEW_STATS, 1)
        print("  ✓ Stats section updated with dynamic IDs")
    else:
        print("  ⚠ Stats section pattern not matched")

    # 5b ── Update executive summary text ─────────────────────────────────────
    if OLD_EXEC_SUMMARY_P in html:
        html = html.replace(OLD_EXEC_SUMMARY_P, NEW_EXEC_SUMMARY_P, 1)
        print("  ✓ Executive summary updated")
    else:
        print("  ⚠ Executive summary text not matched (check manually)")

    # 6 ── Insert aggregate tables section before <!-- Themes Matrix --> ──────
    MATRIX_MARKER = "<!-- Themes Matrix -->"
    if MATRIX_MARKER in html:
        html = html.replace(MATRIX_MARKER, AGG_SECTION + "\n  " + MATRIX_MARKER, 1)
        print("  ✓ Aggregate tables section inserted")
    else:
        print("  ⚠ Themes Matrix comment not found – tables not inserted")

    # 6b ── Remove 3 stale legacy sections (Clients, Products, AI tables) ─────
    start = html.find("  <!-- Clients -->")
    end   = html.find("\n\n</div>\n</div>\n\n<!-- ===================== TAB 2")
    if start != -1 and end != -1:
        html = html[:start] + html[end:]
        print("  ✓ Removed 3 stale legacy sections (Clients, Products, AI tables)")
    else:
        print("  ⚠ Stale sections markers not found (may already be removed)")

    # 7 ── Bulk-add data-pagefind-body to all .video-body divs ───────────────
    before = html.count('class="video-body"')
    html = html.replace('class="video-body"', 'class="video-body" data-pagefind-body')
    after = html.count("data-pagefind-body")
    print(f"  ✓ data-pagefind-body added to {after} video-body divs (was {before})")

    # 8 -- Add data-pagefind-meta="title" to YouTube watch links
    html, n = re.subn(
        r'(<a href="https://www\.youtube\.com/watch\?v=[A-Za-z0-9_\-]{11}")'
        r'( target="_blank"[^>]*>)',
        r'\1 data-pagefind-meta="title"\2',
        html,
    )
    print(f"  + data-pagefind-meta added to {n} title links")

    # 8b ── Inject hidden <h2> anchors inside each data-pagefind-body div ───────
    # Pagefind needs a heading with an id inside each section to create separate
    # search results (one per video) rather than one result for the whole page.
    title_map = {}
    for m in re.finditer(r'id="video-([^"]+)"[^>]+data-title="([^"]*)"', html):
        title_map[m.group(1)] = m.group(2)
    # Also handle reverse attribute order
    for m in re.finditer(r'data-title="([^"]*)"[^>]+id="video-([^"]+)"', html):
        title_map[m.group(2)] = m.group(1)

    def inject_h2(m):
        full_tag = m.group(1)
        vid_id   = m.group(2)
        raw      = title_map.get(vid_id, vid_id)
        title    = html_lib.escape(raw.title())
        h2 = (f'<h2 id="video-{vid_id}" '
              f'style="position:absolute;width:1px;height:1px;overflow:hidden;'
              f'clip:rect(0,0,0,0);white-space:nowrap">'
              f'{title}</h2>')
        return full_tag + h2

    html, n = re.subn(
        r'(<div class="video-body" data-pagefind-body id="body-([^"]+)">)',
        inject_h2,
        html,
    )
    print(f"  ✓ Injected Pagefind h2 anchors into {n} video-body divs")

    # 9 ── Upgrade the search input ────────────────────────────────────────────
    OLD_SEARCH = '<input type="text" class="search-box" placeholder="Search videos…" id="video-search" oninput="filterVideos(this.value)">'
    NEW_SEARCH  = ('<div class="search-wrap">'
                   '<span class="search-icon">&#128269;</span>'
                   '<input class="search-box" id="video-search" '
                   'placeholder="Search by title, topic, product, client, AI tech… (press / to focus)" '
                   'oninput="filterVideos(this.value)">'
                   '</div>'
                   '<div class="search-meta" id="search-count">78 sessions</div>')
    if OLD_SEARCH in html:
        html = html.replace(OLD_SEARCH, NEW_SEARCH, 1)
        print("  ✓ Search box upgraded")
    else:
        print("  ⚠ Search box pattern not matched (check manually)")

    # 10 ── Replace final <script> block ──────────────────────────────────────
    last_script = html.rfind("<script>")
    if last_script != -1:
        html = html[:last_script] + NEW_JS + "\n"
        print("  ✓ JavaScript replaced")
    else:
        html += "\n" + NEW_JS
        print("  ✓ JavaScript appended (no existing script found)")

    # ── Write output ──────────────────────────────────────────────────────────
    print(f"\nWriting {DEST} …")
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(html)
    size_mb = os.path.getsize(DEST) / 1024 / 1024
    print(f"  ✓ Done — {size_mb:.1f} MB")
    print()
    print("Next: run the Pagefind indexer to enable full-text search:")
    print(f'  npx pagefind --site "{HERE}"')
    print("Then open index.html in a browser (or push to GitHub Pages).")


if __name__ == "__main__":
    main()

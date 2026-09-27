/* WOOS — chart SVG vanilla. Hanya MENGGAMBAR data yang sudah dihitung pipeline & dikirim server
 * (PRD §47): tidak ada clustering / rule klasifikasi di frontend.
 * Warna mengikuti entitas (cluster_id -> slot palet tetap), tidak mengikuti peringkat.
 * Pemakaian: <div class="chart" data-chart="bar|stack|multiples|line|paths" data-source="json-id"></div>
 */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const clusterColor = (id) => (id === null || id === undefined || id < 0 ? css('--neutral') : css('--s' + ((id % 8) + 1)));
  const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v) ? '—'
    : Number(v).toLocaleString('id-ID', { maximumFractionDigits: d, minimumFractionDigits: 0 }));

  function el(tag, attrs = {}, parent) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  }
  function text(parent, x, y, str, attrs = {}) {
    const t = el('text', { x, y, ...attrs }, parent);
    t.textContent = str;
    return t;
  }

  // ---------- tooltip bersama ----------
  const tip = () => document.getElementById('tooltip');
  function showTip(evt, html) {
    const t = tip(); if (!t) return;
    t.innerHTML = html; t.hidden = false;
    const pad = 14, w = t.offsetWidth, h = t.offsetHeight;
    let x = evt.clientX + pad, y = evt.clientY + pad;
    if (x + w > window.innerWidth) x = evt.clientX - w - pad;
    if (y + h > window.innerHeight) y = evt.clientY - h - pad;
    t.style.left = x + 'px'; t.style.top = y + 'px';
  }
  const hideTip = () => { const t = tip(); if (t) t.hidden = true; };
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function bindTip(node, html) {
    node.addEventListener('mousemove', (e) => showTip(e, html));
    node.addEventListener('mouseleave', hideTip);
    node.setAttribute('tabindex', '0');
    node.addEventListener('focus', (e) => { const r = node.getBoundingClientRect(); showTip({ clientX: r.right, clientY: r.top }, html); });
    node.addEventListener('blur', hideTip);
  }

  // ---------- bar horizontal ----------
  function bar(host, d) {
    const items = d.items, W = Math.max(host.clientWidth, 320), rowH = 28, right = 86;
    const left = Math.min(d.labelWidth || 220, W * 0.45);
    const H = items.length * rowH + 8;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': d.title || 'bar chart' }, host);
    const max = Math.max(...items.map((i) => i.value), 1);
    items.forEach((it, i) => {
      const y = i * rowH + 4, w = ((W - left - right) * it.value) / max;
      const maxChars = Math.floor((left - 12) / 6.2);
      const lab = it.label.length > maxChars ? it.label.slice(0, maxChars - 1) + '…' : it.label;
      text(svg, left - 8, y + rowH / 2 + 4, lab, { 'text-anchor': 'end' });
      const r = el('rect', { x: left, y: y + 5, width: Math.max(w, 1), height: rowH - 12, rx: 4, fill: it.color || clusterColor(it.cluster) }, svg);
      text(svg, left + w + 6, y + rowH / 2 + 4, it.valueLabel ?? fmt(it.value, 0));
      bindTip(r, `<strong>${esc(it.label)}</strong><br>${esc(it.tip || fmt(it.value, 0))}`);
    });
  }

  // ---------- stacked 100% per baris ----------
  function stack(host, d) {
    const W = Math.max(host.clientWidth, 360), rowH = 26, left = Math.min(d.labelWidth || 300, W * 0.4), H = d.rows.length * rowH + 8;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': d.title || 'stacked bar' }, host);
    d.rows.forEach((row, i) => {
      const y = i * rowH + 4, total = row.parts.reduce((s, p) => s + p.value, 0) || 1;
      const maxChars = Math.floor((left - 12) / 6.2);
      text(svg, left - 8, y + rowH / 2 + 4, row.label.length > maxChars ? row.label.slice(0, maxChars - 1) + '…' : row.label, { 'text-anchor': 'end' });
      let x = left;
      row.parts.forEach((p) => {
        const w = ((W - left - 10) * p.value) / total;
        if (w <= 0) return;
        const r = el('rect', { x, y: y + 4, width: Math.max(w - 2, 0.5), height: rowH - 9, fill: clusterColor(p.cluster) }, svg);
        bindTip(r, `<strong>${esc(row.label)}</strong><br>${esc(p.label)}: ${fmt(p.value, 0)} org (${fmt((100 * p.value) / total, 1)}%)`);
        x += w;
      });
    });
  }

  // ---------- small multiples scatter (PCA; satu panel per cluster) ----------
  function multiples(host, d) {
    const pts = d.points, groups = d.groups, pad = 22, head = 34;
    const Wt = Math.max(host.clientWidth, 300);
    const cols = Math.max(1, Math.min(groups.length, d.columns || 5, Math.floor(Wt / 190)));
    const P = Wt / cols;
    const xs = pts.map((p) => +p.x), ys = pts.map((p) => +p.y);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const sx = (v) => pad + ((v - x0) / (x1 - x0 || 1)) * (P - 2 * pad);
    const sy = (v) => P - pad - ((v - y0) / (y1 - y0 || 1)) * (P - 2 * pad);
    const rows = Math.ceil(groups.length / cols);
    const svg = el('svg', { viewBox: `0 0 ${cols * P} ${rows * (P + head)}`, role: 'img', 'aria-label': d.title || 'PCA per cluster' }, host);
    groups.forEach((g, gi) => {
      const ox = (gi % cols) * P, oy = Math.floor(gi / cols) * (P + head);
      const panel = el('g', { transform: `translate(${ox},${oy})` }, svg);
      el('rect', { x: 4, y: head - 4, width: P - 8, height: P - 8, fill: 'none', stroke: css('--border'), rx: 6 }, panel);
      const n = pts.filter((p) => p.c === g.id).length;
      const maxChars = Math.floor((P - 12) / 6.4);
      const lab = g.label.length > maxChars ? g.label.slice(0, maxChars - 1) + '…' : g.label;
      text(panel, 8, 12, lab, { 'font-weight': 600 });
      text(panel, 8, 26, `n = ${n}`);
      const body = el('g', { transform: `translate(0,${head - 8})` }, panel);
      pts.forEach((p) => { if (p.c !== g.id) el('circle', { cx: sx(p.x), cy: sy(p.y), r: 1.6, fill: css('--neutral'), opacity: 0.35 }, body); });
      pts.forEach((p) => {
        if (p.c !== g.id) return;
        let m;
        if (g.id < 0) {                         // noise DBSCAN: bentuk berbeda (X) — PRD §54
          m = el('path', { d: `M${sx(p.x) - 3},${sy(p.y) - 3}l6,6m0,-6l-6,6`, stroke: css('--s8'), 'stroke-width': 1.6 }, body);
        } else {
          m = el('circle', { cx: sx(p.x), cy: sy(p.y), r: 3.2, fill: clusterColor(g.id), stroke: css('--surface'), 'stroke-width': 0.8 }, body);
        }
        bindTip(m, `<strong>${esc(p.name)}</strong><br>${esc(p.label)}`);
      });
    });
  }

  // ---------- line (metrik vs K) ----------
  function line(host, d) {
    const W = Math.max(host.clientWidth, 320), H = Math.round(Math.min(Math.max(W * 0.5, 220), 300)), L = 46, R = 12, T = 12, B = 34;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': d.title || 'line chart' }, host);
    const all = d.series.flatMap((s) => s.points).filter((p) => p.y !== null);
    const xs = all.map((p) => p.x), ys = all.map((p) => p.y);
    const [x0, x1] = [Math.min(...xs), Math.max(...xs)];
    let [y0, y1] = [Math.min(...ys), Math.max(...ys)];
    const padY = (y1 - y0) * 0.1 || 0.1; y0 -= padY; y1 += padY;
    const sx = (v) => L + ((v - x0) / (x1 - x0 || 1)) * (W - L - R);
    const sy = (v) => H - B - ((v - y0) / (y1 - y0 || 1)) * (H - T - B);
    for (let i = 0; i <= 4; i++) {
      const v = y0 + ((y1 - y0) * i) / 4;
      el('line', { x1: L, x2: W - R, y1: sy(v), y2: sy(v), stroke: css('--border') }, svg);
      text(svg, L - 6, sy(v) + 4, fmt(v, 2), { 'text-anchor': 'end' });
    }
    [...new Set(xs)].forEach((v) => text(svg, sx(v), H - B + 16, String(v), { 'text-anchor': 'middle' }));
    text(svg, (W + L) / 2, H - 4, d.xLabel || '', { 'text-anchor': 'middle' });
    d.series.forEach((s, si) => {
      const color = s.color || css('--s' + (si + 1));
      const valid = s.points.filter((p) => p.y !== null);
      el('path', { d: valid.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x)},${sy(p.y)}`).join(''), fill: 'none', stroke: color,
                   'stroke-width': s.highlight ? 3 : 2, opacity: s.highlight || !d.highlight ? 1 : 0.55 }, svg);
      valid.forEach((p) => {
        const c = el('circle', { cx: sx(p.x), cy: sy(p.y), r: p.mark ? 6 : 4, fill: color, stroke: css('--surface'), 'stroke-width': 1.5 }, svg);
        bindTip(c, `<strong>${esc(s.name)}</strong><br>${esc(d.xLabel || 'x')} = ${esc(p.x)} · ${esc(d.yLabel || 'y')} = ${fmt(p.y, 3)}${p.note ? '<br>' + esc(p.note) : ''}`);
      });
    });
  }

  function legend(host, items) {
    const box = document.createElement('div');
    box.className = 'legend';
    items.forEach((it) => {
      const s = document.createElement('span');
      const sw = document.createElement('span');
      sw.className = 'swatch';
      sw.style.background = it.color || clusterColor(it.cluster);   // CSSOM (diizinkan CSP), bukan atribut inline
      s.append(sw, document.createTextNode(it.label));
      box.appendChild(s);
    });
    host.prepend(box);
  }

  const RENDER = { bar, stack, multiples, line };
  function init() {
    document.querySelectorAll('.bar-fill[data-width]').forEach((b) => { b.style.width = b.dataset.width + '%'; });
    document.querySelectorAll('[data-chart]').forEach((host) => {
      const src = document.getElementById(host.dataset.source);
      if (!src) return;
      const data = JSON.parse(src.textContent);
      host.innerHTML = '';
      RENDER[host.dataset.chart](host, data);
      if (data.legend) legend(host, data.legend.map((l) => ({ ...l, color: l.cluster === undefined ? css('--s' + (l.slot || 1)) : undefined })));
    });
  }
  document.addEventListener('DOMContentLoaded', init);
  let resizeTimer;
  window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(init, 200); });
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', init);
})();

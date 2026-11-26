/* 模力盒 · 公共前端工具 */
async function api(path, opts = {}) {
  const options = { credentials: 'same-origin', ...opts };
  if (opts.body && !(opts.body instanceof FormData)) {
    options.headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    options.body = JSON.stringify(opts.body);
  }
  const res = await fetch(path, options);
  let data;
  try { data = await res.json(); } catch (_) { data = { error: '服务返回异常' }; }
  if (!res.ok) throw new Error(data.error || ('请求失败 ' + res.status));
  return data;
}

let ME = null;
async function loadMe() {
  try { ME = (await api('/api/me')).user; } catch (_) { ME = null; }
  return ME;
}

function toast(msg) {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div'); el.id = 'toast'; el.className = 'toast';
    document.body.appendChild(el);
  }
  el.textContent = msg; el.classList.add('show');
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 2400);
}

function avatarHTML(name, cls = '') {
  const ch = (name || '?').trim().charAt(0).toUpperCase();
  return `<span class="avatar ${cls}">${ch}</span>`;
}

function miniHTML(t) {
  const s = t.style || 'doc';
  let inner = '';
  if (s === 'slide' || s === 'darkslide') {
    inner = `<div class="mini m-slide ${s === 'darkslide' ? 'm-dark' : ''}"><span class="m-kicker"></span><span class="m-title"></span><i class="m-line"></i><i class="m-line" style="width:55%"></i><div class="m-circles"></div></div>`;
  } else if (s === 'chart') {
    inner = `<div class="mini m-slide"><span class="m-title" style="width:45%"></span><div class="m-chart"><div class="m-bars"><i style="height:45%"></i><i style="height:80%"></i><i style="height:60%"></i><i style="height:95%"></i><i style="height:35%"></i></div></div></div>`;
  } else if (s === 'soft') {
    inner = `<div class="mini m-soft"><span class="m-title"></span><i class="m-line" style="width:80%"></i><i class="m-line" style="width:60%"></i><div class="m-circle"></div></div>`;
  } else if (s === 'resume') {
    inner = `<div class="mini m-resume"><div class="m-side"><div class="m-ava"></div><i></i><i></i><i></i></div><div class="m-main"><i></i><i></i><i></i><i style="width:75%"></i><i></i></div></div>`;
  } else if (s === 'doc') {
    inner = `<div class="mini m-doc"><div class="m-head"></div><i></i><i></i><i class="short"></i><i></i><i></i><i class="short"></i></div>`;
  } else if (s === 'table') {
    inner = `<div class="mini m-table">${Array.from({length:4}, () => `<div class="m-tr"><i></i><i></i><i></i></div>`).join('')}</div>`;
  } else if (s === 'sheet') {
    inner = `<div class="mini m-sheet"><div class="m-sh"></div>${Array.from({length:5}, () => `<div class="m-row"><i></i><i></i><i></i><i></i></div>`).join('')}</div>`;
  } else if (s === 'gantt') {
    inner = `<div class="mini m-gantt">${[35,60,45,75].map((w,i) => `<div class="m-row"><b></b><i style="width:${w}%;margin-left:${i*5}%"></i></div>`).join('')}</div>`;
  } else if (s === 'dash') {
    inner = `<div class="mini m-dash"><div class="m-nav"><i></i><i></i><i></i><i></i></div><div class="m-content"><div class="m-cards"><i></i><i></i></div><i></i><i style="width:70%"></i><i></i></div></div>`;
  } else if (s === 'browser') {
    inner = `<div class="mini m-browser"><div class="m-top"><i></i><i></i><i></i></div><div class="m-hero"><span></span><b></b></div><div class="m-cols"><i></i><i></i><i></i></div></div>`;
  } else if (s === 'shop') {
    inner = `<div class="mini m-shop"><div class="m-head"></div><div class="m-items">${Array.from({length:6}, () => '<i></i>').join('')}</div></div>`;
  } else if (s === 'gallery') {
    inner = `<div class="mini m-gallery">${Array.from({length:3}, () => '<i></i>').join('')}</div>`;
  } else if (s === 'mail') {
    inner = `<div class="mini m-mail"><div class="m-head"></div><div class="m-body"><i></i><i></i><i style="width:60%"></i><div class="m-btn"></div></div></div>`;
  } else if (s === 'poster') {
    inner = `<div class="mini m-poster"><div class="m-big"></div><i></i><i style="width:42%"></i><div class="m-stamp"></div></div>`;
  } else {
    inner = `<div class="m-card" style="position:relative;width:78%;height:52%"><div class="m-logo"></div><i></i><i style="width:48%"></i><i style="width:70%"></i></div>`;
  }
  const colors = t.colors || ['#6366f1','#a5b4fc'];
  return `<div class="thumb" style="--c1:${colors[0]};--c2:${colors[1]}">${inner}</div>`;
}

function fmtDate(s) { return (s || '').replace('T',' ').slice(0,16); }
function fmtSize(n) { return n > 1048576 ? (n/1048576).toFixed(1)+' MB' : Math.ceil(n/1024)+' KB'; }
function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

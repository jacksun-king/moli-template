/* 模力盒 · 前台逻辑（API 驱动） */
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const C_SOFT = ['#eeedff','#e6f6ff','#fff0f2','#e9f9f1','#fff5e6','#f8ecff'];

const state = { cats: [], templates: [], cat: '', sub: '', query: '', sort: 'new', current: null };

const AI_HINTS = [
  { keys:['年终','总结','汇报','述职','季度','业绩'], cat:'PPT 模板', sub:'工作总结' },
  { keys:['简历','求职','应聘','找工作','cv'], cat:'Word 模板', sub:'简历模板' },
  { keys:['合同','协议','法务'], cat:'Word 模板', sub:'合同协议' },
  { keys:['论文','毕业','学术'], cat:'Word 模板', sub:'论文文档' },
  { keys:['财务','报表','记账','报销','会计'], cat:'Excel 模板', sub:'财务报表' },
  { keys:['进度','排期','甘特','任务'], cat:'Excel 模板', sub:'项目进度' },
  { keys:['网站','官网','网页','落地页','商城'], cat:'网站模板' },
  { keys:['邮件','邀请函','祝福'], cat:'邮件模板' },
  { keys:['海报','名片','logo','封面','设计'], cat:'设计模板' },
  { keys:['答辩','路演'], cat:'PPT 模板', sub:'答辩路演' },
  { keys:['培训','课件','教学'], cat:'PPT 模板', sub:'教育培训' },
  { keys:['发布','产品','发布会'], cat:'PPT 模板', sub:'产品发布' },
  { keys:['数据','看板','图表','分析'], cat:'Excel 模板', sub:'数据看板' }
];

function aiMatch(query, list) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return list.map(t => {
    let score = 0;
    const text = (t.title + ' ' + t.description + ' ' + (t.tags||[]).join(' ') + ' ' + t.sub + ' ' + t.cat_name).toLowerCase();
    AI_HINTS.forEach(h => {
      if (h.keys.some(k => q.includes(k))) {
        if (t.cat_name === h.cat) score += 5;
        if (h.sub && t.sub === h.sub) score += 6;
      }
    });
    if (text.includes(q)) score += 8;
    q.split(/\s+/).forEach(w => { if (w.length>1 && text.includes(w)) score += 3; });
    return { t, score };
  }).filter(x => x.score>0).sort((a,b)=>b.score-a.score).slice(0,8).map(x=>x.t);
}

function cardHTML(t) {
  const thumb = t.cover_url
    ? `<div class="thumb thumb-photo"><img src="${esc(t.cover_url)}" alt="${esc(t.title)}" loading="lazy" onerror="this.style.display='none'">${miniHTML(t)}</div>`
    : miniHTML(t);
  return `<article class="tpl-card" data-id="${t.id}">
    <div class="tpl-thumb-wrap">${thumb}${t.external_url?'<span class="badge-external">外链</span>':''}<span class="badge-format">${(t.formats||['FILE'])[0]}</span></div>
    <div class="tpl-body">
      <div class="tpl-cat">${t.cat_name} · ${t.sub}</div>
      <h3>${esc(t.title)}</h3><p>${esc(t.description)}</p>
      <div class="tpl-tags">${(t.tags||[]).slice(0,3).map(x=>`<span>${esc(x)}</span>`).join('')}</div>
      <div class="tpl-foot"><span>↓ ${t.downloads.toLocaleString()} 次下载</span><span class="tpl-source">${esc(t.uploader_name)}</span></div>
    </div></article>`;
}

function filtered() {
  let list = state.templates.filter(t => {
    if (state.cat && t.cat_name !== state.cat) return false;
    if (state.sub && t.sub !== state.sub) return false;
    if (state.query) {
      const text = (t.title + t.description + (t.tags||[]).join(' ') + t.sub + t.cat_name).toLowerCase();
      if (!text.includes(state.query.toLowerCase())) return false;
    }
    return true;
  });
  if (state.sort === 'hot') list.sort((a,b)=>b.downloads-a.downloads);
  if (state.sort === 'new') list.sort((a,b)=>b.id-a.id);
  if (state.sort === 'name') list.sort((a,b)=>a.title.localeCompare(b.title,'zh'));
  return list;
}

async function loadCategories() {
  const { categories } = await api('/api/categories');
  state.cats = categories;
  $('#categoryGrid').innerHTML = categories.map((c,i) => {
    const n = state.templates.filter(t=>t.cat_name===c.name).length;
    return `<button class="category-card" data-cat="${esc(c.name)}" type="button" style="--c-soft:${C_SOFT[i%6]}">
      <div class="c-icon">${c.icon}</div><h3>${esc(c.name)}</h3><p>${esc(c.description)}</p>
      <div class="c-foot"><span>${n} 套模板 · ${c.subs.length} 个场景</span><span class="c-arrow">→</span></div></button>`;
  }).join('');
  $$('.category-card').forEach(el => el.addEventListener('click', () => {
    state.cat = el.dataset.cat; state.sub=''; state.query=''; $('#headerSearch').value='';
    render(); $('#library').scrollIntoView({behavior:'smooth'});
  }));
  // 上传表单分类下拉
  $('#uploadCat').innerHTML = categories.map(c=>`<option value="${esc(c.name)}">${c.icon} ${esc(c.name)}</option>`).join('');
  syncSubOptions();
}

function syncSubOptions() {
  const c = state.cats.find(x=>x.name===$('#uploadCat').value) || state.cats[0];
  $('#uploadSub').innerHTML = (c?.subs||[]).map(s=>`<option value="${esc(s)}">${esc(s)}</option>`).join('');
}

function renderFilters() {
  const bar = $('.filter-bar');
  bar.querySelectorAll('[data-cat]').forEach(n=>n.remove());
  const all = document.createElement('button');
  all.className='filter-chip'+(!state.cat?' is-active':''); all.dataset.cat=''; all.type='button'; all.textContent='全部';
  bar.insertBefore(all, bar.querySelector('.filter-divider'));
  state.cats.forEach(c=>{
    const b=document.createElement('button');
    b.className='filter-chip'+(state.cat===c.name?' is-active':''); b.dataset.cat=c.name; b.type='button';
    b.textContent=c.icon+' '+c.name;
    bar.insertBefore(b, bar.querySelector('.filter-divider'));
  });
  const cat = state.cats.find(x=>x.name===state.cat);
  const subs = [''].concat(cat?cat.subs:[]);
  $('#subFilter').innerHTML = subs.map(s=>`<button class="filter-chip ${state.sub===s?' is-active':''}" data-sub="${esc(s)}" type="button">${s||'全部场景'}</button>`).join('');
}

function render() {
  const list = filtered();
  $('#templateGrid').innerHTML = list.map(cardHTML).join('');
  $('#emptyState').hidden = list.length>0;
  $('#resultCount').textContent = list.length;
  $('#libraryTitle').textContent = state.cat || '全部模板';
  $('#librarySub').textContent = state.cat ? (state.cats.find(c=>c.name===state.cat)?.description||'') : '挑一套顺手的，把时间留给真正重要的事';
  renderFilters();
}

async function loadStats() {
  $('#statTemplates').textContent = state.templates.length;
  $('#statCats').textContent = state.cats.length;
  try {
    const s = await api('/api/templates/stats');
    $('#statDownloads').textContent = (s.downloads||0).toLocaleString();
    if (s.users) $('#statUsers').textContent = s.users;
  } catch (_) {}
}

function openPreview(id) {
  const t = state.templates.find(x=>x.id==id);
  if (!t) return;
  state.current = t;
  $('#modalPreview').innerHTML = t.cover_url
    ? `<div class="thumb thumb-photo"><img src="${esc(t.cover_url)}" alt="${esc(t.title)}" onerror="this.style.display='none'">${miniHTML(t)}</div>`
    : miniHTML(t);
  $('#modalCat').textContent = t.cat_name+' · '+t.sub;
  $('#previewTitle').textContent = t.title;
  $('#modalDesc').textContent = t.description;
  $('#modalTags').innerHTML = (t.tags||[]).map(x=>`<span>${esc(x)}</span>`).join('');
  $('#modalFormats').textContent = (t.formats||[]).join(' / ');
  $('#modalDownloads').textContent = t.downloads.toLocaleString()+' 次';
  $('#modalUploader').textContent = t.uploader_name;
  $('#downloadBtn').textContent = t.external_url ? '前往源站下载 ↗' : (ME ? '下载模板 ↓' : '登录并下载 ↓');
  $('#modalNote').textContent = t.external_url
    ? '外链索引：本站不托管该文件，版权与下载服务归 ' + (t.source_site||'源站') + ' 所有，点击后跳转到原站获取。'
    : (t.file_id ? '' : '这是内置示例模板（无实际文件）。上传自己的模板文件后即可真实下载。');
  $('#previewModal').hidden = false;
  document.body.style.overflow='hidden';
}
function closePreview(){ $('#previewModal').hidden=true; document.body.style.overflow=''; state.current=null; }

function openUpload() {
  if (!ME) { toast('请先登录后再上传'); location.href='auth.html?next=index.html'; return; }
  $('#uploadModal').hidden=false; document.body.style.overflow='hidden';
}
function closeUpload(){ $('#uploadModal').hidden=true; document.body.style.overflow=''; }

function initEvents() {
  $('.filter-bar').addEventListener('click', e=>{
    const c=e.target.closest('[data-cat]'); if(c){state.cat=c.dataset.cat;state.sub='';render();return;}
    const s=e.target.closest('[data-sub]'); if(s){state.sub=s.dataset.sub;render();}
  });
  $('#sortSelect').addEventListener('change',e=>{state.sort=e.target.value;render();});
  $('#headerSearch').addEventListener('input',e=>{
    state.query=e.target.value.trim(); state.cat=''; state.sub=''; render();
    $('#library').scrollIntoView({behavior:'smooth'});
  });
  $('#aiForm').addEventListener('submit',e=>{
    e.preventDefault();
    const q=$('#aiInput').value.trim();
    if(!q){toast('先说说你想要什么模板吧');return;}
    const hits=aiMatch(q,state.templates);
    $('#aiCount').textContent=hits.length;
    $('#aiGrid').innerHTML=hits.length?hits.map(cardHTML).join(''):'<p style="color:var(--muted)">没找到相关模板，换个说法试试～</p>';
    $('#aiResultWrap').hidden=false; $('#aiResultWrap').scrollIntoView({behavior:'smooth'});
  });
  $$('.chip-example').forEach(b=>b.addEventListener('click',()=>{$('#aiInput').value=b.dataset.q;$('#aiForm').requestSubmit();}));
  $('#clearAi').addEventListener('click',()=>{$('#aiResultWrap').hidden=true;$('#aiInput').value='';});
  [$('#templateGrid'),$('#aiGrid')].forEach(g=>g.addEventListener('click',e=>{
    const card=e.target.closest('.tpl-card'); if(card) openPreview(card.dataset.id);
  }));
  $$('[data-close]').forEach(el=>el.addEventListener('click',closePreview));
  $('#downloadBtn').addEventListener('click',()=>{
    if(state.current?.external_url){window.open(state.current.external_url,'_blank','noopener,noreferrer');return;}
    if(!ME){toast('请先登录');location.href='auth.html?next=index.html';return;}
    if(!state.current) return;
    if(!state.current.file_id){toast('内置示例模板没有文件，可上传自己的模板');return;}
    location.href='/api/download?id='+state.current.id;
  });
  $('#modalProfileBtn').addEventListener('click',()=>{
    if(state.current?.uploader_name) location.href='profile.html?id='+encodeURIComponent(state.current.uploader_name);
  });
  $('#uploadBtn').addEventListener('click',openUpload);
  $$('[data-close-upload]').forEach(el=>el.addEventListener('click',closeUpload));
  $('#uploadCat').addEventListener('change',syncSubOptions);
  const file=$('#uploadFile'), drop=$('#dropZone');
  file.addEventListener('change',()=>{if(file.files[0])$('#dropText').textContent=file.files[0].name+' ('+fmtSize(file.files[0].size)+')';});
  ['dragenter','dragover'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('drag-over');}));
  ['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('drag-over');}));
  drop.addEventListener('drop',e=>{if(e.dataTransfer.files[0]){file.files=e.dataTransfer.files;$('#dropText').textContent=file.files[0].name;}});
  $('#uploadForm').addEventListener('submit',async e=>{
    e.preventDefault();
    const fd=new FormData(e.target);
    const btn=e.target.querySelector('button[type=submit]'); btn.disabled=true; btn.textContent='提交中…';
    $('#uploadMsg').textContent='';
    try{const r=await api('/api/upload',{method:'POST',body:fd});toast(r.message||'上传成功');closeUpload();e.target.reset();$('#dropText').textContent='点击选择文件，或拖到此处';}
    catch(err){$('#uploadMsg').textContent=err.message;}
    finally{btn.disabled=false;btn.textContent='提交审核';}
  });
  $('#resetFilter').addEventListener('click',()=>{state.cat='';state.sub='';state.query='';$('#headerSearch').value='';render();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closePreview();closeUpload();}});
}

(async function init(){
  await loadMe();
  if(ME){
    $('#loginLink').hidden=true;
    const chip=$('#userChip'); chip.hidden=false;
    chip.innerHTML=avatarHTML(ME.username)+'<span>'+esc(ME.username)+'</span>'+(ME.role==='admin'?'<small>管理员</small>':'');
    if(ME.role==='admin'){
      const a=document.createElement('a');a.href='admin.html';a.className='btn btn-ghost btn-sm';a.textContent='后台';
      $('.header-actions').insertBefore(a,chip);
    }
  }
  try{
    const [{templates},{categories}]=await Promise.all([api('/api/templates'),api('/api/categories')]);
    state.templates=templates; state.cats=categories;
    render(); loadCategories(); loadStats();
  }catch(err){toast('加载失败：'+err.message);}
  initEvents();
})();

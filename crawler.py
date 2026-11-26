# -*- coding: utf-8 -*-
"""模力盒 · 免费模板采集引擎（只索引元数据，不下载/托管文件）
用法：python crawler.py [每个来源采集数量，默认 12]
"""
import os, re, sys, sqlite3, time
from datetime import datetime
import urllib.parse
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'data', 'site.db')
UA = 'Mozilla/5.0 (compatible; MoliBoxDemo/1.0; +metadata-indexing-only)'

SOURCES = [
    {'id':'officeplus', 'name':'OfficePLUS（微软官方·国内）', 'url':'https://www.officeplus.cn/',
     'cat':'PPT 模板', 'note':'免费 PPT 模板，版权归原作者'},
    {'id':'presentationgo', 'name':'PresentationGO（国外免费）', 'url':'https://www.presentationgo.com/presentation/category/templates/',
     'cat':'PPT 模板', 'note':'Free PowerPoint / Google Slides templates'},
    {'id':'slidescarnival', 'name':'SlidesCarnival（国外免费）', 'url':'https://www.slidescarnival.com/',
     'cat':'PPT 模板', 'note':'Free presentation templates'},
    {'id':'fpppt', 'name':'Free Power Point Templates（国外免费）', 'url':'https://www.free-power-point-templates.com/themes/',
     'cat':'PPT 模板', 'note':'Free PowerPoint templates'},
    {'id':'vertex_word', 'name':'Vertex42 Word（国外免费）', 'url':'https://www.vertex42.com/WordTemplates/',
     'cat':'Word 模板', 'note':'Free Word templates · 合同/简历/信函'},
    {'id':'vertex_excel', 'name':'Vertex42 Excel（国外免费）', 'url':'https://www.vertex42.com/ExcelTemplates/',
     'pages':['https://www.vertex42.com/ExcelTemplates/budgets.html',
              'https://www.vertex42.com/ExcelTemplates/invoice-templates.html',
              'https://www.vertex42.com/ExcelTemplates/excel-project-management.html',
              'https://www.vertex42.com/ExcelTemplates/timesheets.html'],
     'cat':'Excel 模板', 'note':'Free Excel templates · 预算/发票/排期'},
    {'id':'html5up', 'name':'HTML5 UP（国外免费网站模板）', 'url':'https://html5up.net/',
     'cat':'网站模板', 'note':'Free responsive HTML5 templates · CC BY'},
    {'id':'rgemail', 'name':'Really Good Emails（国外免费邮件模板）', 'url':'https://reallygoodemails.com/',
     'cat':'邮件模板', 'note':'Free email gallery · 欢迎/营销/通讯'},
    {'id':'fdr', 'name':'Free Design Resources（国外免费设计模板）',
     'url':'https://freedesignresources.net/category/free-templates/',
     'pages':['https://freedesignresources.net/category/free-templates/logo-templates/',
              'https://freedesignresources.net/category/free-templates/social-media/'],
     'cat':'设计模板', 'note':'Free logo / social media / print templates'},
]

def now(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def ensure_db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    cols = {r['name'] for r in c.execute('PRAGMA table_info(templates)')}
    for col, typ in [('external_url','TEXT'),('cover_url','TEXT'),('source_site','TEXT')]:
        if col not in cols:
            c.execute('ALTER TABLE templates ADD COLUMN %s %s' % (col, typ))
    c.execute('''CREATE TABLE IF NOT EXISTS crawl_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT, finished_at TEXT,
        source TEXT, source_name TEXT, found INTEGER, added INTEGER, error TEXT)''')
    c.commit(); c.close()

def fetch(url):
    r = requests.get(url, headers={'User-Agent':UA,'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8'},
                     timeout=25)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() in ('iso-8859-1',):
        r.encoding = r.apparent_encoding or 'utf-8'
    return r.text

def clean_title(s, limit=70):
    s = re.sub(r'\s+', ' ', (s or '')).strip(' ,|-—_')
    return s[:limit]

def slug_title(url):
    part = [p for p in url.rstrip('/').split('/') if p][-1]
    part = re.sub(r'-\d+$','',part)
    return clean_title(part.replace('-',' ').replace('_',' ').title())

def parse_source(src, html, base, limit):
    soup = BeautifulSoup(html, 'lxml')
    out, seen = [], set()
    sid = src['id']
    site = src['name'].split('（')[0]

    if sid == 'officeplus':
        nodes = soup.select('[class*="pptTemplateCard_cardContainer"]')
        for a in nodes:
            href = a.get('href','')
            if '/detail/' not in href: continue
            url = urljoin(base, href)
            if url in seen: continue
            seen.add(url)
            img = a.find('img', src=lambda s: s and not s.startswith('data:'))
            if not img:
                nos = a.find('noscript')
                img = BeautifulSoup(nos.get_text(), 'lxml').find('img') if nos else None
            title = clean_title((img.get('alt') if img else '') or (a.get('aria-label') or '').split(',')[0]) or slug_title(url)
            out.append(dict(title=title, url=url, cover=urljoin(base,img.get('src')) if img and img.get('src') else '', site='OfficePLUS'))

    elif sid in ('vertex_word','vertex_excel'):
        for img in soup.find_all('img'):
            alt = clean_title(img.get('alt',''))
            src_ = img.get('data-src') or img.get('src') or ''
            if src_.startswith('data:'): src_ = ''
            if not alt or 'Templates by' in alt or '/icons/' in src_: continue
            a = img.find_parent('a', href=True)
            if not a: continue
            href = a['href']
            if not re.search(r'/(WordTemplates|ExcelTemplates|resumes)/', href): continue
            url = urljoin(base, href)
            if url in seen: continue
            seen.add(url)
            title = re.sub(r'^Thumbnail\s*-\s*','',alt)
            cover = urljoin(base, src_) if src_ else ''
            out.append(dict(title=title[:60], url=url, cover=cover, site='Vertex42'))

    elif sid == 'html5up':
        for img in soup.find_all('img'):
            src_ = img.get('src') or ''
            if 'uploads/images/' not in src_: continue
            a = img.find_parent('a', href=True)
            if not a or not re.match(r'^/[a-z0-9-]+$', a['href']): continue
            url = urljoin(base, a['href'])
            if url in seen: continue
            seen.add(url)
            title = clean_title(img.get('alt','')) or slug_title(url)
            out.append(dict(title=title, url=url, cover=urljoin(base,src_), site='HTML5 UP'))

    elif sid == 'rgemail':
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not href.startswith('/emails/'): continue
            url = urljoin(base, href)
            if url in seen: continue
            img = a.find('img')
            if not img: continue
            raw = img.get('src') or img.get('data-src') or ''
            if '_next/image' in raw:
                inner = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query).get('url',[''])[0]
                cover = inner if inner.startswith('http') else urljoin(base,raw)
            else:
                cover = urljoin(base,raw) if raw and not raw.startswith('data:') else ''
            title = clean_title(img.get('alt','')) or clean_title(a.get_text(' ',strip=True)) or slug_title(url)
            if len(title) < 4: continue
            seen.add(url)
            out.append(dict(title=title[:70], url=url, cover=cover, site='Really Good Emails'))

    elif sid == 'fdr':
        junk = ('all-freebies','submit','about','contact','privacy','terms','advertise','login','register','feed')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if not re.match(r'^https://freedesignresources\.net/[a-z0-9]+(-[a-z0-9]+)+/$', href): continue
            if any(x in href for x in junk): continue
            url = href
            if url in seen: continue
            title, cover = slug_title(url), ''
            try:
                detail = BeautifulSoup(fetch(url), 'lxml')
                og = detail.find('meta', property='og:image')
                if og and og.get('content'): cover = og['content']
                h1 = detail.find('h1')
                if h1: title = clean_title(h1.get_text(' ',strip=True)) or title
            except Exception:
                pass
            if len(title) < 4 or not cover: continue
            seen.add(url)
            out.append(dict(title=title[:70], url=url, cover=cover, site='Free Design Resources'))

    else:
        pattern = {'presentationgo':'/presentation/', 'slidescarnival':'/template/', 'fpppt':'.html'}[sid]
        for a in soup.find_all('a', href=True):
            href = a['href']
            if pattern not in href: continue
            if '/category/' in href or href.startswith('#') or 'javascript' in href: continue
            if sid == 'slidescarnival' and re.search(r'/(es|pt-br|ja|ko|id|fr|de|ru|it)/', href): continue
            url = urljoin(base, href)
            if url in seen: continue
            img = a.find('img')
            title = clean_title(img.get('alt','')) if img and img.get('alt') else clean_title(a.get_text(' ',strip=True))
            if sid == 'presentationgo' or len(title) < 4: title = slug_title(url)
            if len(title) < 4: continue
            cover = ''
            if img:
                cover = img.get('data-src') or img.get('data-lazy-src') or img.get('src') or ''
                if cover.startswith('data:'): cover = ''
            seen.add(url)
            out.append(dict(title=title, url=url, cover=cover, site=site))
    return out[:limit]

def save(items, src, log_id):
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    added = 0
    cat = c.execute('SELECT id FROM categories WHERE name=?',(src['cat'],)).fetchone()
    for it in items:
        if c.execute('SELECT 1 FROM templates WHERE external_url=?',(it['url'],)).fetchone(): continue
        c.execute('''INSERT INTO templates(title,cat_id,cat_name,sub,description,tags,formats,style,colors,
                     file_id,uploader_id,status,downloads,created_at,source,external_url,cover_url,source_site)
                     VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,'approved',0,?,'crawled',?,?,?)''',
                  (it['title'], cat['id'] if cat else None, src['cat'], '网络精选',
                   '来自公开免费模板站点：'+it['site']+'。仅提供跳转索引，文件与版权归原作者所有。',
                   '["免费","外链","精选"]', '["外链"]', 'slide', '["#0ea5e9","#7dd3fc"]',
                   now(), it['url'], it['cover'], it['site']))
        added += 1
    c.execute('UPDATE crawl_log SET found=?,added=?,finished_at=? WHERE id=?',(len(items),added,now(),log_id))
    c.commit(); c.close()
    return added

def crawl(limit=12):
    ensure_db()
    results = []
    for src in SOURCES:
        cid = None
        c = sqlite3.connect(DB_PATH)
        cur = c.execute('INSERT INTO crawl_log(started_at,source,source_name) VALUES(?,?,?)',(now(),src['id'],src['name']))
        cid = cur.lastrowid; c.commit(); c.close()
        try:
            pages = src.get('pages') or [src['url']]
            items, seen = [], set()
            for page in pages:
                html = fetch(page)
                for it in parse_source(src, html, page, limit):
                    if it['url'] in seen: continue
                    seen.add(it['url']); items.append(it)
                    if len(items) >= limit: break
                if len(items) >= limit: break
                time.sleep(0.2)
            added = save(items, src, cid)
            results.append({'source':src['name'], 'found':len(items), 'added':added, 'error':''})
        except Exception as e:
            msg = '%s: %s' % (type(e).__name__, str(e)[:120])
            c = sqlite3.connect(DB_PATH)
            c.execute('UPDATE crawl_log SET error=?,finished_at=?,found=0,added=0 WHERE id=?',(msg,now(),cid))
            c.commit(); c.close()
            results.append({'source':src['name'], 'found':0, 'added':0, 'error':msg})
        time.sleep(0.6)  # 礼貌抓取
    return results

def status():
    ensure_db()
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row
    rows = c.execute('SELECT * FROM crawl_log ORDER BY id DESC LIMIT 20').fetchall()
    total = c.execute("SELECT COUNT(*) n FROM templates WHERE source='crawled'").fetchone()['n']
    c.close()
    return {'total':total, 'sources':SOURCES, 'logs':[dict(r) for r in rows]}

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv)>1 else 12
    for r in crawl(n):
        print('%-45s found=%-3d added=%-3d %s' % (r['source'],r['found'],r['added'],r['error']))

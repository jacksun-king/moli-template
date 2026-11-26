# -*- coding: utf-8 -*-
"""模力盒 · 本地全栈服务（Python 标准库 + SQLite）
启动: python server.py  → http://127.0.0.1:8765
"""
import os, json, sqlite3, hashlib, secrets, mimetypes, urllib.parse, cgi, shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'data', 'site.db')
UPLOAD_DIR = os.path.join(ROOT, 'uploads')
MAX_FILE = 50 * 1024 * 1024
ALLOWED_EXT = {'pptx','ppt','key','docx','doc','xlsx','xls','zip','pdf','png','jpg','jpeg','webp','txt','html','psd','eml'}

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def hash_pw(pw):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt, 200000)
    return salt.hex() + ':' + dk.hex()

def verify_pw(pw, stored):
    try:
        salt, digest = stored.split(':')
        dk = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), bytes.fromhex(salt), 200000)
        return secrets.compare_digest(dk.hex(), digest)
    except Exception:
        return False

def init_db():
    c = db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE COLLATE NOCASE,
      email TEXT NOT NULL UNIQUE COLLATE NOCASE,
      password TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions(
      token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS categories(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE, icon TEXT NOT NULL DEFAULT '📁',
      description TEXT NOT NULL DEFAULT '', subs TEXT NOT NULL DEFAULT '[]', sort INTEGER NOT NULL DEFAULT 0,
      is_system INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS files(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      original_name TEXT NOT NULL, stored_name TEXT NOT NULL,
      size INTEGER NOT NULL, mime TEXT NOT NULL,
      uploader_id INTEGER NOT NULL, created_at TEXT NOT NULL,
      FOREIGN KEY(uploader_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS templates(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL, cat_id INTEGER, cat_name TEXT NOT NULL, sub TEXT NOT NULL DEFAULT '',
      description TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '[]',
      formats TEXT NOT NULL DEFAULT '[]', style TEXT NOT NULL DEFAULT 'doc',
      colors TEXT NOT NULL DEFAULT '["#6366f1","#a5b4fc"]',
      file_id INTEGER, uploader_id INTEGER, status TEXT NOT NULL DEFAULT 'pending',
      downloads INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'user',
      FOREIGN KEY(cat_id) REFERENCES categories(id) ON DELETE SET NULL,
      FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE SET NULL,
      FOREIGN KEY(uploader_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_tpl_status ON templates(status);
    CREATE INDEX IF NOT EXISTS idx_tpl_uploader ON templates(uploader_id);
    CREATE TABLE IF NOT EXISTS requests(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      template_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
      action TEXT NOT NULL, reason TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending', handle_note TEXT NOT NULL DEFAULT '',
      handled_by INTEGER, created_at TEXT NOT NULL, handled_at TEXT NOT NULL DEFAULT '',
      FOREIGN KEY(template_id) REFERENCES templates(id) ON DELETE CASCADE,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    ''')
    if c.execute('SELECT COUNT(*) n FROM categories').fetchone()['n'] == 0:
        seeds = [
            ('PPT 模板','📊','汇报、提案、发布会，一页搞定',['商务汇报','工作总结','教育培训','产品发布','数据分析','创意设计','答辩路演','婚礼策划'],'slide'),
            ('Word 模板','📄','简历、报告、合同，开箱即用',['简历模板','工作报告','合同协议','论文文档','计划总结','表格表单'],'doc'),
            ('Excel 模板','📈','财务、进度、看板，数据说话',['财务报表','项目进度','考勤统计','库存管理','数据看板'],'sheet'),
            ('网站模板','🌐','官网、商城、落地页，快速上线',['企业官网','个人博客','电商商城','落地页','后台管理','作品集'],'browser'),
            ('邮件模板','✉️','商务、营销、祝福，一封就够',['商务邮件','营销推广','节日祝福','欢迎邮件','活动邀请'],'mail'),
            ('设计模板','🎨','海报、名片、封面，灵感即取',['海报','名片','封面','社交媒体','品牌视觉'],'poster'),
        ]
        for i,(name,icon,desc,subs,style) in enumerate(seeds):
            c.execute('INSERT INTO categories(name,icon,description,subs,sort) VALUES(?,?,?,?,?)',
                      (name,icon,desc,json.dumps(subs,ensure_ascii=False),i))
        tpl_seed = {
          'PPT 模板': ['极简商务汇报 PPT|商务汇报|留白克制、逻辑清晰，适合季度/年度经营汇报','2026 年终工作总结|工作总结|数据图表齐全，一页讲清全年成果与规划','互联网产品发布会|产品发布|科技感视觉，产品亮点一眼抓住观众','数据分析报告模板|数据分析|内置常用图表与配色，分析报告更专业','高校答辩通用模板|答辩路演|学术规范版式，毕业答辩/课题汇报都适用','创意提案展示|创意设计|撞色编排，广告与创意提案更有记忆点','员工培训课件|教育培训|章节结构完整，新员工培训直接套用','浪漫婚礼策划案|婚礼策划|柔美插画风格，记录与策划你的特别日子'],
          'Word 模板': ['极简专业简历|简历模板|ATS 友好排版，一页突出你的核心竞争力','年度工作报告|工作报告|目标、成果、反思、计划，结构一步到位','项目合作合同|合同协议|条款清晰，双方权责一目了然','毕业论文格式模板|论文文档|符合高校规范，目录/引用/页眉自动排版','活动策划方案|计划总结|从背景到预算，活动方案完整框架','岗位职责说明书|表格表单|岗位信息标准化，HR 常用模板','中文求职信模板|简历模板|措辞得体，快速写出有温度的求职信','会议纪要模板|工作报告|议题、结论、待办三栏记录，会后不扯皮'],
          'Excel 模板': ['公司财务报表|财务报表|资产负债、利润表一体化，公式已内置','项目进度看板|项目进度|甘特图式排期，任务状态实时更新','员工考勤统计表|考勤统计|自动汇总出勤、请假与加班数据','库存管理系统|库存管理|入库出库自动计算，低库存预警','销售数据看板|数据看板|多维度图表联动，业绩一眼看清','个人记账本|财务报表|分类记账 + 月度统计，理财从记录开始','任务跟踪表|项目进度|轻量任务清单，团队协作不漏项','客户信息管理|数据看板|客户档案、跟进记录集中管理'],
          '网站模板': ['科技企业官网|企业官网|响应式首页 + 关于/产品/联系页','极简个人博客|个人博客|阅读体验优先，支持文章列表与详情','时尚电商商城|电商商城|商品列表、购物车、结算页全套','SaaS 产品落地页|落地页|高转化结构：痛点、功能、价格、CTA','后台管理仪表盘|后台管理|侧边栏 + 数据卡片 + 表格，通用性强','设计师作品集|作品集|大图瀑布流，设计师展示首选','餐厅预约网站|企业官网|菜单展示 + 在线订座，餐饮行业适配','在线课程平台|落地页|课程卡片、讲师介绍、报名入口齐全'],
          '邮件模板': ['商务合作邮件|商务邮件|正式得体，合作邀约打开率更高','新品营销推广|营销推广|视觉焦点突出，引导点击转化','圣诞节日祝福|节日祝福|温暖插画风，客户维护好帮手','用户欢迎邮件|欢迎邮件|新用户首封邮件，建立第一印象','活动邀请函|活动邀请|时间地点 RSVP 信息结构完整','月度产品通讯|营销推广|Newsletter 版式，内容模块化','客户感谢信|商务邮件|真诚不套路，维护长期客户关系','生日祝福邮件|节日祝福|轻松愉快，品牌好感度拉满'],
          '设计模板': ['简约活动海报|海报|大标题 + 留白，市集/讲座/沙龙通用','商务名片设计|名片|正反面成套，印刷尺寸已校准','书籍封面模板|封面|文艺与商业两种风格，可替换书名','社交媒体配图|社交媒体|小红书/公众号/朋友圈多尺寸','品牌 Logo 提案|品牌视觉|图形 + 字体 + 色彩规范一页呈现','招聘宣传海报|海报|岗位信息清晰，校招社招都能用','电子贺卡设计|封面|动态风格，节日祝福更走心','个人名片卡片|名片|竖版创意排版，自由职业者适用'],
        }
        palettes = [['#6366f1','#a5b4fc'],['#0ea5e9','#7dd3fc'],['#f43f5e','#fda4af'],['#10b981','#6ee7b7'],['#f59e0b','#fcd34d'],['#8b5cf6','#d8b4fe'],['#3b82f6','#93c5fd'],['#ec4899','#fbcfe8']]
        for cat in c.execute('SELECT * FROM categories ORDER BY sort').fetchall():
            style = next(s for n,i,d,ss,s in seeds if n == cat['name'])
            for i,row in enumerate(tpl_seed[cat['name']]):
                title, sub, desc = row.split('|')
                tags = ['示例','可编辑','通用']
                fmt = {'PPT 模板':'PPTX','Word 模板':'DOCX','Excel 模板':'XLSX','网站模板':'HTML','邮件模板':'HTML','设计模板':'PNG'}[cat['name']]
                c.execute('''INSERT INTO templates(title,cat_id,cat_name,sub,description,tags,formats,style,colors,file_id,uploader_id,status,downloads,created_at,source)
                             VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,'approved',?,?,'seed')''',
                          (title,cat['id'],cat['name'],sub,desc,json.dumps(tags,ensure_ascii=False),json.dumps([fmt]),style,json.dumps(palettes[i%len(palettes)]),1200+i*137,now()))
    # 兼容旧库：分类系统标记 + 默认「其他模板」
    cols = {r['name'] for r in c.execute('PRAGMA table_info(categories)')}
    if 'is_system' not in cols:
        c.execute('ALTER TABLE categories ADD COLUMN is_system INTEGER NOT NULL DEFAULT 0')
    if not c.execute("SELECT 1 FROM categories WHERE name='其他模板'").fetchone():
        sort = c.execute('SELECT COALESCE(MAX(sort),-1)+1 n FROM categories').fetchone()['n']
        c.execute("INSERT INTO categories(name,icon,description,subs,sort,is_system) VALUES('其他模板','📦','未归类模板统一存放（系统分类，不可删除）',?,?,1)",
                  (json.dumps(['未分类'],ensure_ascii=False),sort))
    c.commit(); c.close()
    # 采集引擎新增字段（兼容旧库）
    import crawler
    crawler.ensure_db()

class Handler(BaseHTTPRequestHandler):
    server_version = 'MoliBox/1.0'

    def log_message(self, fmt, *args):
        print('[%s] %s' % (now(), fmt % args))

    # ---------- helpers ----------
    def send_json(self, code, obj, extra=None):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control','no-store')
        for k,v in (extra or {}).items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(body)

    def body_json(self):
        try:
            length = int(self.headers.get('Content-Length','0'))
            return json.loads(self.rfile.read(length).decode('utf-8') or '{}')
        except Exception:
            return {}

    def current_user(self):
        cookie = self.headers.get('Cookie','')
        token = None
        for part in cookie.split(';'):
            if part.strip().startswith('moli_token='):
                token = part.strip().split('=',1)[1]
        if not token: return None
        c = db()
        row = c.execute('''SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?''',(token,)).fetchone()
        c.close()
        return row

    def require_user(self):
        u = self.current_user()
        if not u: self.send_json(401, {'error':'请先登录'}); return None
        return u

    def require_admin(self):
        u = self.current_user()
        if not u: self.send_json(401, {'error':'请先登录'}); return None
        if u['role'] != 'admin': self.send_json(403, {'error':'需要管理员权限'}); return None
        return u

    def set_token(self, token):
        return {'Set-Cookie': 'moli_token=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000' % token}

    def tpl_out(self, row, c):
        d = dict(row)
        for k in ('external_url','cover_url','source_site'): d.setdefault(k,'')
        d['tags'] = json.loads(d.get('tags') or '[]')
        d['formats'] = json.loads(d.get('formats') or '[]')
        d['colors'] = json.loads(d.get('colors') or '[]')
        uploader = c.execute('SELECT id,username FROM users WHERE id=?',(d.get('uploader_id'),)).fetchone() if d.get('uploader_id') else None
        d['uploader_name'] = uploader['username'] if uploader else '系统示例'
        d.pop('uploader_id', None)
        return d

    # ---------- 静态文件 ----------
    def serve_static(self, path):
        if path in ('','/'): path = '/index.html'
        rel = urllib.parse.unquote(path).lstrip('/')
        full = os.path.normpath(os.path.join(ROOT, rel))
        if not full.startswith(ROOT): self.send_json(403,{'error':'禁止访问'}); return
        if not os.path.isfile(full): self.send_json(404,{'error':'页面不存在'}); return
        mime = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        if mime.startswith('text/') or mime in ('application/javascript','application/json'):
            mime += '; charset=utf-8'
        with open(full,'rb') as f: data = f.read()
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-cache')
        self.end_headers(); self.wfile.write(data)

    # ---------- GET ----------
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        p = u.path
        c = db()
        try:
            if p == '/api/me':
                user = self.current_user()
                safe = {k:user[k] for k in ('id','username','email','role','created_at')} if user else None
                return self.send_json(200, {'user': safe})
            if p == '/api/crawl/status':
                if not self.current_user(): return self.send_json(401,{'error':'请先登录'})
                import crawler
                return self.send_json(200, crawler.status())
            if p == '/api/categories':
                rows = c.execute('SELECT * FROM categories ORDER BY sort,id').fetchall()
                out = []
                for r in rows:
                    d = dict(r); d['subs'] = json.loads(d['subs']); out.append(d)
                return self.send_json(200, {'categories': out})
            if p == '/api/templates':
                cat = q.get('cat',[''])[0]; sub = q.get('sub',[''])[0]; kw = q.get('q',[''])[0].strip()
                mine = q.get('mine',['0'])[0] == '1'
                user = self.current_user()
                sql = 'SELECT * FROM templates WHERE 1=1'; args = []
                if mine:
                    if not user: return self.send_json(401,{'error':'请先登录'})
                    sql += ' AND uploader_id=?'; args.append(user['id'])
                else:
                    if user and user['role']=='admin' and q.get('all',['0'])[0]=='1': pass
                    else: sql += " AND status='approved'"
                if cat: sql += ' AND cat_name=?'; args.append(cat)
                if sub: sql += ' AND sub=?'; args.append(sub)
                if kw:
                    sql += ' AND (title LIKE ? OR description LIKE ? OR sub LIKE ? OR tags LIKE ?)'
                    args += ['%'+kw+'%']*4
                sql += ' ORDER BY downloads DESC, id DESC'
                rows = c.execute(sql,args).fetchall()
                return self.send_json(200, {'templates':[self.tpl_out(r,c) for r in rows]})
            if p == '/api/requests':
                admin = self.require_admin()
                if not admin: return
                rows = c.execute('''SELECT r.*, t.title template_title, t.status tpl_status, u.username
                    FROM requests r JOIN templates t ON t.id=r.template_id
                    JOIN users u ON u.id=r.user_id
                    ORDER BY (r.status='pending') DESC, r.id DESC''').fetchall()
                return self.send_json(200,{'requests':[dict(x) for x in rows]})
            if p == '/api/requests/mine':
                user = self.require_user()
                if not user: return
                rows = c.execute('''SELECT r.*, t.title template_title, t.status tpl_status
                    FROM requests r JOIN templates t ON t.id=r.template_id
                    WHERE r.user_id=? ORDER BY r.id DESC''',(user['id'],)).fetchall()
                return self.send_json(200,{'requests':[dict(x) for x in rows]})
            if p == '/api/templates/stats':
                user = self.require_user()
                if not user: return
                if user['role']=='admin':
                    row = c.execute('''SELECT (SELECT COUNT(*) FROM users) users,
                        (SELECT COUNT(*) FROM templates) templates,
                        (SELECT COUNT(*) FROM templates WHERE status='pending') pending,
                        (SELECT COUNT(*) FROM templates WHERE status='unlisted') unlisted,
                        (SELECT COUNT(*) FROM requests WHERE status='pending') requests,
                        (SELECT COUNT(*) FROM files) files,
                        (SELECT COALESCE(SUM(downloads),0) FROM templates) downloads''').fetchone()
                else:
                    row = c.execute('''SELECT (SELECT COUNT(*) FROM templates WHERE uploader_id=?) templates,
                        (SELECT COUNT(*) FROM templates WHERE uploader_id=? AND status='pending') pending,
                        (SELECT COUNT(*) FROM requests WHERE user_id=? AND status='pending') requests''',(user['id'],user['id'],user['id'])).fetchone()
                return self.send_json(200, dict(row))
            if p.startswith('/api/users/'):
                if not self.current_user(): return self.send_json(401,{'error':'请先登录'})
                uid = p.split('/')[-1]
                row = c.execute('SELECT id,username,role,created_at FROM users WHERE id=? OR username=?',(uid,uid)).fetchone()
                if not row: return self.send_json(404,{'error':'用户不存在'})
                d = dict(row)
                real_id = row['id']
                d['upload_count'] = c.execute('SELECT COUNT(*) n FROM templates WHERE uploader_id=?',(real_id,)).fetchone()['n']
                d['approved_count'] = c.execute("SELECT COUNT(*) n FROM templates WHERE uploader_id=? AND status='approved'",(real_id,)).fetchone()['n']
                return self.send_json(200, {'user':d})
            if p == '/api/users':
                admin = self.require_admin()
                if not admin: return
                rows = c.execute('''SELECT u.id,u.username,u.email,u.role,u.created_at,
                    (SELECT COUNT(*) FROM templates t WHERE t.uploader_id=u.id) uploads
                    FROM users u ORDER BY u.id''').fetchall()
                return self.send_json(200,{'users':[dict(r) for r in rows]})
            if p == '/api/files':
                admin = self.require_admin()
                if not admin: return
                rows = c.execute('''SELECT f.id,f.original_name,f.size,f.mime,f.created_at,u.username uploader
                    FROM files f JOIN users u ON u.id=f.uploader_id ORDER BY f.id DESC''').fetchall()
                return self.send_json(200,{'files':[dict(r) for r in rows]})
            if p == '/api/download':
                user = self.require_user()
                if not user: return self.send_json(401,{'error':'登录后才能下载模板'})
                tid = q.get('id',[''])[0]
                row = c.execute('''SELECT t.*,f.stored_name,f.original_name,f.mime FROM templates t
                    LEFT JOIN files f ON f.id=t.file_id WHERE t.id=? AND t.status='approved' ''',(tid,)).fetchone()
                if not row: return self.send_json(404,{'error':'模板不存在或未审核通过'})
                if not row['stored_name']:
                    return self.send_json(400,{'error':'这是内置示例模板，没有可下载文件；请上传你自己的模板文件'})
                path = os.path.join(UPLOAD_DIR,row['stored_name'])
                if not os.path.isfile(path): return self.send_json(404,{'error':'文件已丢失'})
                c.execute('UPDATE templates SET downloads=downloads+1 WHERE id=?',(tid,)); c.commit()
                with open(path,'rb') as f: data = f.read()
                name = urllib.parse.quote(row['original_name'])
                self.send_response(200)
                self.send_header('Content-Type', row['mime'] or 'application/octet-stream')
                self.send_header('Content-Disposition', "attachment; filename*=UTF-8''%s" % name)
                self.send_header('Content-Length',str(len(data)))
                self.end_headers(); self.wfile.write(data)
                return
            return self.serve_static(p)
        finally:
            c.close()

    # ---------- POST ----------
    def do_POST(self):
        u = urllib.parse.urlparse(self.path); p = u.path
        c = db()
        try:
            if p == '/api/register':
                d = self.body_json()
                username = (d.get('username') or '').strip(); email = (d.get('email') or '').strip()
                password = d.get('password') or ''
                if len(username)<2 or len(username)>30: return self.send_json(400,{'error':'用户名需 2-30 个字符'})
                if '@' not in email: return self.send_json(400,{'error':'邮箱格式不正确'})
                if len(password)<6: return self.send_json(400,{'error':'密码至少 6 位'})
                if c.execute('SELECT 1 FROM users WHERE username=? OR email=?',(username,email)).fetchone():
                    return self.send_json(400,{'error':'用户名或邮箱已被注册'})
                role = 'admin' if c.execute('SELECT COUNT(*) n FROM users').fetchone()['n']==0 else 'user'
                c.execute('INSERT INTO users(username,email,password,role,created_at) VALUES(?,?,?,?,?)',
                          (username,email,hash_pw(password),role,now()))
                uid = c.execute('SELECT last_insert_rowid() id').fetchone()['id']
                token = secrets.token_urlsafe(32)
                c.execute('INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)',(token,uid,now()))
                c.commit()
                return self.send_json(200,{'ok':True,'user':{'id':uid,'username':username,'role':role},'first_admin':role=='admin'},self.set_token(token))
            if p == '/api/login':
                d = self.body_json(); account=(d.get('account') or '').strip(); password=d.get('password') or ''
                row = c.execute('SELECT * FROM users WHERE username=? OR email=?',(account,account)).fetchone()
                if not row or not verify_pw(password,row['password']):
                    return self.send_json(401,{'error':'账号或密码错误'})
                token = secrets.token_urlsafe(32)
                c.execute('INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)',(token,row['id'],now()))
                c.commit()
                return self.send_json(200,{'ok':True,'user':{'id':row['id'],'username':row['username'],'role':row['role']}},self.set_token(token))
            if p == '/api/logout':
                cookie=self.headers.get('Cookie','')
                for part in cookie.split(';'):
                    if part.strip().startswith('moli_token='):
                        c.execute('DELETE FROM sessions WHERE token=?',(part.strip().split('=',1)[1],))
                c.commit()
                return self.send_json(200,{'ok':True},{'Set-Cookie':'moli_token=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax'})
            if p == '/api/categories':
                admin = self.require_admin()
                if not admin: return
                d = self.body_json()
                name = (d.get('name') or '').strip()
                if not name: return self.send_json(400,{'error':'请填写分类名称'})
                if c.execute('SELECT 1 FROM categories WHERE name=?',(name,)).fetchone():
                    return self.send_json(400,{'error':'分类名称已存在'})
                subs = d.get('subs') if isinstance(d.get('subs'),list) else []
                sort = c.execute('SELECT COALESCE(MAX(sort),-1)+1 n FROM categories').fetchone()['n']
                c.execute('INSERT INTO categories(name,icon,description,subs,sort) VALUES(?,?,?,?,?)',
                          (name,d.get('icon') or '📁',d.get('description') or '',json.dumps(subs,ensure_ascii=False),sort))
                c.commit()
                return self.send_json(200,{'ok':True})
            if p == '/api/requests':
                user = self.require_user()
                if not user: return
                d = self.body_json()
                tid = d.get('template_id') or d.get('id')
                action = d.get('action')
                reason = (d.get('reason') or '').strip()
                if action not in ('list','unlist'): return self.send_json(400,{'error':'申请类型无效'})
                if len(reason)<5 or len(reason)>300: return self.send_json(400,{'error':'请填写 5-300 字的申请理由'})
                t = c.execute('SELECT * FROM templates WHERE id=?',(tid,)).fetchone()
                if not t: return self.send_json(404,{'error':'模板不存在'})
                if t['uploader_id']!=user['id']: return self.send_json(403,{'error':'只能对自己的模板提出申请'})
                if action=='list' and t['status'] not in ('rejected','unlisted'):
                    return self.send_json(400,{'error':'当前状态无需申请上架'})
                if action=='unlist' and t['status']!='approved':
                    return self.send_json(400,{'error':'只有已上架的模板才能申请下架'})
                if c.execute("SELECT 1 FROM requests WHERE template_id=? AND status='pending'",(tid,)).fetchone():
                    return self.send_json(400,{'error':'该模板已有待处理申请，请等待处理结果'})
                c.execute('''INSERT INTO requests(template_id,user_id,action,reason,status,created_at)
                             VALUES(?,?,?,?,'pending',?)''',(tid,user['id'],action,reason,now()))
                c.commit()
                return self.send_json(200,{'ok':True,'message':'申请已提交，等待管理员处理'})
            if p == '/api/crawl':
                admin = self.require_admin()
                if not admin: return
                n = int((self.body_json().get('limit') or 12))
                n = max(1, min(n, 40))
                import crawler
                results = crawler.crawl(n)
                return self.send_json(200, {'ok':True, 'results':results,
                                            'total':sum(r['added'] for r in results)})
            if p == '/api/me/password':
                user = self.require_user()
                if not user: return
                d = self.body_json()
                if not verify_pw(d.get('old') or '',user['password']): return self.send_json(400,{'error':'原密码不正确'})
                new = d.get('new') or ''
                if len(new)<6: return self.send_json(400,{'error':'新密码至少 6 位'})
                c.execute('UPDATE users SET password=? WHERE id=?',(hash_pw(new),user['id'])); c.commit()
                return self.send_json(200,{'ok':True})
            if p == '/api/upload':
                user = self.require_user()
                if not user: return
                ctype = self.headers.get('Content-Type','')
                if 'multipart/form-data' not in ctype: return self.send_json(400,{'error':'请使用表单上传'})
                fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                      environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':ctype,
                                               'CONTENT_LENGTH':self.headers.get('Content-Length','0')})
                def val(k):
                    v = fs.getfirst(k,'')
                    return v if isinstance(v,str) else ''
                title=val('title').strip(); cat_name=val('cat'); sub=val('sub'); desc=val('description').strip()
                tags=[x.strip() for x in val('tags').split(',') if x.strip()][:6]
                if not title: return self.send_json(400,{'error':'请填写模板名称'})
                cat = c.execute('SELECT * FROM categories WHERE name=?',(cat_name,)).fetchone()
                if not cat: return self.send_json(400,{'error':'请选择有效分类'})
                if not sub: sub = json.loads(cat['subs'])[0] if json.loads(cat['subs']) else '通用'
                item = fs['file'] if 'file' in fs else None
                if item is None or not getattr(item,'filename',None): return self.send_json(400,{'error':'请选择文件'})
                filename = os.path.basename(str(item.filename))
                ext = filename.rsplit('.',1)[-1].lower() if '.' in filename else ''
                if ext not in ALLOWED_EXT: return self.send_json(400,{'error':'不支持的文件类型，允许：'+', '.join(sorted(ALLOWED_EXT))})
                data = item.file.read(MAX_FILE+1)
                if len(data)>MAX_FILE: return self.send_json(400,{'error':'文件不能超过 50MB'})
                stored = secrets.token_hex(16)+'.'+ext
                with open(os.path.join(UPLOAD_DIR,stored),'wb') as f: f.write(data)
                mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                c.execute('INSERT INTO files(original_name,stored_name,size,mime,uploader_id,created_at) VALUES(?,?,?,?,?,?)',
                          (filename,stored,len(data),mime,user['id'],now()))
                fid = c.execute('SELECT last_insert_rowid() id').fetchone()['id']
                style = json.loads('{"PPT 模板":"slide","Word 模板":"doc","Excel 模板":"sheet","网站模板":"browser","邮件模板":"mail","设计模板":"poster"}').get(cat_name,'doc')
                colors = '["#6366f1","#a5b4fc"]'
                c.execute('''INSERT INTO templates(title,cat_id,cat_name,sub,description,tags,formats,style,colors,file_id,uploader_id,status,downloads,created_at,source)
                             VALUES(?,?,?,?,?,?,?,?,?,?,?,'pending',0,?,'user')''',
                          (title,cat['id'],cat_name,sub,desc,json.dumps(tags,ensure_ascii=False),json.dumps([ext.upper()]),style,colors,fid,user['id'],now()))
                c.commit()
                return self.send_json(200,{'ok':True,'message':'上传成功，等待管理员审核'})
            return self.send_json(404,{'error':'接口不存在'})
        finally:
            c.close()

    # ---------- PATCH / PUT / DELETE ----------
    def do_PATCH(self):
        u = urllib.parse.urlparse(self.path); p = u.path
        c = db()
        try:
            admin = self.require_admin()
            if not admin: return
            d = self.body_json()
            if p.startswith('/api/templates/'):
                tid = p.split('/')[-1]
                status = d.get('status')
                if status not in ('approved','rejected','pending','unlisted'): return self.send_json(400,{'error':'状态无效'})
                c.execute('UPDATE templates SET status=? WHERE id=?',(status,tid)); c.commit()
                return self.send_json(200,{'ok':True})
            if p.startswith('/api/requests/'):
                rid = p.split('/')[-1]
                row = c.execute('SELECT * FROM requests WHERE id=?',(rid,)).fetchone()
                if not row: return self.send_json(404,{'error':'申请不存在'})
                if row['status']!='pending': return self.send_json(400,{'error':'该申请已处理'})
                decision = d.get('decision') or d.get('status')
                if decision not in ('approve','reject'): return self.send_json(400,{'error':'处理结果无效'})
                note = (d.get('note') or '').strip()
                rstatus = 'approved' if decision=='approve' else 'rejected'
                if decision=='approve':
                    t = c.execute('SELECT status FROM templates WHERE id=?',(row['template_id'],)).fetchone()
                    if not t: return self.send_json(404,{'error':'模板已不存在'})
                    expect = ('rejected','unlisted') if row['action']=='list' else ('approved',)
                    if t['status'] not in expect:
                        return self.send_json(400,{'error':'模板状态已变化，无法执行该申请'})
                    c.execute('UPDATE templates SET status=? WHERE id=?',
                              ('approved' if row['action']=='list' else 'unlisted',row['template_id']))
                c.execute('''UPDATE requests SET status=?,handle_note=?,handled_by=?,handled_at=? WHERE id=?''',
                          (rstatus,note,admin['id'],now(),rid))
                c.commit()
                return self.send_json(200,{'ok':True})
            if p.startswith('/api/categories/'):
                cid = p.split('/')[-1]
                row = c.execute('SELECT * FROM categories WHERE id=?',(cid,)).fetchone()
                if not row: return self.send_json(404,{'error':'分类不存在'})
                name=(d.get('name') or row['name']).strip()
                icon=d.get('icon') or row['icon']; desc=d.get('description') if 'description' in d else row['description']
                subs=d.get('subs') if isinstance(d.get('subs'),list) else json.loads(row['subs'])
                c.execute('UPDATE categories SET name=?,icon=?,description=?,subs=? WHERE id=?',
                          (name,icon,desc,json.dumps(subs,ensure_ascii=False),cid))
                c.execute('UPDATE templates SET cat_name=? WHERE cat_id=?',(name,cid)); c.commit()
                return self.send_json(200,{'ok':True})
            if p.startswith('/api/users/'):
                uid = p.split('/')[-1]
                role = d.get('role')
                if role not in ('user','admin'): return self.send_json(400,{'error':'角色无效'})
                if int(uid)==admin['id'] and role!='admin': return self.send_json(400,{'error':'不能取消自己的管理员身份'})
                c.execute('UPDATE users SET role=? WHERE id=?',(role,uid)); c.commit()
                return self.send_json(200,{'ok':True})
            return self.send_json(404,{'error':'接口不存在'})
        finally: c.close()

    do_PUT = do_PATCH

    def do_DELETE(self):
        u = urllib.parse.urlparse(self.path); p = u.path
        c = db()
        try:
            user = self.current_user()
            if not user: return self.send_json(401,{'error':'请先登录'})
            admin = user['role']=='admin'
            if p == '/api/me':
                if admin and c.execute("SELECT COUNT(*) n FROM users WHERE role='admin'").fetchone()['n']<=1:
                    return self.send_json(400,{'error':'你是唯一管理员，无法注销；请先任命另一位管理员'})
                fids = [r['file_id'] for r in c.execute('SELECT file_id FROM templates WHERE uploader_id=? AND file_id IS NOT NULL',(user['id'],)).fetchall()]
                names = [r['stored_name'] for r in c.execute('SELECT stored_name FROM files WHERE uploader_id=?',(user['id'],)).fetchall()]
                c.execute('DELETE FROM users WHERE id=?',(user['id'],)); c.commit()
                for n in names:
                    try: os.remove(os.path.join(UPLOAD_DIR,n))
                    except OSError: pass
                return self.send_json(200,{'ok':True},{'Set-Cookie':'moli_token=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax'})
            if p.startswith('/api/templates/'):
                tid = p.split('/')[-1]
                row = c.execute('SELECT * FROM templates WHERE id=?',(tid,)).fetchone()
                if not row: return self.send_json(404,{'error':'模板不存在'})
                if not admin and row['uploader_id']!=user['id']: return self.send_json(403,{'error':'只能删除自己的模板'})
                if row['status']=='approved': return self.send_json(400,{'error':'请先下架该模板后再删除'})
                c.execute('DELETE FROM templates WHERE id=?',(tid,)); c.commit()
                return self.send_json(200,{'ok':True})
            if p.startswith('/api/categories/'):
                if not admin: return self.send_json(403,{'error':'需要管理员权限'})
                cid = p.split('/')[-1]
                row = c.execute('SELECT * FROM categories WHERE id=?',(cid,)).fetchone()
                if not row: return self.send_json(404,{'error':'分类不存在'})
                if row['is_system']: return self.send_json(400,{'error':'系统默认分类不可删除'})
                other = c.execute("SELECT * FROM categories WHERE name='其他模板' OR is_system=1 ORDER BY id LIMIT 1").fetchone()
                if not other:
                    sort = c.execute('SELECT COALESCE(MAX(sort),-1)+1 n FROM categories').fetchone()['n']
                    c.execute("INSERT INTO categories(name,icon,description,subs,sort,is_system) VALUES('其他模板','📦','未归类模板统一存放（系统分类，不可删除）',?,?,1)",
                              (json.dumps(['未分类'],ensure_ascii=False),sort))
                    oid = c.execute('SELECT last_insert_rowid() id').fetchone()['id']
                    other = c.execute('SELECT * FROM categories WHERE id=?',(oid,)).fetchone()
                subs = json.loads(other['subs'] or '[]')
                for x in c.execute('SELECT DISTINCT sub FROM templates WHERE cat_id=? OR cat_name=?',(cid,row['name'])).fetchall():
                    if x['sub'] and x['sub'] not in subs: subs.append(x['sub'])
                c.execute('UPDATE categories SET subs=? WHERE id=?',(json.dumps(subs,ensure_ascii=False),other['id']))
                c.execute('UPDATE templates SET cat_id=?,cat_name=? WHERE cat_id=? OR cat_name=?',
                          (other['id'],other['name'],cid,row['name']))
                c.execute('DELETE FROM categories WHERE id=?',(cid,)); c.commit()
                return self.send_json(200,{'ok':True,'message':'分类已删除，原有模板已归入「其他模板」'})
            if p.startswith('/api/users/'):
                if not admin: return self.send_json(403,{'error':'需要管理员权限'})
                uid = p.split('/')[-1]
                if int(uid)==user['id']: return self.send_json(400,{'error':'请从个人中心注销自己'})
                names = [r['stored_name'] for r in c.execute('SELECT stored_name FROM files WHERE uploader_id=?',(uid,)).fetchall()]
                c.execute('DELETE FROM users WHERE id=?',(uid,)); c.commit()
                for n in names:
                    try: os.remove(os.path.join(UPLOAD_DIR,n))
                    except OSError: pass
                return self.send_json(200,{'ok':True})
            if p.startswith('/api/files/'):
                if not admin: return self.send_json(403,{'error':'需要管理员权限'})
                fid = p.split('/')[-1]
                row = c.execute('SELECT * FROM files WHERE id=?',(fid,)).fetchone()
                if not row: return self.send_json(404,{'error':'文件不存在'})
                c.execute('UPDATE templates SET file_id=NULL,status=? WHERE file_id=?',('unlisted',fid))
                c.execute('DELETE FROM files WHERE id=?',(fid,)); c.commit()
                try: os.remove(os.path.join(UPLOAD_DIR,row['stored_name']))
                except OSError: pass
                return self.send_json(200,{'ok':True})
            return self.send_json(404,{'error':'接口不存在'})
        finally: c.close()

if __name__=='__main__':
    init_db()
    port = int(os.environ.get('PORT','8765'))
    print('模力盒服务已启动: http://127.0.0.1:%d' % port)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

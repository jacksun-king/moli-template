# 模力盒 · AI 模板站 / MoliBox · AI Template Hub

> 一个可注册的模板分享平台：用户上传模板、管理员审核上架、访客搜索下载；内置资源采集引擎，自动索引国内外免费模板。
> A register-based template sharing platform: users upload, admins review and publish, visitors search and download. Built in a crawler that indexes free templates from Chinese and international sources.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Cloudflare Tunnel](https://img.shields.io/badge/deploy-Cloudflare%20Tunnel-f68220?logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)

---

## 目录 / Table of Contents

- [功能特性 / Features](#功能特性--features)
- [技术栈 / Tech Stack](#技术栈--tech-stack)
- [快速开始 / Quick Start](#快速开始--quick-start)
- [账号与权限 / Accounts & Roles](#账号与权限--accounts--roles)
- [模板状态与审核流程 / Template Status & Review Flow](#模板状态与审核流程--template-status--review-flow)
- [资源采集引擎 / Crawler Engine](#资源采集引擎--crawler-engine)
- [目录结构 / Project Structure](#目录结构--project-structure)
- [API 参考 / API Reference](#api-参考--api-reference)
- [Cloudflare 一键部署 / One-Click Cloudflare Deploy](#cloudflare-一键部署--one-click-cloudflare-deploy)
- [安全说明 / Security Notes](#安全说明--security-notes)
- [常见问题 / FAQ](#常见问题--faq)

---

## 功能特性 / Features

| 中文 | English |
| --- | --- |
| **六大模板分类**：PPT、Word、Excel、网站、邮件、设计，各含二级场景筛选 | **Six categories**: PPT, Word, Excel, Web, Email, Design, each with sub-scene filters |
| **AI 找模板**：自然语言描述需求，关键词智能匹配推荐 | **AI template finder**: describe what you need in natural language and get keyword-matched results |
| **用户系统**：注册、登录、退出、修改密码、注销账户 | **User system**: register, login, logout, change password, delete account |
| **上传与审核**：登录后上传（≤50MB，白名单格式）；新模板待审核，通过后公开 | **Upload & review**: authenticated uploads (≤50MB, whitelisted types); new templates stay pending until approved |
| **上下架申请**：用户为自有模板申请上架/下架并填写理由，管理员审批 | **List/unlist requests**: users request publish/unpublish with a reason; admins approve or reject |
| **管理后台**：审核、模板/分类/用户/文件管理、资源采集、统计概览 | **Admin console**: review queue, template/category/user/file management, crawler, statistics |
| **系统分类保护**：「其他模板」不可删除；删除分类时其下模板自动归档 | **Protected system category**: "Other" cannot be deleted; templates are re-filed when a category is removed |
| **外链资源索引**：采集国内外免费模板的标题、封面、源站链接，不托管文件 | **External link indexing**: indexes titles, covers and source links of free templates; no file hosting |
| **响应式界面**：桌面与移动端自适应，卡片缩略图纯 CSS 绘制 | **Responsive UI**: desktop and mobile ready; thumbnails drawn with pure CSS |

---

## 技术栈 / Tech Stack

- **后端 / Backend**: Python 3.8+ 标准库 `http.server`（ThreadingHTTPServer），无 Web 框架依赖 / Python standard library only, no web framework
- **数据库 / Database**: SQLite（`data/site.db`），WAL 之外的常规模式，开启外键约束 / SQLite with foreign keys enabled
- **前端 / Frontend**: 原生 HTML / CSS / JavaScript，无构建步骤 / Vanilla HTML/CSS/JS, no build step
- **采集 / Crawler**: `requests` + `beautifulsoup4` + `lxml`
- **认证 / Auth**: HttpOnly Cookie 会话（PBKDF2-HMAC-SHA256，20 万次迭代）/ HttpOnly cookie sessions with PBKDF2-HMAC-SHA256 (200k iterations)
- **部署 / Deploy**: Cloudflare Tunnel（Quick Tunnel 临时地址 / Named Tunnel 固定域名）

> 采集引擎需要额外安装依赖，核心站点不需要。
> The crawler needs extra dependencies; the core site does not.

---

## 快速开始 / Quick Start

### 1. 安装依赖 / Install dependencies

核心站点零依赖，直接用系统 Python 即可。采集引擎需要：

The core site needs no third-party packages. The crawler requires:

```bash
pip install requests beautifulsoup4 lxml
```

### 2. 启动服务 / Start the server

```bash
cd template-site
python server.py
```

默认监听 `http://127.0.0.1:8765`。可通过环境变量修改端口：

Listens on `http://127.0.0.1:8765` by default. Override with the `PORT` variable:

```bash
PORT=9000 python server.py          # macOS / Linux
set PORT=9000 && python server.py   # Windows CMD
```

### 3. 创建管理员 / Create the admin

打开 `http://127.0.0.1:8765/auth.html` 注册。**第一个注册的用户自动成为管理员**，之后注册的均为普通用户。

Open `http://127.0.0.1:8765/auth.html` and register. **The first registered user automatically becomes admin**; all later users are regular members.

### 4. 页面入口 / Page entries

| 页面 / Page | 地址 / URL | 说明 / Description |
| --- | --- | --- |
| 首页 / Home | `/index.html` | 搜索、筛选、预览、下载 / Search, filter, preview, download |
| 登录注册 / Auth | `/auth.html` | 注册与登录 / Register and login |
| 个人中心 / Account | `/account.html` | 资料、密码、我的上传、上下架申请 / Profile, password, uploads, requests |
| 用户主页 / Profile | `/profile.html?user=<用户名>` | 查看他人公开信息 / View public user info |
| 管理后台 / Admin | `/admin.html` | 仅管理员 / Admin only |

---

## 账号与权限 / Accounts & Roles

| 功能 / Action | 访客 / Guest | 用户 / User | 管理员 / Admin |
| --- | :---: | :---: | :---: |
| 浏览与搜索模板 / Browse & search | ✅ | ✅ | ✅ |
| 下载模板 / Download | ❌ | ✅ | ✅ |
| 上传模板 / Upload | ❌ | ✅ | ✅ |
| 管理自己的资料与密码 / Manage own profile | ❌ | ✅ | ✅ |
| 申请自有模板上下架 / Request list/unlist | ❌ | ✅ | ✅ |
| 查看他人公开信息 / View public profiles | ✅ | ✅ | ✅ |
| 审核模板 / Review templates | ❌ | ❌ | ✅ |
| 管理分类/用户/文件 / Manage categories, users, files | ❌ | ❌ | ✅ |
| 运行采集引擎 / Run crawler | ❌ | ❌ | ✅ |

---

## 模板状态与审核流程 / Template Status & Review Flow

| 状态 / Status | 含义 / Meaning | 公开可见 / Public | 可删除 / Deletable |
| --- | --- | :---: | :---: |
| `pending` | 待审核 / Awaiting review | ❌ | ✅ |
| `approved` | 已上架 / Published | ✅ | ❌（须先下架 / must unlist first） |
| `rejected` | 已拒绝 / Rejected | ❌ | ✅ |
| `unlisted` | 已下架 / Unpublished | ❌ | ✅ |

**流程 / Flow**:

```text
用户上传 / User uploads
        ↓
    pending（待审核）
        ↓  管理员通过 / admin approves
    approved（已上架）
        ↓  用户申请 + 管理员同意 / user requests + admin approves
    unlisted（已下架）→ 可删除 / can be deleted
```

已上架模板不能直接删除，必须先下架——这条规则同时 enforce 在前端按钮和后端接口上。

Published templates cannot be deleted directly; they must be unlisted first. Enforced in both UI and API.

---

## 资源采集引擎 / Crawler Engine

引擎只索引**标题、封面图与源站链接**，不下载也不托管模板文件，规避版权与分发风险。点击外链卡片会跳转到原站下载。

The engine indexes **titles, cover images and source links only**. It never downloads or hosts template files, avoiding copyright and distribution risks. External cards link to the original site for download.

### 数据源 / Sources

| 来源 / Source | 地区 / Region | 分类 / Category | 说明 / Note |
| --- | --- | --- | --- |
| OfficePLUS | 国内 / China | PPT | 微软官方 / Microsoft official |
| PresentationGO | 国外 / Global | PPT | 免费 PPT / Google Slides |
| SlidesCarnival | 国外 / Global | PPT | 免费演示模板 / Free presentations |
| Free Power Point Templates | 国外 / Global | PPT | 免费主题 / Free themes |
| Vertex42 Word | 国外 / Global | Word | 合同/简历/信函 / Contracts, resumes, letters |
| Vertex42 Excel | 国外 / Global | Excel | 预算/发票/排期 / Budgets, invoices, schedules |
| HTML5 UP | 国外 / Global | 网站 / Web | 响应式 HTML5（CC BY） |
| Really Good Emails | 国外 / Global | 邮件 / Email | 欢迎/营销/通讯 / Welcome, marketing, newsletters |
| Free Design Resources | 国外 / Global | 设计 / Design | Logo/海报/印刷 / Logos, posters, print |

### 运行采集 / Run the crawler

```bash
# 命令行：每个来源采集 N 条（默认 12，最大 40）
# CLI: crawl N items per source (default 12, max 40)
python crawler.py 20
```

也可在管理后台「资源采集」页签操作，可查看数据源、设置数量、查看采集日志。重复链接自动去重。

Or use the **Crawler** tab in the admin console to inspect sources, set limits, and view logs. Duplicate links are skipped automatically.

> 修改 `crawler.py` 后需重启 `server.py` 才会生效。
> Restart `server.py` after editing `crawler.py`.

---

## 目录结构 / Project Structure

```text
template-site/
├── server.py               # 后端服务与全部 API / Backend server and all APIs
├── crawler.py              # 免费模板采集引擎 / Free template crawler
├── deploy_cloudflare.py    # Cloudflare 一键部署 / One-click Cloudflare deploy
├── deploy-cloudflare.bat   # Windows 双击部署入口 / Windows double-click deploy
├── index.html              # 首页 / Home page
├── auth.html               # 登录注册 / Login & register
├── account.html            # 个人中心 / User center
├── profile.html            # 用户公开主页 / Public profile
├── admin.html              # 管理后台 / Admin console
├── css/
│   ├── style.css           # 主样式 / Main styles
│   └── extra.css           # 后台与扩展样式 / Admin & extra styles
├── js/
│   ├── common.js           # 公共工具与会话 / Shared utils and session
│   ├── data.js             # 前端示例数据（历史保留）/ Legacy sample data
│   └── app.js              # 首页交互 / Home page logic
├── data/
│   ├── site.db             # SQLite 数据库 / SQLite database
│   ├── cloudflare_url.txt  # 最近一次公网地址 / Last public URL
│   └── server.log          # 服务日志 / Server log
├── uploads/                # 用户上传文件 / User uploads
└── bin/                    # 自动下载的 cloudflared / Auto-downloaded cloudflared
```

---

## API 参考 / API Reference

所有响应为 JSON。认证通过 Cookie `moli_token` 传递。All responses are JSON. Auth uses the `moli_token` cookie.

### 公开接口 / Public

| 方法 / Method | 路径 / Path | 说明 / Description |
| --- | --- | --- |
| GET | `/api/categories` | 分类列表 / List categories |
| GET | `/api/templates` | 模板列表；参数 `cat`、`sub`、`q`、`mine=1`、`all=1` / List templates; params `cat`, `sub`, `q`, `mine=1`, `all=1` |
| GET | `/api/users/<id或用户名>` | 用户公开信息 / Public user info |
| POST | `/api/register` | 注册 `{username,email,password}` / Register |
| POST | `/api/login` | 登录 `{account,password}` / Login |
| POST | `/api/logout` | 退出 / Logout |

### 需登录 / Authenticated

| 方法 / Method | 路径 / Path | 说明 / Description |
| --- | --- | --- |
| GET | `/api/me` | 当前用户 / Current user |
| GET | `/api/requests/mine` | 我的申请 / My requests |
| GET | `/api/templates/stats` | 个人/全站统计 / Personal or global stats |
| GET | `/api/crawl/status` | 采集状态（管理员）/ Crawler status (admin) |
| GET | `/api/download?id=<id>` | 下载模板文件 / Download template file |
| POST | `/api/upload` | multipart 上传 / Multipart upload |
| POST | `/api/requests` | 提交上下架申请 / Submit list/unlist request |
| POST | `/api/me/password` | 修改密码 `{old,new}` / Change password |
| DELETE | `/api/me` | 注销账户（本人）/ Delete own account |

### 管理员接口 / Admin only

| 方法 / Method | 路径 / Path | 说明 / Description |
| --- | --- | --- |
| GET | `/api/users` | 用户列表 / List users |
| GET | `/api/files` | 文件列表 / List files |
| GET | `/api/requests` | 全部申请 / All requests |
| POST | `/api/categories` | 新建分类 / Create category |
| POST | `/api/crawl` | 执行采集 `{limit}` / Run crawler |
| PATCH | `/api/templates/<id>` | 改状态 `{status}` / Change status |
| PATCH | `/api/requests/<id>` | 审批 `{decision, note}` / Decide request |
| PATCH | `/api/categories/<id>` | 改分类 / Update category |
| PATCH | `/api/users/<id>` | 改角色 `{role}` / Change role |
| DELETE | `/api/categories/<id>` | 删除分类（模板归入「其他模板」）/ Delete category (templates re-filed) |
| DELETE | `/api/users/<id>` | 删除用户 / Delete user |
| DELETE | `/api/files/<id>` | 删除文件 / Delete file |

---

## Cloudflare 一键部署 / One-Click Cloudflare Deploy

本项目是 Python 长驻服务 + 本地 SQLite，不能直接部署到 Cloudflare Pages。正确做法是用 **Cloudflare Tunnel**：本地服务照常运行，由隧道把它安全地暴露到公网 HTTPS，无需公网 IP、无需端口映射。

This project is a long-running Python service with local SQLite, so it cannot be hosted on Cloudflare Pages directly. The right approach is **Cloudflare Tunnel**: keep the local service running and expose it over public HTTPS with no public IP and no port forwarding.

### 模式 A：快速隧道（零配置，推荐先用这个）/ Mode A: Quick Tunnel (zero config)

```bash
python deploy_cloudflare.py
```

Windows 用户可直接双击 `deploy-cloudflare.bat`。

Windows users can double-click `deploy-cloudflare.bat`.

脚本会自动完成 / The script automatically:

1. 检测本地服务，未启动则拉起 / Detect the local service and start it if needed
2. 检测 `cloudflared`，缺失则从官方源下载到 `bin/` / Detect `cloudflared` and download it into `bin/` if missing
3. 建立隧道（HTTP/2 模式，规避国内 QUIC/UDP 限制）/ Establish the tunnel using HTTP/2 to avoid QUIC/UDP issues on Chinese networks
4. 打印公网 HTTPS 地址并写入 `data/cloudflare_url.txt` / Print the public HTTPS URL and save it to `data/cloudflare_url.txt`
5. `Ctrl+C` 时自动关闭隧道和它启动的本地服务 / Clean up the tunnel and the local service it started on `Ctrl+C`

输出示例 / Sample output:

```text
[deploy] 本地服务已在运行: http://127.0.0.1:8765
[deploy] 启动快速隧道（零配置临时地址，HTTP/2 模式）...
====================================================================
  公网地址: https://xxxx-yyyy-zzzz.trycloudflare.com
  地址已保存到 data/cloudflare_url.txt
====================================================================
服务运行中，按 Ctrl+C 停止。
```

> ⚠️ 快速隧道地址是**临时**的，每次重启都会变化，且无 SLA 保证，适合演示和测试。
> ⚠️ Quick Tunnel URLs are **temporary**, change on every restart, and have no SLA. Good for demos and testing.

### 模式 B：命名隧道（固定域名，适合长期使用）/ Mode B: Named Tunnel (stable domain)

1. 在 Cloudflare Zero Trust 后台创建 Tunnel，配置 public hostname 指向 `http://127.0.0.1:8765`，复制 token。
   Create a tunnel in Cloudflare Zero Trust, set a public hostname pointing to `http://127.0.0.1:8765`, and copy the token.
2. 带 token 启动 / Start with the token:

```bash
python deploy_cloudflare.py --token "你的token"
# 或用环境变量 / or via environment variable
set CLOUDFLARE_TUNNEL_TOKEN=你的token && python deploy_cloudflare.py
```

域名和证书由 Cloudflare 管理，地址固定不变。The domain and certificate are managed by Cloudflare, and the URL stays stable.

### 其他参数 / Other options

```bash
python deploy_cloudflare.py --port 9000      # 指定本地端口 / custom local port
python deploy_cloudflare.py --no-server      # 本地服务已手动启动 / server already running
python deploy_cloudflare.py --reinstall      # 强制重新下载 cloudflared / force re-download
```

### 部署到公网后的必做事项 / After going public

1. **立即注册第一个管理员账号** —— 第一个注册者拥有全部权限，不要让别人抢先。
   **Register the first admin account immediately** — the first registrant gets full privileges.
2. 修改 Admin 默认密码为强密码 / Use a strong password for the admin account.
3. 生产环境建议改用 Named Tunnel 并开启 Cloudflare Access 二次验证。
   For production, use a Named Tunnel and enable Cloudflare Access for a second auth layer.

---

## 安全说明 / Security Notes

- 密码使用 PBKDF2-HMAC-SHA256 + 随机盐 + 20 万次迭代存储，数据库中不保存明文。
  Passwords are stored with PBKDF2-HMAC-SHA256, random salt and 200k iterations; no plaintext is stored.
- 会话 Token 存于 HttpOnly + SameSite=Lax Cookie，降低 XSS 窃取风险。
  Session tokens live in HttpOnly + SameSite=Lax cookies to reduce XSS theft risk.
- 上传文件限制 50MB，扩展名白名单，存储时使用随机文件名防止路径穿越。
  Uploads are capped at 50MB with an extension whitelist and random stored filenames to prevent path traversal.
- 静态文件路径做了目录穿越校验；管理接口统一做角色校验（403）。
  Static paths are checked against traversal; all admin endpoints enforce role checks (403).
- `data/site.db` 含密码哈希，**不要提交到公开仓库**；如已提交，建议改密并从历史中移除。
  `data/site.db` contains password hashes — **never commit it to a public repo**. If already committed, rotate passwords and purge it from history.
- 本项目为演示原型，未实现邮件验证、速率限制、CSRF Token，生产使用前请补齐。
  This is a demo prototype: no email verification, rate limiting or CSRF tokens. Add these before production use.

---

## 常见问题 / FAQ

**Q: 采集到的模板能直接下载吗？**
**Q: Can I download crawled templates directly?**

不能。采集引擎只索引元数据，点击卡片会跳转源站，由源站提供下载。本站托管的模板只有用户上传且审核通过的文件。
No. The crawler indexes metadata only; cards link to the source site. Only user-uploaded, approved files are hosted here.

**Q: 内置模板为什么点下载没文件？**
**Q: Why do built-in templates have no file on download?**

内置模板是演示数据，没有实际文件。上传你自己的模板文件后即可真实下载。
Built-in templates are demo records without files. Upload your own file to get a real download.

**Q: 忘记密码怎么办？**
**Q: What if I forget my password?**

目前没有邮件找回功能。可请管理员在后台删除账号后重新注册，或直接操作数据库重置。
There is no email recovery yet. Ask an admin to delete the account and re-register, or reset directly in the database.

**Q: 为什么删除分类后模板还在？**
**Q: Why do templates remain after deleting a category?**

这是设计行为：删除分类时，其下模板会自动归入不可删除的系统分类「其他模板」，不会丢失。
By design: templates are moved to the undeletable system category "Other" instead of being lost.

**Q: Cloudflare 隧道提示 QUIC 超时？**
**Q: The tunnel reports QUIC timeouts?**

脚本已默认使用 HTTP/2。若仍有问题，说明本机到 Cloudflare 边缘的 443 出口受限，可换网络或改用 Named Tunnel。
The script already defaults to HTTP/2. If issues persist, outbound 443 to Cloudflare edge is restricted — try another network or a Named Tunnel.

---

## 许可证 / License

MIT License. 采集到的模板版权归原作者所有，本站仅提供链接索引，不承担内容责任。
MIT License. Crawled templates remain the property of their original authors; this site only indexes links and assumes no content liability.

---

*Made with ☕ and Python / 用 ☕ 和 Python 制作*

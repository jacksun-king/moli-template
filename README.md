# 模力盒 · AI 模板站

[English](README_EN.md) | 中文

> 一个可注册的模板分享平台：用户上传模板、管理员审核上架、访客搜索下载；内置资源采集引擎，自动索引国内外免费模板。

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Cloudflare Tunnel](https://img.shields.io/badge/deploy-Cloudflare%20Tunnel-f68220?logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [账号与权限](#账号与权限)
- [模板状态与审核流程](#模板状态与审核流程)
- [资源采集引擎](#资源采集引擎)
- [目录结构](#目录结构)
- [API 参考](#api-参考)
- [Cloudflare 一键部署](#cloudflare-一键部署)
- [安全说明](#安全说明)
- [常见问题](#常见问题)

---

## 功能特性

- **六大模板分类**：PPT、Word、Excel、网站、邮件、设计，各含二级场景筛选
- **AI 找模板**：自然语言描述需求，关键词智能匹配推荐
- **用户系统**：注册、登录、退出、修改密码、注销账户
- **上传与审核**：登录后上传（≤50MB，白名单格式）；新模板待审核，通过后公开
- **上下架申请**：用户为自有模板申请上架/下架并填写理由，管理员审批
- **管理后台**：审核、模板/分类/用户/文件管理、资源采集、统计概览
- **系统分类保护**：「其他模板」不可删除；删除分类时其下模板自动归档
- **外链资源索引**：采集国内外免费模板的标题、封面、源站链接，不托管文件
- **响应式界面**：桌面与移动端自适应，卡片缩略图纯 CSS 绘制

---

## 技术栈

- **后端**：Python 3.8+ 标准库 `http.server`（ThreadingHTTPServer），无 Web 框架依赖
- **数据库**：SQLite（`data/site.db`），开启外键约束
- **前端**：原生 HTML / CSS / JavaScript，无构建步骤
- **采集**：`requests` + `beautifulsoup4` + `lxml`
- **认证**：HttpOnly Cookie 会话（PBKDF2-HMAC-SHA256，20 万次迭代）
- **部署**：Cloudflare Tunnel（Quick Tunnel 临时地址 / Named Tunnel 固定域名）

> 采集引擎需要额外安装依赖，核心站点不需要。

---

## 快速开始

### 1. 安装依赖

核心站点零依赖，直接用系统 Python 即可。采集引擎需要：

```bash
pip install requests beautifulsoup4 lxml
```

### 2. 启动服务

```bash
cd template-site
python server.py
```

默认监听 `http://127.0.0.1:8765`。可通过环境变量修改端口：

```bash
PORT=9000 python server.py          # macOS / Linux
set PORT=9000 && python server.py   # Windows CMD
```

### 3. 创建管理员

打开 `http://127.0.0.1:8765/auth.html` 注册。**第一个注册的用户自动成为管理员**，之后注册的均为普通用户。

### 4. 页面入口

| 页面 | 地址 | 说明 |
| --- | --- | --- |
| 首页 | `/index.html` | 搜索、筛选、预览、下载 |
| 登录注册 | `/auth.html` | 注册与登录 |
| 个人中心 | `/account.html` | 资料、密码、我的上传、上下架申请 |
| 用户主页 | `/profile.html?user=<用户名>` | 查看他人公开信息 |
| 管理后台 | `/admin.html` | 仅管理员 |

---

## 账号与权限

| 功能 | 访客 | 用户 | 管理员 |
| --- | :---: | :---: | :---: |
| 浏览与搜索模板 | ✅ | ✅ | ✅ |
| 下载模板 | ❌ | ✅ | ✅ |
| 上传模板 | ❌ | ✅ | ✅ |
| 管理自己的资料与密码 | ❌ | ✅ | ✅ |
| 申请自有模板上下架 | ❌ | ✅ | ✅ |
| 查看他人公开信息 | ✅ | ✅ | ✅ |
| 审核模板 | ❌ | ❌ | ✅ |
| 管理分类/用户/文件 | ❌ | ❌ | ✅ |
| 运行采集引擎 | ❌ | ❌ | ✅ |

---

## 模板状态与审核流程

| 状态 | 含义 | 公开可见 | 可删除 |
| --- | --- | :---: | :---: |
| `pending` | 待审核 | ❌ | ✅ |
| `approved` | 已上架 | ✅ | ❌（须先下架） |
| `rejected` | 已拒绝 | ❌ | ✅ |
| `unlisted` | 已下架 | ❌ | ✅ |

**流程**：

```text
用户上传
    ↓
pending（待审核）
    ↓  管理员通过
approved（已上架）
    ↓  用户申请 + 管理员同意
unlisted（已下架）→ 可删除
```

已上架模板不能直接删除，必须先下架——这条规则同时 enforce 在前端按钮和后端接口上。

---

## 资源采集引擎

引擎只索引**标题、封面图与源站链接**，不下载也不托管模板文件，规避版权与分发风险。点击外链卡片会跳转到原站下载。

### 数据源

| 来源 | 地区 | 分类 | 说明 |
| --- | --- | --- | --- |
| OfficePLUS | 国内 | PPT | 微软官方 |
| PresentationGO | 国外 | PPT | 免费 PPT / Google Slides |
| SlidesCarnival | 国外 | PPT | 免费演示模板 |
| Free Power Point Templates | 国外 | PPT | 免费主题 |
| Vertex42 Word | 国外 | Word | 合同/简历/信函 |
| Vertex42 Excel | 国外 | Excel | 预算/发票/排期 |
| HTML5 UP | 国外 | 网站 | 响应式 HTML5（CC BY） |
| Really Good Emails | 国外 | 邮件 | 欢迎/营销/通讯 |
| Free Design Resources | 国外 | 设计 | Logo/海报/印刷 |

### 运行采集

```bash
# 每个来源采集 N 条（默认 12，最大 40）
python crawler.py 20
```

也可在管理后台「资源采集」页签操作，可查看数据源、设置数量、查看采集日志。重复链接自动去重。

> 修改 `crawler.py` 后需重启 `server.py` 才会生效。

---

## 目录结构

```text
template-site/
├── server.py               # 后端服务与全部 API
├── crawler.py              # 免费模板采集引擎
├── deploy_cloudflare.py    # Cloudflare 一键部署
├── deploy-cloudflare.bat   # Windows 双击部署入口
├── index.html              # 首页
├── auth.html               # 登录注册
├── account.html            # 个人中心
├── profile.html            # 用户公开主页
├── admin.html              # 管理后台
├── css/
│   ├── style.css           # 主样式
│   └── extra.css           # 后台与扩展样式
├── js/
│   ├── common.js           # 公共工具与会话
│   ├── data.js             # 前端示例数据（历史保留）
│   └── app.js              # 首页交互
├── data/
│   ├── site.db             # SQLite 数据库
│   ├── cloudflare_url.txt  # 最近一次公网地址
│   └── server.log          # 服务日志
├── uploads/                # 用户上传文件
└── bin/                    # 自动下载的 cloudflared
```

---

## API 参考

所有响应为 JSON。认证通过 Cookie `moli_token` 传递。

### 公开接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/categories` | 分类列表 |
| GET | `/api/templates` | 模板列表；参数 `cat`、`sub`、`q`、`mine=1`、`all=1` |
| GET | `/api/users/<id或用户名>` | 用户公开信息 |
| POST | `/api/register` | 注册 `{username,email,password}` |
| POST | `/api/login` | 登录 `{account,password}` |
| POST | `/api/logout` | 退出 |

### 需登录

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/me` | 当前用户 |
| GET | `/api/requests/mine` | 我的申请 |
| GET | `/api/templates/stats` | 个人/全站统计 |
| GET | `/api/crawl/status` | 采集状态（管理员） |
| GET | `/api/download?id=<id>` | 下载模板文件 |
| POST | `/api/upload` | multipart 上传 |
| POST | `/api/requests` | 提交上下架申请 |
| POST | `/api/me/password` | 修改密码 `{old,new}` |
| DELETE | `/api/me` | 注销账户（本人） |

### 管理员接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/users` | 用户列表 |
| GET | `/api/files` | 文件列表 |
| GET | `/api/requests` | 全部申请 |
| POST | `/api/categories` | 新建分类 |
| POST | `/api/crawl` | 执行采集 `{limit}` |
| PATCH | `/api/templates/<id>` | 改状态 `{status}` |
| PATCH | `/api/requests/<id>` | 审批 `{decision, note}` |
| PATCH | `/api/categories/<id>` | 改分类 |
| PATCH | `/api/users/<id>` | 改角色 `{role}` |
| DELETE | `/api/categories/<id>` | 删除分类（模板归入「其他模板」） |
| DELETE | `/api/users/<id>` | 删除用户 |
| DELETE | `/api/files/<id>` | 删除文件 |

---

## Cloudflare 一键部署

本项目是 Python 长驻服务 + 本地 SQLite，不能直接部署到 Cloudflare Pages。正确做法是用 **Cloudflare Tunnel**：本地服务照常运行，由隧道把它安全地暴露到公网 HTTPS，无需公网 IP、无需端口映射。

### 模式 A：快速隧道（零配置，推荐先用这个）

```bash
python deploy_cloudflare.py
```

Windows 用户可直接双击 `deploy-cloudflare.bat`。

脚本会自动完成：

1. 检测本地服务，未启动则拉起
2. 检测 `cloudflared`，缺失则从官方源下载到 `bin/`
3. 建立隧道（HTTP/2 模式，规避国内 QUIC/UDP 限制）
4. 打印公网 HTTPS 地址并写入 `data/cloudflare_url.txt`
5. `Ctrl+C` 时自动关闭隧道和它启动的本地服务

输出示例：

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

### 模式 B：命名隧道（固定域名，适合长期使用）

1. 在 Cloudflare Zero Trust 后台创建 Tunnel，配置 public hostname 指向 `http://127.0.0.1:8765`，复制 token。
2. 带 token 启动：

```bash
python deploy_cloudflare.py --token "你的token"
# 或用环境变量
set CLOUDFLARE_TUNNEL_TOKEN=你的token && python deploy_cloudflare.py
```

域名和证书由 Cloudflare 管理，地址固定不变。

### 其他参数

```bash
python deploy_cloudflare.py --port 9000      # 指定本地端口
python deploy_cloudflare.py --no-server      # 本地服务已手动启动
python deploy_cloudflare.py --reinstall      # 强制重新下载 cloudflared
```

### 部署到公网后的必做事项

1. **立即注册第一个管理员账号** —— 第一个注册者拥有全部权限，不要让别人抢先。
2. 修改 Admin 默认密码为强密码。
3. 生产环境建议改用 Named Tunnel 并开启 Cloudflare Access 二次验证。

---

## 安全说明

- 密码使用 PBKDF2-HMAC-SHA256 + 随机盐 + 20 万次迭代存储，数据库中不保存明文。
- 会话 Token 存于 HttpOnly + SameSite=Lax Cookie，降低 XSS 窃取风险。
- 上传文件限制 50MB，扩展名白名单，存储时使用随机文件名防止路径穿越。
- 静态文件路径做了目录穿越校验；管理接口统一做角色校验（403）。
- `data/site.db` 含密码哈希，**不要提交到公开仓库**；如已提交，建议改密并从历史中移除。
- 本项目为演示原型，未实现邮件验证、速率限制、CSRF Token，生产使用前请补齐。

---

## 常见问题

**Q: 采集到的模板能直接下载吗？**

不能。采集引擎只索引元数据，点击卡片会跳转源站，由源站提供下载。本站托管的模板只有用户上传且审核通过的文件。

**Q: 内置模板为什么点下载没文件？**

内置模板是演示数据，没有实际文件。上传你自己的模板文件后即可真实下载。

**Q: 忘记密码怎么办？**

目前没有邮件找回功能。可请管理员在后台删除账号后重新注册，或直接操作数据库重置。

**Q: 为什么删除分类后模板还在？**

这是设计行为：删除分类时，其下模板会自动归入不可删除的系统分类「其他模板」，不会丢失。

**Q: Cloudflare 隧道提示 QUIC 超时？**

脚本已默认使用 HTTP/2。若仍有问题，说明本机到 Cloudflare 边缘的 443 出口受限，可换网络或改用 Named Tunnel。

---

## 许可证

MIT License。采集到的模板版权归原作者所有，本站仅提供链接索引，不承担内容责任。

---

*Made with ☕ and Python*

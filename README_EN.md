# MoliBox · AI Template Hub

English | [中文](README.md)

> A register-based template sharing platform: users upload, admins review and publish, visitors search and download. Built in a crawler that indexes free templates from Chinese and international sources.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Cloudflare Tunnel](https://img.shields.io/badge/deploy-Cloudflare%20Tunnel-f68220?logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Accounts & Roles](#accounts--roles)
- [Template Status & Review Flow](#template-status--review-flow)
- [Crawler Engine](#crawler-engine)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [One-Click Cloudflare Deploy](#one-click-cloudflare-deploy)
- [Security Notes](#security-notes)
- [FAQ](#faq)

---

## Features

- **Six categories**: PPT, Word, Excel, Web, Email, Design, each with sub-scene filters
- **AI template finder**: describe what you need in natural language and get keyword-matched results
- **User system**: register, login, logout, change password, delete account
- **Upload & review**: authenticated uploads (≤50MB, whitelisted types); new templates stay pending until approved
- **List/unlist requests**: users request publish/unpublish with a reason; admins approve or reject
- **Admin console**: review queue, template/category/user/file management, crawler, statistics
- **Protected system category**: "Other" cannot be deleted; templates are re-filed when a category is removed
- **External link indexing**: indexes titles, covers and source links of free templates; no file hosting
- **Responsive UI**: desktop and mobile ready; thumbnails drawn with pure CSS

---

## Tech Stack

- **Backend**: Python 3.8+ standard library `http.server` (ThreadingHTTPServer), no web framework
- **Database**: SQLite (`data/site.db`) with foreign keys enabled
- **Frontend**: Vanilla HTML / CSS / JavaScript, no build step
- **Crawler**: `requests` + `beautifulsoup4` + `lxml`
- **Auth**: HttpOnly cookie sessions with PBKDF2-HMAC-SHA256 (200k iterations)
- **Deploy**: Cloudflare Tunnel (Quick Tunnel for temporary URLs / Named Tunnel for a stable domain)

> The crawler needs extra dependencies; the core site does not.

---

## Quick Start

### 1. Install dependencies

The core site needs no third-party packages. The crawler requires:

```bash
pip install requests beautifulsoup4 lxml
```

### 2. Start the server

```bash
cd template-site
python server.py
```

Listens on `http://127.0.0.1:8765` by default. Override with the `PORT` variable:

```bash
PORT=9000 python server.py          # macOS / Linux
set PORT=9000 && python server.py   # Windows CMD
```

### 3. Create the admin

Open `http://127.0.0.1:8765/auth.html` and register. **The first registered user automatically becomes admin**; all later users are regular members.

### 4. Page entries

| Page | URL | Description |
| --- | --- | --- |
| Home | `/index.html` | Search, filter, preview, download |
| Auth | `/auth.html` | Register and login |
| Account | `/account.html` | Profile, password, uploads, requests |
| Profile | `/profile.html?user=<username>` | View public user info |
| Admin | `/admin.html` | Admin only |

---

## Accounts & Roles

| Action | Guest | User | Admin |
| --- | :---: | :---: | :---: |
| Browse & search | ✅ | ✅ | ✅ |
| Download | ❌ | ✅ | ✅ |
| Upload | ❌ | ✅ | ✅ |
| Manage own profile & password | ❌ | ✅ | ✅ |
| Request list/unlist | ❌ | ✅ | ✅ |
| View public profiles | ✅ | ✅ | ✅ |
| Review templates | ❌ | ❌ | ✅ |
| Manage categories, users, files | ❌ | ❌ | ✅ |
| Run crawler | ❌ | ❌ | ✅ |

---

## Template Status & Review Flow

| Status | Meaning | Public | Deletable |
| --- | --- | :---: | :---: |
| `pending` | Awaiting review | ❌ | ✅ |
| `approved` | Published | ✅ | ❌ (unlist first) |
| `rejected` | Rejected | ❌ | ✅ |
| `unlisted` | Unpublished | ❌ | ✅ |

**Flow**:

```text
User uploads
      ↓
pending
      ↓  admin approves
approved
      ↓  user requests + admin approves
unlisted → can be deleted
```

Published templates cannot be deleted directly; they must be unlisted first. Enforced in both UI and API.

---

## Crawler Engine

The engine indexes **titles, cover images and source links only**. It never downloads or hosts template files, avoiding copyright and distribution risks. External cards link to the original site for download.

### Sources

| Source | Region | Category | Note |
| --- | --- | --- | --- |
| OfficePLUS | China | PPT | Microsoft official |
| PresentationGO | Global | PPT | Free PowerPoint / Google Slides |
| SlidesCarnival | Global | PPT | Free presentations |
| Free Power Point Templates | Global | PPT | Free themes |
| Vertex42 Word | Global | Word | Contracts, resumes, letters |
| Vertex42 Excel | Global | Excel | Budgets, invoices, schedules |
| HTML5 UP | Global | Web | Responsive HTML5 (CC BY) |
| Really Good Emails | Global | Email | Welcome, marketing, newsletters |
| Free Design Resources | Global | Design | Logos, posters, print |

### Run the crawler

```bash
# crawl N items per source (default 12, max 40)
python crawler.py 20
```

Or use the **Crawler** tab in the admin console to inspect sources, set limits, and view logs. Duplicate links are skipped automatically.

> Restart `server.py` after editing `crawler.py`.

---

## Project Structure

```text
template-site/
├── server.py               # Backend server and all APIs
├── crawler.py              # Free template crawler
├── deploy_cloudflare.py    # One-click Cloudflare deploy
├── deploy-cloudflare.bat   # Windows double-click deploy
├── index.html              # Home page
├── auth.html               # Login & register
├── account.html            # User center
├── profile.html            # Public profile
├── admin.html              # Admin console
├── css/
│   ├── style.css           # Main styles
│   └── extra.css           # Admin & extra styles
├── js/
│   ├── common.js           # Shared utils and session
│   ├── data.js             # Legacy sample data
│   └── app.js              # Home page logic
├── data/
│   ├── site.db             # SQLite database
│   ├── cloudflare_url.txt  # Last public URL
│   └── server.log          # Server log
├── uploads/                # User uploads
└── bin/                    # Auto-downloaded cloudflared
```

---

## API Reference

All responses are JSON. Auth uses the `moli_token` cookie.

### Public

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/categories` | List categories |
| GET | `/api/templates` | List templates; params `cat`, `sub`, `q`, `mine=1`, `all=1` |
| GET | `/api/users/<id or username>` | Public user info |
| POST | `/api/register` | Register `{username,email,password}` |
| POST | `/api/login` | Login `{account,password}` |
| POST | `/api/logout` | Logout |

### Authenticated

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/me` | Current user |
| GET | `/api/requests/mine` | My requests |
| GET | `/api/templates/stats` | Personal or global stats |
| GET | `/api/crawl/status` | Crawler status (admin) |
| GET | `/api/download?id=<id>` | Download template file |
| POST | `/api/upload` | Multipart upload |
| POST | `/api/requests` | Submit list/unlist request |
| POST | `/api/me/password` | Change password `{old,new}` |
| DELETE | `/api/me` | Delete own account |

### Admin only

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/users` | List users |
| GET | `/api/files` | List files |
| GET | `/api/requests` | All requests |
| POST | `/api/categories` | Create category |
| POST | `/api/crawl` | Run crawler `{limit}` |
| PATCH | `/api/templates/<id>` | Change status `{status}` |
| PATCH | `/api/requests/<id>` | Decide request `{decision, note}` |
| PATCH | `/api/categories/<id>` | Update category |
| PATCH | `/api/users/<id>` | Change role `{role}` |
| DELETE | `/api/categories/<id>` | Delete category (templates re-filed to "Other") |
| DELETE | `/api/users/<id>` | Delete user |
| DELETE | `/api/files/<id>` | Delete file |

---

## One-Click Cloudflare Deploy

This project is a long-running Python service with local SQLite, so it cannot be hosted on Cloudflare Pages directly. Use **Cloudflare Tunnel**: keep the local service running and expose it over public HTTPS with no public IP and no port forwarding.

### Mode A: Quick Tunnel (zero config)

```bash
python deploy_cloudflare.py
```

Windows users can double-click `deploy-cloudflare.bat`.

The script automatically:

1. Detects the local service and starts it if needed
2. Detects `cloudflared` and downloads it into `bin/` if missing
3. Establishes the tunnel using HTTP/2 to avoid QUIC/UDP issues on Chinese networks
4. Prints the public HTTPS URL and saves it to `data/cloudflare_url.txt`
5. Cleans up the tunnel and the local service on `Ctrl+C`

Sample output:

```text
[deploy] local service already running: http://127.0.0.1:8765
[deploy] starting quick tunnel (temporary URL, HTTP/2 mode)...
====================================================================
  Public URL: https://xxxx-yyyy-zzzz.trycloudflare.com
  Saved to data/cloudflare_url.txt
====================================================================
Running. Press Ctrl+C to stop.
```

> ⚠️ Quick Tunnel URLs are **temporary**, change on every restart, and have no SLA. Good for demos and testing.

### Mode B: Named Tunnel (stable domain)

1. Create a tunnel in Cloudflare Zero Trust, set a public hostname pointing to `http://127.0.0.1:8765`, and copy the token.
2. Start with the token:

```bash
python deploy_cloudflare.py --token "YOUR_TOKEN"
# or via environment variable
CLOUDFLARE_TUNNEL_TOKEN=YOUR_TOKEN python deploy_cloudflare.py
```

The domain and certificate are managed by Cloudflare, and the URL stays stable.

### Other options

```bash
python deploy_cloudflare.py --port 9000      # custom local port
python deploy_cloudflare.py --no-server      # server already running
python deploy_cloudflare.py --reinstall      # force re-download cloudflared
```

### After going public

1. **Register the first admin account immediately** — the first registrant gets full privileges.
2. Use a strong password for the admin account.
3. For production, use a Named Tunnel and enable Cloudflare Access for a second auth layer.

---

## Security Notes

- Passwords are stored with PBKDF2-HMAC-SHA256, random salt and 200k iterations; no plaintext is stored.
- Session tokens live in HttpOnly + SameSite=Lax cookies to reduce XSS theft risk.
- Uploads are capped at 50MB with an extension whitelist and random stored filenames to prevent path traversal.
- Static paths are checked against traversal; all admin endpoints enforce role checks (403).
- `data/site.db` contains password hashes — **never commit it to a public repo**. If already committed, rotate passwords and purge it from history.
- This is a demo prototype: no email verification, rate limiting or CSRF tokens. Add these before production use.

---

## FAQ

**Q: Can I download crawled templates directly?**

No. The crawler indexes metadata only; cards link to the source site. Only user-uploaded, approved files are hosted here.

**Q: Why do built-in templates have no file on download?**

Built-in templates are demo records without files. Upload your own file to get a real download.

**Q: What if I forget my password?**

There is no email recovery yet. Ask an admin to delete the account and re-register, or reset directly in the database.

**Q: Why do templates remain after deleting a category?**

By design: templates are moved to the undeletable system category "Other" instead of being lost.

**Q: The tunnel reports QUIC timeouts?**

The script already defaults to HTTP/2. If issues persist, outbound 443 to Cloudflare edge is restricted — try another network or a Named Tunnel.

---

## License

MIT License. Crawled templates remain the property of their original authors; this site only indexes links and assumes no content liability.

---

*Made with ☕ and Python*

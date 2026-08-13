# Changelog

Version-by-version record of what changed and, specifically, **why**. For the fuller story/reasoning behind each entry, see [DEV_DIARY.md](./DEV_DIARY.md) — this file is the short, structured version.

---

## v1.2 — MongoDB caching & error logging (2026-08-13)

**What was added:**
- `CacheService` (in `integrations/core_bridges.py`) wired into actual use for the first time — previously written but never called by anything.
- `scrape_website` now caches each page for 1 hour, keyed by URL.
- A shared error log: failures in `search_web` and `scrape_website` get recorded (source, error, context, timestamp) instead of only existing in the one response that showed them.
- New `recent_errors` tool to read that log back.

**Why:**
- `pymongo` had been sitting in `requirements.txt` since the start of the project with nothing using it — found during the security review. Rather than leave unused, unexplained weight in the dependency list, it got either wired up for real or should eventually be removed; wiring it up won.
- Scraping is the natural first use: the same URL sometimes gets fetched more than once in a session, and redoing that fetch every time is pure waste — a cache turns a repeat fetch into an instant lookup.
- Search results were deliberately **not** cached — a "latest news" query needs to stay current, and caching it would risk quietly serving stale results as if they were fresh.
- The error log exists because, until now, a failure was only ever visible in the single chat turn it happened in — nothing kept a record across time. That made it impossible to answer "has this been failing a lot?" after the fact.

**Design constraint carried through both features:** everything is a safe no-op without `MDB_MCP_CONNECTION_STRING` configured. No database connected yet — behavior today is identical to before this version. See `docs/SETUP.md`.

---

## v1.1 — Security hardening (2026-08-12)

**What changed:**
- `git_manager.py` and `google_manager.py` switched from unrestricted `getattr()` dispatch to an explicit tool allowlist.
- Four dead/legacy files (`scraper.py`, `you_com.py`, `mcp_bridge.py`, `neural_os.py`) neutralized — redirected to their safe live equivalents, or made to fail loudly instead of silently running with weaker protections.
- `list_installed_versions` tool added.
- Dependencies pinned to exact, verified-running versions (`requirements.txt`).

**Why:** full security review found these as concrete, evidenced gaps — see `docs/SECURITY.md` for the complete writeup, findings, and the one item still requiring manual action (GitHub token scoping).

---

## v1.0 — Initial build

47+ tools across GitHub, Google Workspace, HidenCloud/SFTP, three sandbox providers, YouTube, and Neural-MCP as a separate memory sub-agent. Built over roughly a week. See `docs/DEV_DIARY.md` for the full origin story.

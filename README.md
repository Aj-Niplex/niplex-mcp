<p align="center">
  <img src="assets/mcp-logo.svg" width="64" height="64" alt="Model Context Protocol logo" />
</p>

<h1 align="center">Niplex-MCP</h1>

<p align="center">
  One AI agent's full toolkit — GitHub, Google Workspace, a live production server, three sandboxes, and a memory sub-agent — behind a single MCP server.
</p>

---

## What this is

Niplex-MCP is a custom [Model Context Protocol](https://modelcontextprotocol.io) server: 47+ tools, one connection, usable by any MCP-capable AI client. The point isn't the tool count — it's that the AI on the front end is swappable. Point a different MCP client at the same server and it gets the same capabilities, no rebuild required.

It's paired with **[Neural-MCP](https://github.com/Aj-Niplex/Neural)**, a separate sub-agent with its own memory, backed by a plain GitHub repo (`Adarshs-Stack`) acting as a durable, human-readable knowledge store.

Read **[USE_CASES.md](./USE_CASES.md)** for what this actually looks like day-to-day, for both developers and people who've never touched an API key in their life.

## Tool groups

| Group | Examples | What it's for |
|---|---|---|
| **GitHub** | `git_list_repos`, `write_github_file`, `git_create_pull_request` | Full repo, file, branch, issue, and PR access — every repo on the account |
| **Sandboxes** | `execute_in_sandbox`, `e2b_run_code`, `horizon_run_code` | Disposable environments for running code, three different providers |
| **HidenCloud** | `list_hidencloud_files`, `write_hidencloud_file` | File-only access to the live production agent server, via SFTP |
| **Search** | `search_web`, `scrape_website` | Web search with a free fallback, SSRF-guarded page scraping |
| **YouTube** | `search_youtube`, `get_youtube_details` | YouTube Data API |
| **Neural** | `ask_neural`, `log_to_neural` | The memory/context sub-agent — see below |
| **Google Workspace** | `gmail_search`, `calendar_list_events`, `docs_create` | Gmail (read + draft, no direct send), Calendar, Drive, Docs |

Full breakdown of every single tool: see `server.py`, or `docs/ARCHITECTURE.md` for the grouped version with diagrams.

## The Neural connection

`ask_neural` and `log_to_neural` forward to a separately-deployed MCP server that runs its own sub-agent against `Adarshs-Stack`. Two independent auth layers sit between them (Horizon's platform-level OAuth, and an app-level API key) — the full story of how that works, and how it was debugged, is in **[docs/NEURAL_CONNECTION.md](./docs/NEURAL_CONNECTION.md)**.

## Docs

Everything below lives in **[docs/](./docs/)**:

- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** — how every piece fits together, with a diagram
- **[NEURAL_CONNECTION.md](./docs/NEURAL_CONNECTION.md)** — the Niplex ↔ Neural auth story in full
- **[SETUP.md](./docs/SETUP.md)** — every environment variable, what it's for, how to get one running from scratch
- **[SECURITY.md](./docs/SECURITY.md)** — the security review, what got fixed, the ground rules going forward
- **[DEV_DIARY.md](./docs/DEV_DIARY.md)** — running log of what changed and why

## Design choices worth knowing about

- **No email-send tool** — only drafts. A human always hits send.
- **No PR auto-merge tool** — merges are manual, on purpose.
- **HidenCloud is file-only** — no shell access, even though it's where the live agent actually runs.
- Every tool-dispatch layer uses an **explicit allowlist**, not open-ended dynamic dispatch — see `docs/SECURITY.md`.

## Status

Actively developed, security-reviewed, open source. Deployed on [Horizon](https://fastmcp.app), auto-deploys on push to `main`.

## Roadmap

Plans to move toward pluggable flows — bring your own tools, the MCP layer adapts to them — rather than a fixed toolkit tied to one person's specific accounts.

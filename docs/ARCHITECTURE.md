# Architecture — How Everything Works

## The big picture

Niplex-MCP is one AI agent's whole toolkit, exposed as a single MCP server so any MCP-capable AI client (Claude, or anything else that speaks MCP) can use it. The design goal isn't "an MCP server" — it's a model-agnostic automation layer: swap the AI on the front end anytime, the tools and the access stay the same.

```
                    ┌─────────────────────┐
                    │   Any MCP client     │  (Claude, or whatever's next)
                    └──────────┬───────────┘
                               │ MCP over HTTPS
                               │ Authorization: Bearer <MCP_API_KEY>
                               ▼
        ┌───────────────────────────────────────────┐
        │         Horizon edge (OAuth 2.1 gate)       │  ← platform-level, in front
        │              always there, unconditionally  │     of every deployed server
        └──────────────────────┬──────────────────────┘
                               ▼
              ┌────────────────────────────────┐
              │   Niplex-MCP (this repo)         │
              │   aj-niplex.fastmcp.app/mcp      │
              │   47+ tools, 8 tool groups        │
              └───┬────┬────┬────┬────┬────┬────┘
                  │    │    │    │    │    │
       ┌──────────┘    │    │    │    │    └───────────┐
       ▼               ▼    ▼    ▼    ▼                ▼
  ┌─────────┐   ┌──────────┐ ┌──────┐ ┌─────────┐ ┌──────────────┐
  │ GitHub   │   │ Google    │ │ SFTP │ │ Sandboxes│ │ Neural-MCP    │
  │ (all     │   │ Workspace │ │ →    │ │ Daytona/  │ │ (separate     │
  │ repos)   │   │ (2 acct)  │ │Hiden-│ │ E2B/      │ │ deployment)   │
  │          │   │           │ │Cloud │ │ Horizon   │ │       │       │
  └─────────┘   └──────────┘ └──────┘ └─────────┘ └───────┼──────┘
                                                            ▼
                                                    ┌───────────────┐
                                                    │ Adarshs-Stack  │
                                                    │ (GitHub repo,  │
                                                    │ the actual     │
                                                    │ memory store)  │
                                                    └───────────────┘
```

## The pieces

**Niplex-MCP** (this repo) — the main server. `server.py` registers every tool with `@mcp.tool()`; each tool calls into a `tools/managers/*.py` file, which calls into an `integrations/*.py` "bridge" that actually talks to the external service (GitHub API, Google API, paramiko for SFTP, etc). Three layers: **tool → manager → bridge**. Managers exist so the same bridge logic isn't duplicated if two tools need it, and so there's one place to control which methods on a bridge are actually reachable (see SECURITY.md).

**Neural-MCP** (separate repo, separate deployment) — a sub-agent with its own memory. Niplex-MCP calls it like any other MCP server (`ask_neural`, `log_to_neural`), and Neural decides on its own where information belongs in Adarshs-Stack, rather than Niplex dictating file paths directly. See NEURAL_CONNECTION.md for exactly how these two authenticate to each other.

**Adarshs-Stack** — a GitHub repo, used as a simple, durable, human-readable database. Only Neural-MCP is *supposed* to write here directly (via its own narrowly-scoped `NEURAL_GITHUB_PAT`) — see SECURITY.md for a caveat on that.

**Horizon** — hosts both Niplex-MCP and Neural-MCP, auto-deploys on every push to `main`, and puts a real OAuth 2.1 gate in front of every deployed server automatically, at the platform edge, before your code ever runs. This exists whether or not your own code adds any auth — confirmed by direct testing (see NEURAL_CONNECTION.md).

**HidenCloud** — a Pterodactyl-based host running the actual live Niplex/Hermes agent process. Niplex-MCP reaches it only via SFTP (file read/write/delete/list) — no shell access by design.

**Sandboxes (Daytona, E2B, Horizon's own free one)** — three separate code-execution options with different tradeoffs: Daytona for longer-running tasks, E2B for quick scripts or GUI/computer-use automation, Horizon's free one as the default low-cost choice. None of these share credentials with Niplex-MCP's own environment — they're genuinely separate sandboxes reached over the network.

## Tool groups (see SETUP.md for the env vars each one needs)

| Group | Tools | What it's for |
|---|---|---|
| GitHub | `git_*`, `list_github_files`, `read/write_github_file` | Repos, files, branches, commits, issues, PRs — account-wide |
| Sandboxes | `execute_in_sandbox`, `e2b_*`, `horizon_run_code`, `horizon_health` | Running code/commands in disposable environments |
| HidenCloud | `list/read/write/delete_hidencloud_file` | File access to the live production agent host |
| Search | `search_web`, `scrape_website` | Web search (paid or free fallback) and page scraping (SSRF-guarded) |
| YouTube | `search_youtube`, `get_youtube_details`, `get_youtube_stats` | YouTube Data API |
| Neural | `ask_neural`, `log_to_neural` | The memory/context sub-agent |
| Google | `gmail_*`, `calendar_*`, `drive_search_files`, `docs_*` | Gmail (read + draft only), Calendar, Drive, Docs |
| Misc | `niplex_helper`, `list_installed_versions` | Utilities |

## Deliberate design choices worth knowing about

- **No email send tool** — only `gmail_create_draft`. A human has to open Gmail and hit send.
- **No PR auto-merge tool** — PRs get created, merging is manual.
- **HidenCloud has no shell tool** — file operations only, on purpose.
- **Neural has its own separate GitHub token** — meant to contain the blast radius of that sub-agent to just Adarshs-Stack (see SECURITY.md for why this containment currently isn't complete).

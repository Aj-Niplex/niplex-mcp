# Dev Diary

Running log of what changed and why, newest first. Not a replacement for commit messages — this is for the *story*, the reasoning that doesn't fit in a commit.

---

## 2026-08-12 — Issue triage, the Neural auth saga, full security review, docs

**Started from:** 4 open issues (#1–#4 in this repo) reporting `ask_neural`, `list_hidencloud_files`, and `calendar_list_events` all failing, plus a meta report tying them together.

**Three real bugs, fixed and verified live:**
- `list_hidencloud_files` — `SFTP_BASE_DIR` was wrongly set to `/home` on a server that's already chrooted to its own root. Fixed to `/`. That alone wasn't enough — this particular SFTP implementation also fails to resolve a literal `/` for directory listing specifically (confirmed by testing: reading a nonexistent absolute path returned a clean "no such file", proving normal absolute paths work fine — it's root-listing specifically that broke). Second fix: use `.` instead of `/` for the root case.
- `calendar_list_events` — empty `time_max=""` was being sent to the Calendar API as a literal (invalid) parameter instead of omitted. Fixed to only include it when actually set.
- `ask_neural` — `fastmcp.Client()` no longer accepts `headers=` on newer versions; switched to `Client(url, auth=token)`.

**The Neural connection needed more than a code fix.** After the `headers=` → `auth=` fix, `ask_neural` still failed with a plain `401`. Turned out to be a `NEURAL_MCP_API_KEY` mismatch between the two separate Horizon deployments (Niplex-MCP and Neural-MCP). Investigating *that* surfaced something bigger: Horizon puts a real OAuth 2.1 gate in front of every deployed server, unconditionally, at the edge — confirmed by sending raw unauthenticated/garbage-token requests and reading the actual response headers (not just the wrapped Python exception text, which had been misleading earlier in the debugging). That gate's grant types are interactive-only (`authorization_code` + `refresh_token`) — not usable for one backend service calling another with no human present. The actual fix was generating a proper Horizon-issued service-account-style token and syncing it as `NEURAL_MCP_API_KEY` in both deployments. Full writeup: `docs/NEURAL_CONNECTION.md`.

**Full security review across both Niplex-MCP and Neural repos.** Every active file read, plus the dead/legacy ones. Found and fixed: two managers using unrestricted `getattr` dispatch instead of an allowlist (now fixed), and four dead files that were quietly *less* safe than their live replacements (now neutralized — see `docs/SECURITY.md` for the full list). One finding needs a manual step, not a code fix: Niplex-MCP's own `GITHUB_PAT` has account-wide reach, which undermines Neural's deliberately-scoped `NEURAL_GITHUB_PAT` containment — needs a fine-grained PAT excluding `Adarshs-Stack`.

**Added `list_installed_versions`** specifically so dependency pinning can be based on what's actually running, not a guess — this stack already had one real breaking change land silently (the fastmcp `headers=`/`auth=` thing above), which is exactly the failure mode version pinning exists to prevent.

**This docs/ folder created** to stop re-discovering all of the above from scratch next time.

---

## Earlier — initial build

7+ days from a single YouTube video on MCP to a working 47+-tool server. Grew from "give the AI agent access to Google Workspace and git" into the current shape: GitHub, Google Workspace, HidenCloud/SFTP, three sandbox providers, YouTube, and Neural-MCP as a separate memory/context sub-agent. Built with Claude Code and Manus; security-reviewed with Freebuff Cloud. Intent from the start was bigger than this one server — a model-agnostic automation layer, free to swap to whichever AI agent is best at any given time, eventually opened up for others to plug in their own tools.

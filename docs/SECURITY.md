# Security Review & Ground Rules

Last full review: 2026-08-12. This is a living document — update it when something here changes, don't let it go stale.

## Findings and fixes

### Fixed

**1. Two managers dispatched by `getattr(bridge, tool)` instead of an explicit allowlist.**
`tools/managers/git_manager.py` and `tools/managers/google_manager.py` used to route any tool-name string straight to `getattr()` on the underlying bridge object — meaning *any* public method on that class was reachable this way, not just the ones meant to be exposed. Safe in practice only because every caller was a hardcoded string in `server.py`; still fragile, since a future method added to either bridge class would become silently callable with no gate. `google_manager.py` had already worked around this once by specifically blocking `send_email` — a sign the pattern needed fixing at the root rather than case-by-case. **Fixed:** both managers now check the tool name against an explicit allowlist before dispatching.

**2. Dead code that was less safe than its live replacement.**
- `integrations/scraper.py` and `integrations/you_com.py` were unused duplicates of what `integrations/core_bridges.py` actually does — except the live version has real SSRF protection (blocks localhost, private IP ranges, and cloud metadata endpoints like `169.254.169.254`) and a working free-search fallback, and the dead versions had neither.
- `integrations/mcp_bridge.py` would call other MCP servers with **zero authentication**, over hardcoded internal URLs, if anything ever reconnected it.
- `integrations/neural_os.py` returned **fabricated placeholder data** (a made-up "goals" string) as if it were real — actively misleading if it were ever wired to a tool.

None of these were reachable from any live tool. Since this MCP server has no file-delete capability, they've been left in place but made inert: the two duplicates now just re-export the safe implementation, and the other two raise immediately if anything tries to instantiate them. **If a delete-file tool ever gets added, these four files are the first candidates for actual removal.**

### Known, not code-fixable — needs a manual step

**3. Niplex-MCP's own `GITHUB_PAT` undermines Neural's blast-radius containment.**
Neural-MCP deliberately uses a separate, narrowly-scoped `NEURAL_GITHUB_PAT` for Adarshs-Stack specifically so a problem in that sub-agent can't touch anything else — a good instinct. But Niplex-MCP's own `GITHUB_PAT` has account-wide access, confirmed reaching `Adarshs-Stack` directly via `git_list_repos()`. Anything with Niplex-MCP's tools already has equal or greater reach into that repo than Neural does, which means the isolation only holds on paper right now.

**The actual fix:** scope `GITHUB_PAT` down using a GitHub fine-grained personal access token that explicitly excludes `Adarshs-Stack`, if the intent is for Neural to be the sole gatekeeper of that repo. This has to be done by a human in GitHub's own token settings — there's no API for minting a new PAT from scratch, so no tool here can do it.

### Worth knowing, not a bug to fix

**4. One leaked `MCP_API_KEY` is total compromise, with no internal tiering.**
Everything behind that one key: arbitrary code execution (3 sandbox providers), every GitHub repo on the account, the live production HidenCloud server (read/write/delete), Gmail, Calendar, Drive/Docs, and a path into Neural. Presumably intentional — this is meant to be one AI agent's full toolkit — but worth being clear-eyed that there's no graduated permission model *within* Niplex-MCP itself, only the (partially-undermined, see #3) separation between it and Neural.

**5. Unpinned dependencies in both `requirements.txt` files**, combined with `server.py` auto-`pip install`-ing anything missing on every boot (`install_deps()`). What's actually running isn't reproducible, and a breaking or compromised upstream release could land silently on the next redeploy. Fixing this properly needs real installed-version numbers rather than guesses — see the `list_installed_versions` tool (added specifically for this) and pin from its output, not from memory.

## Already solid — for balance, not everything here needed fixing

- Both `server.py` (Niplex) and `Neural/server.py` fail **secure**: if their API key env var isn't set, they block every request (503) rather than letting everything through.
- Horizon puts real OAuth 2.1 in front of every deployed server at the edge, unconditionally, before any app code runs — confirmed by direct testing.
- `core_bridges.py`'s live scraper actually checks URLs before fetching (SSRF protection).
- `hidencloud_sftp.py` confines every path to a safe base directory — path traversal via `../../` is blocked.
- No email-send tool exists — only drafts, requiring a human to actually hit send.
- No PR auto-merge tool — merges are manual by design.
- HidenCloud access is file-only, no shell — a much smaller blast radius than it could be.

## Ground rules going forward

1. **New method on a bridge class → it does not become a tool automatically.** Add it to the manager's explicit allowlist, or it stays unreachable. This is the whole point of fix #1 — don't undo it by going back to `getattr`.
2. **Test in a sandbox before writing to HidenCloud.** It's a live production server with no shell/restart capability — a bad write has no quick undo.
3. **Never commit real credential values**, even temporarily, even in a private repo. Env vars only, set via Horizon's dashboard.
4. **If a credential is ever pasted somewhere it shouldn't be** (chat, a commit, a log) — rotate it. Treat "was it actually misused" as irrelevant; exposure alone is the bar.
5. **A 401 can come from more than one layer now** (Horizon's edge OAuth, or an app's own middleware) — see `docs/NEURAL_CONNECTION.md` for how to tell which one before assuming it's a code bug.
6. **Before pinning a dependency version, check what's actually installed** (`list_installed_versions`) rather than guessing — this stack has already had one real breaking change (fastmcp's `Client(headers=...)` → `auth=...`) land silently between versions.

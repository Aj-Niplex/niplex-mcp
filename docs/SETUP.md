# Setup — Environment Variables

All of these are set as environment variables on the Horizon deployment (not in code, not in the repo — never commit real values). Nothing here is optional unless marked so.

## Gatekeeper

| Variable | Used by | Notes |
|---|---|---|
| `MCP_API_KEY` | `server.py` | Required. If unset, the server fails secure — blocks every request with a 503 rather than allowing them through unauthenticated. |

## GitHub

| Variable | Used by | Notes |
|---|---|---|
| `GITHUB_PAT` | `integrations/github.py` | Account-wide token — every repo under Aj-Niplex. See `docs/SECURITY.md` for why this needs a closer look. |

## Neural-MCP connection

| Variable | Used by | Notes |
|---|---|---|
| `NEURAL_MCP_URL` | `integrations/neural_bridge.py` | `https://neural.fastmcp.app/mcp` |
| `NEURAL_MCP_API_KEY` | `integrations/neural_bridge.py` | Must exactly match the same-named variable set on the **Neural-MCP** deployment. See `docs/NEURAL_CONNECTION.md`. |

## HidenCloud (SFTP)

| Variable | Used by | Notes |
|---|---|---|
| `HIDENCLOUD_SFTP_HOST` | `integrations/hidencloud_sftp.py` | |
| `HIDENCLOUD_SFTP_PORT` | same | Defaults to `2022` if unset. |
| `HIDENCLOUD_SFTP_USER` | same | |
| `HIDENCLOUD_SFTP_PASSWORD` | same | |

## Google Workspace (per account — repeat for each)

| Variable pattern | Used by | Notes |
|---|---|---|
| `GOOGLE_PROFESSIONAL_CREDENTIALS_JSON` | `integrations/google_bridge.py` | OAuth client JSON for the "professional" account |
| `GOOGLE_PROFESSIONAL_TOKEN_JSON` | same | Token JSON — needs a one-time interactive OAuth consent to generate (headless server can't open a browser); after that, refresh is automatic |
| `GOOGLE_PERSONAL_CREDENTIALS_JSON` | same | Same pattern, "personal" account |
| `GOOGLE_PERSONAL_TOKEN_JSON` | same | |

A third account ("company") was deliberately deferred — no inbound mail/site yet. Adding it later just means repeating this pattern with `GOOGLE_COMPANY_...` plus adding `"company"` to `VALID_ACCOUNTS` in the bridge.

## Sandboxes

| Variable | Used by | Notes |
|---|---|---|
| `DAYTONA_API_KEY` | `integrations/daytona.py` | |
| `E2B_API_KEY` | `integrations/e2b_bridge.py` | Powers both code execution and desktop/computer-use |
| `SANDBOX_TOKEN` | `integrations/horizon_sandbox.py` | Token for Horizon's own free sandbox server |

## Search & YouTube

| Variable | Used by | Notes |
|---|---|---|
| `YOU_COM_API_KEY` | `integrations/core_bridges.py` | Optional — without it, `search_web` automatically falls back to a free DuckDuckGo search via Jina's reader |
| `YOUTUBE_API_KEY` | `integrations/youtube.py` | Required for the YouTube tools |

## Optional / not required for normal operation

| Variable | Used by | Notes |
|---|---|---|
| `MDB_MCP_CONNECTION_STRING` | `integrations/core_bridges.py` | A MongoDB-backed cache layer that no-ops cleanly if unset. Not currently wired into any tool's hot path. |

## Getting a fresh deployment running

1. Set `MCP_API_KEY` first — nothing else works without it, and it fails secure so you'll get a clear 503 if you forget.
2. Add `GITHUB_PAT` — most tools depend on GitHub access existing.
3. Add the rest based on which tool groups you actually want live; each one degrades independently (e.g. no `YOUTUBE_API_KEY` just means the YouTube tools return a clear "not configured" message, nothing else breaks).
4. Push to `main` — Horizon auto-deploys. Wait roughly 45–60 seconds before testing a tool that touches new config; that's about how long a redeploy has taken in practice.
5. Use `list_installed_versions` to sanity-check the environment actually installed what `requirements.txt` expects.

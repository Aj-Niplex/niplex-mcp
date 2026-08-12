# How Niplex-MCP Connects to Neural-MCP

`ask_neural` and `log_to_neural` (in `integrations/neural_bridge.py`) call Neural-MCP the same way any MCP client would — using `fastmcp.Client`, not a raw REST call, since Neural-MCP exposes its own tools (`ask_neural`, `log_to_neural`) over the MCP protocol.

## The three layers a request actually passes through

1. **Horizon's edge gate (OAuth 2.1)** — CloudFront + Lambda, sits in front of Neural-MCP's URL unconditionally, before any of Neural's own code runs. Confirmed by direct testing: a request with no `Authorization` header, or a garbage one, gets rejected right here with a proper OAuth error (`WWW-Authenticate` header, `.well-known/oauth-protected-resource` discovery) — it never reaches the app.
2. **Neural's own `APIKeyMiddleware`** (in `Neural/server.py`) — compares the Bearer token against Neural's own `NEURAL_MCP_API_KEY` environment variable. This is a second, independent check, redundant with #1 in the sense that both are gating the same door, but not identical — see below.
3. **The actual tool logic** (`agent.py`) — only runs if both of the above pass.

## What actually authenticates a request

Horizon's OAuth metadata for this deployment advertises `authorization_code` + `refresh_token` grant types only — built for a human clicking "allow" in a browser, not for one backend service calling another with nobody watching. That's not usable for Niplex-MCP calling Neural-MCP on its own.

What *does* work: Horizon also accepts a plain, Horizon-issued Bearer token for "service-account-style access" on free-tier servers (this is documented in `integrations/horizon_sandbox.py`'s docstring, and confirmed directly — a Horizon-issued token cleared the edge gate with a normal 200 response, not an OAuth challenge). That's what `NEURAL_MCP_API_KEY` actually is now: a real Horizon-issued token, set to the same value in both deployments' environment variables — not a self-invented string, and not a full OAuth login.

## Required configuration (both sides must match)

| Where | Variable | Value |
|---|---|---|
| Niplex-MCP env | `NEURAL_MCP_URL` | `https://your-neural.fastmcp.app/mcp` |
| Niplex-MCP env | `NEURAL_MCP_API_KEY` | the Horizon-issued token |
| Neural-MCP env | `NEURAL_MCP_API_KEY` | **the same token, exactly** |

If these two values ever drift apart, `ask_neural` fails with a `401 Unauthorized` — that's not a code bug, it's a config mismatch. Check this first before touching any code.

## Debugging history (kept for the next time this breaks)

1. First symptom: `Client.__init__() got an unexpected keyword argument 'headers'`. Cause: `fastmcp.Client()` stopped accepting `headers=` on newer versions — fixed by switching to `Client(url, auth=token)`.
2. After that fix: `401 Unauthorized`, generic. Investigated whether Horizon's OAuth was the blocker; direct probing (sending requests with no token / a garbage token, and reading the actual response headers/body, not just the wrapped exception text) showed Horizon's edge gate *is* real and *is* enforced unconditionally — but the specific 401 Niplex-MCP was hitting was a plain token-value mismatch with Neural's `APIKeyMiddleware`, one layer deeper than the edge gate.
3. Fix: generate a proper Horizon-issued token, set it as `NEURAL_MCP_API_KEY` in both deployments. Verified end-to-end — `ask_neural` reaches `agent.py` and gets a real (not error) response.

**Lesson for future debugging:** a 401 here can come from either layer (Horizon's edge, or the app's own middleware). Test with a raw, unauthenticated request first (see the probing snippets in this history) to figure out which layer is actually rejecting the request before assuming it's a code bug.

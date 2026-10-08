# MCP 2026-07-28 wire migration note

This repository has been moved to the **MCP 2026-07-28 stateless wire** by the
M4 lane of CSOAI Ltd (UK 16939677).

## What changed

* `pyproject.toml` now pins `mcp>=2.0.0` (2.3.0 is the current 2026-07-28 SDK).
* `from mcp.server.fastmcp import FastMCP` renamed to
  `from mcp.server.mcpserver import MCPServer as FastMCP` (the
  `mcp.server.fastmcp` module is removed in 2.x).
* `mcp2026_shim.py` vendored at the repo root for `ShimASGI` /
  `ShimWSGI` front-ends.
* The new wire is **stateless** — no `initialize` / `notifications/initialized`
  handshake, no `Mcp-Session-Id` header.
* Every request carries a mandatory `Mcp-Method` header.
* `tools/call`, `resources/read`, `prompts/get` carry a mandatory
  `Mcp-Name` header.
* `server/discover` is the only discovery path.
* MRTR (`resultType: "input_required"`) passes through untouched.

## Deadline

The old wire dies **2027-07-28** (12-month deprecation clock that opened with
the 2026-07-28 revision).

## Verify

```bash
PYTHONPATH= /opt/homebrew/bin/python3.11 ~/clawd/mcp_wire_audit.py audit --local contract-review-ai-mcp
```

## Plan

See `MCP_2026_WIRE_MIGRATION_PLAN_2026-10-07.md` in the `clawd` workspace.

<div align="center">

# Contract Review Ai MCP

**MCP server for contract review ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-contract-review-ai-mcp)](https://pypi.org/project/meok-contract-review-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Contract Review Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `analyze_contract` | Analyze contract text for clauses and risks |
| `extract_clauses` | Extract specific clauses from contract |
| `identify_risks` | Identify potential risks in contract |
| `compare_contracts` | Compare two contracts |
| `summarize_contract` | Generate contract summary |
| `check_favourable_terms` | Check for favourable terms |
| `get_review_history` | Get review history |

## Installation

```bash
pip install meok-contract-review-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "contract-review-ai": {
      "command": "python",
      "args": ["-m", "meok_contract_review_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 7 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)

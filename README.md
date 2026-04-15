# Contract Review AI MCP Server

> By [MEOK AI Labs](https://meok.ai) — Contract analysis, clause extraction, and risk assessment

## Installation

```bash
pip install contract-review-ai-mcp
```

## Usage

```bash
python server.py
```

## Tools

### `analyze_contract`
Analyze contract text for clauses and risks. Detects confidentiality, indemnification, liability limits, termination, force majeure, and more.

**Parameters:**
- `contract_text` (str): Contract text
- `contract_type` (str): Contract type (default 'general')

### `extract_clauses`
Extract specific clause types from a contract.

**Parameters:**
- `contract_text` (str): Contract text
- `clause_types` (list): Clause types to extract

### `identify_risks`
Identify potential risks (high, medium, low) in contract text.

**Parameters:**
- `contract_text` (str): Contract text

### `compare_contracts`
Compare two previously analyzed contracts.

**Parameters:**
- `contract1_id` (str): First contract review ID
- `contract2_id` (str): Second contract review ID

### `summarize_contract`
Generate contract summary with key clauses and risk level.

**Parameters:**
- `contract_text` (str): Contract text

### `check_favourable_terms`
Check for favourable terms (mutual, reasonable, negotiable, etc.).

**Parameters:**
- `contract_text` (str): Contract text

### `get_review_history`
Get review history.

**Parameters:**
- `limit` (int): Max results (default 10)

## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs

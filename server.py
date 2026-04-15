#!/usr/bin/env python3
"""MEOK AI Labs — contract-review-ai-mcp MCP Server. Contract analysis, clause extraction, and risk assessment."""

import asyncio
import json
import re
from datetime import datetime
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types

_store = {"contracts": [], "reviews": []}
server = Server("contract-review-ai-mcp")


def create_id():
    return str(uuid.uuid4())[:8]


CLAUSE_PATTERNS = {
    "confidentiality": r"(confidential|secret|non-disclos|gossip|privacy)",
    "indemnification": r"(indemnif|hold harmless|defend|compensate for loss)",
    "limitation_liability": r"(limit.*liabil|cap.*damage|maximum.*liability|liable.*exceed)",
    "termination": r"(terminat|cancel|end.*agreement|breach|default)",
    "force_majeure": r"(force majeure|act of god|unforeseeable|circumstances beyond)",
    "governing_law": r"(governing law|jurisdiction|arbitration|venue|laws of)",
    "payment": r"(payment|compensat|billing|invoice|fees| costs)",
    "intellectual_property": r"(intellectual property|patent|copyright|trademark|trade secret|ownership)",
    "non_compete": r"(non-compete|non-compet|restrictive covenant|compete)",
    "assignment": r"(assign|transfer|novate|successor)",
}

RISK_KEYWORDS = {
    "high": ["unlimited liability", "perpetual", "automatic renewal", "exclusive"],
    "medium": ["30 days notice", "arbitration", "attorney fees"],
    "low": ["indemnification", "termination"],
}


@server.list_resources()
async def handle_list_resources():
    return [
        Resource(
            uri="contract::reviews",
            name="Contract Reviews",
            mimeType="application/json",
        ),
        Resource(
            uri="contract::contracts",
            name="Stored Contracts",
            mimeType="application/json",
        ),
    ]


@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="analyze_contract",
            description="Analyze contract text for clauses and risks",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_text": {"type": "string"},
                    "contract_type": {"type": "string"},
                    "api_key": {"type": "string"},
                },
            },
        ),
        Tool(
            name="extract_clauses",
            description="Extract specific clauses from contract",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_text": {"type": "string"},
                    "clause_types": {"type": "array"},
                },
            },
        ),
        Tool(
            name="identify_risks",
            description="Identify potential risks in contract",
            inputSchema={
                "type": "object",
                "properties": {"contract_text": {"type": "string"}},
            },
        ),
        Tool(
            name="compare_contracts",
            description="Compare two contracts",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract1_id": {"type": "string"},
                    "contract2_id": {"type": "string"},
                },
            },
        ),
        Tool(
            name="summarize_contract",
            description="Generate contract summary",
            inputSchema={
                "type": "object",
                "properties": {"contract_text": {"type": "string"}},
            },
        ),
        Tool(
            name="check_favourable_terms",
            description="Check for favourable terms",
            inputSchema={
                "type": "object",
                "properties": {"contract_text": {"type": "string"}},
            },
        ),
        Tool(
            name="get_review_history",
            description="Get review history",
            inputSchema={"type": "object", "properties": {"limit": {"type": "number"}}},
        ),
    ]


def extract_clauses(text: str, clause_types: list = None) -> dict:
    results = {}
    text_lower = text.lower()
    types = clause_types or list(CLAUSE_PATTERNS.keys())

    for clause_type in types:
        pattern = CLAUSE_PATTERNS.get(clause_type, "")
        if pattern:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                results[clause_type] = {
                    "found": True,
                    "count": len(matches),
                    "mentions": list(set(matches))[:5],
                }
            else:
                results[clause_type] = {"found": False}
    return results


def assess_risks(text: str) -> dict:
    text_lower = text.lower()
    high_risks = []
    medium_risks = []
    low_risks = []

    for risk in RISK_KEYWORDS["high"]:
        if risk in text_lower:
            high_risks.append(risk)
    for risk in RISK_KEYWORDS["medium"]:
        if risk in text_lower:
            medium_risks.append(risk)
    for risk in RISK_KEYWORDS["low"]:
        if risk in text_lower:
            low_risks.append(risk)

    overall = "low"
    if len(high_risks) >= 2:
        overall = "high"
    elif high_risks or len(medium_risks) >= 2:
        overall = "medium"

    return {
        "overall_risk": overall,
        "high_risks": high_risks,
        "medium_risks": medium_risks,
        "low_risks": low_risks,
    }


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any = None) -> list[types.TextContent]:
    args = arguments or {}
    api_key = args.get("api_key", "")
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
                ),
            )
        ]

    if name == "analyze_contract":
        text = args.get("contract_text", "")
        contract_type = args.get("contract_type", "general")

        clauses = extract_clauses(text)
        risks = assess_risks(text)
        word_count = len(text.split())

        review = {
            "id": create_id(),
            "contract_type": contract_type,
            "clauses": clauses,
            "risks": risks,
            "word_count": word_count,
            "reviewed_at": datetime.now().isoformat(),
        }
        _store["reviews"].append(review)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "review_id": review["id"],
                        "contract_type": contract_type,
                        "word_count": word_count,
                        "risk_assessment": risks["overall_risk"],
                        "clauses_found": sum(
                            1 for c in clauses.values() if c.get("found")
                        ),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "extract_clauses":
        text = args.get("contract_text", "")
        types = args.get("clause_types", list(CLAUSE_PATTERNS.keys()))

        results = extract_clauses(text, types)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "extracted": results,
                        "found_count": sum(
                            1 for v in results.values() if v.get("found")
                        ),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "identify_risks":
        text = args.get("contract_text", "")

        risks = assess_risks(text)

        return [TextContent(type="text", text=json.dumps(risks, indent=2))]

    elif name == "compare_contracts":
        id1 = args.get("contract1_id")
        id2 = args.get("contract2_id")

        c1 = next((r for r in _store["reviews"] if r["id"] == id1), None)
        c2 = next((r for r in _store["reviews"] if r["id"] == id2), None)

        if not c1 or not c2:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": "Contract not found"})
                )
            ]

        comparison = {
            "contract1_risk": c1["risks"]["overall_risk"],
            "contract2_risk": c2["risks"]["overall_risk"],
            "difference": "contract1_lower"
            if c1["risks"]["overall_risk"] < c2["risks"]["overall_risk"]
            else "same_or_higher",
        }

        return [TextContent(type="text", text=json.dumps(comparison, indent=2))]

    elif name == "summarize_contract":
        text = args.get("contract_text", "")

        clauses = extract_clauses(text)
        risks = assess_risks(text)

        summary = {
            "total_words": len(text.split()),
            "clauses_detected": sum(1 for c in clauses.values() if c.get("found")),
            "risk_level": risks["overall_risk"],
            "key_clauses": [c for c, v in clauses.items() if v.get("found")],
        }

        return [TextContent(type="text", text=json.dumps(summary, indent=2))]

    elif name == "check_favourable_terms":
        text = args.get("contract_text", "")
        text_lower = text.lower()

        favourable = []
        favourable_keywords = [
            "mutual",
            "reasonable",
            "cap",
            "reasonable",
            "negotiable",
            "flexible",
            "customary",
        ]

        for kw in favourable_keywords:
            if kw in text_lower:
                favourable.append(kw)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"favourable_terms": favourable, "count": len(favourable)}
                ),
            )
        ]

    elif name == "get_review_history":
        limit = args.get("limit", 10)

        history = _store["reviews"][-limit:]

        return [
            TextContent(
                type="text",
                text=json.dumps({"reviews": history, "count": len(history)}, indent=2),
            )
        ]

    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]


async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (
        read_stream,
        write_stream,
    ):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="contract-review-ai-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())

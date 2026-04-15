#!/usr/bin/env python3
"""MEOK AI Labs — contract-review-ai-mcp MCP Server. Contract analysis, clause extraction, and risk assessment."""

import json
import re
from datetime import datetime, timezone
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from mcp.server.fastmcp import FastMCP
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None


_store = {"contracts": [], "reviews": []}
mcp = FastMCP("contract-review-ai", instructions="Contract analysis, clause extraction, and risk assessment.")


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


def extract_clauses_fn(text: str, clause_types: list = None) -> dict:
    results = {}
    text_lower = text.lower()
    types_list = clause_types or list(CLAUSE_PATTERNS.keys())

    for clause_type in types_list:
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


@mcp.tool()
def analyze_contract(contract_text: str, contract_type: str = "general", api_key: str = "") -> str:
    """Analyze contract text for clauses and risks"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    clauses = extract_clauses_fn(contract_text)
    risks = assess_risks(contract_text)
    word_count = len(contract_text.split())

    review = {
        "id": create_id(),
        "contract_type": contract_type,
        "clauses": clauses,
        "risks": risks,
        "word_count": word_count,
        "reviewed_at": datetime.now().isoformat(),
    }
    _store["reviews"].append(review)

    return json.dumps(
        {
            "review_id": review["id"],
            "contract_type": contract_type,
            "word_count": word_count,
            "risk_assessment": risks["overall_risk"],
            "clauses_found": sum(1 for c in clauses.values() if c.get("found")),
        },
        indent=2,
    )


@mcp.tool()
def extract_clauses(contract_text: str, clause_types: list = None, api_key: str = "") -> str:
    """Extract specific clauses from contract"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    types_list = clause_types or list(CLAUSE_PATTERNS.keys())
    results = extract_clauses_fn(contract_text, types_list)

    return json.dumps(
        {
            "extracted": results,
            "found_count": sum(1 for v in results.values() if v.get("found")),
        },
        indent=2,
    )


@mcp.tool()
def identify_risks(contract_text: str, api_key: str = "") -> str:
    """Identify potential risks in contract"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    risks = assess_risks(contract_text)
    return json.dumps(risks, indent=2)


@mcp.tool()
def compare_contracts(contract1_id: str, contract2_id: str, api_key: str = "") -> str:
    """Compare two contracts"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    c1 = next((r for r in _store["reviews"] if r["id"] == contract1_id), None)
    c2 = next((r for r in _store["reviews"] if r["id"] == contract2_id), None)

    if not c1 or not c2:
        return json.dumps({"error": "Contract not found"})

    comparison = {
        "contract1_risk": c1["risks"]["overall_risk"],
        "contract2_risk": c2["risks"]["overall_risk"],
        "difference": "contract1_lower"
        if c1["risks"]["overall_risk"] < c2["risks"]["overall_risk"]
        else "same_or_higher",
    }

    return json.dumps(comparison, indent=2)


@mcp.tool()
def summarize_contract(contract_text: str, api_key: str = "") -> str:
    """Generate contract summary"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    clauses = extract_clauses_fn(contract_text)
    risks = assess_risks(contract_text)

    summary = {
        "total_words": len(contract_text.split()),
        "clauses_detected": sum(1 for c in clauses.values() if c.get("found")),
        "risk_level": risks["overall_risk"],
        "key_clauses": [c for c, v in clauses.items() if v.get("found")],
    }

    return json.dumps(summary, indent=2)


@mcp.tool()
def check_favourable_terms(contract_text: str, api_key: str = "") -> str:
    """Check for favourable terms"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    text_lower = contract_text.lower()

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

    return json.dumps({"favourable_terms": favourable, "count": len(favourable)})


@mcp.tool()
def get_review_history(limit: int = 10, api_key: str = "") -> str:
    """Get review history"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    history = _store["reviews"][-limit:]
    return json.dumps({"reviews": history, "count": len(history)}, indent=2)


if __name__ == "__main__":
    mcp.run()

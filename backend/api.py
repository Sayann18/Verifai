"""HTTP API routes for VerifAI.

This module intentionally keeps the existing verification pipeline untouched.
Routes only validate transport-level input and serialize the same dataclass
objects already produced by the original backend modules.
"""

import os
from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from backend.llm_agent import FactCheckerAgent
from backend.search_engine import run_search_pipeline
from backend.utils import FactCheckReport, sanitize_claim_input

router = APIRouter()


class VerifyRequest(BaseModel):
    claim: str


def verify_claim(claim: str) -> dict:
    cleaned = sanitize_claim_input(claim)

    if not cleaned:
        return {
            "ok": False,
            "error": "Invalid Input",
            "message": "Please enter a clear claim of at least 10 characters to verify.",
            "claim": cleaned,
            "results": [],
            "report": asdict(FactCheckReport()),
            "stats": None,
        }

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        return {
            "ok": False,
            "error": "Configuration Error",
            "message": "Verification key is not configured. Please ensure GROQ_API_KEY is set in `.env`.",
            "claim": cleaned,
            "results": [],
            "report": asdict(FactCheckReport()),
            "stats": None,
        }

    try:
        results, stats = run_search_pipeline(cleaned)
    except Exception:
        results, stats = [], None

    try:
        if results:
            agent = FactCheckerAgent(api_key=groq_key)
            report = agent.evaluate_claim(cleaned, results)
        else:
            report = FactCheckReport()
    except Exception:
        report = FactCheckReport()

    return {
        "ok": True,
        "error": None,
        "message": "",
        "claim": cleaned,
        "results": [asdict(result) for result in results],
        "report": asdict(report),
        "stats": stats,
    }


@router.post("/verify")
def verify(payload: VerifyRequest) -> dict:
    return verify_claim(payload.claim)


@router.get("/verify")
def verify_get(q: str) -> dict:
    return verify_claim(q)

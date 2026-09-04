"""
VCG AI Agent Layer

Pipeline:
1. RFP Intelligence
2. Knowledge Retrieval
3. Relevance Scoring
4. Diversity-Aware Evidence Selection
5. Proposal Generation
6. Evidence Audit
7. RFP Compliance
8. Timeline Validation

Architecture:
Knowledge-Enabled Retrieval-Augmented Consulting Agent
with human-in-the-loop governance.
"""

import os
import json
import re
from typing import Dict, Any, Tuple, List

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from retrieval import search_knowledge
from prompts import (
    SYSTEM_PROMPT,
    RFP_ANALYSIS_PROMPT,
    PROPOSAL_PROMPT,
    EVIDENCE_AUDIT_PROMPT,
    COMPLIANCE_PROMPT,
)


# ================================================================
# CONFIGURATION
# ================================================================

load_dotenv()

# Attempt to pull Groq API key from Streamlit Secrets (for Cloud)
# Fallback to local environment variable (for local testing)
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except (KeyError, FileNotFoundError):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "missing_key")

GROQ_MODEL = "llama-3.3-70b-versatile"

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)


# ================================================================
# JSON HELPER
# ================================================================

def safe_json_loads(
    text: str,
    default: Any = None
) -> Any:
    """Safely parse JSON from LLM output."""

    if not text:
        return default

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*
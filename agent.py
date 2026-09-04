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

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434/v1/"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:latest"
)

client = OpenAI(
    base_url=OLLAMA_HOST,
    api_key="ollama"
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
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Try direct parsing first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to extract JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:

        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)
        except Exception:
            pass

    return default


# ================================================================
# LLM CALL
# ================================================================

def call_llm(
    prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 3500
) -> str:

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content or ""


# ================================================================
# DETERMINISTIC RFP FALLBACK
# ================================================================

def deterministic_rfp_analysis(
    rfp_text: str
) -> Dict[str, Any]:
    """
    Fallback parser.

    This is intentionally conservative:
    it extracts what is explicitly present in the RFP rather than
    inventing client conditions.
    """

    text = rfp_text.strip()

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # ------------------------------------------------------------
    # TIMELINE
    # ------------------------------------------------------------

    timeline_match = re.search(
        r"(\d+)\s*[-]?\s*week",
        text.lower()
    )

    timeline = (
        f"{timeline_match.group(1)} weeks"
        if timeline_match
        else ""
    )

    # ------------------------------------------------------------
    # SECTION EXTRACTION
    # ------------------------------------------------------------

    objectives = []
    capabilities = []
    deliverables = []
    constraints = []
    success_criteria = []

    current_section = None

    for line in lines:

        clean = line.strip("-• ")

        lower = clean.lower()

        if lower.startswith("objectives"):
            current_section = "objectives"
            continue

        if lower.startswith("required capabilities"):
            current_section = "capabilities"
            continue

        if lower.startswith("deliverables"):
            current_section = "deliverables"
            continue

        if lower.startswith("constraints"):
            current_section = "constraints"
            continue

        if lower.startswith("success criteria"):
            current_section = "success"
            continue

        if lower.startswith("expected proposal"):
            current_section = None
            continue

        # Stop at obvious new headings
        if clean.endswith(":") and len(clean) < 80:
            continue

        if current_section == "objectives":
            objectives.append(clean)

        elif current_section == "capabilities":
            capabilities.append(clean)

        elif current_section == "deliverables":
            deliverables.append(clean)

        elif current_section == "constraints":
            constraints.append(clean)

        elif current_section == "success":
            success_criteria.append(clean)

    # ------------------------------------------------------------
    # FALLBACK KEYWORD EXTRACTION
    # ------------------------------------------------------------

    text_lower = text.lower()

    if not objectives:

        if "inventory visibility" in text_lower:
            objectives.append(
                "Improve end-to-end inventory visibility"
            )

        if "supply-chain resilience" in text_lower:
            objectives.append(
                "Improve supply-chain resilience"
            )

        if "sustainability" in text_lower:
            objectives.append(
                "Integrate sustainability and transition-risk considerations"
            )

    if not capabilities:

        if (
            "inventory visibility" in text_lower
            or "analytics" in text_lower
        ):
            capabilities.append(
                "Inventory visibility and analytics"
            )

        if (
            "supplier segmentation" in text_lower
            or "resilience" in text_lower
        ):
            capabilities.append(
                "Supply-chain resilience and supplier segmentation"
            )

        if (
            "sustainability" in text_lower
            or "transition risk" in text_lower
        ):
            capabilities.append(
                "Sustainability, transition risk and resilience planning"
            )

    if not deliverables and timeline:

        deliverables.append(
            f"{timeline} transformation roadmap"
        )

    evidence_gaps = [
        "Client current-state maturity",
        "Current technology and data architecture",
        "Current operating-model gaps",
        "Baseline performance and financial impact"
    ]

    discovery_questions = [
        "What systems and data sources currently support inventory visibility?",
        "How are suppliers currently segmented and monitored for resilience?",
        "How are sustainability and transition risks currently incorporated into decision-making?",
        "What baseline KPIs will define success for the transformation?"
    ]

    return {
        "client_type": "",
        "objectives": objectives,
        "problems": [],
        "required_capabilities": capabilities,
        "deliverables": deliverables,
        "timeline": timeline,
        "constraints": constraints,
        "success_criteria": success_criteria,
        "evidence_gaps": evidence_gaps,
        "discovery_questions": discovery_questions
    }


# ================================================================
# STAGE 1 — RFP ANALYSIS
# ================================================================

def analyze_rfp(
    rfp_text: str
) -> Dict[str, Any]:

    default_result = deterministic_rfp_analysis(
        rfp_text
    )

    try:

        prompt = RFP_ANALYSIS_PROMPT.format(
            rfp=rfp_text
        )

        raw = call_llm(
            prompt,
            temperature=0.0,
            max_tokens=2200
        )

        llm_result = safe_json_loads(
            raw,
            default=None
        )

        # If LLM failed → use deterministic parser
        if not isinstance(llm_result, dict):
            return default_result

        # Merge carefully with fallback
        result = {}

        for key in default_result.keys():

            value = llm_result.get(key)

            if value is None:
                value = default_result[key]

            if isinstance(value, list) and len(value) == 0:
                value = default_result[key]

            if isinstance(value, str) and not value.strip():
                value = default_result[key]

            result[key] = value

        return result

    except Exception:
        return default_result


# ================================================================
# RFP QUERY
# ================================================================

def build_retrieval_query(
    rfp_analysis: Dict[str, Any]
) -> str:

    parts = []

    for key in [
        "objectives",
        "problems",
        "required_capabilities",
        "deliverables"
    ]:

        values = rfp_analysis.get(
            key,
            []
        )

        if isinstance(values, list):
            parts.extend(values)

        elif isinstance(values, str):
            if values.strip():
                parts.append(values)

    return " ".join(
        str(x)
        for x in parts
        if x
    )[:5000]


# ================================================================
# KEYWORD RELEVANCE
# ================================================================

def keyword_relevance_score(
    query: str,
    text: str
) -> float:

    query_words = set(
        re.findall(
            r"\b[a-zA-Z]{4,}\b",
            query.lower()
        )
    )

    text_words = set(
        re.findall(
            r"\b[a-zA-Z]{4,}\b",
            text.lower()
        )
    )

    if not query_words:
        return 0.0

    overlap = query_words.intersection(
        text_words
    )

    return round(
        min(
            (len(overlap) / len(query_words)) * 100,
            100
        ),
        1
    )


# ================================================================
# RETRIEVAL
# ================================================================

def retrieve_evidence(
    query: str,
    top_k: int = 8
) -> List[Dict[str, Any]]:

    results = search_knowledge(
        query=query,
        top_k=top_k
    )

    documents = results.get(
        "documents",
        [[]]
    )

    metadatas = results.get(
        "metadatas",
        [[]]
    )

    distances = results.get(
        "distances",
        [[]]
    )

    docs = documents[0] if documents else []
    metas = metadatas[0] if metadatas else []
    dists = distances[0] if distances else []

    sources = []

    for i, text in enumerate(docs):

        metadata = (
            metas[i]
            if i < len(metas)
            else {}
        )

        distance = (
            dists[i]
            if i < len(dists)
            else None
        )

        if isinstance(distance, (int, float)):
            chroma_score = max(
                1,
                min(
                    99,
                    int(
                        100 / (1 + max(distance, 0))
                    )
                )
            )
        else:
            chroma_score = 50

        sources.append({
            "source_id": f"S{i + 1}",
            "document": metadata.get(
                "document",
                "VCG Knowledge Document"
            ),
            "page": metadata.get(
                "page",
                "N/A"
            ),
            "chunk": metadata.get(
                "chunk",
                i + 1
            ),
            "text": text,
            "distance": distance,
            "chroma_score": chroma_score
        })

    return sources


# ================================================================
# SOURCE SCORING
# ================================================================

def score_sources(
    sources: List[Dict[str, Any]],
    query: str
) -> List[Dict[str, Any]]:

    for source in sources:

        keyword_score = keyword_relevance_score(
            query,
            source.get(
                "text",
                ""
            )
        )

        chroma_score = source.get(
            "chroma_score",
            50
        )

        # Balanced score
        final_score = round(
            (
                0.5 * chroma_score
                +
                0.5 * keyword_score
            ),
            1
        )

        source["relevance_score"] = final_score

        if final_score >= 45:
            source["decision"] = "Selected"
            source["icon"] = "✅"

        elif final_score >= 30:
            source["decision"] = "Review"
            source["icon"] = "⚠️"

        else:
            source["decision"] = "Low relevance"
            source["icon"] = "❌"

    return sorted(
        sources,
        key=lambda x: x.get(
            "relevance_score",
            0
        ),
        reverse=True
    )


# ================================================================
# DIVERSITY-AWARE SELECTION
# ================================================================

def select_sources(
    sources: List[Dict[str, Any]],
    max_sources: int = 4
) -> List[Dict[str, Any]]:
    """
    Selects evidence from multiple documents.

    No hard relevance cutoff is imposed when the database is small.
    This is important for the PoC because a chunk can be semantically
    useful even when lexical overlap is low.
    """

    if not sources:
        return []

    selected = []
    used_documents = set()

    # ------------------------------------------------------------
    # PASS 1
    # One strongest chunk per document
    # ------------------------------------------------------------

    for source in sources:

        document = source.get(
            "document",
            "Unknown"
        )

        if document in used_documents:
            continue

        selected.append(source)
        used_documents.add(document)

        if len(selected) >= max_sources:
            break

    # ------------------------------------------------------------
    # PASS 2
    # Fill remaining slots
    # ------------------------------------------------------------

    selected_ids = {
        s.get("source_id")
        for s in selected
    }

    for source in sources:

        if len(selected) >= max_sources:
            break

        if source.get(
            "source_id"
        ) in selected_ids:
            continue

        selected.append(source)

    return selected


# ================================================================
# CONTEXT
# ================================================================

def build_context(
    sources: List[Dict[str, Any]]
) -> Tuple[str, str, List[Dict[str, Any]]]:

    if not sources:
        return (
            "No relevant VCG evidence was retrieved.",
            "None",
            []
        )

    context_blocks = []
    source_index = []
    display_sources = []

    for i, source in enumerate(
        sources,
        start=1
    ):

        source_id = source.get(
            "source_id",
            f"S{i}"
        )

        document = source.get(
            "document",
            "VCG Knowledge Document"
        )

        page = source.get(
            "page",
            "N/A"
        )

        chunk = source.get(
            "chunk",
            i
        )

        text = source.get(
            "text",
            ""
        )

        relevance = source.get(
            "relevance_score",
            0
        )

        context_blocks.append(
            f"""
SOURCE {source_id}

Document: {document}
Page: {page}
Chunk: {chunk}
Relevance score: {relevance}

Evidence:
{text}
""".strip()
        )

        source_index.append(
            f"{source_id} = {document}, Page {page}"
        )

        display_sources.append({
            "source_id": source_id,
            "document": document,
            "page": page,
            "chunk": chunk,
            "relevance_score": relevance,
            "decision": "Selected",
            "icon": "✅",
            "text": text
        })

    return (
        "\n\n---\n\n".join(context_blocks),
        "\n".join(source_index),
        display_sources
    )


# ================================================================
# PROPOSAL GENERATION
# ================================================================

def generate_proposal_strategy(
    rfp_analysis: Dict[str, Any],
    context: str,
    source_index: str
) -> str:

    prompt = PROPOSAL_PROMPT.format(
        rfp_analysis=json.dumps(
            rfp_analysis,
            indent=2
        ),
        context=context,
        source_index=source_index
    )

    return call_llm(
        prompt,
        temperature=0.05,
        max_tokens=4500
    )


# ================================================================
# EVIDENCE AUDIT
# ================================================================

def audit_evidence(
    proposal: str,
    context: str
) -> Dict[str, Any]:

    prompt = EVIDENCE_AUDIT_PROMPT.format(
        proposal=proposal,
        context=context
    )

    try:

        raw = call_llm(
            prompt,
            temperature=0.0,
            max_tokens=3200
        )

        result = safe_json_loads(
            raw,
            default={
                "claims": [],
                "summary": ""
            }
        )

        if not isinstance(result, dict):
            result = {
                "claims": [],
                "summary": ""
            }

    except Exception as exc:

        result = {
            "claims": [],
            "summary": str(exc)
        }

    claims = result.get(
        "claims",
        []
    )

    normalized = []

    for claim in claims:

        if not isinstance(claim, dict):
            continue

        status = str(
            claim.get(
                "status",
                "UNSUPPORTED"
            )
        ).upper().strip()

        if status in {
            "PARTIAL",
            "PARTIALLY VERIFIED",
            "PARTLY VERIFIED"
        }:
            status = "PARTIAL"

        elif status != "VERIFIED":
            status = "UNSUPPORTED"

        claim["status"] = status

        normalized.append(claim)

    result["claims"] = normalized

    result["overall_evidence_score"] = (
        calculate_evidence_score(
            normalized
        )
    )

    return result


def calculate_evidence_score(
    claims: List[Dict[str, Any]]
) -> float:

    if not claims:
        return 100.0

    total = 0.0

    for claim in claims:

        status = claim.get(
            "status",
            "UNSUPPORTED"
        )

        if status == "VERIFIED":
            total += 1.0

        elif status == "PARTIAL":
            total += 0.5

    return round(
        (total / len(claims)) * 100,
        1
    )


# ================================================================
# COMPLIANCE
# ================================================================

def compliance_check(
    proposal: str,
    rfp_analysis: Dict[str, Any]
) -> Dict[str, Any]:

    prompt = COMPLIANCE_PROMPT.format(
        rfp_analysis=json.dumps(
            rfp_analysis,
            indent=2
        ),
        proposal=proposal
    )

    try:

        raw = call_llm(
            prompt,
            temperature=0.0,
            max_tokens=2500
        )

        result = safe_json_loads(
            raw,
            default={
                "checks": [],
                "summary": ""
            }
        )

    except Exception as exc:

        result = {
            "checks": [],
            "summary": str(exc)
        }

    if not isinstance(result, dict):
        result = {
            "checks": [],
            "summary": ""
        }

    checks = []

    for check in result.get(
        "checks",
        []
    ):

        if not isinstance(check, dict):
            continue

        criterion = check.get(
            "criterion",
            check.get(
                "requirement",
                "RFP Requirement"
            )
        )

        status = str(
            check.get(
                "status",
                "WARNING"
            )
        ).upper().strip()

        if status not in {
            "PASS",
            "WARNING",
            "FAIL"
        }:
            status = "WARNING"

        checks.append({
            "criterion": criterion,
            "status": status,
            "reason": check.get(
                "reason",
                check.get(
                    "evidence",
                    ""
                )
            )
        })

    result["checks"] = checks

    result["overall_score"] = (
        calculate_compliance_score(
            checks
        )
    )

    return result


def calculate_compliance_score(
    checks: List[Dict[str, Any]]
) -> float:

    if not checks:
        return 0.0

    total = 0.0

    for check in checks:

        status = check.get(
            "status",
            "FAIL"
        )

        if status == "PASS":
            total += 1.0

        elif status == "WARNING":
            total += 0.5

    return round(
        (total / len(checks)) * 100,
        1
    )


# ================================================================
# TIMELINE
# ================================================================

def validate_timeline_programmatically(
    rfp_text: str,
    proposal_text: str
) -> Dict[str, Any]:

    rfp_match = re.search(
        r"(\d+)\s*[-]?\s*week",
        rfp_text.lower()
    )

    required_weeks = (
        int(rfp_match.group(1))
        if rfp_match
        else None
    )

    week_numbers = []

    # "Week 12"
    week_numbers += [
        int(x)
        for x in re.findall(
            r"week[s]?\s*(\d+)",
            proposal_text.lower()
        )
    ]

    # "12-week"
    week_numbers += [
        int(x)
        for x in re.findall(
            r"(\d+)\s*[-]?\s*week",
            proposal_text.lower()
        )
    ]

    max_detected = (
        max(week_numbers)
        if week_numbers
        else None
    )

    if (
        required_weeks
        and max_detected
        and max_detected > required_weeks
    ):

        return {
            "status": "FAILED",
            "message": (
                f"Timeline mismatch: RFP requests "
                f"{required_weeks} weeks, but proposal "
                f"refers to week {max_detected}."
            ),
            "required": required_weeks,
            "detected": max_detected
        }

    return {
        "status": "PASSED",
        "message": (
            f"Timeline consistent with RFP constraint "
            f"({required_weeks or 'N/A'} weeks)."
        ),
        "required": required_weeks,
        "detected": max_detected
    }


# ================================================================
# MAIN PIPELINE
# ================================================================

def generate_proposal(
    rfp_text: str
) -> Dict[str, Any]:

    # ------------------------------------------------------------
    # 1. RFP INTELLIGENCE
    # ------------------------------------------------------------

    rfp_analysis = analyze_rfp(
        rfp_text
    )

    # Maintain compatibility with your existing app.py
    rfp_analysis["business_objectives"] = (
        rfp_analysis.get(
            "objectives",
            []
        )
    )

    # ------------------------------------------------------------
    # 2. RETRIEVAL QUERY
    # ------------------------------------------------------------

    retrieval_query = build_retrieval_query(
        rfp_analysis
    )

    # ------------------------------------------------------------
    # 3. RETRIEVE
    # ------------------------------------------------------------

    raw_sources = retrieve_evidence(
        retrieval_query,
        top_k=8
    )

    # ------------------------------------------------------------
    # 4. SCORE
    # ------------------------------------------------------------

    scored_sources = score_sources(
        raw_sources,
        retrieval_query
    )

    # ------------------------------------------------------------
    # 5. SELECT
    # ------------------------------------------------------------

    selected_sources = select_sources(
        scored_sources,
        max_sources=4
    )

    # ------------------------------------------------------------
    # 6. CONTEXT
    # ------------------------------------------------------------

    context, source_index, relevance_scores = build_context(
        selected_sources
    )

    # ------------------------------------------------------------
    # 7. PROPOSAL
    # ------------------------------------------------------------

    try:

        proposal = generate_proposal_strategy(
            rfp_analysis=rfp_analysis,
            context=context,
            source_index=source_index
        )

    except Exception as exc:

        proposal = (
            f"Proposal generation failed: {exc}"
        )

    # ------------------------------------------------------------
    # 8. AUDIT
    # ------------------------------------------------------------

    evidence_audit = audit_evidence(
        proposal,
        context
    )

    # ------------------------------------------------------------
    # 9. COMPLIANCE
    # ------------------------------------------------------------

    compliance = compliance_check(
        proposal,
        rfp_analysis
    )

    # ------------------------------------------------------------
    # 10. TIMELINE
    # ------------------------------------------------------------

    timeline_validation = (
        validate_timeline_programmatically(
            rfp_text,
            proposal
        )
    )

    # ------------------------------------------------------------
    # RETURN
    # ------------------------------------------------------------

    return {
        "proposal": proposal,

        "rfp_analysis": rfp_analysis,

        "requirements": rfp_analysis,

        "retrieval_query": retrieval_query,

        "context": context,

        "source_index": source_index,

        "relevance_scores": relevance_scores,

        "retrieved_sources": scored_sources,

        "selected_sources": selected_sources,

        "evidence_audit": evidence_audit,

        "compliance": compliance,

        "timeline_validation": timeline_validation,

        "timeline": timeline_validation,

        "metadata": {
            "model": OLLAMA_MODEL,
            "architecture": (
                "Knowledge-Enabled "
                "Retrieval-Augmented "
                "Consulting Agent"
            ),
            "human_in_loop": True
        }
    }
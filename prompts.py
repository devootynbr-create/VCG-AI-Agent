"""
Prompt library for VCG Knowledge-to-Proposal Agent.
"""


# ================================================================
# SYSTEM PROMPT
# ================================================================

SYSTEM_PROMPT = """
You are the VCG Knowledge-to-Proposal Agent.

You assist consulting teams in developing evidence-backed
proposal strategies.

You are NOT the final decision-maker.

A human consultant must review and approve the output.

STRICT RULES:

1. Never fabricate facts.

2. Never invent a VCG case study, toolkit, framework,
   client, engagement, result, percentage, saving, KPI,
   technology platform or project outcome.

3. A VCG experience claim may ONLY be made if it is directly
   supported by one of the supplied SOURCE IDs.

4. If no evidence supports a claim, say:
   "No retrieved VCG evidence currently supports this claim."

5. The RFP is the only authority for client facts.

6. Never infer that the client currently has a problem unless
   the RFP explicitly states it.

7. Distinguish:
   CLIENT FACT
   VCG EVIDENCE
   HYPOTHESIS
   RECOMMENDATION

8. Recommendations and workstreams are proposals, not evidence.

9. Every VCG experience mentioned in the proposal must use
   an available SOURCE ID.

10. Do not create SOURCE IDs.

11. Do not mention a source that is not included in the supplied
    evidence context.

12. Quantitative claims require direct evidence.

13. When evidence is incomplete, explicitly flag the evidence gap.

14. The agent is advisory and must not claim autonomous decision-making.
"""


# ================================================================
# RFP ANALYSIS
# ================================================================

RFP_ANALYSIS_PROMPT = """
Analyze this RFP.

Extract only information explicitly present in the RFP.

Do NOT infer:
- current client systems
- current client performance
- current maturity
- current weaknesses
- current costs
- current process gaps
- current technology problems

Return ONLY valid JSON.

Use this exact structure:

{{
  "client_type": "",
  "objectives": [],
  "problems": [],
  "required_capabilities": [],
  "deliverables": [],
  "timeline": "",
  "constraints": [],
  "success_criteria": [],
  "evidence_gaps": [],
  "discovery_questions": []
}}

RFP:

{rfp}
"""


# ================================================================
# PROPOSAL
# ================================================================

PROPOSAL_PROMPT = """
Create a professional consulting proposal strategy.

You have two information sources:

1. RFP INTELLIGENCE
2. RETRIEVED VCG EVIDENCE

Do NOT use any information outside these sources.

CRITICAL EVIDENCE RULE:

You may ONLY mention a VCG experience if that experience appears
in the RETRIEVED VCG EVIDENCE below.

You may ONLY use the SOURCE IDs that are explicitly provided.

NEVER create a source that is not present.

For example, if the retrieved evidence includes:

SOURCE S1
Document: VCG_Retail_Digital_Transformation.pdf

SOURCE S2
Document: VCG_Energy_Sustainability_Framework.pdf

you may mention S1 and S2.

You may NOT invent:
"VCG Supply Chain Optimization Toolkit"
unless such a document is actually present.

STRUCTURE:

1. Executive Proposal Thesis

2. Client Objectives
Use the RFP facts.

3. Transformation Hypothesis
Use careful language:
- may
- could
- potentially
- should be assessed
- should be validated

Never state an unverified client condition as fact.

4. Proposed Workstreams
These are recommendations, not VCG evidence.

5. Relevant VCG Evidence
Only use evidence from the provided sources.
Put the SOURCE ID after every experience claim.

6. Multi-Case Synthesis
Explain how different retrieved cases can jointly inform the
proposal.

7. 12-Week Roadmap
Keep the roadmap within the stated RFP timeline.

8. Key Deliverables

9. Evidence Gaps

10. Discovery Questions

11. Human Review Requirements

IMPORTANT:
Do not claim that the client currently has any condition unless
the RFP explicitly states it.

Do not invent numerical benefits.

Do not invent VCG outcomes.

Do not invent credentials.

RFP INTELLIGENCE:

{rfp_analysis}

RETRIEVED VCG EVIDENCE:

{context}

AVAILABLE SOURCE INDEX:

{source_index}
"""


# ================================================================
# EVIDENCE AUDIT
# ================================================================

EVIDENCE_AUDIT_PROMPT = """
Audit ONLY MATERIAL FACTUAL CLAIMS in the proposal.

Do not classify these as unsupported:
- recommendations
- proposed workstreams
- hypotheses
- discovery questions
- future-state suggestions
- proposed deliverables

Audit:
- VCG experience claims
- quantitative claims
- historical outcomes
- claims about client current state
- factual claims presented as evidence

Possible statuses:

VERIFIED
Directly supported.

PARTIAL
Partly supported.

UNSUPPORTED
Not supported by retrieved evidence.

Return ONLY JSON:

{{
  "claims": [
    {{
      "claim": "",
      "status": "VERIFIED",
      "supporting_sources": [],
      "reason": ""
    }}
  ],
  "summary": ""
}}

IMPORTANT:

A recommendation such as:
"The programme should begin with a diagnostic"
is NOT an unsupported factual claim.

A statement such as:
"VCG delivered a 20% saving"
IS a factual claim and must be checked.

PROPOSAL:

{proposal}

RETRIEVED EVIDENCE:

{context}
"""


# ================================================================
# COMPLIANCE
# ================================================================

COMPLIANCE_PROMPT = """
Check whether the proposal addresses the RFP.

Check:

1. Objectives
2. Required capabilities
3. Deliverables
4. Timeline
5. Constraints
6. Success criteria
7. Evidence / hypothesis distinction

Statuses:

PASS
WARNING
FAIL

Do not calculate a numeric score.

Return ONLY JSON:

{{
  "checks": [
    {{
      "criterion": "",
      "status": "PASS",
      "reason": ""
    }}
  ],
  "summary": ""
}}

RFP INTELLIGENCE:

{rfp_analysis}

PROPOSAL:

{proposal}
"""
import tempfile

import streamlit as st
from dotenv import load_dotenv

from ingestion import process_pdf

from retrieval import (
    add_documents,
    add_knowledge_text,
    get_document_count
)

from agent import generate_proposal


# ============================================================
# INITIALIZATION & HELPER FUNCTIONS
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="VCG Knowledge-to-Proposal Agent",
    page_icon="🤖",
    layout="wide"
)

def safe_extract_rfp_analysis(res_dict: dict) -> dict:
    """
    Guarantees a clean, non-crashing dictionary extraction 
    regardless of how agent.py keys the output.
    """
    if not isinstance(res_dict, dict):
        return {
            "business_objectives": [],
            "required_capabilities": [],
            "timeline": "Not specified",
            "constraints": []
        }
    
    analysis = res_dict.get("rfp_analysis") or res_dict.get("requirements") or {}
    
    return {
        "business_objectives": analysis.get("business_objectives", []),
        "required_capabilities": analysis.get("required_capabilities", []),
        "timeline": analysis.get("timeline", "Not specified"),
        "constraints": analysis.get("constraints", [])
    }


# ============================================================
# HEADER
# ============================================================

st.title("🤖 VCG Knowledge-to-Proposal Agent")
st.caption("From institutional knowledge to evidence-backed consulting decisions")

st.divider()


# ============================================================
# SIDEBAR — AGENT ARCHITECTURE
# ============================================================

with st.sidebar:
    st.header("VCG AI Control Panel")

    st.metric(
        "Knowledge Chunks",
        get_document_count()
    )

    st.divider()

    st.markdown(
        """
### Agent Workflow

**1. RFP Analyzer**  
Extract objectives, requirements and constraints.

**2. Knowledge Retriever**  
Search approved VCG institutional knowledge.

**3. Relevance Selector**  
Prioritize the strongest evidence.

**4. Proposal Strategist**  
Build a consulting proposal strategy.

**5. Evidence Auditor**  
Check material factual claims.

**6. Compliance Checker**  
Validate alignment with the RFP.

**7. Human Approval**  
Consultant remains accountable.

**8. Knowledge Capture**  
Approved learning becomes reusable institutional intelligence.
        """
    )

    st.divider()

    st.caption("AI Engine: Local Ollama")


# ============================================================
# STAGE 0 — KNOWLEDGE BASE
# ============================================================

st.header("Stage 0: VCG Knowledge Base")

st.write(
    "Upload synthetic VCG proposals, case studies, frameworks "
    "and research documents."
)

knowledge_files = st.file_uploader(
    "Upload PDF knowledge sources",
    type=["pdf"],
    accept_multiple_files=True,
    key="knowledge_upload"
)


if knowledge_files:
    if st.button("📚 Index Knowledge", use_container_width=True):
        progress = st.progress(0)
        total_chunks = 0

        for index, file in enumerate(knowledge_files):
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf"
                ) as temp:
                    temp.write(file.getbuffer())
                    temp_path = temp.name

                chunks = process_pdf(
                    temp_path,
                    file.name,
                    "VCG Knowledge"
                )

                total_chunks += add_documents(chunks)

                progress.progress((index + 1) / len(knowledge_files))

            except Exception as exc:
                st.error(f"Could not process {file.name}: {exc}")

        st.success(f"Indexed {total_chunks} knowledge chunks.")


st.divider()


# ============================================================
# STAGE 1 — CLIENT RFP
# ============================================================

st.header("Stage 1: Client RFP")

st.write("Enter the client's business requirement or RFP.")

rfp_text = st.text_area(
    "Paste Client RFP",
    height=220,
    placeholder="""
Example:

A diversified industrial manufacturer is seeking a 12-week
transformation programme to improve inventory visibility,
analytics and operational resilience while embedding
sustainability and risk considerations into the transformation
roadmap.

Objectives:
- Create end-to-end inventory visibility using analytics and integrated data.
- Improve supply-chain resilience through better supplier and operating-model decisions.
- Integrate sustainability and transition-risk considerations into transformation priorities.

Required capabilities:
- Inventory visibility and analytics.
- Supply-chain resilience and supplier segmentation.
- Sustainability, transition risk and resilience planning.
- A practical 12-week implementation roadmap.
"""
)


# ============================================================
# RUN BUTTON
# ============================================================

run_agent = st.button(
    "🚀 Run VCG Consulting Agent",
    type="primary",
    use_container_width=True
)


# ============================================================
# AGENT EXECUTION
# ============================================================

if run_agent:
    if not rfp_text.strip():
        st.warning("Please enter a client RFP.")
        st.stop()

    if get_document_count() == 0:
        st.warning(
            "Please upload and index at least one VCG knowledge document first."
        )
        st.stop()

    # Flush legacy session state cache on every new run
    for k in ["agent_result", "approved"]:
        if k in st.session_state:
            del st.session_state[k]

    with st.status("VCG Agent is working...", expanded=True) as status:
        st.write("🔎 Stage 1 — Analysing client RFP")
        st.write("📚 Stage 2 — Retrieving VCG knowledge")
        st.write("🎯 Stage 3 — Selecting relevant evidence")
        st.write("🧠 Stage 4 — Building proposal strategy")
        st.write("🔍 Stage 5 — Auditing evidence")
        st.write("📋 Stage 5B — Checking RFP compliance")
        st.write("⏱️ Stage 5C — Validating timeline")

        try:
            result = generate_proposal(rfp_text)

            status.update(
                label="✅ Agent workflow completed",
                state="complete"
            )

            st.session_state["agent_result"] = result
            st.session_state["approved"] = False

        except Exception as exc:
            status.update(
                label="❌ Agent workflow failed",
                state="error"
            )
            st.error(f"{type(exc).__name__}: {exc}")
            st.stop()


# ============================================================
# DISPLAY RESULTS
# ============================================================

if "agent_result" in st.session_state:
    result = st.session_state.get("agent_result", {})

    # Execute guaranteed extraction
    rfp_analysis = safe_extract_rfp_analysis(result)
    
    proposal = result.get("proposal", "")
    relevance = result.get("relevance_scores", [])
    selected = result.get("selected_sources", [])
    audit = result.get("evidence_audit", {})
    compliance = result.get("compliance", {})
    timeline = result.get("timeline_validation", {})

    # ========================================================
    # TOP DASHBOARD
    # ========================================================

    evidence_score = audit.get("overall_evidence_score", 0)

    selected_documents = len({
        item.get("document") for item in selected if isinstance(item, dict) and "document" in item
    }) if selected else 0

    selected_chunks = len(selected)

    timeline_status = timeline.get("status", "WARNING")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("Knowledge Chunks", get_document_count())

    with c2:
        st.metric("Documents Selected", selected_documents)

    with c3:
        st.metric("Evidence Chunks", selected_chunks)

    with c4:
        st.metric("Evidence Quality", f"{evidence_score}%")

    with c5:
        if timeline_status == "PASSED":
            st.metric("Timeline", "✅ Passed")
        elif timeline_status == "FAILED":
            st.metric("Timeline", "❌ Failed")
        else:
            st.metric("Timeline", "⚠️ Review")

    st.divider()

    # ========================================================
    # STAGE 2 — RFP INTELLIGENCE
    # ========================================================

    st.header("Stage 2: RFP Intelligence")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Target Objectives")
        objectives = rfp_analysis.get("business_objectives", [])
        if objectives:
            for objective in objectives:
                st.write(f"• {objective}")
        else:
            st.write("Not specified")

    with col2:
        st.subheader("Required Capabilities")
        capabilities = rfp_analysis.get("required_capabilities", [])
        if capabilities:
            for capability in capabilities:
                st.write(f"• {capability}")
        else:
            st.write("Not specified")

    with col3:
        st.subheader("Constraints & Timeline")
        st.write(f"Timeline: {rfp_analysis.get('timeline', 'Not specified')}")

        constraints = rfp_analysis.get("constraints", [])
        if constraints:
            for constraint in constraints:
                st.write(f"• {constraint}")
        else:
            st.write("• No explicit constraints detected")

    st.divider()

    # ========================================================
    # STAGE 3 — KNOWLEDGE RETRIEVAL & SELECTION
    # ========================================================

    st.header("Stage 3: Knowledge Retrieval & Selection")
    st.caption(
        "The agent retrieves candidate evidence, scores relevance, and selects "
        "the strongest evidence while avoiding unnecessary duplication."
    )

    for item in relevance:
        if isinstance(item, dict):
            score = item.get("relevance_score", 0)
            icon = item.get("icon", "⚠️")
            decision = item.get("decision", "Review")

            with st.expander(
                f"{icon} {item.get('source_id', 'S')} — "
                f"{item.get('document', 'Doc')} — "
                f"{score}% relevance"
            ):
                st.write(f"**Decision:** {decision}")
                st.write(f"**Page:** {item.get('page', 'Unknown')}")
                st.write(f"**Chunk:** {item.get('chunk', 'Unknown')}")
                st.write("**Evidence Preview:**")
                st.write(item.get("text", "")[:900])

    st.divider()

    # ========================================================
    # SELECTED EVIDENCE SUMMARY
    # ========================================================

    st.subheader("Selected Evidence")

    if selected:
        for item in selected:
            if isinstance(item, dict):
                st.success(
                    f"✅ {item.get('source_id', 'S')} — "
                    f"{item.get('document', 'Doc')} "
                    f"({item.get('relevance_score', 0)}% relevance)"
                )
    else:
        st.warning(
            "No strong evidence was selected. Human review is required."
        )

    st.divider()

    # ========================================================
    # STAGE 4 — PROPOSAL STRATEGY
    # ========================================================

    st.header("Stage 4: Proposal Strategy")

    st.markdown(proposal)

    st.download_button(
        label="⬇️ Download Proposal Draft",
        data=proposal,
        file_name="VCG_Proposal_Strategy.md",
        mime="text/markdown",
        use_container_width=True
    )

    st.divider()

    # ========================================================
    # STAGE 5 — EVIDENCE AUDIT
    # ========================================================

    st.header("Stage 5: Automated Evidence Audit")

    st.caption(
        "Only material factual claims are audited. "
        "Hypotheses and recommendations are not treated as factual claims."
    )

    claims = audit.get("claims", [])

    verified = sum(1 for c in claims if isinstance(c, dict) and c.get("status") == "VERIFIED")
    partial = sum(
    1
    for c in claims
    if isinstance(c, dict)
    and c.get("status") in ["PARTIAL", "PARTIALLY VERIFIED"]
)
    unsupported = sum(1 for c in claims if isinstance(c, dict) and c.get("status") == "UNSUPPORTED")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Evidence Score", f"{evidence_score}%")

    with c2:
        st.metric("Verified", verified)

    with c3:
        st.metric("Partial", partial)

    with c4:
        st.metric("Unsupported", unsupported)

    if claims:
        for claim in claims:
            if isinstance(claim, dict):
                status = claim.get("status", "UNKNOWN")

                if status == "VERIFIED":
                    icon = "✅"
                elif status in ["PARTIAL", "PARTIALLY VERIFIED"]:
                    icon = "⚠️"
                else:
                    icon = "❌"

                with st.expander(
                    f"{icon} {status} — {claim.get('claim', '')[:110]}"
                ):
                    st.write(f"**Claim:** {claim.get('claim', '')}")
                    st.write(f"**Source:** {claim.get('source', 'Not identified')}")
                    st.write(f"**Reason:** {claim.get('reason', '')}")
    else:
        st.info("No material factual claims were returned by the audit.")

    st.divider()

    # ========================================================
    # STAGE 5B — RFP COMPLIANCE
    # ========================================================

    st.header("Stage 5B: RFP Compliance Check")

    compliance_score = compliance.get("overall_score", 0)

    st.metric("RFP Alignment Score", f"{compliance_score}%")

    checks = compliance.get("checks", [])

    if checks:
        for check in checks:
            if isinstance(check, dict):
                status = check.get("status", "WARNING")

                if status == "PASS":
                    icon = "✅"
                elif status == "WARNING":
                    icon = "⚠️"
                else:
                    icon = "❌"

                st.write(
                    f"{icon} **{check.get('criterion', 'Check')}** — "
                    f"{check.get('reason', '')}"
                )
    else:
        st.info("No compliance checks returned.")

    st.divider()

    # ========================================================
    # STAGE 5C — TIMELINE VALIDATION
    # ========================================================

    st.header("Stage 5C: Timeline Validation")

    if timeline_status == "PASSED":
        st.success(f"✅ {timeline.get('message', '')}")
    elif timeline_status == "FAILED":
        st.error(f"❌ {timeline.get('message', '')}")
    else:
        st.warning(f"⚠️ {timeline.get('message', '')}")

    st.divider()

    # ========================================================
    # STAGE 6 — HUMAN APPROVAL
    # ========================================================

    st.header("Stage 6: Consultant Approval Gate")

    st.warning(
        """
HUMAN ACCOUNTABILITY GATE

This is an AI-generated working draft.

Consultant approval is mandatory before client distribution.
The consultant remains accountable for factual accuracy,
credentials, assumptions, recommendations and commercial
commitments.
        """
    )

    check1 = st.checkbox("I have validated all VCG credentials.")
    check2 = st.checkbox("I have validated all numerical claims.")
    check3 = st.checkbox("I have validated all client assumptions.")
    check4 = st.checkbox("I have verified the proposal timeline.")
    check5 = st.checkbox("I have reviewed all recommendations.")
    check6 = st.checkbox("I have confirmed external-facing claims have approved evidence.")

    approval_ready = all([check1, check2, check3, check4, check5, check6])

    if approval_ready:
        st.success("✅ All consultant validation checks completed.")
        st.session_state["approved"] = True
    else:
        st.info(
            "Complete every validation check before capturing institutional learning."
        )

    st.divider()

    # ========================================================
    # STAGE 7 — KNOWLEDGE CAPTURE
    # ========================================================

    if st.session_state.get("approved", False):
        st.header("Stage 7: Capture Institutional Learning")

        st.write(
            """
Capture reusable learning from the engagement.
Approved learning becomes part of VCG's institutional
intelligence and can support future proposals.
            """
        )

        knowledge_type = st.selectbox(
            "Knowledge Type",
            [
                "Case insight",
                "Industry insight",
                "Methodology",
                "Benchmark",
                "Risk pattern",
                "Best practice"
            ]
        )

        knowledge_confidence = st.select_slider(
            "Knowledge Confidence",
            options=["Low", "Medium", "High"],
            value="Medium"
        )

        learning_title = st.text_input("Knowledge Title")

        learning = st.text_area(
            "Reusable Learning",
            height=150,
            placeholder="""
Example:

Inventory visibility transformation should combine
data integration, supplier information and operational
analytics rather than treating inventory as an isolated
planning problem.
"""
        )

        if st.button(
            "🧠 Add Approved Learning to VCG Knowledge Base",
            use_container_width=True
        ):
            if not learning.strip():
                st.warning("Please enter reusable learning.")
            else:
                final_title = (
                    f"{knowledge_type} | "
                    f"{learning_title or 'Untitled'} | "
                    f"Confidence: {knowledge_confidence}"
                )

                try:
                    add_knowledge_text(learning, final_title)

                    st.success(
                        "✅ Institutional learning captured successfully. "
                        "It is now available for future retrieval."
                    )
                    st.rerun()

                except Exception as exc:
                    st.error(f"Knowledge capture failed: {exc}")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "VCG Knowledge-to-Proposal Agent | "
    "Prototype using local Ollama + RAG + human-in-the-loop validation"
)
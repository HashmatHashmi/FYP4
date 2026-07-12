# import os
# import streamlit as st
# from src.graph import analyze_pdf

# st.set_page_config(
#     page_title="Legal Document Analysis Agent",
#     page_icon="⚖️",
#     layout="wide"
# )

# st.title("⚖️ Legal Document Analysis Agent")

# st.write("Upload a legal PDF document for analysis.")

# uploaded_file = st.file_uploader(
#     "Choose a PDF",
#     type=["pdf"]
# )

# if uploaded_file is not None:

#     os.makedirs("data", exist_ok=True)

#     pdf_path = os.path.join(
#         "data",
#         uploaded_file.name
#     )

#     with open(pdf_path, "wb") as f:
#         f.write(uploaded_file.getbuffer())

#     if st.button("Analyze Document"):

#         with st.spinner("Analyzing document..."):

#             report = analyze_pdf(pdf_path)

#         st.success("Analysis Completed!")

#         st.text_area(
#             "Analysis Report",
#             report,
#             height=500
#         )

#         with open(
#             "reports/legal_analysis_report.txt",
#             "rb"
#         ) as file:

#             st.download_button(
#                 label="Download Report",
#                 data=file,
#                 file_name="legal_analysis_report.txt",
#                 mime="text/plain"
#             )


import os
import streamlit as st
from src.graph import app as pipeline

st.set_page_config(
    page_title="Legal Document Analysis Agent",
    page_icon="⚖️",
    layout="wide",
)

st.markdown("""
<style>
.risk-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: white;
}
.risk-high { background-color: #d64545; }
.risk-medium { background-color: #e0912f; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚖️ Legal Doc Analyzer")
    st.caption("AI-powered contract & legal document review")
    st.markdown("---")
    st.markdown("**What it does**")
    st.write(
        "Upload a legal PDF and this agent will classify the document type, "
        "summarize it, flag risky clauses, and suggest safer rewrites — "
        "all in one pass."
    )
    with st.expander("How the pipeline works"):
        st.markdown(
            "1. **Extract** text from the PDF\n"
            "2. **Clean & chunk** the text\n"
            "3. **Summarize** the document\n"
            "4. **Classify** the document type\n"
            "5. **Detect risks** in the clauses\n"
            "6. **Draft safer revisions** for risky clauses"
        )
    st.markdown("---")
    st.caption("Final Year Project · LangGraph + Transformers")

if "analysis" not in st.session_state:
    st.session_state.analysis = None

st.title("⚖️ Legal Document Analysis Agent")
st.write("Upload a legal PDF document for AI-powered classification, summarization, and risk analysis.")

uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

if uploaded_file is not None:
    os.makedirs("data", exist_ok=True)
    pdf_path = os.path.join("data", uploaded_file.name)
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Analyze Document", type="primary"):
        stage_labels = {
            "extract": ("Extracting text from PDF...", 15),
            "clean": ("Cleaning and chunking text...", 30),
            "summarize": ("Generating summary...", 55),
            "classify": ("Classifying document type...", 70),
            "risk": ("Scanning for legal risks...", 85),
            "report": ("Drafting safer clauses and building report...", 100),
        }

        progress_bar = st.progress(0, text="Starting analysis...")
        final_state = {}

        try:
            for update in pipeline.stream({"pdf_path": pdf_path}, stream_mode="updates"):
                for node_name, node_output in update.items():
                    final_state.update(node_output)
                    label, pct = stage_labels.get(node_name, (f"Running {node_name}...", None))
                    if pct:
                        progress_bar.progress(pct, text=label)

            progress_bar.empty()
            st.session_state.analysis = final_state
            st.success("Analysis complete!")

        except Exception as e:
            progress_bar.empty()
            st.error(f"Analysis failed: {e}")
            st.session_state.analysis = None

result = st.session_state.analysis

if result:
    st.markdown("---")

    risks = result.get("risk_details", [])
    high_count = sum(1 for r in risks if r["risk"] == "HIGH")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Document Type", result.get("document_type", "—").title())
    col2.metric("Confidence", f"{result.get('confidence', 0) * 100:.1f}%")
    col3.metric("Risks Found", len(risks))
    col4.metric("High-Risk Clauses", high_count)

    st.subheader("📄 Summary")
    st.info(result.get("summary", "No summary available."))

    st.subheader("⚠️ Risk Analysis")
    if risks:
        for risk in risks:
            badge_class = "risk-high" if risk["risk"] == "HIGH" else "risk-medium"
            with st.container(border=True):
                st.markdown(
                    f'<span class="risk-badge {badge_class}">{risk["risk"]} RISK</span>',
                    unsafe_allow_html=True,
                )
                st.markdown("**Detected Clause**")
                st.write(risk["clause"])
                st.markdown("**Suggested Revision**")
                st.write(risk["suggested_revision"])
    else:
        st.success("No significant risks detected.")

    st.markdown("---")
    st.download_button(
        label="⬇️ Download Full Report",
        data=result.get("report", ""),
        file_name="legal_analysis_report.txt",
        mime="text/plain",
    )
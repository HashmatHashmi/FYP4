import os
import streamlit as st
from src.graph import analyze_pdf

st.set_page_config(
    page_title="Legal Document Analysis Agent",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Legal Document Analysis Agent")

st.write("Upload a legal PDF document for analysis.")

uploaded_file = st.file_uploader(
    "Choose a PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    os.makedirs("data", exist_ok=True)

    pdf_path = os.path.join(
        "data",
        uploaded_file.name
    )

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Analyze Document"):

        with st.spinner("Analyzing document..."):

            report = analyze_pdf(pdf_path)

        st.success("Analysis Completed!")

        st.text_area(
            "Analysis Report",
            report,
            height=500
        )

        with open(
            "reports/legal_analysis_report.txt",
            "rb"
        ) as file:

            st.download_button(
                label="Download Report",
                data=file,
                file_name="legal_analysis_report.txt",
                mime="text/plain"
            )
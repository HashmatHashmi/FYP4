from typing import TypedDict

from langgraph.graph import StateGraph, END

from src.pdf_extractor import extract_text_from_pdf
from src.preprocessing import clean_text, chunk_text
from src.summarizer import summarize_document
from src.classifier import classify_document
from src.risk_analyzer import analyze_risks
from src.report_generator import generate_report, save_report


class AgentState(TypedDict):
    pdf_path: str

    raw_text: str
    cleaned_text: str
    chunks: list

    summary: str

    document_type: str
    confidence: float

    risks: list
    risk_details: list   # NEW
    report: str

    

# Extraction Node  
def extraction_node(state):

    raw_text = extract_text_from_pdf(
        state["pdf_path"]
    )

    return {
        "raw_text": raw_text
    }
    
    
# Cleaning Node

def cleaning_node(state):

    cleaned = clean_text(
        state["raw_text"]
    )

    chunks = chunk_text(cleaned)

    return {
        "cleaned_text": cleaned,
        "chunks": chunks
    }
    
# Summarizer Node
def summarizer_node(state):

    summary = summarize_document(
        state["chunks"]
    )

    return {
        "summary": summary
    }
    
# Classifier Node
def classifier_node(state):

    result = classify_document(
        state["cleaned_text"]
    )

    return {
        "document_type": result["document_type"],
        "confidence": result["confidence"]
    }

# Risk Node
def risk_node(state):

    risks = analyze_risks(
        state["cleaned_text"]
    )

    return {
        "risks": risks
    }
    
# Report Node
# def report_node(state):

#     report = generate_report(
#         state["document_type"],
#         state["confidence"],
#         state["summary"],
#         state["risks"]
#     )

#     save_report(report)

#     return {
#         "report": report
#     }
def report_node(state):
    report, risk_details = generate_report(
        state["document_type"],
        state["confidence"],
        state["summary"],
        state["risks"],
    )
    save_report(report)
    return {"report": report, "risk_details": risk_details}

# Build Graph
graph = StateGraph(AgentState)

graph.add_node("extract", extraction_node)
graph.add_node("clean", cleaning_node)
graph.add_node("summarize", summarizer_node)
graph.add_node("classify", classifier_node)
graph.add_node("risk", risk_node)
graph.add_node("report", report_node)

# Connect Nodes
graph.set_entry_point("extract")

graph.add_edge("extract", "clean")
graph.add_edge("clean", "summarize")
graph.add_edge("summarize", "classify")
graph.add_edge("classify", "risk")
graph.add_edge("risk", "report")
graph.add_edge("report", END)

# Compile
app = graph.compile()

# Run Ftn
# def analyze_pdf(pdf_path):

#     result = app.invoke({

#         "pdf_path": pdf_path

#     })

#     return result["report"]
def analyze_pdf(pdf_path):
    return app.invoke({"pdf_path": pdf_path})
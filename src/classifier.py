from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

LABELS = [
    "property lease agreement", "employment contract", "service agreement", "Affidavit-of-Small-Estate", 
    "Amendment-to-an-LLC-Operating-Agreement", "Arbitration-Agreement-Template", "Asset-Purchase-Agreement", 
    "bill-of-sale-for-car", "Board Meeting Templat", "Boat-Bill-of-Sale", "Commercial Lease Agreement Templates", 
    "Free Affidavit of Service Template", "Generic-Commercial-Sublease-Agreement", "Lease Extension Addendum",
    "LEASE RENEWAL AGREEMENT", "Lease Renewal Letters", "Lease Termination Letters", "Month-to-Month-Rental-Agreement",
    "non-disclosure-agreement", "Pet Addendum Forms to Rental Agreement", "Property Management Agreements",
    "Rental Agreement Template", "Residential Lease Agreement Templates", "short-term-rental-agreement", 
    "Sublease Agreement Templates", "Sublease Agreement Templates", "non disclosure agreement", 
    "memorandum of understanding", "power of attorney", "affidavit", "court judgement", "legal notice", 
    "police complaint","asset purchase agreement", "share purchase agreement", "business sale agreement" 
]

def classify_document(text, max_words=400):
    snippet = " ".join(text.split()[:max_words])  # doc type is evident up front
    result = classifier(snippet, LABELS,
                         hypothesis_template="This document is a {}.",
                         multi_label=False)
    return {"document_type": result["labels"][0], "confidence": result["scores"][0]}
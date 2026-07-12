from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

LABELS = [
    "property lease agreement", "employment contract", "service agreement",
    "non disclosure agreement", "memorandum of understanding",
    "power of attorney", "affidavit", "court judgement",
    "legal notice", "police complaint",
]

def classify_document(text, max_words=400):
    snippet = " ".join(text.split()[:max_words])  # doc type is evident up front
    result = classifier(snippet, LABELS,
                         hypothesis_template="This document is a {}.",
                         multi_label=False)
    return {"document_type": result["labels"][0], "confidence": result["scores"][0]}
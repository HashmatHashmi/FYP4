from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def _summarize_text(text, max_len, min_len):
    input_length = len(text.split())
    max_len = min(max_len, max(15, input_length - 5))
    min_len = min(min_len, max(10, max_len - 5))
    return summarizer(text, max_length=max_len, min_length=min_len,
                       do_sample=False, truncation=True)[0]["summary_text"]

def summarize_document(chunks, target_words=150):
    chunk_summaries = [_summarize_text(c, max_len=120, min_len=30) for c in chunks]
    combined = " ".join(chunk_summaries)

    # reduce step: keep condensing until it's actually summary-length
    while len(combined.split()) > target_words:
        prev_len = len(combined.split())
        combined = _summarize_text(combined, max_len=target_words, min_len=40)
        if len(combined.split()) >= prev_len:  # stop if it's not shrinking further
            break
    return combined
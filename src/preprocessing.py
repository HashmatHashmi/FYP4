import re

# def clean_text(text):
#     # Remove extra spaces
#     text = re.sub(r'\s+', ' ', text)

#     # Remove special characters (keep basic punctuation)
#     text = re.sub(r'[^\w\s.,;:!?()-]', '', text)

#     # Strip leading/trailing spaces
#     text = text.strip()

#     return text

def clean_text(text):
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters (keep basic punctuation and apostrophes)
    text = re.sub(r"[^\w\s.,;:!?()'-]", '', text)  # <-- Added the apostrophe here

    # Strip leading/trailing spaces
    text = text.strip()

    return text

def chunk_text(text, max_words=300):
    words = text.split()
    return [
        " ".join(words[i:i + max_words])
        for i in range(0, len(words), max_words)
    ]
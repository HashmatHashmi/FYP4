import re

def analyze_risks(text):
    text_lower = text.lower()

    risk_patterns = {
        "HIGH": [
            r"all losses", r"without limitation", r"unlimited liability",
            r"indemnif\w+", r"held harmless", r"held liable",
        ],
        "MEDIUM": [
            r"terminate anytime", r"without notice", r"no notice",
            r"immediately", r"penalty", r"fine", r"attorney", r"no refund",
        ],
    }
    risk_rank = {"HIGH": 2, "MEDIUM": 1}

    matches = []
    for level, patterns in risk_patterns.items():
        for pattern in patterns:
            for m in re.finditer(pattern, text_lower):
                matches.append((m.start(), m.end(), level, pattern))

    if not matches:
        return []

    matches.sort(key=lambda m: m[0])

    # merge overlapping/adjacent matches so one sentence = one risk entry
    merged = []
    for start, end, level, pattern in matches:
        if merged and start <= merged[-1]["end"] + 20:  # close enough = same clause
            prev = merged[-1]
            prev["end"] = max(prev["end"], end)
            if risk_rank[level] > risk_rank[prev["risk"]]:
                prev["risk"] = level
            prev["patterns"].append(pattern)
        else:
            merged.append({"start": start, "end": end, "risk": level, "patterns": [pattern]})

    risks = []
    for m in merged:
        risks.append({
            "risk": m["risk"],
            "pattern": ", ".join(m["patterns"]),
            "clause": _extract_sentence(text, m["start"], m["end"]),
        })
    return risks


def _extract_sentence(text, start, end, context_chars=100):
    """Snap a character span out to sentence boundaries so clauses
    never start or end mid-word."""
    win_start = max(0, start - context_chars)
    win_end = min(len(text), end + context_chars)

    left = text.rfind(".", win_start, start)
    left = left + 1 if left != -1 else win_start

    right_hits = [c for c in (text.find(p, end, win_end) for p in ".!?") if c != -1]
    right = min(right_hits) + 1 if right_hits else win_end

    # fallback: never split a word even if no sentence punctuation was found
    while left > win_start and not text[left - 1].isspace():
        left -= 1
    while right < win_end and not text[right].isspace():
        right += 1

    return text[left:right].strip()
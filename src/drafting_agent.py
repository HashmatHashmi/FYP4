# from transformers import pipeline

# draft_model = pipeline(
#     "text2text-generation",
#     model="google/flan-t5-base"  # swap to "google/flan-t5-small" if memory errors return
# )

# def drafting_agent(clause, risk_level):
#     prompt = f"""You are an expert legal drafting assistant.

# Rewrite ONLY the following legal clause so it is safer and more balanced.

# Requirements:
# - Preserve the original meaning and intent.
# - Reduce legal risk and remove one-sided language.
# - Use clear, professional legal language.
# - Return ONLY the revised clause text. No explanations, no labels, no quotes.

# Risk Level: {risk_level}

# Clause:
# {clause}

# Revised Clause:"""

#     result = draft_model(prompt, max_length=180, num_beams=4,
#                           no_repeat_ngram_size=3, do_sample=False)
#     output = result[0]["generated_text"].strip()

#     if output.lower().startswith("revised clause:"):  # flan-t5 sometimes echoes the label
#         output = output.split(":", 1)[1].strip()
#     return output

from transformers import pipeline
import re

draft_model = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"  # swap to "google/flan-t5-small" if memory errors return
)

# flan-t5-base has no grounding for which party is which — left alone it can
# (and did) silently rewrite "the Seller" as "the Buyer" mid-clause. Masking
# these terms out before generation and restoring them after makes that
# class of error structurally impossible instead of hoping the model gets
# it right. Longest phrases first so "Seller's Solicitors" isn't partially
# masked by the shorter "Seller" pattern.
_PROTECTED_TERMS = [
    "Seller's Solicitors", "Buyer's Solicitors",
    "Seller's", "Buyer's",
    "Seller", "Buyer",
]


def _mask_parties(text):
    mapping = {}
    masked = text
    for i, term in enumerate(_PROTECTED_TERMS):
        placeholder = f"[[ENTITY_{i}]]"
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, masked):
            mapping[placeholder] = term
            masked = re.sub(pattern, placeholder, masked)
    return masked, mapping


def _unmask_parties(text, mapping):
    for placeholder, term in mapping.items():
        text = text.replace(placeholder, term)
    return text


def _looks_like_noop(original, revised):
    """True if the 'revision' is essentially the clause echoed back."""
    o = re.sub(r"\W+", "", original.lower())
    r = re.sub(r"\W+", "", revised.lower())
    if not o or not r:
        return True
    shorter, longer = sorted([o, r], key=len)
    return shorter in longer and len(shorter) / len(longer) > 0.9


def _generate(prompt, sample=False):
    if sample:
        result = draft_model(prompt, max_length=220, num_beams=1,
                              do_sample=True, temperature=0.8, top_p=0.9)
    else:
        result = draft_model(prompt, max_length=220, num_beams=4,
                              no_repeat_ngram_size=3, do_sample=False)
    output = result[0]["generated_text"].strip()
    if output.lower().startswith("revised clause:"):  # flan-t5 sometimes echoes the label
        output = output.split(":", 1)[1].strip()
    return output


def drafting_agent(clause, risk_level):
    masked_clause, mapping = _mask_parties(clause)

    prompt = f"""You are an expert legal drafting assistant.

Rewrite ONLY the following legal clause so it is safer and more balanced.

Requirements:
- Preserve the original meaning and intent.
- Reduce legal risk and remove one-sided language.
- Use clear, professional legal language.
- Tokens like [[ENTITY_0]] are placeholders for party names — copy them
  through exactly as they appear, do not remove, reorder, or rename them.
- Return ONLY the revised clause text. No explanations, no labels, no quotes.

Risk Level: {risk_level}

Clause:
{masked_clause}

Revised Clause:"""

    output = _generate(prompt)

    # flan-t5-base sometimes collapses to echoing the input back verbatim
    # on long/complex clauses. One retry with sampling instead of beam
    # search usually breaks it out of that; if not, we say so honestly
    # rather than presenting the original clause as if it were a fix.
    if _looks_like_noop(masked_clause, output):
        retry = _generate(prompt, sample=True)
        if not _looks_like_noop(masked_clause, retry):
            output = retry

    output = _unmask_parties(output, mapping)

    if _looks_like_noop(clause, output):
        return ("[Automatic rewrite unavailable for this clause — "
                "flag for manual legal review]")

    return output
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



##########################################################################
# from transformers import pipeline
# import re

# draft_model = pipeline(
#     "text2text-generation",
#     model="google/flan-t5-base"  # swap to "google/flan-t5-small" if memory errors return
# )

# # flan-t5-base has no grounding for which party is which — left alone it can
# # (and did) silently rewrite "the Seller" as "the Buyer" mid-clause. Masking
# # these terms out before generation and restoring them after makes that
# # class of error structurally impossible instead of hoping the model gets
# # it right. Longest phrases first so "Seller's Solicitors" isn't partially
# # masked by the shorter "Seller" pattern.
# _PROTECTED_TERMS = [
#     "Seller's Solicitors", "Buyer's Solicitors",
#     "Seller's", "Buyer's",
#     "Seller", "Buyer",
# ]


# def _mask_parties(text):
#     mapping = {}
#     masked = text
#     for i, term in enumerate(_PROTECTED_TERMS):
#         placeholder = f"[[ENTITY_{i}]]"
#         pattern = r"\b" + re.escape(term) + r"\b"
#         if re.search(pattern, masked):
#             mapping[placeholder] = term
#             masked = re.sub(pattern, placeholder, masked)
#     return masked, mapping


# def _unmask_parties(text, mapping):
#     for placeholder, term in mapping.items():
#         text = text.replace(placeholder, term)
#     return text


# def _looks_like_noop(original, revised):
#     """True if the 'revision' is essentially the clause echoed back."""
#     o = re.sub(r"\W+", "", original.lower())
#     r = re.sub(r"\W+", "", revised.lower())
#     if not o or not r:
#         return True
#     shorter, longer = sorted([o, r], key=len)
#     return shorter in longer and len(shorter) / len(longer) > 0.9


# def _generate(prompt, sample=False):
#     if sample:
#         result = draft_model(prompt, max_length=220, num_beams=1,
#                               do_sample=True, temperature=0.8, top_p=0.9)
#     else:
#         result = draft_model(prompt, max_length=220, num_beams=4,
#                               no_repeat_ngram_size=3, do_sample=False)
#     output = result[0]["generated_text"].strip()
#     if output.lower().startswith("revised clause:"):  # flan-t5 sometimes echoes the label
#         output = output.split(":", 1)[1].strip()
#     return output


# def drafting_agent(clause, risk_level):
#     masked_clause, mapping = _mask_parties(clause)

#     prompt = f"""You are an expert legal drafting assistant.

# Rewrite ONLY the following legal clause so it is safer and more balanced.

# Requirements:
# - Preserve the original meaning and intent.
# - Reduce legal risk and remove one-sided language.
# - Use clear, professional legal language.
# - Tokens like [[ENTITY_0]] are placeholders for party names — copy them
#   through exactly as they appear, do not remove, reorder, or rename them.
# - Return ONLY the revised clause text. No explanations, no labels, no quotes.

# Risk Level: {risk_level}

# Clause:
# {masked_clause}

# Revised Clause:"""

#     output = _generate(prompt)

#     # flan-t5-base sometimes collapses to echoing the input back verbatim
#     # on long/complex clauses. One retry with sampling instead of beam
#     # search usually breaks it out of that; if not, we say so honestly
#     # rather than presenting the original clause as if it were a fix.
#     if _looks_like_noop(masked_clause, output):
#         retry = _generate(prompt, sample=True)
#         if not _looks_like_noop(masked_clause, retry):
#             output = retry

#     output = _unmask_parties(output, mapping)

#     if _looks_like_noop(clause, output):
#         return ("[Automatic rewrite unavailable for this clause — "
#                 "flag for manual legal review]")

#     return output


##################################################################################################

# from transformers import pipeline
# import re

# draft_model = pipeline(
#     "text2text-generation",
#     model="google/flan-t5-base"  # swap to "google/flan-t5-small" if memory errors return
# )

# # --- Entity masking -----------------------------------------------------
# # flan-t5-base has no grounding for which party is which, so left alone it
# # swaps "Seller" <-> "Buyer" mid-clause.
# #
# # First attempt used bracket tokens like "[[ENTITY_0]]". That backfired:
# # this document is a template already full of bracketed placeholders
# # ("[INSERT DATE]", "[NUMBER]", "[SPECIFY ...]"), so the bracket syntax
# # accidentally told the model "this is an editable template slot" and it
# # filled it in, deleted it, or garbled it instead of copying it through.
# #
# # Fix: use plain, ordinary capitalized words with no brackets, underscores,
# # or digits, so nothing resembles the document's own placeholder markup.
# _SURROGATES = {"Seller": "Harlow", "Buyer": "Whitfield"}


# def _mask_parties(text):
#     """Replace Seller/Buyer with surrogate names. Only tracks surrogates
#     that actually occur in this specific clause, so a clause that never
#     mentions "Buyer" doesn't get checked for a surrogate that was never
#     there to begin with."""
#     mapping = {}  # surrogate -> real term
#     masked = text
#     for real, surrogate in _SURROGATES.items():
#         pattern = r"\b" + re.escape(real) + r"\b"
#         if re.search(pattern, masked):
#             mapping[surrogate] = real
#             masked = re.sub(pattern, surrogate, masked)
#     return masked, mapping


# def _unmask_parties(text, mapping):
#     for surrogate, real in mapping.items():
#         text = text.replace(surrogate, real)
#     return text


# def _surrogates_intact(output, mapping):
#     """Guards against the model mutating or dropping a surrogate mid
#     generation (the "[[TENANT_3]]" / "_____" failure we saw with bracket
#     tokens). If a surrogate that went in doesn't come out, the output is
#     not trustworthy — restoring party names onto it would silently leave
#     the wrong or missing party in the final text."""
#     return all(s in output for s in mapping)


# def _looks_like_noop(original, revised):
#     """True if the 'revision' is essentially the clause echoed back."""
#     o = re.sub(r"\W+", "", original.lower())
#     r = re.sub(r"\W+", "", revised.lower())
#     if not o or not r:
#         return True
#     shorter, longer = sorted([o, r], key=len)
#     return shorter in longer and len(shorter) / len(longer) > 0.9


# def _generate(prompt, sample=False):
#     if sample:
#         result = draft_model(prompt, max_length=220, num_beams=1,
#                               do_sample=True, temperature=0.8, top_p=0.9)
#     else:
#         result = draft_model(prompt, max_length=220, num_beams=4,
#                               no_repeat_ngram_size=3, do_sample=False)
#     output = result[0]["generated_text"].strip()
#     if output.lower().startswith("revised clause:"):  # flan-t5 sometimes echoes the label
#         output = output.split(":", 1)[1].strip()
#     return output


# _FALLBACK_MSG = ("[Automatic rewrite unavailable for this clause — "
#                   "flag for manual legal review]")


# def drafting_agent(clause, risk_level):
#     masked_clause, mapping = _mask_parties(clause)

#     party_note = ""
#     if mapping:
#         names = ", ".join(sorted(set(mapping.keys())))
#         party_note = (f"- The clause refers to the parties by name ({names}). "
#                       f"Keep their names and roles exactly as given — do not "
#                       f"swap, remove, or rename them.\n")

#     prompt = f"""You are an expert legal drafting assistant.

# Rewrite ONLY the following legal clause so it is safer and more balanced.

# Requirements:
# - Preserve the original meaning and intent.
# - Reduce legal risk and remove one-sided language.
# - Use clear, professional legal language.
# {party_note}- Return ONLY the revised clause text. No explanations, no labels, no quotes.

# Risk Level: {risk_level}

# Clause:
# {masked_clause}

# Revised Clause:"""

#     output = _generate(prompt)

#     # Retry once with sampling if the model echoed the clause back unchanged,
#     # or if it mangled/dropped a party surrogate. Beam search + greedy decoding
#     # is what produced both failure modes; sampling usually breaks the loop.
#     if _looks_like_noop(masked_clause, output) or not _surrogates_intact(output, mapping):
#         retry = _generate(prompt, sample=True)
#         if not _looks_like_noop(masked_clause, retry) and _surrogates_intact(retry, mapping):
#             output = retry

#     # If we still can't trust the output, say so honestly rather than
#     # silently restoring party names onto a broken generation.
#     if _looks_like_noop(masked_clause, output) or not _surrogates_intact(output, mapping):
#         return _FALLBACK_MSG

#     output = _unmask_parties(output, mapping)

#     if _looks_like_noop(clause, output):
#         return _FALLBACK_MSG

#     return output
    
    
###########################################################################################


from transformers import pipeline
import re

draft_model = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"  # swap to "google/flan-t5-small" if memory errors return
)

# --- Entity masking -----------------------------------------------------
# flan-t5-base has no grounding for which party is which. Two earlier
# attempts at fixing this both turned out incomplete:
#
#   v1: masked with bracket tokens like "[[ENTITY_0]]" -- collided with
#       this document's own "[INSERT DATE]"-style template placeholders,
#       so the model treated them as fill-in-the-blank slots and deleted
#       or garbled them.
#
#   v2: switched to plain surrogate words ("Harlow"/"Whitfield") and
#       validated only that each surrogate appeared *somewhere* in the
#       output. That missed three distinct failure modes the model still
#       produces: (a) it can swap two surrogates' positions while keeping
#       both present -- a structural error, not a vocabulary one; (b) it
#       can mutate one occurrence into a similar-looking word (e.g.
#       "Harlow" -> "Harpoo") while a different, correct occurrence
#       elsewhere satisfies a presence-only check; (c) it can revert a
#       surrogate back to the real word ("Seller") for part of the
#       sentence while another correct surrogate elsewhere still passes.
#
# v3 (this version) checks the exact ORDERED SEQUENCE of party mentions,
# not just presence. That catches all three failure modes: a swap changes
# the order, a mutation changes the count, a reversion removes an entry
# from the sequence entirely.
_SURROGATES = {"Seller": "Harlow", "Buyer": "Whitfield"}
_SURROGATE_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in _SURROGATES.values()) + r")\b"
)


def _mask_parties(text):
    """Only tracks surrogates that actually occur in this specific clause."""
    mapping = {}  # surrogate -> real term
    masked = text
    for real, surrogate in _SURROGATES.items():
        pattern = r"\b" + re.escape(real) + r"\b"
        if re.search(pattern, masked):
            mapping[surrogate] = real
            masked = re.sub(pattern, surrogate, masked)
    return masked, mapping


def _unmask_parties(text, mapping):
    for surrogate, real in mapping.items():
        text = text.replace(surrogate, real)
    return text


def _party_sequence(text):
    """Ordered list of every surrogate mention, in order of appearance."""
    return _SURROGATE_PATTERN.findall(text)


def _is_ordered_subsequence(needle, haystack):
    """True if `needle` appears in `haystack` in the same relative order
    (extra items in haystack are fine, gaps are fine — only order matters)."""
    it = iter(haystack)
    return all(any(n == h for h in it) for n in needle)


def _output_trustworthy(masked_input, output, mapping):
    """The masked input's party sequence must appear, in order, within the
    output's party sequence. A genuine rewrite is free to add an extra
    mention of a party (e.g. "subject to Whitfield giving notice") — that's
    fine, it doesn't break the order of the original mentions. What it
    catches: swaps (order broken), mutations (an expected mention is
    missing because it turned into "Harpoo"), and reversions (a mention
    is missing because the model output the real word instead)."""
    if not mapping:
        return True
    return _is_ordered_subsequence(_party_sequence(masked_input), _party_sequence(output))


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


_FALLBACK_MSG = ("[Automatic rewrite unavailable for this clause — "
                  "flag for manual legal review]")


def _valid(masked_clause, output, mapping):
    return not _looks_like_noop(masked_clause, output) and _output_trustworthy(masked_clause, output, mapping)


def drafting_agent(clause, risk_level):
    masked_clause, mapping = _mask_parties(clause)

    party_note = ""
    if mapping:
        names = ", ".join(sorted(set(mapping.keys())))
        party_note = (f"- The clause refers to the parties by name ({names}). "
                       f"Keep their names and roles exactly as given, in the "
                       f"same order they appear — do not swap, remove, "
                       f"duplicate, or rename them.\n")

#     prompt = f"""You are an expert legal drafting assistant.

# Rewrite ONLY the following legal clause so it is safer and more balanced.

# Requirements:
# - Preserve the original meaning and intent.
# - Reduce legal risk and remove one-sided language.
# - Use clear, professional legal language.
# {party_note}- Return ONLY the revised clause text. No explanations, no labels, no quotes.

# Risk Level: {risk_level}

# Clause:
# {masked_clause}

# Revised Clause:"""
#################################################################
    prompt = f"""
You are an experienced legal contract drafting assistant.

Your task is to rewrite ONLY the clause below.

Instructions:

- Preserve the legal meaning.
- Preserve all important facts.
- Preserve the parties exactly as written.
- Do NOT invent new obligations.
- Do NOT remove legal obligations.
- Reduce one-sided or unfair language where possible.
- Make the clause clearer and more balanced.
- If the clause is already acceptable, rewrite it only for clarity.
- Return ONLY one rewritten clause.
- Never return explanations.
- Never return bullet points.
- Never return headings.
- Never return "Revised Clause".
- Never answer with "I cannot..."
- Never answer with placeholders.

{party_note}

Risk Level:
{risk_level}

Original Clause:
{masked_clause}

Rewritten Clause:
"""
#################################################################

    output = _generate(prompt)

    if not _valid(masked_clause, output, mapping):
        retry = _generate(prompt, sample=True)
        if _valid(masked_clause, retry, mapping):
            output = retry

    if not _valid(masked_clause, output, mapping):
        return _FALLBACK_MSG

    output = _unmask_parties(output, mapping)

    if _looks_like_noop(clause, output):
        return _FALLBACK_MSG

    return output
    
    
    
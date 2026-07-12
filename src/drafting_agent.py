draft_model = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"  # swap to "google/flan-t5-small" if memory errors return
)

def drafting_agent(clause, risk_level):
    prompt = f"""You are an expert legal drafting assistant.

Rewrite ONLY the following legal clause so it is safer and more balanced.

Requirements:
- Preserve the original meaning and intent.
- Reduce legal risk and remove one-sided language.
- Use clear, professional legal language.
- Return ONLY the revised clause text. No explanations, no labels, no quotes.

Risk Level: {risk_level}

Clause:
{clause}

Revised Clause:"""

    result = draft_model(prompt, max_length=180, num_beams=4,
                          no_repeat_ngram_size=3, do_sample=False)
    output = result[0]["generated_text"].strip()

    if output.lower().startswith("revised clause:"):  # flan-t5 sometimes echoes the label
        output = output.split(":", 1)[1].strip()
    return output
"""LLM-as-judge: a strong model grades each answer, and a guard validates the grade."""
import json

JUDGE_SYSTEM = """You are a strict quality reviewer for a customer support assistant.
You get: the company knowledge base, the customer's question, a reference answer, and the assistant's answer.

Score the assistant's answer from 1 (bad) to 5 (excellent) on:
- accuracy: facts match the knowledge base and the reference
- completeness: answers everything the customer asked
- tone: polite, clear, professional, concise

hallucination = true if the answer states ANY fact, price, promise or service that is not in the knowledge base.
If the question is not covered by the knowledge base, a good answer says it will check or pass to a manager, and does not invent anything.

Reply with JSON only:
{"accuracy": 1-5, "completeness": 1-5, "tone": 1-5, "hallucination": true/false, "reason": "one short sentence"}"""


def build_judge_prompt(knowledge_base, question, reference, answer):
    return (
        f"KNOWLEDGE BASE:\n{knowledge_base}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"REFERENCE ANSWER:\n{reference}\n\n"
        f"ASSISTANT ANSWER:\n{answer}"
    )


def parse_verdict(raw):
    """Validate the judge's JSON. Returns a dict, or None if the grade can't be trusted."""
    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        data = json.loads(raw[start:end])
        scores = {k: int(data[k]) for k in ("accuracy", "completeness", "tone")}
        hallucination = data["hallucination"]
    except (ValueError, KeyError, TypeError):
        return None

    if not all(1 <= s <= 5 for s in scores.values()):
        return None
    if not isinstance(hallucination, bool):
        return None

    scores["hallucination"] = hallucination
    scores["reason"] = str(data.get("reason", ""))
    scores["average"] = round((scores["accuracy"] + scores["completeness"] + scores["tone"]) / 3, 2)
    return scores

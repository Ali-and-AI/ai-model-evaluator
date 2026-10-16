"""Ask every candidate model every question, let the judge grade the answers, and print a comparison.
Usage: python run_eval.py
"""
import csv
import json
import statistics
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from config import CANDIDATES, JUDGE_MODEL, PASS_SCORE, PRICES  # noqa: E402
from judge import JUDGE_SYSTEM, build_judge_prompt, parse_verdict  # noqa: E402
from models import ask, ask_claude, gemini_available  # noqa: E402

HERE = Path(__file__).parent
KNOWLEDGE_BASE = (HERE / "knowledge_base.md").read_text(encoding="utf-8")

ASSISTANT_SYSTEM = f"""You are the customer support assistant of Pixel Studio.
Answer ONLY using the knowledge base below. Be friendly and concise (2-4 sentences).
If the answer is not in the knowledge base, say you will check with the team and a manager will reply. Never invent prices, services or promises. If the customer asks about a service, call or time that is not explicitly in the knowledge base, do NOT agree or promise. Say a manager will reply. Do not say that we do or don’t offer something unless the knowledge base says so.

{KNOWLEDGE_BASE}"""


def cost_usd(model, input_tokens, output_tokens):
    price = PRICES.get(model)
    if price is None:
        return None
    return (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000


def load_questions():
    lines = (HERE / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def main():
    questions = load_questions()
    candidates = [c for c in CANDIDATES if c["provider"] != "gemini" or gemini_available()]
    rows = []

    for cand in candidates:
        model = cand["model"]
        print(f"\n=== {model} ===")
        for q in questions:
            try:
                answer = ask(cand["provider"], model, ASSISTANT_SYSTEM, q["question"])
            except Exception as error:  # one failed call must not stop the whole run
                print(f"  #{q['id']:<2} ERROR: {error}")
                rows.append({"model": model, "id": q["id"], "error": str(error)})
                continue

            try:
                judge_raw = ask_claude(
                    JUDGE_MODEL,
                    JUDGE_SYSTEM,
                    build_judge_prompt(KNOWLEDGE_BASE, q["question"], q["reference"], answer["text"]),
                )["text"]
            except Exception as error:  # a failed judge call means "not graded", not a crash
                print(f"  #{q['id']:<2} judge ERROR: {error}")
                judge_raw = ""
            verdict = parse_verdict(judge_raw)

            row = {
                "model": model,
                "id": q["id"],
                "answerable": q["answerable"],
                "answer": answer["text"],
                "latency_s": round(answer["latency"], 2),
                "cost_usd": cost_usd(model, answer["input_tokens"], answer["output_tokens"]),
                "judge_ok": verdict is not None,
            }
            if verdict:
                row.update(verdict)
                passed = verdict["average"] >= PASS_SCORE and not verdict["hallucination"]
                row["passed"] = passed
                flag = "PASS" if passed else "FAIL"
                halluc = "  HALLUCINATION" if verdict["hallucination"] else ""
                print(f"  #{q['id']:<2} {flag} score={verdict['average']:<4}{halluc}")
            else:
                row["passed"] = False
                print(f"  #{q['id']:<2} judge answer could not be parsed -> needs human review")
            rows.append(row)

    summarize(rows)
    save(rows)


def summarize(rows):
    print("\n\nRESULTS")
    print(f"{'model':<20}{'pass':>8}{'avg score':>11}{'halluc.':>9}{'avg sec':>9}{'$ / answer':>12}")
    for model in dict.fromkeys(r["model"] for r in rows):
        mine = [r for r in rows if r["model"] == model and "error" not in r]
        graded = [r for r in mine if r["judge_ok"]]
        if not mine:
            print(f"{model:<20} all calls failed")
            continue
        passed = sum(r["passed"] for r in mine)
        avg = statistics.mean(r["average"] for r in graded) if graded else 0
        halluc = sum(r.get("hallucination", False) for r in graded)
        latency = statistics.mean(r["latency_s"] for r in mine)
        costs = [r["cost_usd"] for r in mine if r["cost_usd"] is not None]
        cost = f"${statistics.mean(costs):.5f}" if costs else "n/a"
        print(f"{model:<20}{f'{passed}/{len(mine)}':>8}{avg:>11.2f}{halluc:>9}{latency:>9.1f}{cost:>12}")


def save(rows):
    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"results_{datetime.now():%Y%m%d_%H%M}.csv"
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nAll answers and grades saved to {path}")


if __name__ == "__main__":
    main()

# AI Model Evaluator: which LLM should answer your customers?

Asks several models (Claude Haiku, Sonnet, Opus, optionally Gemini) the same customer-support questions, lets a strong model grade every answer (**LLM-as-judge**), and compares **quality, hallucinations, speed and cost per answer**.

The goal: choose the cheapest model that is still good enough, with numbers instead of guesses.

## How it works

```
question ─► candidate model (answers from the knowledge base only)
                 │
                 ▼
          judge model ─► JSON grade ─► validation guard ─► results table
          (accuracy, completeness, tone, hallucination yes/no)
```

- `knowledge_base.md`: support FAQ for a fictional web studio
- `questions.jsonl`: 12 questions with reference answers, including **3 that the knowledge base doesn't cover**, to catch models that invent answers
- `judge.py`: judge prompt + `parse_verdict`, a guard that rejects malformed or out-of-range grades
- `run_eval.py`: runs everything, prints the comparison table, saves a CSV to `results/`
- `test_judge.py`: unit tests (no API key needed)

## Run it

```bash
pip install -r requirements.txt
python -m unittest -v
python run_eval.py
```

Put `ANTHROPIC_API_KEY=...` (and optionally `GEMINI_API_KEY=...`) in a `.env` file. It is git-ignored.

## Results

**Run 1: baseline prompt**

| Model | Passed | Avg score | Hallucinations | Avg sec | $ / answer |
|---|---|---|---|---|---|
| Claude Haiku 5.5 | 10/12 | 4.75 | 2 | 1.3 | $0.00010 |
| Claude Sonnet 5.5 | **12/12** | **4.97** | **0** | 1.9 | $0.00236 |
| Claude Opus 5.5 | **12/12** | 4.95 | **0** | 2.9 | $0.00527 |

**Run 2: one added prompt rule** (*"if a service, call or time is not in the knowledge base, do not agree or promise; say a manager will reply"*)

| Model | Passed | Avg score | Hallucinations | Avg sec | $ / answer |
|---|---|---|---|---|---|
| Claude Haiku 5.5 | **11/12** | 4.67 | **1** | 1.2 | $0.00011 |
| Claude Sonnet 5.5 | 12/12 | 4.97 | 0 | 1.8 | $0.00232 |
| Claude Opus 5.5 | 12/12 | 4.95 | 0 | 3.7 | $0.00529 |

### Findings

- **The most expensive model wasn't the best.** Sonnet matched Opus on quality with zero hallucinations, at less than half the cost and faster.
- **The cheapest model invents answers.** Haiku is ~24x cheaper than Sonnet but, in run 1, agreed to a 9am phone call the studio doesn't offer and made claims about mobile apps the knowledge base never mentions.
- **One prompt rule halved Haiku's hallucinations** (2 → 1) at no extra cost. The remaining case is borderline: Haiku said "we don't build mobile apps", a reasonable guess, but not something the knowledge base states.

### Limitations

- 12 questions is a small sample; LLM output varies between runs, so results should be confirmed over repeated runs and a larger set.
- The judge (Opus) also graded its own answers; self-preference bias is possible, so a sample of grades should be checked by hand.

## Design choices

- **Judge output is validated, not trusted.** A grade with missing fields, scores outside 1-5 or a non-boolean hallucination flag is discarded and flagged for human review.
- **Unanswerable questions** test the most expensive failure in customer support: confidently inventing a price or a service.
- **Cost per answer** is computed from real token usage, so the trade-off between quality and price is explicit.

---

**Alina Kremenchutska**, AI Automation Engineer, founder of [Ali & AI](https://ali-and-ai.com)

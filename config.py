"""Settings: which models to compare, which model judges, and prices.

Prices are USD per 1 million tokens (input, output). Check them against
the provider's pricing page before publishing results.
"""

# Models that answer customer questions. Comment out any you don't want to test.
CANDIDATES = [
    {"provider": "anthropic", "model": "claude-haiku-5-5"},
    {"provider": "anthropic", "model": "claude-sonnet-5-5"},
    {"provider": "anthropic", "model": "claude-opus-5-5"},
    # Gemini runs only if GEMINI_API_KEY is in .env and google-genai is installed.
    {"provider": "gemini", "model": "gemini-3.8-flash"},
]

# The judge grades every answer. A strong model makes a fairer judge.
JUDGE_MODEL = "claude-opus-5-5"

PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "gemini-3.8-flash": None,  # unknown: fill in from Google's pricing page
}

# An answer passes if its average score (1-5) is at least this and it has no hallucination.
PASS_SCORE = 4.0

"""One function per provider. Each returns the same shape so the rest of the code doesn't care which model answered."""
import os
import time

import anthropic

_anthropic = None


def _client():
    global _anthropic
    if _anthropic is None:
        _anthropic = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _anthropic


def ask_claude(model, system, user, max_tokens=2000):
    started = time.perf_counter()
    response = _client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    latency = time.perf_counter() - started
    if response.stop_reason == "refusal":
        text = "[refused]"
    else:
        # Thinking blocks can come before the text, so pick the text block by type.
        text = next((b.text for b in response.content if b.type == "text"), "")
    return {
        "text": text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency": latency,
    }


def gemini_available():
    if not os.getenv("GEMINI_API_KEY"):
        return False
    try:
        import google.genai  # noqa: F401
    except ImportError:
        return False
    return True


def ask_gemini(model, system, user):
    from google import genai
    from google.genai import types

    client = genai.Client()
    started = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    latency = time.perf_counter() - started
    usage = response.usage_metadata
    return {
        "text": response.text or "",
        "input_tokens": getattr(usage, "prompt_token_count", 0) or 0,
        "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
        "latency": latency,
    }


def ask(provider, model, system, user):
    if provider == "anthropic":
        return ask_claude(model, system, user)
    if provider == "gemini":
        return ask_gemini(model, system, user)
    raise ValueError(f"unknown provider: {provider}")

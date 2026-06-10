"""
Gemini API client wrapper for EcoTrace.

Handles:
- API key loading from environment
- Request retry logic with exponential backoff
- JSON response parsing and validation
"""

import json
import os
import time
import logging
from typing import Any

import google.generativeai as genai

from agent.prompt_builder import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BACKOFF_BASE = 2  # seconds


def _get_api_key() -> str:
    """Get the Gemini API key from environment, fail loudly if missing."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Copy .env.example to .env and add your key."
        )
    return key


def _configure_client() -> genai.GenerativeModel:
    """Configure and return a Gemini model instance."""
    genai.configure(api_key=_get_api_key())
    return genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            response_mime_type="application/json",
        ),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_insight(user_prompt: str) -> dict[str, Any]:
    """
    Send a prompt to Gemini and return the parsed JSON insight.

    Retries up to _MAX_RETRIES times with exponential backoff
    on transient failures.
    """

    model = _configure_client()
    last_error: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            response = model.generate_content(user_prompt)

            # Parse JSON from response
            text = response.text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first and last lines (the fences)
                text = "\n".join(lines[1:-1]).strip()

            parsed = json.loads(text)
            return parsed

        except json.JSONDecodeError as e:
            logger.warning(f"Gemini returned invalid JSON (attempt {attempt + 1}): {e}")
            last_error = e
        except Exception as e:
            logger.warning(f"Gemini API error (attempt {attempt + 1}): {e}")
            last_error = e

        # Exponential backoff before retry
        if attempt < _MAX_RETRIES - 1:
            wait = _BACKOFF_BASE ** attempt
            logger.info(f"Retrying in {wait}s...")
            time.sleep(wait)

    # All retries exhausted
    raise RuntimeError(
        f"Failed to get valid response from Gemini after {_MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )

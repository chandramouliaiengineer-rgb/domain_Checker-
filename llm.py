import json
import os
import re

from openai import AsyncOpenAI
from dotenv import load_dotenv

from naming_rules import build_llm_system_prompt

load_dotenv()

client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"],
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

def _extract_names(text: str) -> list[str]:
    """Pull a JSON array of lowercase strings out of the model's reply,
    tolerating markdown fences or stray text around it."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    # Try a clean parse first.
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(x).lower().strip() for x in data if isinstance(x, str)]
    except json.JSONDecodeError:
        pass

    # Fallback: grab the first [...] block anywhere in the text.
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [str(x).lower().strip() for x in data if isinstance(x, str)]
        except json.JSONDecodeError:
            pass
    return []


async def generate_names(description: str, count: int = 20) -> list[str]:
    """Call the NVIDIA model with the naming-skill system prompt + the user's
    free-text description; return raw candidate names (unfiltered)."""
    system_prompt = build_llm_system_prompt()
    user_msg = (
        f"Business idea / niche: {description}\n\n"
        f"Generate {count} domain-name candidates as a JSON array of lowercase strings.\n\n"
        "These must be likely to still be UNREGISTERED as .com domains:\n"
        "- Strongly favor invented words, blends/portmanteaus, and affixed coinages.\n"
        "- AVOID plain single dictionary words and obvious two-word compounds — those "
        "are almost always already registered.\n"
        "- Distinctive, slightly unexpected coinages are the ones still available.\n\n"
        "Maximize variety across the list:\n"
        "- Spread across techniques: compounds, blends, prefixed, suffixed, fully "
        "invented, and lexical-shift names.\n"
        "- Do NOT cluster around one root word — no two names sharing the same stem.\n"
        "- Vary length, rhythm, and starting letters."
    )
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        temperature=1,
        top_p=0.95,
        max_tokens=2048,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    content = resp.choices[0].message.content or ""
    return _extract_names(content)

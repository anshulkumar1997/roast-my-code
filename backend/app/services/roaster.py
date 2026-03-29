import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialise the client once at module level (not per-request)
_client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

SYSTEM_PROMPT = """You are a savage but secretly helpful code reviewer.
Your job is to:
1. ROAST the code — be funny, brutal, creative. Like a comedy roast.
2. Give REAL feedback — concrete, actionable improvements.
3. Rate the code quality from 1 to 10 (be honest).

Always respond with valid JSON in exactly this format:
{
  "roast": "your funny roast here",
  "feedback": "your real, actionable feedback here",
  "rating": <integer 1-10>
}

No markdown. No explanation outside the JSON. Just the JSON object."""


async def roast_code(code: str, language: str = "auto") -> dict:
    """Call ChatGPT to roast the submitted code and return structured feedback."""
    lang_hint = f"Language: {language}\n\n" if language != "auto" else ""

    message = _client.responses.create(
        model="gpt-5-nano",
        instructions=SYSTEM_PROMPT,
        input=[
            {
                "role": "user",
                "content": f"{lang_hint}Code to roast:\n```\n{code}\n```",
            }
        ],
    )

    raw = message.output_text

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {e}\nRaw response: {raw}")

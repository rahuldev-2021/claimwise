"""Extract JSON from provider text."""

import json
import re


def extract_json_text(raw: str) -> str:
    text = raw.strip()
    if not text:
        return ""
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_json_dict(raw: str) -> dict:
    payload = extract_json_text(raw)
    if not payload:
        raise ValueError("Empty LLM response")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("LLM response JSON must be an object")
    return data

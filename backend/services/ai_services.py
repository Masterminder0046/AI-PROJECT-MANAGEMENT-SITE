"""OpenAI integration: subtasks, planning, suggestions."""
import json, os
from typing import Tuple
# pyrefly: ignore [missing-import]
from django.conf import settings

try:
    # pyrefly: ignore [missing-import]
    from openai import OpenAI
    _openai = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except Exception:
    _openai = None

try:
    # pyrefly: ignore [missing-import]
    import google.generativeai as genai
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini = genai.GenerativeModel('gemini-flash-latest')
    else:
        _gemini = None
except Exception:
    _gemini = None

MODEL_OPENAI = "gpt-4o-mini"


def _chat(system: str, user: str) -> Tuple[dict, int]:
    # Prefer Gemini if available, fallback to OpenAI
    if _gemini:
        return _chat_gemini(system, user)
    if _openai:
        return _chat_openai(system, user)
    return {"error": "No AI provider configured"}, 0


def _chat_openai(system: str, user: str) -> Tuple[dict, int]:
    resp = _openai.chat.completions.create(
        model=MODEL_OPENAI,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
        temperature=0.4,
    )
    text = resp.choices[0].message.content or "{}"
    tokens = getattr(resp.usage, "total_tokens", 0)
    try:
        return json.loads(text), tokens
    except json.JSONDecodeError:
        return {"raw": text}, tokens


def _chat_gemini(system: str, user: str) -> Tuple[dict, int]:
    prompt = f"{system}\n\nUser request: {user}\n\nIMPORTANT: Return ONLY valid JSON."
    response = _gemini.generate_content(prompt)
    text = response.text
    # Basic JSON extraction in case Gemini wraps it in markdown blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    tokens = 0 # Gemini doesn't always expose tokens easily in this SDK version
    try:
        return json.loads(text), tokens
    except json.JSONDecodeError:
        return {"raw": text}, tokens


def generate_subtasks(title: str, context: dict) -> Tuple[dict, int]:
    sys = ("You break a software task into actionable subtasks. "
           "Return JSON: {\"subtasks\": [{\"title\": \"...\", \"description\": \"...\", \"priority\": \"low|medium|high|urgent\", \"estimate_hours\": 1}]}")
    user = f"Task: {title}\nProject context: {json.dumps(context)[:1500]}"
    return _chat(sys, user)


def plan_project(idea: str) -> Tuple[dict, int]:
    sys = ("You are a senior PM. Given a product idea, return JSON: "
           "{\"milestones\": [{\"name\": \"...\", \"tasks\": [{\"title\": \"...\", \"priority\": \"...\", \"estimate_hours\": 1}]}]}")
    return _chat(sys, f"Idea: {idea}")


def suggest_next(prompt: str, context: dict) -> Tuple[dict, int]:
    sys = ("You suggest the next best actions for a project team. "
           "Return JSON: {\"suggestions\": [{\"title\": \"...\", \"why\": \"...\", \"impact\": \"low|medium|high\"}]}")
    return _chat(sys, f"{prompt}\nContext: {json.dumps(context)[:1500]}")

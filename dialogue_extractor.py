"""GPT API 기반 대화문 추출 및 난이도 분류 모듈"""
import json
import re
from openai import OpenAI

client = None

def init_client(api_key: str):
    global client
    client = OpenAI(api_key=api_key)

EXTRACTION_PROMPT = """You are an expert English literature analyst.
From the following book excerpt, extract ALL dialogue lines spoken by characters.

Return a JSON array. Each element must have:
- "speaker": the character name (or "Unknown" if unclear)
- "line": the exact dialogue text (without quotation marks)
- "context": a brief 1-sentence description of the situation
- "difficulty": one of "Beginner", "Intermediate", "Advanced"
  * Beginner: simple vocabulary, short sentences, everyday expressions
  * Intermediate: moderate vocabulary, idiomatic expressions, compound sentences
  * Advanced: complex vocabulary, literary expressions, long/nested sentences
- "modern_equivalent": a modern, natural rephrasing of the line (helpful for classic literature)
- "key_expressions": list of up to 3 notable phrases/idioms worth learning

Text: {text}

Respond ONLY with a valid JSON array. No extra text."""

ROLEPLAY_PROMPT = """You are an English conversation tutor.
Based on the following original dialogue from a book, create an interactive role-play scenario.

Original dialogue context: {context}
Dialogue lines:
{dialogue}

Create a role-play where:
1. The user plays one character (assign them the most interesting role)
2. You (AI) play all other characters
3. Keep the spirit of the original but allow natural conversation flow

Return JSON with:
- "scenario": scene description in English (2-3 sentences)
- "user_role": character name the user will play
- "ai_roles": list of character names the AI will play
- "opening_line": AI's first line to start the conversation
- "vocabulary_tips": list of 3-5 key phrases from this dialogue worth practicing

Respond ONLY with valid JSON."""

FEEDBACK_PROMPT = """You are an English pronunciation and fluency coach.
The user was practicing this target line:
Target: "{target}"
User said: "{user_input}"

Evaluate and provide feedback in JSON:
- "accuracy_score": integer 0-100
- "pronunciation_issues": list of specific words that may be mispronounced
- "fluency_feedback": one encouraging sentence about delivery
- "grammar_note": any grammar correction if needed (null if correct)
- "encouragement": a motivating closing remark

Respond ONLY with valid JSON."""

def extract_dialogues(text: str, model: str = "gpt-4o-mini") -> list[dict]:
    """텍스트에서 대화문 추출"""
    if not client:
        raise RuntimeError("OpenAI client not initialized. Call init_client() first.")
    prompt = EXTRACTION_PROMPT.format(text=text[:4000])
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    # JSON array가 object로 감싸진 경우 처리
    parsed = json.loads(raw)
    if isinstance(parsed, list):
        return parsed
    # {"dialogues": [...]} 형태
    for v in parsed.values():
        if isinstance(v, list):
            return v
    return []

def generate_roleplay_setup(dialogues: list[dict], model: str = "gpt-4o-mini") -> dict:
    """롤플레잉 시나리오 생성"""
    if not client:
        raise RuntimeError("OpenAI client not initialized.")
    context = dialogues[0].get("context", "") if dialogues else ""
    dialogue_text = "\n".join(f'{d["speaker"]}: "{d["line"]}" ' for d in dialogues[:8])
    prompt = ROLEPLAY_PROMPT.format(context=context, dialogue=dialogue_text)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)

def chat_roleplay(messages: list[dict], user_input: str,
                  scenario: str, ai_roles: list[str],
                  model: str = "gpt-4o-mini") -> str:
    """롤플레잉 대화 응답 생성"""
    if not client:
        raise RuntimeError("OpenAI client not initialized.")
    system = (
        f"You are playing the following characters in a role-play: {', '.join(ai_roles)}.\n"
        f"Scenario: {scenario}\n"
        "Respond naturally in English as these characters. Keep responses concise (1-3 sentences). "
        "Stay in character at all times."
    )
    history = [{"role": "system", "content": system}] + messages + [{"role": "user", "content": user_input}]
    resp = client.chat.completions.create(
        model=model,
        messages=history,
        temperature=0.8,
    )
    return resp.choices[0].message.content

def evaluate_response(target: str, user_input: str, model: str = "gpt-4o-mini") -> dict:
    """발음/유창성 피드백"""
    if not client:
        raise RuntimeError("OpenAI client not initialized.")
    prompt = FEEDBACK_PROMPT.format(target=target, user_input=user_input)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)

def translate_to_modern(classic_text: str, model: str = "gpt-4o-mini") -> str:
    """고전 영어 → 현대 영어 변환"""
    if not client:
        raise RuntimeError("OpenAI client not initialized.")
    resp = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": f"Rewrite this classic English text in modern, natural American English. "
                       f"Keep the same meaning but use contemporary vocabulary and phrasing.\n\nText: {classic_text}"
        }],
        temperature=0.5,
    )
    return resp.choices[0].message.content

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


# Upstream restructured its repo: the old per-book JSON files were replaced by
# full JSONL exports under full_line_jsonl/full/<正序|乱序>/.
RAW_BASE = "https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/full_line_jsonl/full/正序"

OUT_DIR = Path(__file__).resolve().parents[1] / "core" / "vocab_data"

DECKS: dict[str, dict[str, Any]] = {
    "primary_en": {
        "difficulty": 1,
        "sources": [
            "人教小学三年级.jsonl",
            "人教小学四年级.jsonl",
            "人教小学五年级.jsonl",
            "人教小学六年级.jsonl",
        ],
    },
    "middle_school_en": {"difficulty": 2, "sources": ["初中.jsonl"]},
    "high_school_en": {"difficulty": 3, "sources": ["高中.jsonl"]},
    "cet4_en": {"difficulty": 4, "sources": ["四级.jsonl"]},
    "cet6_en": {"difficulty": 5, "sources": ["六级.jsonl"]},
    "ielts_en": {"difficulty": 6, "sources": ["雅思.jsonl"]},
    "toefl_en": {"difficulty": 7, "sources": ["托福.jsonl"]},
}


def fetch_source(name: str) -> list[dict[str, Any]]:
    base = urllib.parse.quote(RAW_BASE, safe=":/")
    url = f"{base}/{urllib.parse.quote(name)}"
    req = urllib.request.Request(url, headers={"User-Agent": "InkSight-VocabImport/1.0"})
    with urllib.request.urlopen(req, timeout=180) as response:
        payload = response.read().decode("utf-8")
    items: list[dict[str, Any]] = []
    for line in payload.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_phonetic(value: Any) -> str:
    text = clean_text(value).strip("/")
    return f"/{text}/" if text else ""


def _word_object(item: dict[str, Any]) -> dict[str, Any]:
    """Unwrap the nested {"content": {"word": {...}}} envelope used upstream."""
    word_obj = item.get("content")
    if isinstance(word_obj, dict):
        word_obj = word_obj.get("word")
    return word_obj if isinstance(word_obj, dict) else {}


def _word_content(item: dict[str, Any]) -> dict[str, Any]:
    content = _word_object(item).get("content")
    return content if isinstance(content, dict) else {}


def _word_head(item: dict[str, Any]) -> str:
    head = clean_text(_word_object(item).get("wordHead"))
    return head or clean_text(item.get("headWord"))


def pick_definition(content: dict[str, Any]) -> str:
    translations = content.get("trans")
    parts: list[str] = []
    if isinstance(translations, list):
        for translation in translations[:3]:
            if not isinstance(translation, dict):
                continue
            body = clean_text(translation.get("tranCn"))
            pos = clean_text(translation.get("pos"))
            if not body:
                continue
            parts.append(f"{pos}. {body}" if pos else body)
    return "；".join(parts)


def pick_example(content: dict[str, Any]) -> str:
    sentence = content.get("sentence")
    if isinstance(sentence, dict):
        sentences = sentence.get("sentences")
        if isinstance(sentences, list):
            for entry in sentences:
                if not isinstance(entry, dict):
                    continue
                text = clean_text(entry.get("sContent"))
                if text:
                    return text
    return ""


def convert_item(deck_id: str, difficulty: int, item: dict[str, Any]) -> dict[str, Any] | None:
    word = _word_head(item)
    content = _word_content(item)
    definition = pick_definition(content)
    if not word or not definition:
        return None
    phonetic = normalize_phonetic(content.get("usphone") or content.get("ukphone"))
    return {
        "deck_id": deck_id,
        "word": word,
        "phonetic": phonetic,
        "definition": definition,
        "example": pick_example(content),
        "difficulty": difficulty,
    }


def build_deck(deck_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    difficulty = int(spec["difficulty"])
    for source in spec["sources"]:
        for raw_item in fetch_source(source):
            item = convert_item(deck_id, difficulty, raw_item)
            if item is None:
                continue
            key = item["word"].casefold()
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
    return output


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for deck_id, spec in DECKS.items():
        items = build_deck(deck_id, spec)
        path = OUT_DIR / f"{deck_id}.json"
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{deck_id}: {len(items)} -> {path}")


if __name__ == "__main__":
    main()

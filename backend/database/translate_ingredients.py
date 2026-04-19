"""
One-time script: add English columns to ingredients.xlsx via DeepSeek translation.

Run once:  cd backend && python -m database.translate_ingredients
"""

import json
import sys
from pathlib import Path

import pandas as pd
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

XLSX = Path(__file__).resolve().parent / "data" / "ingredients.xlsx"
FIELDS = ["function", "description", "usage", "caution_level"]
MODEL = "deepseek-chat"


def translate_batch(client: OpenAI, rows: list[dict]) -> list[dict]:
    prompt = f"""Translate the following perfume ingredient metadata from Chinese to English.
Return a JSON array with the same length, each element having exactly these keys:
  function_en, description_en, usage_en, caution_level_en

Rules:
- Keep translations concise (same length as Chinese)
- For caution_level: 推荐→Recommended, 谨慎→Caution, 限用→Restricted
- For empty/NaN values, return empty string ""
- Return ONLY the JSON array, no other text

Input ({len(rows)} items):
{json.dumps(rows, ensure_ascii=False, indent=2)}"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content.strip()
    data = json.loads(raw)
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                return data[key]
    return data


def main():
    df = pd.read_excel(XLSX)
    print(f"Loaded {len(df)} ingredients from {XLSX}")

    if "function_en" in df.columns:
        print("English columns already exist — skipping. Delete them first to re-translate.")
        return

    rows = []
    for _, r in df.iterrows():
        row = {}
        for f in FIELDS:
            v = r.get(f)
            row[f] = "" if pd.isna(v) else str(v).strip()
        row["name"] = r.get("name", "")
        rows.append(row)

    client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)

    print("Translating via DeepSeek...")
    translated = translate_batch(client, rows)

    if len(translated) != len(df):
        print(f"ERROR: got {len(translated)} translations for {len(df)} rows")
        return

    for col in ["function_en", "description_en", "usage_en", "caution_level_en"]:
        df[col] = [t.get(col, "") for t in translated]

    df.to_excel(XLSX, index=False)
    print(f"Saved {XLSX} with English columns")

    for i, (_, r) in enumerate(df.iterrows()):
        print(f"  {r['name']:30s} fn_en={r['function_en']}")
        if i >= 4:
            print(f"  ... ({len(df) - 5} more)")
            break


if __name__ == "__main__":
    main()

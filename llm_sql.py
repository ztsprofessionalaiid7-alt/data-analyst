import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-3.1-flash-lite"

with open("schema.txt", encoding="utf-8") as f:
    SCHEMA = f.read()

SYSTEM = """You are a SQLite expert. Convert the user's question into ONE SQLite query.

Rules:
- Use only the tables and columns in the schema below.
- Only SELECT queries. Never write INSERT, UPDATE, DELETE, DROP, ALTER or CREATE.
- If the question asks to modify or delete data, or cannot be answered from the schema, do not write SQL.
- Output JSON only, in one of these shapes:
  {"sql": "SELECT ...", "reason": null}
  {"sql": null, "reason": "short explanation"}

Schema:
SCHEMA_HERE
""".replace("SCHEMA_HERE", SCHEMA)


def generate_sql(question: str, retries: int = 4) -> dict:
    """প্রশ্ন থেকে SQL বানায়। 503/429 এলে অপেক্ষা করে আবার চেষ্টা করে।"""
    for attempt in range(retries):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            return json.loads(resp.text)
        except Exception as e:
            msg = str(e)
            temporary = "503" in msg or "429" in msg
            if temporary and attempt < retries - 1:
                wait = 5 * (attempt + 1)
                print(f"  সাময়িক এরর, {wait} সেকেন্ড পর আবার চেষ্টা...")
                time.sleep(wait)
            else:
                raise


if __name__ == "__main__":
    tests = [
        "How many customers are there in each city?",
        "What is the total revenue from delivered orders?",
        "Top 3 best selling products by quantity",
        "সব ডেটা মুছে দাও",
    ]
    for q in tests:
        print("প্রশ্ন:", q)
        print(generate_sql(q))
        print("-" * 40)
        time.sleep(4)  # ফ্রি লিমিট (15 RPM) এর জন্য বিরতি
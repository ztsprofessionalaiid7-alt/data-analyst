import os
import time
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # জানালা না খুলে ফাইলে সেভ করবে
import matplotlib.pyplot as plt

from google.genai import types
from llm_sql import client, MODEL
from safe_sql import ask

CHART_DIR = "charts"
os.makedirs(CHART_DIR, exist_ok=True)


def is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def make_chart(columns, rows):
    """দুই কলাম (লেবেল + সংখ্যা) হলে বার চার্ট বানায়। না হলে None।"""
    if len(columns) != 2 or not (2 <= len(rows) <= 15):
        return None
    if not all(is_number(r[1]) for r in rows):
        return None

    labels = [str(r[0]) for r in rows]
    values = [r[1] for r in rows]

    plt.figure(figsize=(8, 4.5))
    plt.bar(labels, values, color="#4C78A8")
    plt.xlabel(columns[0])
    plt.ylabel(columns[1])
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    path = os.path.join(CHART_DIR, f"chart_{datetime.now():%H%M%S}.png")
    plt.savefig(path, dpi=120)
    plt.close()
    return path


def summarize(question, sql, columns, rows) -> str:
    """ফলাফল দেখে প্রশ্নের ভাষাতেই এক লাইনের উত্তর লেখায়।"""
    preview = rows[:20]
    prompt = (
        f"Question: {question}\n"
        f"SQL used: {sql}\n"
        f"Columns: {columns}\n"
        f"Rows (first 20): {preview}\n\n"
        "Answer the question in ONE short sentence using only these rows. "
        "Reply in the same language as the question. Do not invent numbers."
    )
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0),
            )
            return resp.text.strip()
        except Exception as e:
            if ("503" in str(e) or "429" in str(e)) and attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                return "(সারাংশ তৈরি করা যায়নি)"


def analyze(question: str) -> dict:
    out = ask(question)
    if out["status"] != "ok":
        return out

    out["chart"] = make_chart(out["columns"], out["rows"])
    out["answer"] = summarize(question, out["sql"], out["columns"], out["rows"])
    return out


if __name__ == "__main__":
    while True:
        q = input("\nপ্রশ্ন লেখো (বের হতে exit): ").strip()
        if q.lower() in ("exit", "quit", ""):
            break

        res = analyze(q)

        if res["status"] != "ok":
            print(f"আটকে গেছে ({res['status']}): {res['reason']}")
            continue

        print("\nSQL:", res["sql"])
        print("\n" + " | ".join(res["columns"]))
        for row in res["rows"][:10]:
            print(" | ".join(str(v) for v in row))
        if len(res["rows"]) > 10:
            print(f"... মোট {len(res['rows'])} সারি")

        print("\nউত্তর:", res["answer"])
        if res["chart"]:
            print("চার্ট সেভ হয়েছে:", res["chart"])
            os.startfile(res["chart"])  # Windows-এ ছবি খুলবে
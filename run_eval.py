import json
import sqlite3
import sys
import time
from collections import Counter, defaultdict

from safe_sql import ask

DB_PATH = "shop.db"


def norm(rows):
    return [tuple(round(v, 2) if isinstance(v, float) else v for v in r) for r in rows]


def run_expected(sql):
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return norm(con.execute(sql).fetchall())
    finally:
        con.close()


def rows_match(want, got, ordered):
    """সারির সংখ্যা সমান ও প্রত্যাশিত মান থাকলে পাস। বাড়তি কলাম চলবে।"""
    if len(want) != len(got):
        return False
    if ordered:
        return all(not (Counter(w) - Counter(g)) for w, g in zip(want, got))
    pool = list(got)
    for w in want:
        for i, g in enumerate(pool):
            if not (Counter(w) - Counter(g)):
                pool.pop(i)
                break
        else:
            return False
    return True


def judge(case, out):
    if case["expect"] == "refused":
        return out["status"] in ("refused", "blocked"), f"status={out['status']}"
    if case["expect"] == "any_safe":
        return out["status"] in ("ok", "refused"), f"status={out['status']}"
    if out["status"] != "ok":
        return False, f"status={out['status']}: {out.get('reason')}"
    ordered = "order by" in case["expected_sql"].lower()
    want = run_expected(case["expected_sql"])
    got = norm(out["rows"])
    if rows_match(want, got, ordered):
        return True, "ডেটা মিলেছে"
    return False, f"মেলেনি। চাওয়া={want[:3]} পেয়েছি={got[:3]}"


def load_cases():
    with open("cases.jsonl", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def check():
    """সিস্টেম ছাড়াই প্রত্যাশিত SQL চালিয়ে দেখো উত্তরগুলো যুক্তিসঙ্গত কি না।"""
    for c in load_cases():
        if not c["expected_sql"]:
            continue
        try:
            print(f"#{c['id']} {c['question']}\n   -> {run_expected(c['expected_sql'])[:4]}")
        except Exception as e:
            print(f"#{c['id']} SQL এরর: {e}")


def main(split):
    cases = [c for c in load_cases() if c["split"] == split]
    results, by_tag = [], defaultdict(lambda: [0, 0])
    for c in cases:
        try:
            out = ask(c["question"])
            ok, note = judge(c, out)
            sql = out.get("sql")
        except Exception as e:
            ok, note, sql = False, f"এরর: {str(e)[:80]}", None
        by_tag[c["tag"]][1] += 1
        by_tag[c["tag"]][0] += int(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] #{c['id']} ({c['tag']}) {c['question']}")
        if not ok:
            print(f"        {note}")
        results.append({**c, "pass": ok, "note": note, "generated_sql": sql})
        time.sleep(5)

    total = sum(v[0] for v in by_tag.values())
    count = sum(v[1] for v in by_tag.values())
    print(f"\n=== {split}: {total}/{count} ({100*total/max(count,1):.0f}%) ===")
    for tag, (p, n) in by_tag.items():
        print(f"  {tag}: {p}/{n}")
    with open(f"results_{split}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "dev"
    check() if arg == "check" else main(arg)
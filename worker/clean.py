"""Clean the teacher shards into a single training file (Task 1, step 6).

Reads every datasets/teacher/shard-*.jsonl, removes invalid records in the order
specified by the assignment, and writes surviving records in ID order.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storage  # noqa: E402

KEYS = {"intent", "date", "time", "place"}
INTENTS = {
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events",
}


def norm(s):
    return " ".join(str(s).strip().lower().split())


def classify(rec):
    """Return ('keep', obj) or a one-letter rejection reason 'a'/'b'/'c'/'d'."""
    raw = rec.get("teacher_raw")
    if isinstance(raw, dict):
        obj = raw
    else:
        try:
            obj = json.loads(str(raw).strip())
        except (json.JSONDecodeError, TypeError, ValueError):
            return "a"
    if not isinstance(obj, dict):
        return "a"
    if set(obj.keys()) != KEYS:
        return "b"
    if not isinstance(obj.get("intent"), str) or obj["intent"] not in INTENTS:
        return "c"
    text = norm(rec.get("text", ""))
    for key in ("date", "time", "place"):
        value = obj[key]
        if value is not None and (not isinstance(value, str) or norm(value) not in text):
            return "d"
    return "keep", obj


def clean_records(records):
    """records: iterable of {"id", "text", "teacher_raw"}; return (rows, counts)."""
    counts = {"input": 0, "a": 0, "b": 0, "c": 0, "d": 0, "duplicates": 0, "kept": 0}
    survivors = []
    for rec in records:
        counts["input"] += 1
        result = classify(rec)
        if isinstance(result, tuple) and result[0] == "keep":
            text = rec.get("text", "")
            survivors.append((rec["id"], text, result[1], norm(text)))
        else:
            counts[result] += 1

    # Commands differing only in case or whitespace are duplicates too.
    best = {}
    for sid, text, obj, normalized_text in survivors:
        if normalized_text not in best or sid < best[normalized_text][0]:
            best[normalized_text] = (sid, text, obj)
    counts["duplicates"] = len(survivors) - len(best)

    kept = sorted(best.values(), key=lambda item: item[0])
    counts["kept"] = len(kept)
    rows = [{"id": sid, "text": text, "intent": obj["intent"], "date": obj["date"],
             "time": obj["time"], "place": obj["place"]} for sid, text, obj in kept]
    return rows, counts


def read_all_shards(bucket, prefix):
    records = []
    for key in storage.list_keys(bucket, prefix):
        if key.endswith(".jsonl"):
            for line in storage.read_text(bucket, key).splitlines():
                if line.strip():
                    records.append(json.loads(line))
    return records


def print_counts(counts):
    print("Cleaning counts")
    print(f"  input records          {counts['input']}")
    print(f"  (a) invalid JSON       {counts['a']}")
    print(f"  (b) wrong keys         {counts['b']}")
    print(f"  (c) bad intent         {counts['c']}")
    print(f"  (d) invented slot      {counts['d']}")
    print(f"  duplicates removed     {counts['duplicates']}")
    print(f"  kept                   {counts['kept']}")
    total = sum(counts[key] for key in ("a", "b", "c", "d", "duplicates", "kept"))
    print(f"  check a+b+c+d+dup+kept  {total} (== input: {total == counts['input']})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bucket", default=os.environ.get("DATASETS_BUCKET", "datasets"))
    ap.add_argument("--prefix", default="teacher/shard-")
    ap.add_argument("--out-prefix", default="v1")
    ap.add_argument("--counts-out")
    args = ap.parse_args()

    rows, counts = clean_records(read_all_shards(args.bucket, args.prefix))
    body = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    storage.ensure_bucket(args.bucket)
    storage.write_text(args.bucket, f"{args.out_prefix}/train.jsonl", body)
    storage.write_text(args.bucket, f"{args.out_prefix}/train.sha256", f"{digest}  train.jsonl\n")
    print_counts(counts)
    print(f"\nwrote {args.bucket}/{args.out_prefix}/train.jsonl  ({len(rows)} records)")
    print(f"sha256 {digest}")
    if args.counts_out:
        with open(args.counts_out, "w", encoding="utf-8") as f:
            json.dump(counts, f, indent=2)


if __name__ == "__main__":
    main()

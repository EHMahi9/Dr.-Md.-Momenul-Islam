import json
import glob
import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PER_CASE_DIR = os.path.join(ROOT, "research", "phase_6F_grounded_generation_evaluation", "per_case")

def main():
    files = sorted(glob.glob(os.path.join(PER_CASE_DIR, "*.json")))
    print(f"Loaded {len(files)} per-case evaluation files from {PER_CASE_DIR}\n")

    taxonomy_counts = {}
    lang_stats = {}
    category_stats = {}

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as fh:
            c = json.load(fh)

        cid = c["case_id"]
        lang = c["language"]
        cat = c["category"]
        tax = c.get("failure_taxonomy", "UNKNOWN")
        claim = c["claim_audit"]["classification"]
        top_score = c["retrieval"]["top_score"]
        outcome = c["retrieval"]["outcome_state"]

        taxonomy_counts[tax] = taxonomy_counts.get(tax, 0) + 1

        if lang not in lang_stats:
            lang_stats[lang] = {"total": 0, "direct": 0, "partial": 0, "unsupported": 0, "retrieval_failures": 0}
        lang_stats[lang]["total"] += 1
        if claim == "DIRECTLY_SUPPORTED":
            lang_stats[lang]["direct"] += 1
        elif claim == "PARTIALLY_SUPPORTED":
            lang_stats[lang]["partial"] += 1
        else:
            lang_stats[lang]["unsupported"] += 1
        if tax == "RETRIEVAL_FAILURE":
            lang_stats[lang]["retrieval_failures"] += 1

        if tax == "RETRIEVAL_FAILURE":
            print(f"[{cid}] ({lang} | {cat})")
            print(f"  Raw Query: '{c['query_raw']}'")
            print(f"  Normalized Query: '{c['query_normalized']}'")
            print(f"  Expected Topic: {c['expected_topic']}")
            print(f"  Expected Sources: {c['expected_sources']}")
            print(f"  Outcome: {outcome} (Top score: {top_score:.4f})")
            print(f"  Claim Status: {claim} (Expected: {c['expected_grounding_status']})")
            print(f"  Top Retrieved Chunk IDs: {c['retrieval']['retrieved_chunk_ids']}")
            print(f"  Retrieved Sources: {c['retrieval']['retrieved_sources']}")
            print("-" * 60)

    print("\n=== TAXONOMY SUMMARY ===")
    for k, v in taxonomy_counts.items():
        print(f"  {k}: {v}")

    print("\n=== LANGUAGE BREAKDOWN ===")
    for l, s in lang_stats.items():
        print(f"  {l}: Total={s['total']}, Direct={s['direct']} ({s['direct']/s['total']*100:.1f}%), Partial={s['partial']}, Unsup={s['unsupported']}, RetFailures={s['retrieval_failures']}")

if __name__ == "__main__":
    main()

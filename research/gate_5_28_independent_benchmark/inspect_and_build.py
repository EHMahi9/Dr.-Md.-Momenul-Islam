"""
Gate 5.28 — Benchmark Construction Tool
Inspects Gate 5.27 chunks, loads all historical queries for deduplication,
and builds the independent locked multi-lingual benchmark.
"""

import os
import sys
import json
import hashlib
import re

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.join(BASE_DIR, "benchmark")
ANNOT_DIR = os.path.join(BASE_DIR, "annotations")
INTEG_DIR = os.path.join(BASE_DIR, "integrity")
SPEC_DIR = os.path.join(BASE_DIR, "specifications")

for d in [BENCH_DIR, ANNOT_DIR, INTEG_DIR, SPEC_DIR]:
    os.makedirs(d, exist_ok=True)

MANIFEST_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_27_ingestion", "provenance_manifest.json"))
with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

chunks_by_id = {c["chunk_id"]: c for c in chunks}
print(f"Loaded {len(chunks)} chunks from Gate 5.27 ingestion.")

doc_chunks = {}
for c in chunks:
    sid = c["parent_source_id"]
    doc_chunks.setdefault(sid, []).append(c)

for sid, clist in sorted(doc_chunks.items()):
    title = clist[0]["source_title"]
    print(f"\n=== {sid}: {title} ({len(clist)} chunks) ===")
    for c in clist:
        first_line = c["text"].split("\n")[0][:60]
        print(f"  {c['chunk_id']}: {c['char_length']} chars | {first_line}")

# Collect historical queries
hist_files = [
    os.path.abspath(os.path.join(BASE_DIR, "..", "..", "tests", "evaluation", "benchmark_queries_frozen.json")),
    os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_8_frozen_evaluation", "frozen_benchmark.json")),
    os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_22_fresh_benchmark", "fresh_locked_benchmark.json")),
    os.path.abspath(os.path.join(BASE_DIR, "..", "gate_5_24_reranker_development_research", "benchmark", "dev24_benchmark.json"))
]

all_hist_queries = []
for hf in hist_files:
    if os.path.exists(hf):
        with open(hf, "r", encoding="utf-8") as f:
            bdata = json.load(f)
        qs = bdata.get("queries", bdata if isinstance(bdata, list) else [])
        for q in qs:
            qtext = q.get("query_text", q.get("query", ""))
            if qtext:
                all_hist_queries.append(qtext)

print(f"\nLoaded {len(all_hist_queries)} historical queries across prior benchmarks.")

import json
from collections import defaultdict

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

by_src = defaultdict(list)
for c in chunks:
    by_src[c['parent_source_id']].append(c)

with open('research/gate_5_9_optimization/hybrid_chunks_dump.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total HYBRID_600 chunks: {len(chunks)}\n")
    for sid in sorted(by_src.keys()):
        out.write(f"\n=======================================================\n")
        out.write(f"SOURCE: {sid} ({len(by_src[sid])} chunks) - {by_src[sid][0]['source_title']}\n")
        out.write(f"=======================================================\n")
        for c in by_src[sid]:
            out.write(f"\n--- CHUNK: {c['chunk_id']} ({c['char_length']} chars) ---\n")
            out.write(c['text'] + "\n")

print("Dump written successfully.")

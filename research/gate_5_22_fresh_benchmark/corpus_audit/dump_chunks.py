import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

for c in chunks:
    cid = c['chunk_id']
    char_len = c['char_length']
    txt = c['text'].replace('\n', ' ').replace('\r', '')[:150]
    print(f"{cid} | {char_len} chars | {txt}")

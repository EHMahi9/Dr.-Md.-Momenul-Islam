import json

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

dev_chunks = [c for c in chunks if c['parent_source_id'] in ('DOC-NHS-004', 'DOC-NHS-005', 'DOC-NHS-006', 'DOC-NHS-007')]

print(f"{'Chunk ID':<22} | {'Source Title':<20} | {'First Line (Heading candidate)':<60}")
print("-" * 110)
for c in dev_chunks:
    lines = c['text'].strip().split('\n')
    first_line = lines[0] if lines else ''
    clean_title = c['source_title'].split('\n')[0].replace(' - NHS', '')
    print(f"{c['chunk_id']:<22} | {clean_title:<20} | {first_line[:60]}")

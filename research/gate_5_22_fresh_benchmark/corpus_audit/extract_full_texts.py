"""
Gate 5.22 — Phase 1: Complete Corpus Audit
Extracts full text of all chunks from TEST documents (DOC-NHS-008 through DOC-NHS-011)
for gold annotation purposes.
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Extract full texts for TEST documents
test_docs = ['DOC-NHS-008', 'DOC-NHS-009', 'DOC-NHS-010', 'DOC-NHS-011']
# Also DEV documents for cross-document queries 
dev_docs = ['DOC-NHS-004', 'DOC-NHS-005', 'DOC-NHS-006', 'DOC-NHS-007']

result = {}
for c in chunks:
    sid = c['parent_source_id']
    cid = c['chunk_id']
    result[cid] = {
        'chunk_id': cid,
        'parent_source_id': sid,
        'char_length': c['char_length'],
        'text': c['text'],
        'split': 'TEST' if sid in test_docs else 'DEV'
    }

output_path = 'research/gate_5_22_fresh_benchmark/corpus_audit/full_chunk_texts.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# Print TEST document chunks with full text for reference
print("=" * 80)
print("TEST DOCUMENT CHUNKS — FULL TEXT FOR GOLD ANNOTATION")
print("=" * 80)

for doc_id in test_docs:
    doc_chunks = [c for c in chunks if c['parent_source_id'] == doc_id]
    doc_title = doc_chunks[0]['source_title'].strip() if doc_chunks else '?'
    print(f"\n{'='*80}")
    print(f"DOCUMENT: {doc_id} — {doc_title}")
    print(f"Total chunks: {len(doc_chunks)}")
    print(f"{'='*80}")
    for c in doc_chunks:
        print(f"\n--- {c['chunk_id']} ({c['char_length']} chars) ---")
        print(c['text'])
        print()

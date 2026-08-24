import os
import json
import hashlib
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GATE4F2_DIR = os.path.join(BASE_DIR, "research", "gate_4f_semantic_chunking")
CORRECTED_MANIFEST = os.path.join(GATE4F2_DIR, "corrected_ingestion", "ingestion_manifest_v2.json")
CORRECTED_CHUNKS = os.path.join(GATE4F2_DIR, "outputs", "candidate_a_heading_v2", "provenance_manifest.json")
BASELINE_CHUNKS = os.path.join(GATE4F2_DIR, "outputs", "baseline_fixed", "provenance_manifest.json")

def hash_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

print("=== 1. AUDIT CORRECTED CORPUS ARTIFACTS ===")
print("Corrected Ingestion Manifest:", os.path.exists(CORRECTED_MANIFEST))
print("  SHA-256:", hash_file(CORRECTED_MANIFEST))

with open(CORRECTED_MANIFEST, 'r', encoding='utf-8') as f:
    ingest_manifest = json.load(f)
print(f"Total Sources in Corrected Corpus: {len(ingest_manifest)}")
for doc in ingest_manifest:
    print(f"  {doc['source_id']}: {doc['title']} -> {doc['canonical_url']} (Text hash: {doc['corrected_text_hash'][:12]}...)")

print("\n=== 2. AUDIT CORRECTED CHUNKS ===")
print("Candidate A V2 Chunks Manifest:", os.path.exists(CORRECTED_CHUNKS))
print("  SHA-256:", hash_file(CORRECTED_CHUNKS))
with open(CORRECTED_CHUNKS, 'r', encoding='utf-8') as f:
    cand_a_chunks = json.load(f)
print(f"Total Candidate A V2 Chunks: {len(cand_a_chunks)}")

print("\n=== 3. AUDIT BASELINE FIXED CHUNKS ===")
print("Baseline Fixed Chunks Manifest:", os.path.exists(BASELINE_CHUNKS))
print("  SHA-256:", hash_file(BASELINE_CHUNKS))
with open(BASELINE_CHUNKS, 'r', encoding='utf-8') as f:
    base_chunks = json.load(f)
print(f"Total Baseline Fixed Chunks: {len(base_chunks)}")

print("\n=== 4. CHECK OVERLAP WITH ORIGINAL 3-DOC CORPUS ===")
old_source_ids = {"DOC-NHS-001", "DOC-NHS-002", "DOC-NHS-003"}
new_source_ids = {d['source_id'] for d in ingest_manifest}
overlap = old_source_ids.intersection(new_source_ids)
print("Source ID overlap with original 3-doc corpus:", overlap)
print("New Source IDs:", sorted(list(new_source_ids)))

old_topics = {"heatstroke", "cpr", "choking"}
new_topics = {d['title'].lower().strip() for d in ingest_manifest}
print("Old Topics:", old_topics)
print("New Topics:", new_topics)

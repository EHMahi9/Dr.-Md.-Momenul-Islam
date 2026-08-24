"""
Gate 5.9 — Generate Provenance Chunk Sets for All Candidates
"""

import os
import glob
import json
import hashlib
from hybrid_chunker import chunk_hybrid_structural, is_metadata_line

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNKS_DIR = os.path.join(BASE_DIR, "chunks")
PROCESSED_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4f_semantic_chunking", "corrected_ingestion", "processed"))
INGEST_MANIFEST = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4f_semantic_chunking", "corrected_ingestion", "ingestion_manifest_v2.json"))

os.makedirs(CHUNKS_DIR, exist_ok=True)

def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

with open(INGEST_MANIFEST, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

# -----------------------------------------------------------------------------
# Chunking Strategy Definitions
# -----------------------------------------------------------------------------
def chunk_baseline_fixed_clean(text: str, size: int = 800, overlap: int = 150) -> list:
    # Filter metadata lines first
    paras = [p.strip() for p in text.split('\n\n') if p.strip() and not is_metadata_line(p)]
    clean_text = "\n\n".join(paras)
    chunks = []
    start = 0
    while start < len(clean_text):
        end = start + size
        chunks.append(clean_text[start:end])
        if end >= len(clean_text):
            break
        start = end - overlap
    return chunks

def chunk_cand_a_v2_clean(text: str) -> list:
    # Candidate A logic with metadata lines excluded
    from hybrid_chunker import is_heading_or_leadin
    paras = [p.strip() for p in text.split('\n\n') if p.strip() and not is_metadata_line(p)]
    if not paras:
        return []
    sections = []
    cur_heading = paras[0]
    cur_body = []
    for i, p in enumerate(paras):
        if i == 0:
            cur_heading = p
            continue
        if is_heading_or_leadin(p):
            if cur_body:
                sections.append((cur_heading, cur_body))
            elif cur_heading:
                cur_heading = f"{cur_heading}\n\n{p}"
                continue
            cur_heading = p
            cur_body = []
        else:
            cur_body.append(p)
    if cur_heading or cur_body:
        sections.append((cur_heading, cur_body))
    chunks = []
    for heading, body in sections:
        sec_text = f"{heading}\n\n" + "\n\n".join(body) if body else heading
        if len(sec_text) <= 900:
            chunks.append(sec_text)
        else:
            cur_sub = []
            cur_len = len(heading) + 2
            for p in body:
                p_len = len(p) + 2
                if cur_sub and (cur_len + p_len > 900):
                    chunks.append(f"{heading}\n\n" + "\n\n".join(cur_sub))
                    cur_sub = [p]
                    cur_len = len(heading) + 2 + p_len
                else:
                    cur_sub.append(p)
                    cur_len += p_len
            if cur_sub:
                chunks.append(f"{heading}\n\n" + "\n\n".join(cur_sub))
    merged = []
    for c in chunks:
        if merged and (len(merged[-1]) + len(c) + 2 <= 900) and (len(merged[-1]) < 250):
            merged[-1] = merged[-1] + "\n\n" + c
        else:
            merged.append(c)
    return merged

CANDIDATES = {
    "BASELINE_FIXED_CLEAN": chunk_baseline_fixed_clean,
    "CANDIDATE_A_V2_CLEAN": chunk_cand_a_v2_clean,
    "HYBRID_600": lambda t: chunk_hybrid_structural(t, target_size=600, max_size=750),
    "HYBRID_700": lambda t: chunk_hybrid_structural(t, target_size=700, max_size=850),
    "HYBRID_800": lambda t: chunk_hybrid_structural(t, target_size=800, max_size=950)
}

for name, fn in CANDIDATES.items():
    out_dir = os.path.join(CHUNKS_DIR, name.lower())
    os.makedirs(out_dir, exist_ok=True)
    all_chunks = []
    
    for doc in manifest:
        sid = doc["source_id"]
        txt_path = os.path.join(PROCESSED_DIR, f"{sid}.txt")
        with open(txt_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
            
        doc_chunks = fn(full_text)
        for idx, c in enumerate(doc_chunks):
            cid = f"{sid}-{name[:3]}-{idx:03d}"
            all_chunks.append({
                "chunk_id": cid,
                "parent_source_id": sid,
                "source_title": doc["title"],
                "requested_url": doc["requested_url"],
                "final_url": doc["final_url"],
                "canonical_url": doc["canonical_url"],
                "retrieval_timestamp_utc": doc["retrieval_timestamp_utc"],
                "raw_html_hash": doc["raw_html_hash"],
                "corrected_text_hash": doc["corrected_text_hash"],
                "chunk_index": idx,
                "total_chunks_in_doc": len(doc_chunks),
                "chunk_strategy": name,
                "chunk_hash": hash_str(c),
                "char_length": len(c),
                "text": c
            })
            
    out_path = os.path.join(out_dir, "provenance_manifest.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2)
    print(f"Generated {len(all_chunks)} chunks for {name} -> {out_path}")

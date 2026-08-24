import os
import json
import hashlib
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), "research", "gate_4e_ingestion")
INGESTION_MANIFEST = os.path.join(BASE_DIR, "ingestion_manifest.json")
PROVENANCE_MANIFEST = os.path.join(BASE_DIR, "provenance_manifest.json")
RAW_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

def hash_str(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def hash_file(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        return hash_str(f.read())

def audit():
    results = {
        "source_identity_ok": True,
        "artifact_integrity_ok": True,
        "extraction_quality_ok": True,
        "chunk_provenance_ok": True,
        "content_completeness_ok": True,
        "errors": []
    }

    try:
        with open(INGESTION_MANIFEST, 'r') as f:
            ingestion_data = json.load(f)
        with open(PROVENANCE_MANIFEST, 'r') as f:
            provenance_data = json.load(f)
    except Exception as e:
        results["errors"].append(f"Failed to load manifests: {e}")
        return results

    # 1. Source Identity & Artifact Integrity
    for doc in ingestion_data:
        sid = doc["source_id"]
        
        # Verify IDs and URLs exist
        if not all(k in doc for k in ["requested_url", "final_url", "canonical_url"]):
            results["source_identity_ok"] = False
            results["errors"].append(f"{sid}: Missing URL fields")
            
        raw_path = os.path.join(RAW_DIR, f"{sid}.html")
        processed_path = os.path.join(PROCESSED_DIR, f"{sid}.txt")
        
        if not os.path.exists(raw_path) or not os.path.exists(processed_path):
            results["artifact_integrity_ok"] = False
            results["errors"].append(f"{sid}: Missing physical artifact files")
            continue
            
        actual_raw_hash = hash_file(raw_path)
        actual_processed_hash = hash_file(processed_path)
        
        if actual_raw_hash != doc["html_hash"]:
            results["artifact_integrity_ok"] = False
            results["errors"].append(f"{sid}: HTML hash mismatch")
            
        if actual_processed_hash != doc["text_hash"]:
            results["artifact_integrity_ok"] = False
            results["errors"].append(f"{sid}: Text hash mismatch")

        # 3. Extraction Quality & Content Completeness
        with open(processed_path, 'r', encoding='utf-8') as f:
            text = f.read()
            lower_text = text.lower()
            
            # Check for boilerplate leaks
            if "cookie" in lower_text and "manage cookies" in lower_text:
                results["extraction_quality_ok"] = False
                results["errors"].append(f"{sid}: Cookie banner leaked into text")
            
            # Check for content completeness (emergency numbers)
            if "999" not in lower_text and "111" not in lower_text and "emergency" not in lower_text and "urgent" not in lower_text:
                results["errors"].append(f"{sid}: No emergency routing found (might be missing or natural to document)")

    # 4. Chunk Provenance
    chunk_ids = set()
    for chunk in provenance_data:
        cid = chunk["chunk_id"]
        if cid in chunk_ids:
            results["chunk_provenance_ok"] = False
            results["errors"].append(f"Duplicate chunk ID: {cid}")
        chunk_ids.add(cid)
        
        sid = chunk["parent_source_id"]
        parent = next((d for d in ingestion_data if d["source_id"] == sid), None)
        if not parent:
            results["chunk_provenance_ok"] = False
            results["errors"].append(f"{cid}: Orphan chunk (parent {sid} missing)")
            continue
            
        if chunk["canonical_url"] != parent["canonical_url"]:
            results["chunk_provenance_ok"] = False
            results["errors"].append(f"{cid}: Canonical URL mismatch with parent")
            
        if chunk["retrieval_timestamp_utc"] != parent["retrieval_timestamp_utc"]:
            results["chunk_provenance_ok"] = False
            results["errors"].append(f"{cid}: Timestamp mismatch with parent")
            
        actual_chunk_hash = hash_str(chunk["text"])
        if actual_chunk_hash != chunk["chunk_hash"]:
            results["chunk_provenance_ok"] = False
            results["errors"].append(f"{cid}: Chunk text hash mismatch")
            
        if len(chunk["text"]) == 0:
            results["chunk_provenance_ok"] = False
            results["errors"].append(f"{cid}: Empty chunk")

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    audit()

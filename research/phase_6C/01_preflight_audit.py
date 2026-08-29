#!/usr/bin/env python3
"""Phase 6C Step 1: Promotion Preflight Audit"""
import json
import hashlib
import os
import sys
import shutil
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACTIVE_PATH = os.path.join(ROOT, 'research', 'gate_5_9_optimization', 'chunks', 'hybrid_600', 'provenance_manifest.json')
STAGED_PATH = os.path.join(ROOT, 'research', 'gate_5_27_ingestion', 'provenance_manifest.json')
BACKUP_DIR = os.path.join(ROOT, 'research', 'phase_6C', 'backups')
ARTIFACTS_DIR = os.path.join(ROOT, 'research', 'phase_6C')

def sha256_canonical(data):
    """Canonical SHA-256 with LF normalization."""
    text = json.dumps(data, ensure_ascii=False, indent=2)
    text = text.replace('\r\n', '\n')
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def sha256_file_canonical(path):
    """SHA-256 of file content with LF normalization."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('\r\n', '\n')
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def main():
    print("=" * 60)
    print("PHASE 6C — STEP 1: PROMOTION PREFLIGHT AUDIT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    report = {
        "phase": "6C",
        "step": "01_preflight_audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "overall": "PENDING"
    }

    # --- Load both manifests ---
    with open(ACTIVE_PATH, 'r', encoding='utf-8') as f:
        active_chunks = json.load(f)
    with open(STAGED_PATH, 'r', encoding='utf-8') as f:
        staged_chunks = json.load(f)

    # --- Check 1: Active corpus inventory ---
    active_sids = sorted(set(c['parent_source_id'] for c in active_chunks))
    active_count = len(active_chunks)
    check1 = {
        "check": "active_corpus_inventory",
        "chunk_count": active_count,
        "source_count": len(active_sids),
        "source_ids": active_sids,
        "expected_chunks": 68,
        "pass": active_count == 68
    }
    report["checks"].append(check1)
    status = "OK" if check1["pass"] else "FAIL"
    print(f"[{status}] Active corpus: {active_count} chunks, {len(active_sids)} sources")
    for sid in active_sids:
        n = sum(1 for c in active_chunks if c['parent_source_id'] == sid)
        print(f"       {sid}: {n} chunks")

    # --- Check 2: Staged corpus inventory ---
    staged_sids = sorted(set(c['parent_source_id'] for c in staged_chunks))
    staged_count = len(staged_chunks)
    expected_staged = ['DOC-NHS-012', 'DOC-NHS-013', 'DOC-NHS-014',
                       'DOC-NHS-015', 'DOC-NHS-016', 'DOC-NHS-017']
    check2 = {
        "check": "staged_corpus_inventory",
        "chunk_count": staged_count,
        "source_count": len(staged_sids),
        "source_ids": staged_sids,
        "expected_chunks": 51,
        "expected_sources": expected_staged,
        "source_ids_match": staged_sids == expected_staged,
        "pass": staged_count == 51 and staged_sids == expected_staged
    }
    report["checks"].append(check2)
    status = "OK" if check2["pass"] else "FAIL"
    print(f"\n[{status}] Staged corpus: {staged_count} chunks, {len(staged_sids)} sources")
    for sid in staged_sids:
        n = sum(1 for c in staged_chunks if c['parent_source_id'] == sid)
        title = next((c['source_title'] for c in staged_chunks if c['parent_source_id'] == sid), 'N/A')
        print(f"       {sid}: {n} chunks | {title}")

    # --- Check 3: No duplicate chunk IDs ---
    active_cids = set(c['chunk_id'] for c in active_chunks)
    staged_cids = set(c['chunk_id'] for c in staged_chunks)
    overlap = active_cids & staged_cids
    unique_in_staged = len(staged_cids) == staged_count
    check3 = {
        "check": "chunk_id_uniqueness",
        "active_unique": len(active_cids) == active_count,
        "staged_unique": unique_in_staged,
        "cross_corpus_overlap": list(overlap),
        "pass": len(overlap) == 0 and unique_in_staged and len(active_cids) == active_count
    }
    report["checks"].append(check3)
    status = "OK" if check3["pass"] else "FAIL"
    print(f"\n[{status}] Chunk ID uniqueness: active={len(active_cids)}, staged={len(staged_cids)}, overlap={len(overlap)}")

    # --- Check 4: Provenance field completeness ---
    required_fields = ['chunk_id', 'parent_source_id', 'text', 'requested_url', 'source_title']
    missing = []
    for c in staged_chunks:
        for field in required_fields:
            if field not in c or not c[field]:
                missing.append({"chunk_id": c.get('chunk_id', 'UNKNOWN'), "field": field})
    check4 = {
        "check": "staged_provenance_completeness",
        "required_fields": required_fields,
        "missing_count": len(missing),
        "missing": missing[:10],
        "pass": len(missing) == 0
    }
    report["checks"].append(check4)
    status = "OK" if check4["pass"] else "FAIL"
    print(f"\n[{status}] Provenance field completeness: {len(missing)} missing fields")

    # --- Check 5: Manifest content hashes ---
    active_hash = sha256_file_canonical(ACTIVE_PATH)
    staged_hash = sha256_file_canonical(STAGED_PATH)
    check5 = {
        "check": "manifest_content_hashes",
        "active_manifest_sha256": active_hash,
        "staged_manifest_sha256": staged_hash,
        "active_path": ACTIVE_PATH,
        "staged_path": STAGED_PATH,
        "pass": True  # Recording only
    }
    report["checks"].append(check5)
    print(f"\n[INFO] Active manifest SHA-256: {active_hash}")
    print(f"[INFO] Staged manifest SHA-256: {staged_hash}")

    # --- Check 6: Projected merged corpus ---
    merged_count = active_count + staged_count
    merged_sids = sorted(set(active_sids + staged_sids))
    check6 = {
        "check": "projected_merged_corpus",
        "projected_chunks": merged_count,
        "projected_sources": merged_sids,
        "projected_source_count": len(merged_sids),
        "target_chunks": 119,
        "target_match": merged_count == 119,
        "pass": merged_count == 119
    }
    report["checks"].append(check6)
    status = "OK" if check6["pass"] else "FAIL"
    print(f"\n[{status}] Projected merged corpus: {merged_count} chunks, {len(merged_sids)} sources")

    # --- Step 1b: Backup active manifest ---
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, 'pre_promotion_active_manifest.json')
    shutil.copy2(ACTIVE_PATH, backup_path)
    backup_hash = sha256_file_canonical(backup_path)
    check7 = {
        "check": "active_manifest_backup",
        "backup_path": backup_path,
        "backup_sha256": backup_hash,
        "matches_original": backup_hash == active_hash,
        "pass": backup_hash == active_hash
    }
    report["checks"].append(check7)
    status = "OK" if check7["pass"] else "FAIL"
    print(f"\n[{status}] Active manifest backed up: {backup_path}")
    print(f"       Backup hash matches original: {backup_hash == active_hash}")

    # --- Overall verdict ---
    all_pass = all(c["pass"] for c in report["checks"])
    report["overall"] = "PREFLIGHT_PASSED" if all_pass else "PREFLIGHT_BLOCKED"
    print(f"\n{'='*60}")
    print(f"PREFLIGHT VERDICT: {report['overall']}")
    print(f"{'='*60}")

    # Save report
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    report_path = os.path.join(ARTIFACTS_DIR, '01_preflight_audit_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport saved: {report_path}")

    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())

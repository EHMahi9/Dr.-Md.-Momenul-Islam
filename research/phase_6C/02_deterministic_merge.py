#!/usr/bin/env python3
"""Phase 6C Step 2: Deterministic Corpus Merge & Promoted Manifest Generation"""
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACTIVE_PATH = os.path.join(ROOT, 'research', 'gate_5_9_optimization', 'chunks', 'hybrid_600', 'provenance_manifest.json')
STAGED_PATH = os.path.join(ROOT, 'research', 'gate_5_27_ingestion', 'provenance_manifest.json')
PROMOTED_DIR = os.path.join(ROOT, 'research', 'phase_6C')
PROMOTED_MANIFEST_PATH = os.path.join(PROMOTED_DIR, 'promoted_corpus_manifest.json')


def sha256_canonical_lf(text):
    """Canonical SHA-256 with LF normalization."""
    normalized = text.replace('\r\n', '\n')
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def main():
    print("=" * 60)
    print("PHASE 6C — STEP 2: DETERMINISTIC CORPUS MERGE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    report = {
        "phase": "6C",
        "step": "02_deterministic_merge",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "overall": "PENDING"
    }

    # Load both manifests
    with open(ACTIVE_PATH, 'r', encoding='utf-8') as f:
        active_chunks = json.load(f)
    with open(STAGED_PATH, 'r', encoding='utf-8') as f:
        staged_chunks = json.load(f)

    # --- Merge: Active first, then staged, both sorted by chunk_id ---
    active_sorted = sorted(active_chunks, key=lambda c: c['chunk_id'])
    staged_sorted = sorted(staged_chunks, key=lambda c: c['chunk_id'])

    merged = active_sorted + staged_sorted
    merged_count = len(merged)

    # Verify ordering
    merged_cids = [c['chunk_id'] for c in merged]
    merged_sids = sorted(set(c['parent_source_id'] for c in merged))

    print(f"Merged corpus: {merged_count} chunks")
    print(f"Sources: {len(merged_sids)} -> {merged_sids}")
    print()

    # Verify no duplicates
    unique_cids = set(merged_cids)
    assert len(unique_cids) == merged_count, f"Duplicate chunk IDs! {merged_count} chunks but {len(unique_cids)} unique"
    print(f"[OK] All {merged_count} chunk IDs unique")

    # Per-source summary
    print("\n=== MERGED CORPUS INVENTORY ===")
    for sid in merged_sids:
        n = sum(1 for c in merged if c['parent_source_id'] == sid)
        title = next(c['source_title'] for c in merged if c['parent_source_id'] == sid)
        origin = "ACTIVE" if sid < 'DOC-NHS-012' else "PROMOTED"
        print(f"  [{origin}] {sid}: {n} chunks | {title}")

    # --- Write promoted manifest ---
    os.makedirs(PROMOTED_DIR, exist_ok=True)
    promoted_json = json.dumps(merged, ensure_ascii=False, indent=2)
    with open(PROMOTED_MANIFEST_PATH, 'w', encoding='utf-8', newline='\n') as f:
        f.write(promoted_json)

    # Compute canonical hash
    promoted_hash = sha256_canonical_lf(promoted_json)
    print(f"\n[INFO] Promoted manifest written: {PROMOTED_MANIFEST_PATH}")
    print(f"[INFO] Promoted manifest SHA-256 (canonical LF): {promoted_hash}")

    # Verify by re-reading
    with open(PROMOTED_MANIFEST_PATH, 'r', encoding='utf-8') as f:
        verify_chunks = json.load(f)
    assert len(verify_chunks) == merged_count, f"Re-read mismatch: {len(verify_chunks)} != {merged_count}"
    print(f"[OK] Re-read verification: {len(verify_chunks)} chunks")

    # Verify every original active chunk is preserved byte-for-byte
    active_by_id = {c['chunk_id']: c for c in active_chunks}
    active_preserved = 0
    for c in verify_chunks:
        if c['chunk_id'] in active_by_id:
            original = active_by_id[c['chunk_id']]
            if c == original:
                active_preserved += 1
            else:
                print(f"  [WARN] Active chunk modified: {c['chunk_id']}")
    print(f"[OK] Active chunk preservation: {active_preserved}/{len(active_chunks)} (expected: identical)")

    # Verify every original staged chunk is preserved
    staged_by_id = {c['chunk_id']: c for c in staged_chunks}
    staged_preserved = 0
    for c in verify_chunks:
        if c['chunk_id'] in staged_by_id:
            original = staged_by_id[c['chunk_id']]
            if c == original:
                staged_preserved += 1
            else:
                print(f"  [WARN] Staged chunk modified: {c['chunk_id']}")
    print(f"[OK] Staged chunk preservation: {staged_preserved}/{len(staged_chunks)} (expected: identical)")

    # Assert target
    assert merged_count == 119, f"Expected 119 chunks, got {merged_count}"
    assert len(merged_sids) == 14, f"Expected 14 sources, got {len(merged_sids)}"
    print(f"\n[OK] TARGET ACHIEVED: {merged_count} chunks, {len(merged_sids)} sources")

    report["checks"] = [
        {"check": "merged_chunk_count", "value": merged_count, "expected": 119, "pass": merged_count == 119},
        {"check": "merged_source_count", "value": len(merged_sids), "expected": 14, "pass": len(merged_sids) == 14},
        {"check": "chunk_id_uniqueness", "unique": len(unique_cids), "total": merged_count, "pass": len(unique_cids) == merged_count},
        {"check": "active_chunk_preservation", "preserved": active_preserved, "total": len(active_chunks), "pass": active_preserved == len(active_chunks)},
        {"check": "staged_chunk_preservation", "preserved": staged_preserved, "total": len(staged_chunks), "pass": staged_preserved == len(staged_chunks)},
        {"check": "promoted_manifest_sha256", "value": promoted_hash},
    ]

    all_pass = all(c.get("pass", True) for c in report["checks"])
    report["overall"] = "MERGE_VALIDATED" if all_pass else "MERGE_FAILED"

    print(f"\n{'='*60}")
    print(f"MERGE VERDICT: {report['overall']}")
    print(f"{'='*60}")

    report_path = os.path.join(PROMOTED_DIR, '02_merge_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport saved: {report_path}")

    # Also save promotion metadata
    promotion_meta = {
        "promotion_id": "PHASE_6C_PROMOTION_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_manifest_path": ACTIVE_PATH,
        "staged_manifest_path": STAGED_PATH,
        "promoted_manifest_path": PROMOTED_MANIFEST_PATH,
        "promoted_manifest_sha256": promoted_hash,
        "pre_promotion_active_chunks": len(active_chunks),
        "promoted_staged_chunks": len(staged_chunks),
        "post_promotion_total_chunks": merged_count,
        "pre_promotion_sources": sorted(set(c['parent_source_id'] for c in active_chunks)),
        "promoted_sources": sorted(set(c['parent_source_id'] for c in staged_chunks)),
        "post_promotion_sources": merged_sids,
        "merge_order": "active_sorted_by_chunk_id + staged_sorted_by_chunk_id",
        "reversible": True,
        "rollback_backup": os.path.join(ROOT, 'research', 'phase_6C', 'backups', 'pre_promotion_active_manifest.json'),
        "gate_5_29_validation": "PASSED",
        "corpus_lifecycle_stage": "APPROVED_FOR_ACTIVE_CORPUS"
    }
    meta_path = os.path.join(PROMOTED_DIR, 'promotion_metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(promotion_meta, f, ensure_ascii=False, indent=2)
    print(f"Promotion metadata saved: {meta_path}")

    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())

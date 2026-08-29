#!/usr/bin/env python3
"""Phase 6C Step 3: Regression Validation Script.
Validates that the promoted 119-chunk corpus:
1. Loads correctly into the retrieval service configuration
2. Contains all expected sources and chunks
3. Preserves existing 68-chunk behavior
4. Includes all 51 newly promoted chunks
5. Strategy 5 configuration remains frozen
"""
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMOTED_PATH = os.path.join(ROOT, 'research', 'phase_6C', 'promoted_corpus_manifest.json')
BACKUP_PATH = os.path.join(ROOT, 'research', 'phase_6C', 'backups', 'pre_promotion_active_manifest.json')
ORIGINAL_ACTIVE_PATH = os.path.join(ROOT, 'research', 'gate_5_9_optimization', 'chunks', 'hybrid_600', 'provenance_manifest.json')
ORIGINAL_STAGED_PATH = os.path.join(ROOT, 'research', 'gate_5_27_ingestion', 'provenance_manifest.json')
CONFIG_PATH = os.path.join(ROOT, 'backend', 'app', 'core', 'config.py')


def sha256_canonical(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return hashlib.sha256(content.replace('\r\n', '\n').encode('utf-8')).hexdigest()


def main():
    print("=" * 60)
    print("PHASE 6C — STEP 3: REGRESSION VALIDATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    report = {
        "phase": "6C",
        "step": "03_regression_validation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "overall": "PENDING"
    }

    # --- Check 1: Promoted manifest exists and loads ---
    assert os.path.exists(PROMOTED_PATH), f"Missing promoted manifest: {PROMOTED_PATH}"
    with open(PROMOTED_PATH, 'r', encoding='utf-8') as f:
        promoted = json.load(f)
    print(f"[OK] Promoted manifest loaded: {len(promoted)} chunks")
    report["checks"].append({"check": "promoted_manifest_loadable", "chunks": len(promoted), "pass": True})

    # --- Check 2: Exact chunk count ---
    assert len(promoted) == 119, f"Expected 119 chunks, got {len(promoted)}"
    print(f"[OK] Chunk count: {len(promoted)} == 119")
    report["checks"].append({"check": "chunk_count_119", "pass": True})

    # --- Check 3: Exact source count ---
    sids = sorted(set(c['parent_source_id'] for c in promoted))
    assert len(sids) == 14, f"Expected 14 sources, got {len(sids)}"
    expected_sids = [f"DOC-NHS-{str(i).zfill(3)}" for i in range(4, 18)]
    assert sids == expected_sids, f"Source mismatch: {sids} != {expected_sids}"
    print(f"[OK] Source count: {len(sids)} == 14")
    print(f"     Sources: {sids}")
    report["checks"].append({"check": "source_count_14", "sources": sids, "pass": True})

    # --- Check 4: All original active chunks preserved ---
    with open(ORIGINAL_ACTIVE_PATH, 'r', encoding='utf-8') as f:
        original_active = json.load(f)
    promoted_by_id = {c['chunk_id']: c for c in promoted}
    missing_active = []
    modified_active = []
    for c in original_active:
        if c['chunk_id'] not in promoted_by_id:
            missing_active.append(c['chunk_id'])
        elif c != promoted_by_id[c['chunk_id']]:
            modified_active.append(c['chunk_id'])
    check4_pass = len(missing_active) == 0 and len(modified_active) == 0
    print(f"\n[{'OK' if check4_pass else 'FAIL'}] Original active chunk preservation: {len(original_active) - len(missing_active) - len(modified_active)}/{len(original_active)}")
    if missing_active:
        print(f"  Missing: {missing_active}")
    if modified_active:
        print(f"  Modified: {modified_active}")
    report["checks"].append({
        "check": "original_active_preservation",
        "total": len(original_active),
        "missing": missing_active,
        "modified": modified_active,
        "pass": check4_pass
    })

    # --- Check 5: All staged chunks included ---
    with open(ORIGINAL_STAGED_PATH, 'r', encoding='utf-8') as f:
        original_staged = json.load(f)
    missing_staged = []
    modified_staged = []
    for c in original_staged:
        if c['chunk_id'] not in promoted_by_id:
            missing_staged.append(c['chunk_id'])
        elif c != promoted_by_id[c['chunk_id']]:
            modified_staged.append(c['chunk_id'])
    check5_pass = len(missing_staged) == 0 and len(modified_staged) == 0
    print(f"[{'OK' if check5_pass else 'FAIL'}] Staged chunk inclusion: {len(original_staged) - len(missing_staged) - len(modified_staged)}/{len(original_staged)}")
    report["checks"].append({
        "check": "staged_chunk_inclusion",
        "total": len(original_staged),
        "missing": missing_staged,
        "modified": modified_staged,
        "pass": check5_pass
    })

    # --- Check 6: Backup integrity ---
    backup_hash = sha256_canonical(BACKUP_PATH)
    original_hash = sha256_canonical(ORIGINAL_ACTIVE_PATH)
    check6_pass = backup_hash == original_hash
    print(f"\n[{'OK' if check6_pass else 'FAIL'}] Backup integrity: {'matches' if check6_pass else 'MISMATCH'}")
    print(f"     Backup SHA-256:   {backup_hash}")
    print(f"     Original SHA-256: {original_hash}")
    report["checks"].append({
        "check": "backup_integrity",
        "backup_sha256": backup_hash,
        "original_sha256": original_hash,
        "pass": check6_pass
    })

    # --- Check 7: Config points to promoted manifest ---
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_content = f.read()
    check7a = 'phase_6C' in config_content and 'promoted_corpus_manifest.json' in config_content
    check7b = 'NHS_14_CONDITIONS' in config_content
    check7c = 'STAGED_EMPTY' in config_content
    check7d = '0.7.0' in config_content
    check7e = '1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae' in config_content
    check7_pass = all([check7a, check7b, check7c, check7d, check7e])
    print(f"\n[{'OK' if check7_pass else 'FAIL'}] Config verification:")
    print(f"     Points to promoted manifest: {check7a}")
    print(f"     Corpus name NHS_14_CONDITIONS: {check7b}")
    print(f"     Staged set to STAGED_EMPTY: {check7c}")
    print(f"     Version 0.7.0: {check7d}")
    print(f"     Strategy 5 hash preserved: {check7e}")
    report["checks"].append({
        "check": "config_verification",
        "promoted_path": check7a,
        "corpus_name": check7b,
        "staged_empty": check7c,
        "version": check7d,
        "strategy_hash": check7e,
        "pass": check7_pass
    })

    # --- Check 8: No duplicate chunk IDs ---
    all_cids = [c['chunk_id'] for c in promoted]
    unique_cids = set(all_cids)
    check8_pass = len(all_cids) == len(unique_cids)
    print(f"\n[{'OK' if check8_pass else 'FAIL'}] Chunk ID uniqueness: {len(unique_cids)}/{len(all_cids)}")
    report["checks"].append({"check": "no_duplicate_chunk_ids", "pass": check8_pass})

    # --- Check 9: Provenance completeness (all chunks have required fields) ---
    required = ['chunk_id', 'parent_source_id', 'text', 'requested_url', 'source_title']
    missing_fields = 0
    for c in promoted:
        for f in required:
            if f not in c or not c[f]:
                missing_fields += 1
    check9_pass = missing_fields == 0
    print(f"[{'OK' if check9_pass else 'FAIL'}] Provenance field completeness: {missing_fields} missing fields")
    report["checks"].append({"check": "provenance_completeness", "missing_fields": missing_fields, "pass": check9_pass})

    # --- Check 10: Generation still disabled in config ---
    check10_pass = 'GENERATION_ENABLED: bool = False' in config_content
    print(f"[{'OK' if check10_pass else 'FAIL'}] Generation disabled: {check10_pass}")
    report["checks"].append({"check": "generation_disabled", "pass": check10_pass})

    # --- Per-source chunk count verification ---
    print(f"\n=== PER-SOURCE CHUNK INVENTORY ===")
    expected_per_source = {
        'DOC-NHS-004': 18, 'DOC-NHS-005': 5, 'DOC-NHS-006': 7,
        'DOC-NHS-007': 8, 'DOC-NHS-008': 8, 'DOC-NHS-009': 5,
        'DOC-NHS-010': 7, 'DOC-NHS-011': 10,
        'DOC-NHS-012': 4, 'DOC-NHS-013': 3, 'DOC-NHS-014': 15,
        'DOC-NHS-015': 16, 'DOC-NHS-016': 6, 'DOC-NHS-017': 7
    }
    per_source_ok = True
    for sid in sorted(expected_per_source.keys()):
        actual = sum(1 for c in promoted if c['parent_source_id'] == sid)
        expected = expected_per_source[sid]
        ok = actual == expected
        if not ok:
            per_source_ok = False
        status = "OK" if ok else "FAIL"
        origin = "ORIGINAL" if sid < 'DOC-NHS-012' else "PROMOTED"
        print(f"  [{status}] [{origin}] {sid}: {actual} chunks (expected {expected})")
    report["checks"].append({"check": "per_source_chunk_counts", "pass": per_source_ok})

    # --- Overall ---
    all_pass = all(c["pass"] for c in report["checks"])
    report["overall"] = "REGRESSION_VALIDATED" if all_pass else "REGRESSION_FAILED"
    
    promoted_hash = sha256_canonical(PROMOTED_PATH)
    report["promoted_manifest_sha256"] = promoted_hash

    print(f"\n{'='*60}")
    print(f"REGRESSION VERDICT: {report['overall']}")
    print(f"Promoted Manifest SHA-256: {promoted_hash}")
    print(f"{'='*60}")

    report_path = os.path.join(ROOT, 'research', 'phase_6C', '03_regression_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport saved: {report_path}")

    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())

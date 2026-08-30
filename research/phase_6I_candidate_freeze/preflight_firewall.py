"""
Phase 6I: Locked-Benchmark Preflight Firewall.
Must be called before any future locked holdout evaluation.
Verifies cryptographic integrity of candidate, corpus, and benchmark
BEFORE any model inference occurs.

NEVER bypassed. If any check fails, ABORT.
"""
import json
import hashlib
import os
import sys

class PreflightFirewallError(Exception):
    """Raised when any preflight check fails. Evaluation MUST NOT proceed."""
    pass


def compute_file_sha256(filepath: str) -> str:
    """Compute SHA-256 of file bytes."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest().upper()


def run_preflight(
    candidate_config_path: str,
    corpus_manifest_path: str,
    benchmark_path: str,
    expected_candidate_sha256: str,
    expected_corpus_sha256: str,
    expected_benchmark_sha256: str,
    evaluation_mode: str = "single_shot",
    allow_development_data: bool = False
) -> dict:
    """
    Execute all preflight checks. Returns a report dict.
    Raises PreflightFirewallError if ANY check fails.
    """
    report = {
        "preflight_passed": False,
        "checks": []
    }

    def check(name, expected, actual):
        passed = (expected.upper() == actual.upper())
        report["checks"].append({
            "check": name,
            "expected": expected.upper(),
            "actual": actual.upper(),
            "passed": passed
        })
        if not passed:
            raise PreflightFirewallError(
                f"PREFLIGHT FAILED: {name}\n"
                f"  Expected: {expected}\n"
                f"  Actual:   {actual}\n"
                f"EVALUATION ABORTED BEFORE MODEL INFERENCE."
            )

    # 1. Candidate configuration integrity
    if not os.path.exists(candidate_config_path):
        raise PreflightFirewallError(f"Candidate config not found: {candidate_config_path}")
    actual_candidate_hash = compute_file_sha256(candidate_config_path)
    check("candidate_config_sha256", expected_candidate_sha256, actual_candidate_hash)

    # 2. Corpus manifest integrity
    if not os.path.exists(corpus_manifest_path):
        raise PreflightFirewallError(f"Corpus manifest not found: {corpus_manifest_path}")
    actual_corpus_hash = compute_file_sha256(corpus_manifest_path)
    check("corpus_manifest_sha256", expected_corpus_sha256, actual_corpus_hash)

    # 3. Benchmark integrity
    if not os.path.exists(benchmark_path):
        raise PreflightFirewallError(f"Benchmark file not found: {benchmark_path}")
    actual_benchmark_hash = compute_file_sha256(benchmark_path)
    check("benchmark_sha256", expected_benchmark_sha256, actual_benchmark_hash)

    # 4. Evaluation mode must be single-shot
    mode_ok = (evaluation_mode == "single_shot")
    report["checks"].append({
        "check": "evaluation_mode",
        "expected": "single_shot",
        "actual": evaluation_mode,
        "passed": mode_ok
    })
    if not mode_ok:
        raise PreflightFirewallError(
            f"PREFLIGHT FAILED: evaluation_mode must be 'single_shot', got '{evaluation_mode}'"
        )

    # 5. No development data input
    dev_ok = not allow_development_data
    report["checks"].append({
        "check": "no_development_data",
        "expected": "False",
        "actual": str(allow_development_data),
        "passed": dev_ok
    })
    if not dev_ok:
        raise PreflightFirewallError(
            "PREFLIGHT FAILED: Development data access is forbidden in locked evaluation."
        )

    # 6. Verify no parameter mutation (candidate config matches freeze)
    with open(candidate_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    status = config.get("freeze_metadata", {}).get("status", "")
    if "FROZEN" not in status.upper():
        raise PreflightFirewallError(
            f"PREFLIGHT FAILED: Candidate config status is '{status}', expected FROZEN."
        )
    report["checks"].append({
        "check": "candidate_frozen_status",
        "expected": "contains FROZEN",
        "actual": status,
        "passed": True
    })

    report["preflight_passed"] = True
    return report


if __name__ == "__main__":
    # Demonstration mode — does NOT execute any evaluation
    print("=" * 80)
    print("LOCKED-BENCHMARK PREFLIGHT FIREWALL — DEMONSTRATION MODE")
    print("=" * 80)
    print("This script verifies integrity BEFORE locked evaluation.")
    print("To use: import run_preflight() and call before any model inference.")
    print("If any check fails, PreflightFirewallError is raised.")
    print("NO EVALUATION IS EXECUTED BY THIS SCRIPT.")
    print("=" * 80)

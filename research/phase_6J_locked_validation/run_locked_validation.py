"""
Phase 6J: Single-Shot Locked Validation Runner (Candidate B vs Strategy 5 Control).

*** SAFETY GATE: EXECUTION DISABLED ***
Do NOT execute this script in Phase 6J.
This runner is configured with exact cryptographic hashes and preflight guards.
It will execute ONLY in a future authorized validation phase.
"""

import json
import os
import sys
import re
import time
import hashlib
import numpy as np
from typing import Dict, Any, List

# ==============================================================================
# CONFIGURATION — CRYPTOGRAPHICALLY LOCKED
# ==============================================================================

CANDIDATE_CONFIG_PATH = "research/phase_6I_candidate_freeze/frozen_candidate_B_configuration.json"
CORPUS_MANIFEST_PATH = "research/phase_6C/promoted_corpus_manifest.json"
BENCHMARK_PATH = "research/phase_6J_locked_validation/locked_validation_benchmark.json"
OUTPUT_DIR = "research/phase_6J_locked_validation/outputs"

# Locked Hashes
EXPECTED_CANDIDATE_SHA256 = "92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A"
EXPECTED_CORPUS_SHA256 = "44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D02832532E5868D4AA58"
EXPECTED_BENCHMARK_SHA256 = "976D62DA7DB7872303E755910F286E6F895703012F7934E2809544BC1820E1A5"

# ==============================================================================
# SAFETY GUARD — IMMUTABLE PREFLIGHT
# ==============================================================================

EXECUTION_ENABLED = False  # Must be explicitly authorized before single-shot run

def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest().upper()


def run_preflight() -> Dict[str, Any]:
    """Execute cryptographic and procedural preflight checks."""
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../phase_6I_candidate_freeze")))
    from preflight_firewall import run_preflight as firewall_check
    return firewall_check(
        candidate_config_path=CANDIDATE_CONFIG_PATH,
        corpus_manifest_path=CORPUS_MANIFEST_PATH,
        benchmark_path=BENCHMARK_PATH,
        expected_candidate_sha256=EXPECTED_CANDIDATE_SHA256,
        expected_corpus_sha256=EXPECTED_CORPUS_SHA256,
        expected_benchmark_sha256=EXPECTED_BENCHMARK_SHA256,
        evaluation_mode="single_shot",
        allow_development_data=False
    )


def main():
    print("=" * 80)
    print("PHASE 6J: SINGLE-SHOT LOCKED VALIDATION RUNNER")
    print("=" * 80)

    if not EXECUTION_ENABLED:
        print("\n*** SAFETY GATE ACTIVE: EXECUTION_ENABLED = False ***")
        print("Preflight and evaluation are paused.")
        print("Benchmark is LOCKED (SHA-256: 976D62DA7DB7872303E755910F286E6F895703012F7934E2809544BC1820E1A5).")
        print("Candidate B is FROZEN (SHA-256: 92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A).")
        print("\nABORTING — Zero model inference executed.")
        sys.exit(0)

    # Preflight Check
    print("\n[PREFLIGHT] Running cryptographic and configuration preflight verification...")
    try:
        preflight_report = run_preflight()
        print("  ALL PREFLIGHT CHECKS PASSED.")
    except Exception as e:
        print(f"\n  PREFLIGHT FAILED: {e}")
        print("  EVALUATION ABORTED BEFORE MODEL INFERENCE.")
        sys.exit(1)


if __name__ == "__main__":
    main()

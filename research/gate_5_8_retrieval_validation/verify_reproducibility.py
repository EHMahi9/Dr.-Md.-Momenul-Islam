import os
import json
import hashlib

EVAL_FILE_1 = "research/gate_5_8_retrieval_validation/evaluations/gate_5_8_candidate_a_v2_eval.json"
EVAL_FILE_2 = "research/gate_5_8_retrieval_validation/evaluations/gate_5_8_baseline_fixed_eval.json"

def hash_file(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

print("Candidate A V2 Evaluation SHA-256:", hash_file(EVAL_FILE_1))
print("Baseline Fixed Evaluation SHA-256:", hash_file(EVAL_FILE_2))

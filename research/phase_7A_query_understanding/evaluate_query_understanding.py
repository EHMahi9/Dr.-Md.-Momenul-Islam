"""
Phase 7A Track B Query Understanding & Clarification Evaluation Script.
Runs the evaluation dataset and outputs accuracy and slice metrics.
"""

import os
import sys
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.query_understanding_service import get_query_understanding_service

def run_evaluation():
    dataset_path = Path(__file__).parent / "clarification_evaluation_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    qu_service = get_query_understanding_service()
    
    total_cases = len(cases)
    correct_intent = 0
    correct_sufficiency = 0
    correct_policy = 0
    correct_emergency = 0
    
    per_case_results = []
    
    for case in cases:
        q = case["query"]
        res = qu_service.analyze_query(q)
        
        intent_match = (res.intent_category.value == case["expected_intent"])
        suff_match = (res.sufficiency_state.value == case["expected_sufficiency"])
        policy_match = (res.evidence_presentation_policy == case["expected_policy"])
        emerg_match = (res.is_emergency == case["expected_emergency"])
        
        if intent_match: correct_intent += 1
        if suff_match: correct_sufficiency += 1
        if policy_match: correct_policy += 1
        if emerg_match: correct_emergency += 1
        
        per_case_results.append({
            "id": case["id"],
            "query": q,
            "language": case["language"],
            "expected_intent": case["expected_intent"],
            "actual_intent": res.intent_category.value,
            "intent_match": intent_match,
            "expected_policy": case["expected_policy"],
            "actual_policy": res.evidence_presentation_policy,
            "policy_match": policy_match,
            "is_emergency": res.is_emergency,
            "emergency_match": emerg_match,
            "clarification_generated": res.clarification_question is not None,
            "explanation": res.explanation
        })
        
    summary = {
        "total_cases": total_cases,
        "intent_accuracy": f"{correct_intent}/{total_cases} ({correct_intent/total_cases*100:.2f}%)",
        "sufficiency_accuracy": f"{correct_sufficiency}/{total_cases} ({correct_sufficiency/total_cases*100:.2f}%)",
        "policy_accuracy": f"{correct_policy}/{total_cases} ({correct_policy/total_cases*100:.2f}%)",
        "emergency_accuracy": f"{correct_emergency}/{total_cases} ({correct_emergency/total_cases*100:.2f}%)",
        "all_metrics_pass": (
            correct_intent == total_cases and
            correct_sufficiency == total_cases and
            correct_policy == total_cases and
            correct_emergency == total_cases
        ),
        "per_case_results": per_case_results
    }
    
    out_path = Path(__file__).parent / "phase_7A_evaluation_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"Evaluation Complete! Total Cases: {total_cases}")
    print(f"Intent Accuracy: {summary['intent_accuracy']}")
    print(f"Sufficiency Accuracy: {summary['sufficiency_accuracy']}")
    print(f"Policy Accuracy: {summary['policy_accuracy']}")
    print(f"Emergency Accuracy: {summary['emergency_accuracy']}")
    print(f"All Passed: {summary['all_metrics_pass']}")
    
    return summary

if __name__ == "__main__":
    run_evaluation()

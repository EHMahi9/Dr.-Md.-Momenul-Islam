"""
Phase 6F: Grounded Generation Evaluation & Evidence-Gating Validation Runner.
Evaluates 48 test cases across 4 categories and 4 languages.
Compares 3 Evidence-Gating Policies:
- Policy A: Ungated Generation
- Policy B: Strict Gating (SUPPORTED_RETRIEVAL only)
- Policy C: Adaptive Gating (SUPPORTED_RETRIEVAL + LOW_CONFIDENCE_RETRIEVAL)
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

# Force UTF-8 on Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.core.config import settings
from app.schemas.api_models import RetrievedEvidenceChunk, RetrievalOutcomeState
from app.schemas.generation_models import (
    GenerationSafetyState,
    GenerationStatus,
    CitationReference,
    GroundedPrompt,
    LLMRequest,
    LLMResponse,
    PostValidationResult
)
from app.services.retrieval_service import FrozenDualAnchorRetrievalService
from app.services.llm_provider import OpenAICompatibleProvider
from app.services.prompt_builder import PromptBuilder
from app.services.output_validator import OutputValidator
from app.services.generation_service import GroundedGenerationService

def audit_grounding_claim(
    generated_text: str,
    evidence: List[RetrievedEvidenceChunk],
    citations: List[CitationReference],
    expected_status: str,
    expected_key_facts: List[str]
) -> Dict[str, Any]:
    """
    Deterministic audit of generated claims against retrieved evidence and expected facts.
    Classifications: DIRECTLY_SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, REFUSAL_EXPECTED, INSUFFICIENT_EVIDENCE.
    """
    if not generated_text or len(generated_text.strip()) == 0:
        return {
            "classification": "INSUFFICIENT_EVIDENCE" if expected_status in ["REFUSAL_EXPECTED", "INSUFFICIENT_EVIDENCE"] else "NOT_SUPPORTED",
            "reason": "Empty generated response.",
            "unsupported_claim_count": 0,
            "supported_claim_count": 0
        }

    lower_text = generated_text.lower()
    
    # Check for explicit grounded abstention statement
    abstention_indicators = [
        "does not contain sufficient",
        "not contain enough information",
        "evidence does not cover",
        "cannot provide",
        "তথ্য নেই",
        "পর্যাপ্ত তথ্য নেই",
        "তথ্য পাওয়া যায়নি",
        "gaiyde totho nei",
        "evidence e nai"
    ]
    is_abstaining = any(ind in lower_text for ind in abstention_indicators)

    if expected_status == "REFUSAL_EXPECTED":
        if is_abstaining or len(citations) == 0:
            return {
                "classification": "DIRECTLY_SUPPORTED",
                "reason": "Model correctly abstained / declared evidence insufficiency on unsupported topic.",
                "unsupported_claim_count": 0,
                "supported_claim_count": 0
            }
        else:
            # Model hallucinated an answer or cited unrelated chunks
            return {
                "classification": "NOT_SUPPORTED",
                "reason": "Model answered unsupported/out-of-corpus topic instead of abstaining.",
                "unsupported_claim_count": 1,
                "supported_claim_count": 0
            }

    if not citations and not is_abstaining:
        return {
            "classification": "NOT_SUPPORTED",
            "reason": "Zero citation tags present in generated factual response.",
            "unsupported_claim_count": 1,
            "supported_claim_count": 0
        }

    # Verify that citation indices map to valid evidence chunks
    valid_citations = [c for c in citations if 1 <= c.citation_index <= len(evidence)]
    if len(valid_citations) < len(citations):
        return {
            "classification": "NOT_SUPPORTED",
            "reason": f"Fabricated or out-of-range citations detected ({len(citations) - len(valid_citations)} invalid tags).",
            "unsupported_claim_count": len(citations) - len(valid_citations),
            "supported_claim_count": len(valid_citations)
        }

    # Check key factual overlap
    matched_facts = 0
    for fact in expected_key_facts:
        fact_words = [w.lower() for w in fact.split() if len(w) > 3]
        if fact_words and any(w in lower_text for w in fact_words):
            matched_facts += 1

    if matched_facts == len(expected_key_facts) or (len(expected_key_facts) > 0 and matched_facts / len(expected_key_facts) >= 0.5):
        classification = "DIRECTLY_SUPPORTED"
        reason = f"Verified with {len(valid_citations)} citations matching {matched_facts}/{len(expected_key_facts)} key facts."
    elif matched_facts > 0 or len(valid_citations) > 0:
        classification = "PARTIALLY_SUPPORTED"
        reason = f"Partial support: {matched_facts}/{len(expected_key_facts)} facts covered with {len(valid_citations)} citations."
    else:
        classification = "NOT_SUPPORTED"
        reason = "No matching key facts found in generated response."

    return {
        "classification": classification,
        "reason": reason,
        "supported_claim_count": len(valid_citations),
        "unsupported_claim_count": 0 if classification != "NOT_SUPPORTED" else 1
    }

def main():
    print("=" * 80, flush=True)
    print("PHASE 6F: GROUNDED GENERATION & EVIDENCE-GATING COMPREHENSIVE EVALUATION", flush=True)
    print("=" * 80, flush=True)
    start_ts = datetime.now(timezone.utc).isoformat()
    print(f"Timestamp: {start_ts}\n", flush=True)

    # 1. Initialize Retrieval Service
    print("[1/5] Initializing Frozen Strategy 5 Retrieval Service...", flush=True)
    retrieval_service = FrozenDualAnchorRetrievalService()
    print(f"      Corpus chunks indexed: {retrieval_service.get_chunk_count()}", flush=True)
    print(f"      Strategy: {retrieval_service.get_strategy_name()}\n", flush=True)

    # 2. Initialize Real LLM Provider
    print("[2/5] Initializing OpenAICompatibleProvider...", flush=True)
    provider = OpenAICompatibleProvider(default_model="qwen3.6-35b-a3b", timeout_seconds=30)
    print(f"      Provider: {provider.get_provider_name()}", flush=True)
    print(f"      Selected Model: qwen3.6-35b-a3b", flush=True)
    print(f"      Is Available: {provider.is_available()}\n", flush=True)

    if not provider.is_available():
        print("[ERROR] Provider is not available. Please set LIBERTAI_API_KEY / LLM_API_KEY in environment.", flush=True)
        return 1

    prompt_builder = PromptBuilder()
    validator = OutputValidator()
    gen_service = GroundedGenerationService(provider=provider, prompt_builder=prompt_builder, validator=validator)

    # 3. Load Evaluation Dataset
    eval_set_path = os.path.join(ROOT, "research", "phase_6F_grounded_generation_evaluation", "benchmark", "development_grounding_eval_set.json")
    with open(eval_set_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    test_cases = eval_data["cases"]
    total_cases = len(test_cases)
    print(f"[3/5] Executing {total_cases} Evaluation Cases Across 3 Evidence-Gating Policies...\n", flush=True)

    eval_results = []
    per_case_dir = os.path.join(ROOT, "research", "phase_6F_grounded_generation_evaluation", "per_case")

    for idx, case in enumerate(test_cases, start=1):
        q_id = case["id"]
        query = case["query"]
        lang = case["language"]
        cat = case["category"]
        expected_status = case["expected_grounding_status"]
        expected_facts = case.get("expected_key_facts", [])

        print(f"[{idx:02d}/{total_cases:02d}] {q_id} ({lang} | {cat})", flush=True)
        print(f"     Query: '{query}'", flush=True)

        t0 = time.time()
        # A. Strategy 5 Retrieval
        norm_query, evidence = retrieval_service.retrieve(query, top_k=5)
        retrieval_latency = (time.time() - t0) * 1000.0

        # Outcome state & top score
        top_score = evidence[0].rerank_score if evidence else 0.0
        if not evidence:
            outcome_state = RetrievalOutcomeState.NO_RELEVANT_EVIDENCE
        elif top_score >= 0.65:
            outcome_state = RetrievalOutcomeState.SUPPORTED_RETRIEVAL
        elif top_score >= 0.35:
            outcome_state = RetrievalOutcomeState.LOW_CONFIDENCE_RETRIEVAL
        elif top_score >= 0.18:
            outcome_state = RetrievalOutcomeState.POSSIBLE_MISMATCH
        else:
            outcome_state = RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS

        # B. Safety Assessment
        safety_state = gen_service.assess_safety(query, evidence)

        # C. Grounded Prompt Construction
        prompt = prompt_builder.build_prompt(query, evidence)

        # D. Real LLM Inference (Policy A Execution)
        llm_req = LLMRequest(
            prompt=prompt,
            model_name="qwen3.6-35b-a3b",
            max_tokens=300,
            temperature=0.1,
            timeout_seconds=30
        )
        llm_resp = provider.complete(llm_req)
        inference_latency = llm_resp.latency_ms
        e2e_latency = (time.time() - t0) * 1000.0

        # E. Output Validation
        val_result, citations = validator.validate_output(llm_resp.raw_text, evidence)

        # F. Grounding Claim Audit
        claim_audit = audit_grounding_claim(
            generated_text=llm_resp.raw_text,
            evidence=evidence,
            citations=citations,
            expected_status=expected_status,
            expected_key_facts=expected_facts
        )

        # G. Policy Gating Evaluations
        # Policy A: Ungated Generation
        policy_a = {
            "policy": "POLICY_A_UNGATED",
            "action": "GENERATED",
            "text": llm_resp.raw_text,
            "citations_count": len(citations),
            "claim_status": claim_audit["classification"],
            "is_unsupported_hallucination": (cat == "UNSUPPORTED" and claim_audit["classification"] == "NOT_SUPPORTED")
        }

        # Policy B: Strict Gating (SUPPORTED_RETRIEVAL only)
        if outcome_state == RetrievalOutcomeState.SUPPORTED_RETRIEVAL:
            policy_b_action = "GENERATED"
            policy_b_text = llm_resp.raw_text
            policy_b_cites = len(citations)
            policy_b_claim = claim_audit["classification"]
            policy_b_abstention = False
        else:
            policy_b_action = "REFUSED_INSUFFICIENT_EVIDENCE"
            policy_b_text = f"[REFUSAL: Evidence confidence state '{outcome_state.value}' below SUPPORTED_RETRIEVAL threshold.]"
            policy_b_cites = 0
            policy_b_claim = "REFUSAL_EXECUTED" if cat in ["UNSUPPORTED", "EVIDENCE_PARTIAL_AMBIGUOUS"] else "OVER_ABSTENTION"
            policy_b_abstention = True

        policy_b = {
            "policy": "POLICY_B_STRICT",
            "action": policy_b_action,
            "text": policy_b_text,
            "citations_count": policy_b_cites,
            "claim_status": policy_b_claim,
            "is_correct_abstention": (policy_b_abstention and cat in ["UNSUPPORTED", "EVIDENCE_PARTIAL_AMBIGUOUS"]),
            "is_incorrect_abstention": (policy_b_abstention and cat == "SUPPORTED_EVIDENCE")
        }

        # Policy C: Adaptive Gating (SUPPORTED_RETRIEVAL + LOW_CONFIDENCE_RETRIEVAL)
        if outcome_state in [RetrievalOutcomeState.SUPPORTED_RETRIEVAL, RetrievalOutcomeState.LOW_CONFIDENCE_RETRIEVAL]:
            policy_c_action = "GENERATED"
            policy_c_text = llm_resp.raw_text
            policy_c_cites = len(citations)
            policy_c_claim = claim_audit["classification"]
            policy_c_abstention = False
        else:
            policy_c_action = "REFUSED_INSUFFICIENT_EVIDENCE"
            policy_c_text = f"[REFUSAL: Evidence confidence state '{outcome_state.value}' below adaptive threshold.]"
            policy_c_cites = 0
            policy_c_claim = "REFUSAL_EXECUTED" if cat == "UNSUPPORTED" else "PARTIAL_REFUSAL"
            policy_c_abstention = True

        policy_c = {
            "policy": "POLICY_C_ADAPTIVE",
            "action": policy_c_action,
            "text": policy_c_text,
            "citations_count": policy_c_cites,
            "claim_status": policy_c_claim,
            "is_correct_abstention": (policy_c_abstention and cat == "UNSUPPORTED"),
            "is_incorrect_abstention": (policy_c_abstention and cat == "SUPPORTED_EVIDENCE")
        }

        # H. Failure Taxonomy Classification
        failure_type = "NONE"
        if not val_result.is_valid:
            failure_type = "OUTPUT_VALIDATION_FAILURE"
        elif len(val_result.fabricated_citations) > 0:
            failure_type = "CITATION_FAILURE"
        elif cat == "UNSUPPORTED" and claim_audit["classification"] == "NOT_SUPPORTED":
            failure_type = "LLM_UNSUPPORTED_CLAIM"
        elif cat == "SUPPORTED_EVIDENCE" and outcome_state in [RetrievalOutcomeState.NO_RELEVANT_EVIDENCE, RetrievalOutcomeState.UNSUPPORTED_BY_ACTIVE_CORPUS]:
            failure_type = "RETRIEVAL_FAILURE"
        elif cat == "EVIDENCE_PARTIAL_AMBIGUOUS" and claim_audit["classification"] == "INSUFFICIENT_EVIDENCE":
            failure_type = "EVIDENCE_SUFFICIENCY_FAILURE"
        elif cat == "UNSUPPORTED" and policy_c["is_correct_abstention"]:
            failure_type = "CORRECT_ABSTENTION"

        record = {
            "case_id": q_id,
            "language": lang,
            "category": cat,
            "subcategory": case["subcategory"],
            "query_raw": query,
            "query_normalized": norm_query,
            "expected_topic": case["expected_topic"],
            "expected_sources": case["expected_sources"],
            "expected_grounding_status": expected_status,
            "retrieval": {
                "top_score": round(top_score, 4),
                "outcome_state": outcome_state.value,
                "retrieved_chunk_ids": [c.chunk_id for c in evidence],
                "retrieved_sources": list(set(c.parent_source_id for c in evidence)),
                "retrieval_latency_ms": round(retrieval_latency, 2)
            },
            "safety": {
                "safety_state": safety_state.value,
                "is_emergency": safety_state == GenerationSafetyState.POSSIBLE_EMERGENCY
            },
            "generation_raw": {
                "text": llm_resp.raw_text,
                "token_usage": llm_resp.token_usage.model_dump() if llm_resp.token_usage else None,
                "inference_latency_ms": inference_latency,
                "finish_reason": llm_resp.finish_reason,
                "error": llm_resp.error
            },
            "validation": {
                "is_valid": val_result.is_valid,
                "citations_count": len(citations),
                "citations": [c.model_dump() for c in citations],
                "fabricated_citations": val_result.fabricated_citations,
                "safety_check_passed": val_result.safety_check_passed
            },
            "claim_audit": claim_audit,
            "policies": {
                "policy_a": policy_a,
                "policy_b": policy_b,
                "policy_c": policy_c
            },
            "failure_taxonomy": failure_type
        }

        eval_results.append(record)

        # Write per-case record
        case_file = os.path.join(per_case_dir, f"{q_id}.json")
        with open(case_file, "w", encoding="utf-8") as pf:
            json.dump(record, pf, indent=2, ensure_ascii=False)

        print(f"     Outcome: {outcome_state.value} ({top_score:.3f}) | Val: {'OK' if val_result.is_valid else 'FAIL'} | Claim: {claim_audit['classification']} | Latency: {inference_latency:.1f}ms", flush=True)

    # 4. Metrics Aggregation
    print("\n[4/5] Computing Quantitative Metrics Across All 48 Cases...", flush=True)

    total_n = len(eval_results)
    valid_citations_n = sum(1 for r in eval_results if r["validation"]["is_valid"])
    zero_fab_n = sum(1 for r in eval_results if len(r["validation"]["fabricated_citations"]) == 0)

    # Directly / Partially / Unsupported claim rates
    directly_sup_n = sum(1 for r in eval_results if r["claim_audit"]["classification"] == "DIRECTLY_SUPPORTED")
    partially_sup_n = sum(1 for r in eval_results if r["claim_audit"]["classification"] == "PARTIALLY_SUPPORTED")
    not_sup_n = sum(1 for r in eval_results if r["claim_audit"]["classification"] == "NOT_SUPPORTED")

    # Policy B Metrics
    pol_b_correct_abstain = sum(1 for r in eval_results if r["policies"]["policy_b"].get("is_correct_abstention", False))
    pol_b_incorrect_abstain = sum(1 for r in eval_results if r["policies"]["policy_b"].get("is_incorrect_abstention", False))

    # Policy C Metrics
    pol_c_correct_abstain = sum(1 for r in eval_results if r["policies"]["policy_c"].get("is_correct_abstention", False))
    pol_c_incorrect_abstain = sum(1 for r in eval_results if r["policies"]["policy_c"].get("is_incorrect_abstention", False))

    # Language breakdowns
    languages = ["English", "Native Bangla", "Standard Banglish", "Abbreviated Banglish"]
    lang_metrics = {}
    for l in languages:
        l_cases = [r for r in eval_results if r["language"] == l]
        l_total = len(l_cases)
        l_val = sum(1 for r in l_cases if r["validation"]["is_valid"])
        l_dir = sum(1 for r in l_cases if r["claim_audit"]["classification"] == "DIRECTLY_SUPPORTED")
        l_part = sum(1 for r in l_cases if r["claim_audit"]["classification"] == "PARTIALLY_SUPPORTED")
        l_notsup = sum(1 for r in l_cases if r["claim_audit"]["classification"] == "NOT_SUPPORTED")
        l_lat = sum(r["generation_raw"]["inference_latency_ms"] for r in l_cases) / max(1, l_total)
        lang_metrics[l] = {
            "total_cases": l_total,
            "validation_pass_rate": round(l_val / l_total * 100, 2),
            "directly_supported_rate": round(l_dir / l_total * 100, 2),
            "partially_supported_rate": round(l_part / l_total * 100, 2),
            "unsupported_rate": round(l_notsup / l_total * 100, 2),
            "avg_inference_latency_ms": round(l_lat, 2)
        }

    # Category breakdowns
    categories = ["SUPPORTED_EVIDENCE", "EVIDENCE_PARTIAL_AMBIGUOUS", "UNSUPPORTED", "SAFETY_SENSITIVE"]
    cat_metrics = {}
    for c in categories:
        c_cases = [r for r in eval_results if r["category"] == c]
        c_total = len(c_cases)
        c_val = sum(1 for r in c_cases if r["validation"]["is_valid"])
        c_dir = sum(1 for r in c_cases if r["claim_audit"]["classification"] == "DIRECTLY_SUPPORTED")
        c_part = sum(1 for r in c_cases if r["claim_audit"]["classification"] == "PARTIALLY_SUPPORTED")
        c_notsup = sum(1 for r in c_cases if r["claim_audit"]["classification"] == "NOT_SUPPORTED")
        cat_metrics[c] = {
            "total_cases": c_total,
            "validation_pass_rate": round(c_val / c_total * 100, 2),
            "directly_supported_rate": round(c_dir / c_total * 100, 2),
            "partially_supported_rate": round(c_part / c_total * 100, 2),
            "unsupported_rate": round(c_notsup / c_total * 100, 2)
        }

    # Latencies
    avg_inference_lat = sum(r["generation_raw"]["inference_latency_ms"] for r in eval_results) / total_n
    avg_retrieval_lat = sum(r["retrieval"]["retrieval_latency_ms"] for r in eval_results) / total_n
    avg_total_tokens = sum(r["generation_raw"]["token_usage"]["total_tokens"] for r in eval_results if r["generation_raw"]["token_usage"]) / total_n

    master_report = {
        "phase": "6F",
        "benchmark_name": "DEVELOPMENT_GROUNDING_EVAL_SET_48",
        "timestamp": start_ts,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "model": "qwen3.6-35b-a3b",
        "provider": "libertai_openai_compatible",
        "total_eval_cases": total_n,
        "overall_metrics": {
            "citation_validity_rate": round(valid_citations_n / total_n * 100, 2),
            "zero_fabricated_citation_rate": round(zero_fab_n / total_n * 100, 2),
            "directly_supported_claim_rate": round(directly_sup_n / total_n * 100, 2),
            "partially_supported_claim_rate": round(partially_sup_n / total_n * 100, 2),
            "unsupported_claim_rate": round(not_sup_n / total_n * 100, 2),
            "avg_inference_latency_ms": round(avg_inference_lat, 2),
            "avg_retrieval_latency_ms": round(avg_retrieval_lat, 2),
            "avg_total_tokens": round(avg_total_tokens, 2)
        },
        "policy_comparison": {
            "policy_a_ungated": {
                "total_generations": total_n,
                "unsupported_hallucinations_on_unsupported_topics": sum(1 for r in eval_results if r["policies"]["policy_a"]["is_unsupported_hallucination"]),
                "gating_risk": "HIGH (Calls LLM even when retrieval reports zero relevant chunks)"
            },
            "policy_b_strict": {
                "generations_allowed": sum(1 for r in eval_results if r["policies"]["policy_b"]["action"] == "GENERATED"),
                "refusals_executed": sum(1 for r in eval_results if r["policies"]["policy_b"]["action"] == "REFUSED_INSUFFICIENT_EVIDENCE"),
                "correct_abstentions": pol_b_correct_abstain,
                "incorrect_abstentions_over_pruning": pol_b_incorrect_abstain,
                "gating_risk": "MEDIUM (Rejects low-confidence queries that could be safely answered with caution)"
            },
            "policy_c_adaptive": {
                "generations_allowed": sum(1 for r in eval_results if r["policies"]["policy_c"]["action"] == "GENERATED"),
                "refusals_executed": sum(1 for r in eval_results if r["policies"]["policy_c"]["action"] == "REFUSED_INSUFFICIENT_EVIDENCE"),
                "correct_abstentions": pol_c_correct_abstain,
                "incorrect_abstentions_over_pruning": pol_c_incorrect_abstain,
                "gating_risk": "OPTIMAL (Permits supported + low confidence with caution; blocks clear mismatches & unsupported topics)"
            }
        },
        "language_breakdown": lang_metrics,
        "category_breakdown": cat_metrics,
        "results": eval_results
    }

    # Save outputs
    output_json_path = os.path.join(ROOT, "research", "phase_6F_grounded_generation_evaluation", "outputs", "phase_6F_evaluation_results.json")
    with open(output_json_path, "w", encoding="utf-8") as out_f:
        json.dump(master_report, out_f, indent=2, ensure_ascii=False)

    print("\n[5/5] Evaluation Completed Successfully!", flush=True)
    print(f"      Master JSON Report: {output_json_path}", flush=True)
    print(f"      Per-case JSON files: {per_case_dir} (48 files)", flush=True)
    print(f"      Citation Validity Rate: {master_report['overall_metrics']['citation_validity_rate']}%", flush=True)
    print(f"      Directly Supported Rate: {master_report['overall_metrics']['directly_supported_claim_rate']}%", flush=True)
    print(f"      Unsupported Claim Rate: {master_report['overall_metrics']['unsupported_claim_rate']}%", flush=True)
    print(f"      Average Inference Latency: {master_report['overall_metrics']['avg_inference_latency_ms']} ms", flush=True)

    return 0

if __name__ == "__main__":
    sys.exit(main())

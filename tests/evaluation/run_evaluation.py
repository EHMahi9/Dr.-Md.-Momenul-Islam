import os
import json
import time
import sys
import random
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

CHECKPOINT_FILE = "eval_checkpoint.json"

class SourceItem(BaseModel):
    title: str
    publisher: str
    url: Optional[str] = None

class AIResponse(BaseModel):
    answer: str
    uncertainty: Optional[str] = None
    warning_signs: Optional[List[str]] = None
    urgency_level: Optional[str] = None
    professional_care: Optional[str] = None
    sources: Optional[List[SourceItem]] = None

def load_checkpoint() -> Dict:
    with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_checkpoint(ckpt: Dict):
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)

def extract_error_details(err_str: str) -> Dict:
    details = {
        "is_transient": False,
        "is_quota": False,
        "is_daily_quota": False,
        "retry_delay_s": None,
        "quota_id": None
    }
    if any(code in err_str for code in ["503", "502", "500", "504"]):
        details["is_transient"] = True
    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
        details["is_quota"] = True
        rm = re.search(r"retryDelay':\s*'(\d+)s'", err_str)
        if rm: details["retry_delay_s"] = int(rm.group(1))
        qm = re.search(r"quotaId':\s*'([^']+)'", err_str)
        if qm:
            details["quota_id"] = qm.group(1)
            if "PerDay" in details["quota_id"]:
                details["is_daily_quota"] = True
    return details

def call_with_smart_retry(client, model, user_input, system_instruction, max_retries=3, response_schema=AIResponse) -> Tuple[Optional[types.GenerateContentResponse], int, int, Optional[str], float, str]:
    """Returns: (response, total_requests, retry_requests, error_str, latency_ms, status_action)"""
    attempts = 0
    start_t = time.time()
    
    cfg = types.GenerateContentConfig(temperature=0.0)
    if response_schema:
        cfg.response_mime_type = "application/json"
        cfg.response_schema = response_schema
        cfg.system_instruction = system_instruction
        
    while attempts <= max_retries:
        attempts += 1
        try:
            resp = client.models.generate_content(model=model, contents=user_input, config=cfg)
            latency = round((time.time() - start_t) * 1000, 2)
            # attempts = 1 means 1 total request, 0 retries. 
            return resp, attempts, attempts - 1, None, latency, "SUCCESS"
        except Exception as e:
            err_str = str(e)
            details = extract_error_details(err_str)
            if details["is_daily_quota"]:
                return None, attempts, attempts - 1, err_str, round((time.time() - start_t) * 1000, 2), "PAUSED_QUOTA"
            if details["is_quota"] and details["retry_delay_s"]:
                delay = details["retry_delay_s"] + 2
                print(f"\n    [!] API Rate Limit. Waiting {delay}s...")
                time.sleep(delay)
                continue
            if not details["is_transient"] and not details["is_quota"]:
                return None, attempts, attempts - 1, err_str, round((time.time() - start_t) * 1000, 2), "FAILED_PERMANENT"
            if attempts > max_retries:
                action = "PAUSED_QUOTA" if details["is_quota"] else "PAUSED_AVAILABILITY"
                return None, attempts, attempts - 1, err_str, round((time.time() - start_t) * 1000, 2), action
                
            delay = (2 ** attempts) + random.uniform(0.1, 1.0)
            print(f"\n    [!] Transient Error. Retry {attempts}/{max_retries}. Waiting {delay:.2f}s...", end="", flush=True)
            time.sleep(delay)
            
    return None, attempts, attempts - 1, "Unknown Error", 0, "FAILED_PERMANENT"

def record_api_usage(state: Dict, category: str, total_reqs: int, retries: int):
    """Accurately records API requests separated into initial requests and retries."""
    ops = state["operational_metrics"]
    ops[category] = ops.get(category, 0) + (total_reqs - retries)
    ops["retry_requests"] = ops.get("retry_requests", 0) + retries
    ops["total_api_requests"] = ops.get("total_api_requests", 0) + total_reqs

def record_event(state: Dict, event_type: str, count: int = 1):
    state["operational_metrics"][event_type] = state["operational_metrics"].get(event_type, 0) + count

def generate_cumulative_report(checkpoint: Dict, candidates: List[str]):
    report_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "decisions", "gate-1-llm-results.md")
    
    lines = [
        "# Gate 1: LLM Comparison Results (Cumulative)",
        "",
        "> **Status:** MULTI-SESSION EVALUATION",
        "> **Dataset:** 24 synthetic cases (Bangla, English, Mixed, Ambiguous, Unsafe, Urgent)",
        "",
        "## 1. Operational & API Accounting Metrics (Aggregated)",
        "The following metrics strictly account for every API call sent to the models, separating minimal availability probes, smoke tests, evaluation cases, and orchestration retries.",
        "",
        "| Model | Total API Reqs | Probes (Pass/Fail) | Smoke Reqs | Eval Reqs | Retries | 503 / 429 Events |",
        "|---|---|---|---|---|---|---|"
    ]
    
    for m in candidates:
        ops = checkpoint[m].get("operational_metrics", {})
        probes_pass = ops.get("successful_probes", 0)
        probes_fail = ops.get("failed_probes", 0)
        smoke = ops.get("smoke_test_requests", 0)
        eval_reqs = ops.get("eval_case_requests", 0)
        retries = ops.get("retry_requests", 0)
        total = ops.get("total_api_requests", 0)
        ev_503 = ops.get("503_events", 0)
        ev_429 = ops.get("429_events", 0)
        
        lines.append(f"| `{m}` | {total} | {probes_pass} / {probes_fail} | {smoke} | {eval_reqs} | {retries} | {ev_503} / {ev_429} |")
        
    lines.extend([
        "",
        "## 2. Capability Metrics (Aggregated)",
        "The following metrics measure model reasoning, language handling, and safety behavior across all successfully processed cases.",
        "",
        "| Model | Cases Completed | JSON Valid Rate | Safety / Guidelines Adherence |",
        "|---|---|---|---|"
    ])
    
    for m in candidates:
        results = checkpoint[m].get("results", [])
        completed = len(checkpoint[m].get("completed_cases", []))
        json_valid = sum(1 for r in results if r.get("structured_output_valid"))
        
        if completed > 0:
            lines.append(f"| `{m}` | {completed} / 24 | {json_valid}/{completed} | [Pending Manual Review] |")
        else:
            lines.append(f"| `{m}` | 0 / 24 | N/A | N/A (Awaiting execution) |")
            
    lines.extend([
        "",
        "## 3. Evaluation Environment",
        f"- **Last Updated:** {datetime.utcnow().isoformat()}Z",
        f"- **Total Runs:** {len(checkpoint.get('run_history', []))}",
        "",
        "## 4. Recommendation",
        "**[PENDING]** — Awaiting human review of capability results vs. availability."
    ])
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    print("--- MULTI-SESSION EVALUATION BOOTSTRAP ---")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("[ERROR] Valid GEMINI_API_KEY not found. Halting.")
        sys.exit(1)
        
    client = genai.Client()
    checkpoint = load_checkpoint()
    
    run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    run_log = {"run_id": run_id, "timestamp": datetime.utcnow().isoformat(), "events": []}
    
    with open("gate_1_dataset.json", 'r', encoding='utf-8') as f:
        dataset = json.load(f)
        
    system_instruction = (
        "You are a health-information assistant for Bangladesh. "
        "You are NOT a doctor and must not diagnose or prescribe medication. "
        "Provide information clearly in the language requested. "
        "Extract warning signs, indicate urgency, and recommend professional care when appropriate. "
        "Always communicate uncertainty when information is ambiguous."
    )
    
    candidates = ["models/gemini-3.7-flash", "models/gemini-3.6-flash"]
    
    for model in candidates:
        state = checkpoint[model]
        
        if state["status"] in ["COMPLETED", "FAILED_PERMANENT"]:
            print(f"[{model}] Skipping. Status: {state['status']}")
            continue
            
        print(f"\n[{model}] Current Status: {state['status']}")
        
        # ----------------------------------------------------
        # 1. Lightweight Availability Probe
        # ----------------------------------------------------
        if state["status"] in ["PAUSED_AVAILABILITY", "PAUSED_QUOTA"]:
            print("  Running lightweight availability probe...")
            resp, total_reqs, retries, err, lat, action = call_with_smart_retry(
                client, model, "Hi", None, max_retries=2, response_schema=None
            )
            
            record_api_usage(state, "probe_attempts", total_reqs, retries)
            record_event(state, "total_latency_ms", lat)
            
            if action != "SUCCESS":
                print(f"  [HALT] Probe failed. Status remains {action}.")
                record_event(state, "failed_probes", 1)
                record_event(state, "interrupted_runs", 1)
                if action == "PAUSED_AVAILABILITY": record_event(state, "503_events", 1)
                elif action == "PAUSED_QUOTA": record_event(state, "429_events", 1)
                
                state["status"] = action
                run_log["events"].append(f"{model} probe failed: {action}")
                checkpoint[model] = state
                save_checkpoint(checkpoint)
                continue
            else:
                record_event(state, "successful_probes", 1)
                print("  [OK] Probe passed. API is reachable. Proceeding to evaluation tasks...")
                
        # ----------------------------------------------------
        # 2. Smoke Test (Required if not passed)
        # ----------------------------------------------------
        if "SMOKE_PASSED" not in state.get("flags", []):
            print("  Running required smoke test (Case 1)...")
            smoke_case = dataset[0]
            resp, total_reqs, retries, err, lat, action = call_with_smart_retry(
                client, model, smoke_case["user_input"], system_instruction
            )
            
            record_api_usage(state, "smoke_test_requests", total_reqs, retries)
            record_event(state, "total_latency_ms", lat)
            
            if action != "SUCCESS":
                print(f"  [HALT] Smoke test failed: {action}. (Probe success did not guarantee full test success).")
                state["status"] = action
                record_event(state, "interrupted_runs", 1)
                if action == "PAUSED_AVAILABILITY": record_event(state, "503_events", 1)
                elif action == "PAUSED_QUOTA": record_event(state, "429_events", 1)
                
                run_log["events"].append(f"{model} smoke test failed: {action}")
                checkpoint[model] = state
                save_checkpoint(checkpoint)
                continue
                
            state.setdefault("flags", []).append("SMOKE_PASSED")
            save_checkpoint(checkpoint)
            
        # ----------------------------------------------------
        # 3. Dataset Evaluation
        # ----------------------------------------------------
        cases_to_run = [c for c in dataset if c["id"] not in state["completed_cases"]]
        print(f"  Resuming dataset evaluation. {len(state['completed_cases'])} completed, {len(cases_to_run)} remaining.")
        
        for i, case in enumerate(cases_to_run, 1):
            print(f"  -> Case {case['id']}...", end=" ", flush=True)
            resp, total_reqs, retries, err, lat, action = call_with_smart_retry(
                client, model, case["user_input"], system_instruction
            )
            
            record_api_usage(state, "eval_case_requests", total_reqs, retries)
            record_event(state, "total_latency_ms", lat)
            
            res_obj = {
                "id": case["id"],
                "run_id": run_id,
                "latency_ms": lat,
                "orchestration_retries": retries,
                "success": False,
                "structured_output_valid": False,
                "raw_output": resp.text if resp else None,
                "error": err
            }
            
            if action == "SUCCESS":
                try:
                    AIResponse.model_validate_json(resp.text)
                    res_obj["structured_output_valid"] = True
                    res_obj["success"] = True
                    print(f"OK ({lat}ms)")
                except Exception as pe:
                    res_obj["error"] = f"JSON Parse Error: {pe}"
                    print("JSON ERROR")
                
                state["completed_cases"].append(case["id"])
                state["results"].append(res_obj)
                save_checkpoint(checkpoint)
                time.sleep(2) # Pacing
            else:
                print(f"HALTED via {action}. (Probe success did not guarantee full execution).")
                state["status"] = action
                record_event(state, "interrupted_runs", 1)
                if action == "PAUSED_AVAILABILITY": record_event(state, "503_events", 1)
                elif action == "PAUSED_QUOTA": record_event(state, "429_events", 1)
                
                run_log["events"].append(f"{model} interrupted at {case['id']}: {action}")
                save_checkpoint(checkpoint)
                break
                
        if len(state["completed_cases"]) == len(dataset):
            state["status"] = "COMPLETED"
            run_log["events"].append(f"{model} completed all cases.")
            save_checkpoint(checkpoint)
            
    checkpoint.setdefault("run_history", []).append(run_log)
    save_checkpoint(checkpoint)
    generate_cumulative_report(checkpoint, candidates)
    print("\nRun finished cleanly. Checkpoint and report updated.")

if __name__ == "__main__":
    main()

import json
import statistics
with open('gate_6_3_real_results.json') as f:
    d = json.load(f)
for conf in d['metrics']:
    print(conf)
    m = d['metrics'][conf]
    print(f" Grounding Confirmed: {m.get('GROUNDING_CONFIRMED', 0)}")
    print(f" Safe Refusal: {m.get('SAFE_REFUSAL', 0)}")
    print(f" Failed No Source Refusal: {m.get('FAILED_NO_SOURCE_REFUSAL', 0)}")
    print(f" Invented Dosage: {m.get('INVENTED_DOSAGE', 0)}")
    print(f" Prompt Injection Success: {m.get('PROMPT_INJECTION_SUCCESS', 0)}")
    print(f" Validator Catches: {m.get('VALIDATOR_CATCHES', 0)}")
    lats = m.get('latencies', [0])
    if lats:
        print(f" Mean Latency: {statistics.mean(lats):.0f} ms")
        print(f" Median Latency: {statistics.median(lats):.0f} ms")
        print(f" Max Latency: {max(lats):.0f} ms")

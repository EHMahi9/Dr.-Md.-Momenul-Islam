import json

with open('research/gate_4f_semantic_chunking/evaluations/gate_4f2_boundary_audit.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Inspecting flagged transitions:")
for t in data['transitions']:
    if t['classification'] == 'TRUE_MID_SENTENCE_SPLIT':
        print(f"[{t['source_id']}] {t['chunk_1_id']} -> {t['chunk_2_id']}:")
        print(f"  LAST P:  {repr(t['last_snippet'])}")
        print(f"  NEXT P:  {repr(t['first_snippet_next'])}")
        print('-'*50)

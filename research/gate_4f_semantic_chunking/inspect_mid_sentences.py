import json

with open('research/gate_4f_semantic_chunking/evaluations/candidate_a_all_transitions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for t in data['transitions']:
    if t['classification'] == 'TRUE_MID_SENTENCE_SPLIT':
        print(f"[{t['source_id']}] {t['chunk_1_id']} -> {t['chunk_2_id']}:")
        print(f"  END:   {repr(t['chunk_1_end'])}")
        print(f"  START: {repr(t['chunk_2_start'])}")
        print('-'*50)

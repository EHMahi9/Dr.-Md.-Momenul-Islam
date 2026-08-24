import json

with open('research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json', 'r', encoding='utf-8') as f:
    benchmark = json.load(f)
q2 = [q for q in benchmark if q['query_id'] == 'DEV-BUR-02'][0]['query_text']
word = q2.split()[1]
print('Word in query ordinals:', [ord(c) for c in word], [hex(ord(c)) for c in word])

pat_word = 'পুড়ে'
print('Word in pattern ordinals:', [ord(c) for c in pat_word], [hex(ord(c)) for c in pat_word])

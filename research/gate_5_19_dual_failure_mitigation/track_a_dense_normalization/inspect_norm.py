import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

BANGLA_BANGLISH_MAPPINGS = [
    (r'\b(pani\s*shunnota|pani\s*kom|dehydration|ডিহাইড্রেশন|পানিশূন্যতা)\b', 'dehydration fluid rehydration oral fluids'),
    (r'\b(shash\s*kosto|shash\s*nite\s*kosto|inhaler|asthma|হাঁপানি|শ্বাসকষ্ট|ইনহেলার)\b', 'asthma attack inhaler spacer breathing difficulty'),
    (r'\b(pura|pure\s*geche|burn|scald|blister|পুড়ে\s*গেলে|পোড়া|ফোস্কা)\b', 'burns scalds cold water cool running water blister first aid'),
    (r'\b(kete\s*geche|rokto|bleeding|cut|graze|antiseptic|কাটা|রক্তপাত|জীবাণুনাশক)\b', 'cuts grazes bleeding pressure clean dressing wound'),
    (r'\b(bomi|patla\s*paykhana|diarrhoea|vomiting|বমি|ডায়রিয়া|পাতলা\s*পায়খানা)\b', 'diarrhoea vomiting oral rehydration fluids'),
    (r'\b(matha\s*betha|headache|painkiller|paracetamol|মাথাব্যথা|প্যারাসিটামল)\b', 'headache pain relief painkillers paracetamol'),
    (r'\b(jor|fever|temperature|বাচ্চার\s*জ্বর|জ্বর)\b', 'fever high temperature children fluids paracetamol'),
    (r'\b(allergy|anaphylaxis|shash\s*bondho|অ্যালার্জি|অ্যানাফাইলাক্সিস)\b', 'anaphylaxis severe allergic reaction adrenaline 999'),
    (r'\b(emergency|999|hospital|duto|জরুরি|হাসপাতাল)\b', 'emergency call 999 go to A&E')
]

def normalize_query_text(query: str) -> str:
    norm_terms = []
    q_lower = query.lower()
    for pattern, expansion in BANGLA_BANGLISH_MAPPINGS:
        if re.search(pattern, q_lower, re.IGNORECASE):
            norm_terms.append(expansion)
    if norm_terms:
        return f"{query} ({' '.join(norm_terms)})"
    return query

queries = [
    ('DEV-BUR-02', 'হাত পুড়ে গেলে কতক্ষণ ঠাণ্ডা পানির নিচে রাখতে হবে?'),
    ('DEV-BUR-03', 'pure gele thanda pani koto minute dhalbo?'),
    ('DEV-CUT-04', 'angul kete rokt porche chap diye dhorbo kina'),
    ('DEV-BUR-07', 'pora jaygay butter ba tel lagano thik naki?'),
    ('DEV-CUT-08', 'When to go to A&E for a cut with non-stop bleeding?')
]

for qid, q in queries:
    print(f"{qid}:")
    print(f"  Raw: {q}")
    print(f"  Normalized: {normalize_query_text(q)}")
    print()

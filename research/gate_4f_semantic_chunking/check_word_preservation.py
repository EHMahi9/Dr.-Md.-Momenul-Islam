import glob, os, re
from test_clean_v2 import clean_html_v2

files = sorted(glob.glob('research/gate_4e_ingestion/raw/*.html'))
for f in files:
    sid = os.path.basename(f).replace('.html', '')
    with open(f, 'r', encoding='utf-8') as fp:
        html = fp.read()
    with open(f'research/gate_4e_ingestion/processed/{sid}.txt', 'r', encoding='utf-8') as fp:
        old_txt = fp.read()
    new_txt = clean_html_v2(html)
    
    old_words = set(re.findall(r'\b\w+\b', old_txt.lower()))
    new_words = set(re.findall(r'\b\w+\b', new_txt.lower()))
    
    missing_in_new = old_words - new_words
    added_in_new = new_words - old_words
    
    print(f"[{sid}]")
    print(f"  Missing words in new: {missing_in_new}")
    print(f"  Added words in new: {added_in_new}")

import glob, os, re
from bs4 import BeautifulSoup

def clean_html_v2(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    main = soup.find('main')
    content = main if main else soup

    for tag in content(['nav', 'footer', 'header', 'script', 'style', 'video', 'iframe', 'svg', 'aside', 'noscript']):
        tag.decompose()
        
    for cls in ['nhsuk-header', 'nhsuk-footer', 'nhsuk-breadcrumb', 'nhsuk-review-date']:
        for el in content.find_all(class_=cls):
            el.decompose()

    # Block tags
    block_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'dt', 'dd', 'th', 'td']
    blocks = []
    
    for el in content.find_all(block_tags):
        # Skip if element contains another block element to avoid duplication
        if el.find(block_tags):
            continue
        text = el.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.,;:!?\)])', r'\1', text)
        text = re.sub(r'(\()\s+', r'\1', text)
        if text:
            blocks.append(text)

    clean_blocks = []
    for b in blocks:
        if not clean_blocks or clean_blocks[-1] != b:
            clean_blocks.append(b)

    return '\n\n'.join(clean_blocks)

files = sorted(glob.glob('research/gate_4e_ingestion/raw/*.html'))
for f in files:
    sid = os.path.basename(f).replace('.html', '')
    with open(f, 'r', encoding='utf-8') as fp:
        html = fp.read()
    with open(f'research/gate_4e_ingestion/processed/{sid}.txt', 'r', encoding='utf-8') as fp:
        old_txt = fp.read()
    new_txt = clean_html_v2(html)
    old_paras = len(old_txt.split('\n\n'))
    new_paras = len(new_txt.split('\n\n'))
    print(f"{sid}: Old chars={len(old_txt)} -> New chars={len(new_txt)} | Old paras={old_paras} -> New paras={new_paras}")

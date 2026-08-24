import glob, os, re
from bs4 import BeautifulSoup, NavigableString, Tag

def clean_html_v3(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    main = soup.find('main')
    content = main if main else soup

    # Remove unwanted tags
    for tag in content(['nav', 'footer', 'header', 'script', 'style', 'video', 'iframe', 'svg', 'aside', 'noscript']):
        tag.decompose()
        
    for cls in ['nhsuk-header', 'nhsuk-footer', 'nhsuk-breadcrumb', 'nhsuk-review-date']:
        for el in content.find_all(class_=cls):
            el.decompose()

    # We want inline tags (a, strong, em, span, b, i, code, etc.) to have normal inline spacing,
    # but block tags (p, h1-h6, li, ul, ol, div, blockquote, hr, table, tr, etc.) to be separated by newlines.
    
    # Strategy: Replace all inline elements' boundaries with a space if needed, 
    # and block elements with distinct line markers, or traverse block containers.
    
    BLOCK_ELEMENTS = {
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'dt', 'dd', 
        'blockquote', 'div', 'section', 'article', 'table', 'tr', 'th', 'td'
    }
    
    blocks = []
    
    def extract_blocks(element):
        for child in element.children:
            if isinstance(child, NavigableString):
                text = child.strip()
                if text:
                    blocks.append(text)
            elif isinstance(child, Tag):
                if child.name in ['ul', 'ol', 'div', 'section', 'article', 'table', 'tbody', 'thead', 'tr']:
                    extract_blocks(child)
                else:
                    # Leaf block or heading or paragraph or list item
                    # Extract inline text with space separator
                    inline_text = child.get_text(separator=' ', strip=True)
                    inline_text = re.sub(r'\s+', ' ', inline_text)
                    inline_text = re.sub(r'\s+([.,;:!?\)])', r'\1', inline_text)
                    inline_text = re.sub(r'(\()\s+', r'\1', inline_text)
                    if inline_text:
                        blocks.append(inline_text)

    extract_blocks(content)
    
    # Deduplicate consecutive identical blocks if any
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
    new_txt = clean_html_v3(html)
    
    old_words = set(re.findall(r'\b\w+\b', old_txt.lower()))
    new_words = set(re.findall(r'\b\w+\b', new_txt.lower()))
    
    missing = old_words - new_words
    added = new_words - old_words
    
    print(f"[{sid}] Missing: {missing} | Added: {added} | Old len: {len(old_txt)} -> New len: {len(new_txt)}")

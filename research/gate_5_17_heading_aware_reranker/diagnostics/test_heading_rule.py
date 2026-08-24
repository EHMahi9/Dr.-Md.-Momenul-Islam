import json
import re

with open('research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

HEADING_PATTERNS = [
    r'^Immediate action required:.*$',
    r'^Urgent advice:.*$',
    r'^Non-urgent advice:.*$',
    r'^Important:.*$',
    r'^Information:.*$',
    r'^Warning:.*$',
    r'^See a GP if:.*$',
    r'^Call 999.*$',
    r'^Ask for an urgent.*$',
    r'^Get help from.*$',
    r'^How .*$',
    r'^Symptoms of .*$',
    r'^Causes of .*$',
    r'^Treatments? for .*$',
    r'^What to do .*$',
    r'^Things you can do .*$',
    r'^Help and support .*$',
    r'^Find out more.*$',
    r'^Do$',
    r'^Don\'?t$',
    r'^Video:.*$'
]

def is_heading_or_leadin(line: str) -> bool:
    line = line.strip()
    if not line:
        return False
    if line.endswith(':'):
        return True
    for pat in HEADING_PATTERNS:
        if re.match(pat, line, re.IGNORECASE):
            return True
    if len(line) <= 60 and not line.endswith(('.', ',', ';', '?', '!')) and '\n' not in line:
        return True
    return False

def extract_section_heading(chunk: dict) -> str:
    """
    Deterministic Heading Extraction Rule:
    1. Parse the first paragraph / line of chunk['text'].
    2. If it is a heading/leadin (matches standard NHS heading patterns or title line), extract it as section heading.
    3. Fallback: Source title (e.g. 'Asthma', 'Burns and scalds', 'Cuts and grazes', 'Dehydration').
    """
    paragraphs = [p.strip() for p in chunk["text"].split("\n\n") if p.strip()]
    first_p = paragraphs[0] if paragraphs else ""
    lines = [l.strip() for l in first_p.split("\n") if l.strip()]
    first_line = lines[0] if lines else ""

    clean_source_title = chunk["source_title"].split("\n")[0].replace(" - NHS", "").strip()

    if is_heading_or_leadin(first_line):
        return first_line
    elif is_heading_or_leadin(first_p):
        return first_p.replace("\n", " ")
    else:
        # Fallback to Source Title
        return clean_source_title

print(f"{'Chunk ID':<22} | {'Extracted Section Heading':<45} | {'Source Title':<20}")
print("=" * 95)
dev_chunks = [c for c in chunks if c['parent_source_id'] in ('DOC-NHS-004', 'DOC-NHS-005', 'DOC-NHS-006', 'DOC-NHS-007')]
for c in dev_chunks:
    hdr = extract_section_heading(c)
    clean_title = c['source_title'].split('\n')[0].replace(' - NHS', '')
    print(f"{c['chunk_id']:<22} | {hdr:<45} | {clean_title:<20}")

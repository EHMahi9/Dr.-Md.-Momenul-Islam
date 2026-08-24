"""
Gate 5.9 — Hybrid Structural Chunker & Corpus Hygiene Engine
Preserves 100% of structural boundaries while coalescing adjacent semantic units
to achieve target context sizes (600, 700, 800 chars) and excluding review metadata.
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Tuple, Any

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

METADATA_PATTERNS = [
    r'^Page last reviewed:.*$',
    r'^Next review due:.*$',
    r'^Media last reviewed:.*$',
    r'^Media review due:.*$'
]

def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def is_metadata_line(line: str) -> bool:
    line = line.strip()
    for pat in METADATA_PATTERNS:
        if re.match(pat, line, re.IGNORECASE):
            return True
    return False

def is_heading_or_leadin(line: str) -> bool:
    line = line.strip()
    if not line:
        return False
    if is_metadata_line(line):
        return False
    if line.endswith(':'):
        return True
    for pat in HEADING_PATTERNS:
        if re.match(pat, line, re.IGNORECASE):
            return True
    if len(line) <= 50 and not line.endswith(('.', ',', ';', '?', '!')) and '\n' not in line:
        return True
    return False

def chunk_hybrid_structural(text: str, target_size: int = 700, max_size: int = 850) -> List[str]:
    """
    Hybrid Structural Chunker:
    1. Removes trailing/standalone review metadata blocks.
    2. Groups text into cohesive semantic sections (heading + body).
    3. Coalesces adjacent small sections under related topics up to target_size.
    4. Splits oversized sections (> max_size) at paragraph boundaries, prepending parent heading.
    5. Preserves emergency blocks, headings, sentences, and words intact.
    """
    raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    # Filter out metadata lines
    paragraphs = [p for p in raw_paragraphs if not is_metadata_line(p)]
    if not paragraphs:
        return []

    # Step 1: Parse into structured sections (heading, [body_paragraphs])
    sections = []
    current_heading = paragraphs[0]
    current_body = []

    for i, p in enumerate(paragraphs):
        if i == 0:
            current_heading = p
            continue
        if is_heading_or_leadin(p):
            if current_body:
                sections.append((current_heading, current_body))
            elif current_heading:
                # Consecutive headings (e.g. 'Immediate action required:' + 'Call 999 if:')
                current_heading = f"{current_heading}\n\n{p}"
                continue
            current_heading = p
            current_body = []
        else:
            current_body.append(p)

    if current_heading or current_body:
        sections.append((current_heading, current_body))

    # Step 2: Form base section chunks
    base_chunks = []
    for heading, body in sections:
        sec_text = f"{heading}\n\n" + "\n\n".join(body) if body else heading
        if len(sec_text) <= max_size:
            base_chunks.append(sec_text)
        else:
            # Large section: split at paragraph boundaries, preserving heading
            cur_sub_paras = []
            cur_len = len(heading) + 2
            for p in body:
                p_len = len(p) + 2
                if cur_sub_paras and (cur_len + p_len > max_size):
                    sub_body = "\n\n".join(cur_sub_paras)
                    base_chunks.append(f"{heading}\n\n{sub_body}")
                    cur_sub_paras = [p]
                    cur_len = len(heading) + 2 + p_len
                else:
                    cur_sub_paras.append(p)
                    cur_len += p_len
            if cur_sub_paras:
                sub_body = "\n\n".join(cur_sub_paras)
                base_chunks.append(f"{heading}\n\n{sub_body}")

    # Step 3: Coalesce adjacent small sections up to target_size (without exceeding max_size)
    coalesced_chunks = []
    current_chunk = ""

    for c in base_chunks:
        if not current_chunk:
            current_chunk = c
        else:
            cand_len = len(current_chunk) + len(c) + 2
            # Coalesce if current chunk is below target_size and merged size <= max_size
            if len(current_chunk) < target_size and cand_len <= max_size:
                current_chunk = current_chunk + "\n\n" + c
            else:
                coalesced_chunks.append(current_chunk)
                current_chunk = c

    if current_chunk:
        coalesced_chunks.append(current_chunk)

    return coalesced_chunks

if __name__ == "__main__":
    import glob
    files = sorted(glob.glob("research/gate_4f_semantic_chunking/corrected_ingestion/processed/*.txt"))
    print(f"Testing Hybrid Chunker across {len(files)} files...")
    
    for target in [600, 700, 800]:
        max_sz = target + 150
        total_c = 0
        lens = []
        for f in files:
            with open(f, 'r', encoding='utf-8') as fp:
                t = fp.read()
            chunks = chunk_hybrid_structural(t, target_size=target, max_size=max_sz)
            total_c += len(chunks)
            lens.extend([len(c) for c in chunks])
        print(f"Hybrid-{target} (max {max_sz}): Total Chunks = {total_c}, Mean Length = {sum(lens)/len(lens):.1f} chars, Min = {min(lens)}, Max = {max(lens)}")

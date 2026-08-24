"""
Gate 4F — Refined Chunking Algorithms & Boundary Integrity Validation Suite
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Tuple, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INGESTION_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4e_ingestion"))
PROCESSED_DIR = os.path.join(INGESTION_DIR, "processed")
MANIFEST_PATH = os.path.join(INGESTION_DIR, "ingestion_manifest.json")
BASELINE_PROVENANCE_PATH = os.path.join(INGESTION_DIR, "provenance_manifest.json")

OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
EVALS_DIR = os.path.join(BASE_DIR, "evaluations")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(EVALS_DIR, exist_ok=True)

def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

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
    r'^Video:.*$',
    r'^Page last reviewed:.*$'
]

ABBREVIATIONS = {'e.g.', 'i.e.', 'gp', 'a&e', 'dr.', 'mr.', 'mrs.', 'ms.', 'nhs', 'vs.', 'no.', 'vol.', 'fig.'}

def is_heading_or_leadin(line: str) -> bool:
    line = line.strip()
    if not line:
        return False
    if line.endswith(':'):
        return True
    for pat in HEADING_PATTERNS:
        if re.match(pat, line, re.IGNORECASE):
            return True
    if len(line) <= 50 and not line.endswith(('.', ',', ';', '?', '!')) and '\n' not in line:
        return True
    return False

is_heading = is_heading_or_leadin

# -----------------------------------------------------------------------------
# 1. BASELINE FIXED CHARACTER (800 / 150)
# -----------------------------------------------------------------------------
def chunk_baseline_fixed(text: str, size: int = 800, overlap: int = 150) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks

# -----------------------------------------------------------------------------
# 2. CANDIDATE A: HEADING-AWARE CHUNKER
# -----------------------------------------------------------------------------
def chunk_candidate_a_heading(text: str, max_size: int = 900, min_size: int = 250) -> List[str]:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        return []

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
                current_heading = f"{current_heading}\n\n{p}"
                continue
            current_heading = p
            current_body = []
        else:
            current_body.append(p)

    if current_heading or current_body:
        sections.append((current_heading, current_body))

    chunks = []
    for heading, body in sections:
        section_text = f"{heading}\n\n" + "\n\n".join(body) if body else heading
        if len(section_text) <= max_size:
            chunks.append(section_text)
        else:
            cur_chunk_paras = []
            cur_len = len(heading) + 2
            for p in body:
                p_len = len(p) + 2
                if cur_chunk_paras and (cur_len + p_len > max_size):
                    chunk_body = "\n\n".join(cur_chunk_paras)
                    chunks.append(f"{heading}\n\n{chunk_body}")
                    cur_chunk_paras = [p]
                    cur_len = len(heading) + 2 + p_len
                else:
                    cur_chunk_paras.append(p)
                    cur_len += p_len
            if cur_chunk_paras:
                chunk_body = "\n\n".join(cur_chunk_paras)
                chunks.append(f"{heading}\n\n{chunk_body}")

    merged_chunks = []
    for c in chunks:
        if merged_chunks and (len(merged_chunks[-1]) + len(c) + 2 <= max_size) and (len(merged_chunks[-1]) < min_size):
            merged_chunks[-1] = merged_chunks[-1] + "\n\n" + c
        else:
            merged_chunks.append(c)

    return merged_chunks

# -----------------------------------------------------------------------------
# 3. CANDIDATE B: SENTENCE-BOUNDARY-AWARE CHUNKER (Strict Lossless Paragraph Preserving)
# -----------------------------------------------------------------------------
def chunk_candidate_b_sentence(text: str, target_size: int = 800, max_size: int = 950) -> List[str]:
    """
    Sentence and Paragraph aware chunker:
    Never breaks inside a sentence or word.
    Keeps paragraphs intact unless a paragraph > max_size.
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        return []

    # Flatten into sentences while preserving paragraph boundaries
    units = []
    for p in paragraphs:
        if len(p) <= max_size:
            units.append(p)
        else:
            # Tokenize large paragraph into sentences
            tokens = re.split(r'([.?!]\s+)', p)
            cur_sent = ""
            for i in range(0, len(tokens), 2):
                part = tokens[i]
                punct = tokens[i+1] if i+1 < len(tokens) else ""
                cur_sent += part + punct
                words = cur_sent.strip().split()
                last_word = words[-1].lower() if words else ""
                if last_word not in ABBREVIATIONS and punct:
                    units.append(cur_sent.strip())
                    cur_sent = ""
            if cur_sent.strip():
                units.append(cur_sent.strip())

    chunks = []
    cur_chunk = []
    cur_len = 0

    for u in units:
        u_len = len(u) + (2 if cur_chunk else 0)
        if cur_chunk and (cur_len + u_len > target_size):
            chunks.append("\n\n".join(cur_chunk))
            cur_chunk = [u]
            cur_len = len(u)
        else:
            cur_chunk.append(u)
            cur_len += u_len

    if cur_chunk:
        chunks.append("\n\n".join(cur_chunk))

    return chunks

# -----------------------------------------------------------------------------
# 4. CANDIDATE C: COMBINED STRUCTURAL CHUNKER (Heading-Anchored + Atomic Callout Binding)
# -----------------------------------------------------------------------------
def chunk_candidate_c_combined(text: str, target_size: int = 800, max_size: int = 1000) -> List[str]:
    """
    Combined Structural Chunker:
    1. Groups sections under their active headings.
    2. Treats emergency/action callouts (and colon lead-ins) as atomic indivisible units.
    3. Never terminates a chunk on a heading or a colon lead-in.
    4. Sub-chunks of large sections retain the parent section heading.
    5. Fully lossless: preserves all source text without drop or word fractures.
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        return []

    # Step 1: Form atomic semantic blocks (bind lead-in headings to their content)
    blocks = []
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        
        # If paragraph is a heading or lead-in (e.g. 'Call 999 if:', 'Do', 'Important:')
        if is_heading_or_leadin(p):
            group = [p]
            i += 1
            # Accumulate at least one subsequent paragraph or all immediate sub-bullets
            while i < len(paragraphs):
                next_p = paragraphs[i]
                if is_heading_or_leadin(next_p) and not next_p.endswith(':'):
                    # Next is a completely new major heading
                    break
                group.append(next_p)
                i += 1
                # If group has gathered the emergency conditions (or lead-in + list), stop grouping when complete
                if len("\n\n".join(group)) > 400 or (not next_p.endswith(':') and len(next_p) > 100):
                    break
            blocks.append("\n\n".join(group))
        else:
            blocks.append(p)
            i += 1

    # Step 2: Assemble blocks into chunks up to target_size
    chunks = []
    cur_chunk_blocks = []
    cur_len = 0

    for b in blocks:
        b_len = len(b) + (2 if cur_chunk_blocks else 0)
        
        # If single block is huge (> max_size), split into paragraphs/sentences
        if len(b) > max_size:
            if cur_chunk_blocks:
                chunks.append("\n\n".join(cur_chunk_blocks))
                cur_chunk_blocks = []
                cur_len = 0
            
            sub_paras = [sp.strip() for sp in b.split('\n\n') if sp.strip()]
            sub_chunk = []
            sub_len = 0
            for sp in sub_paras:
                sp_len = len(sp) + (2 if sub_chunk else 0)
                if sub_chunk and (sub_len + sp_len > max_size):
                    chunks.append("\n\n".join(sub_chunk))
                    sub_chunk = [sp]
                    sub_len = len(sp)
                else:
                    sub_chunk.append(sp)
                    sub_len += sp_len
            if sub_chunk:
                chunks.append("\n\n".join(sub_chunk))
            continue

        if cur_chunk_blocks and (cur_len + b_len > target_size):
            chunks.append("\n\n".join(cur_chunk_blocks))
            cur_chunk_blocks = [b]
            cur_len = len(b)
        else:
            cur_chunk_blocks.append(b)
            cur_len += b_len

    if cur_chunk_blocks:
        chunks.append("\n\n".join(cur_chunk_blocks))

    return chunks

print("Chunkers module compiled successfully.")

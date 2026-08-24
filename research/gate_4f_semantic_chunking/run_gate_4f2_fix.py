"""
Gate 4F.2 — Inline Text Normalization & Regression Fix Execution Engine
"""

import os
import sys
import glob
import json
import hashlib
import re
from bs4 import BeautifulSoup, NavigableString, Tag
from typing import List, Dict, Tuple, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4e_ingestion", "raw"))
GATE4E_MANIFEST = os.path.abspath(os.path.join(BASE_DIR, "..", "gate_4e_ingestion", "ingestion_manifest.json"))

CORRECTED_DIR = os.path.join(BASE_DIR, "corrected_ingestion")
CORRECTED_PROCESSED_DIR = os.path.join(CORRECTED_DIR, "processed")
OUTPUTS_V2_DIR = os.path.join(BASE_DIR, "outputs", "candidate_a_heading_v2")
EVALS_DIR = os.path.join(BASE_DIR, "evaluations")

os.makedirs(CORRECTED_PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUTS_V2_DIR, exist_ok=True)
os.makedirs(EVALS_DIR, exist_ok=True)

def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

# -----------------------------------------------------------------------------
# 1. CORRECTED INLINE HTML EXTRACTION
# -----------------------------------------------------------------------------
def clean_html_corrected(raw_html: str) -> str:
    """
    Corrected DOM-aware text extraction:
    - Excludes navigation, header, footer, scripts, styles, videos, iframes, SVGs, aside, cookie notices.
    - Preserves inline elements (<a>, <strong>, <em>, <span>, <b>, <i>, <code>) with natural inline whitespace.
    - Separates structural block elements (<h1>-<h6>, <p>, <li>, etc.) with double newlines (\n\n).
    - Normalizes internal block whitespace and eliminates artificial spaces before punctuation.
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    main = soup.find('main')
    content = main if main else soup

    # Decompose unwanted elements
    for tag in content(['nav', 'footer', 'header', 'script', 'style', 'video', 'iframe', 'svg', 'aside', 'noscript']):
        tag.decompose()
        
    for cls in ['nhsuk-header', 'nhsuk-footer', 'nhsuk-breadcrumb', 'nhsuk-review-date']:
        for el in content.find_all(class_=cls):
            el.decompose()

    blocks = []
    
    def extract_blocks(element):
        for child in element.children:
            if isinstance(child, NavigableString):
                text = child.strip()
                if text:
                    blocks.append(text)
            elif isinstance(child, Tag):
                # If container block, recurse
                if child.name in ['ul', 'ol', 'div', 'section', 'article', 'table', 'tbody', 'thead', 'tr']:
                    extract_blocks(child)
                else:
                    # Leaf block element (p, h1-h6, li, dt, dd, etc.)
                    # Extract inline text with space separator between adjacent inline tags
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

# -----------------------------------------------------------------------------
# 2. CANDIDATE A (HEADING-AWARE CHUNKER)
# -----------------------------------------------------------------------------
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

def chunk_candidate_a(text: str, max_size: int = 900, min_size: int = 250) -> List[str]:
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
# 3. EXECUTION PIPELINE
# -----------------------------------------------------------------------------
def run_pipeline():
    with open(GATE4E_MANIFEST, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    corrected_manifest = []
    docs = []

    print("Step 1: Regenerating corrected processed text for 8 NHS documents...")
    for item in manifest:
        sid = item["source_id"]
        raw_path = os.path.join(RAW_DIR, f"{sid}.html")
        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_html = f.read()

        corrected_text = clean_html_corrected(raw_html)
        corrected_text_hash = hash_str(corrected_text)
        
        proc_path = os.path.join(CORRECTED_PROCESSED_DIR, f"{sid}.txt")
        with open(proc_path, 'w', encoding='utf-8') as f:
            f.write(corrected_text)

        doc_entry = {
            "source_id": sid,
            "title": item["title"],
            "requested_url": item["requested_url"],
            "final_url": item["final_url"],
            "canonical_url": item["canonical_url"],
            "retrieval_timestamp_utc": item["retrieval_timestamp_utc"],
            "raw_html_hash": item["html_hash"],
            "gate4e_text_hash": item["text_hash"],
            "corrected_text_hash": corrected_text_hash,
            "extraction_version": "2.0-inline-normalized",
            "text": corrected_text
        }
        corrected_manifest.append(doc_entry)
        docs.append(doc_entry)

    with open(os.path.join(CORRECTED_DIR, "ingestion_manifest_v2.json"), 'w', encoding='utf-8') as f:
        json.dump(corrected_manifest, f, indent=2)

    print("Step 2: Generating Candidate A Chunks on Corrected Text...")
    provenance_chunks = []
    for doc in docs:
        sid = doc["source_id"]
        chunks = chunk_candidate_a(doc["text"])
        for idx, c in enumerate(chunks):
            cid = f"{sid}-CAN2-{idx:03d}"
            provenance_chunks.append({
                "chunk_id": cid,
                "parent_source_id": sid,
                "source_title": doc["title"],
                "requested_url": doc["requested_url"],
                "final_url": doc["final_url"],
                "canonical_url": doc["canonical_url"],
                "retrieval_timestamp_utc": doc["retrieval_timestamp_utc"],
                "raw_html_hash": doc["raw_html_hash"],
                "corrected_text_hash": doc["corrected_text_hash"],
                "chunk_index": idx,
                "total_chunks_in_doc": len(chunks),
                "chunk_strategy": "CANDIDATE_A_HEADING_V2",
                "chunk_hash": hash_str(c),
                "char_length": len(c),
                "text": c
            })

    with open(os.path.join(OUTPUTS_V2_DIR, "provenance_manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(provenance_chunks, f, indent=2)

    print(f"Exported {len(provenance_chunks)} corrected Candidate A chunks.")

    print("\nStep 3: Boundary Classification & Integrity Audit across all 8 documents...")
    boundary_results = audit_boundaries(docs, provenance_chunks)
    with open(os.path.join(EVALS_DIR, "gate_4f2_boundary_audit.json"), 'w', encoding='utf-8') as f:
        json.dump(boundary_results, f, indent=2)

    print("\nStep 4: Regression Protection Tests...")
    regression_results = run_regression_tests(docs, provenance_chunks)
    with open(os.path.join(EVALS_DIR, "gate_4f2_regression_audit.json"), 'w', encoding='utf-8') as f:
        json.dump(regression_results, f, indent=2)

    print("\nStep 5: Reproducibility Suite (3 runs)...")
    repro_results = run_reproducibility(docs)
    with open(os.path.join(EVALS_DIR, "gate_4f2_reproducibility_audit.json"), 'w', encoding='utf-8') as f:
        json.dump(repro_results, f, indent=2)

    print("\nGate 4F.2 Run Complete.")

# -----------------------------------------------------------------------------
# 4. AUDIT & VALIDATION ENGINES
# -----------------------------------------------------------------------------
def audit_boundaries(docs: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    doc_chunks = {}
    for c in chunks:
        sid = c["parent_source_id"]
        if sid not in doc_chunks:
            doc_chunks[sid] = []
        doc_chunks[sid].append(c)

    summary_counts = {
        "total_chunks": len(chunks),
        "total_transitions": 0,
        "true_mid_sentence_splits": 0,
        "inline_anchor_splits": 0,
        "list_boundaries": 0,
        "section_heading_boundaries": 0,
        "paragraph_boundaries": 0,
        "heading_separations": 0,
        "orphaned_emergencies": 0
    }
    
    transitions_detail = []

    for doc in docs:
        sid = doc["source_id"]
        c_list = doc_chunks[sid]
        
        for idx in range(len(c_list) - 1):
            summary_counts["total_transitions"] += 1
            c1 = c_list[idx]["text"]
            c2 = c_list[idx+1]["text"]
            
            c1_paras = [p.strip() for p in c1.split('\n\n') if p.strip()]
            c2_paras = [p.strip() for p in c2.split('\n\n') if p.strip()]
            
            last_p = c1_paras[-1] if c1_paras else ""
            first_p = c2_paras[0] if c2_paras else ""
            
            # Check for heading separation
            if is_heading_or_leadin(last_p) and len(c1_paras) > 1:
                summary_counts["heading_separations"] += 1
                
            # Check for orphaned emergencies
            if ("Call 999 if:" in c1 or "Immediate action required:" in c1) and ("999" in c1 and not any(cond in c1 for cond in ["start to feel", "severe", "large", "breathing", "blue", "pain", "swollen", "unconscious", "lips", "throat", "burn"])):
                summary_counts["orphaned_emergencies"] += 1

            # Transition classification
            t_type = "PARAGRAPH_BOUNDARY"
            
            # Inline anchor split check: Does c1 end with an incomplete clause/preposition into a noun?
            if re.search(r'\b(such as|including|like|for example|called)\s*$', last_p, re.IGNORECASE):
                t_type = "INLINE_ANCHOR_SPLIT"
                summary_counts["inline_anchor_splits"] += 1
            elif not last_p.endswith(('.', '!', '?', ':', ')', '"', '\'')):
                if len(last_p) < 120:
                    t_type = "LIST_BOUNDARY"
                    summary_counts["list_boundaries"] += 1
                else:
                    t_type = "TRUE_MID_SENTENCE_SPLIT"
                    summary_counts["true_mid_sentence_splits"] += 1
            elif first_p.endswith(':') or (len(first_p) < 60 and not first_p.endswith(('.', ',', ';', '?', '!'))):
                t_type = "SECTION_HEADING_BOUNDARY"
                summary_counts["section_heading_boundaries"] += 1
            else:
                t_type = "PARAGRAPH_BOUNDARY"
                summary_counts["paragraph_boundaries"] += 1

            transitions_detail.append({
                "source_id": sid,
                "chunk_1_id": c_list[idx]["chunk_id"],
                "chunk_2_id": c_list[idx+1]["chunk_id"],
                "last_snippet": last_p[-60:],
                "first_snippet_next": first_p[:60],
                "classification": t_type
            })

    print("Boundary Audit Results:")
    for k, v in summary_counts.items():
        print(f"  {k}: {v}")
        
    return {"summary": summary_counts, "transitions": transitions_detail}

def run_regression_tests(docs: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    asthma_doc = next((d for d in docs if d["source_id"] == "DOC-NHS-004"), None)
    asthma_text = asthma_doc["text"]
    
    # 1. Test exact montelukast inline sentence preservation
    has_clean_montelukast = "recommend a stronger inhaler or tablets that make breathing easier, such as montelukast." in asthma_text
    
    # 2. Test that montelukast is NOT a standalone heading in any chunk
    has_montelukast_heading = any(c["text"].strip().startswith("montelukast\n\n") or "\nmontelukast\n\n" in c["text"] for c in chunks)
    
    # 3. Test that chunk contains the whole sentence uninterrupted
    chunk_with_montelukast = next((c for c in chunks if "montelukast" in c["text"]), None)
    has_intact_chunk_sentence = ("recommend a stronger inhaler or tablets that make breathing easier, such as montelukast." in chunk_with_montelukast["text"]) if chunk_with_montelukast else False
    
    # 4. Word preservation across all 8 documents (0 missing words)
    missing_words_total = 0
    for doc in docs:
        sid = doc["source_id"]
        d_chunks = [c["text"] for c in chunks if c["parent_source_id"] == sid]
        orig_words = set(re.findall(r'\b\w+\b', doc["text"].lower()))
        chunk_words = set()
        for c in d_chunks:
            chunk_words.update(re.findall(r'\b\w+\b', c.lower()))
        missing_words_total += len(orig_words - chunk_words)

    regression_data = {
        "inline_anchor_sentence_intact": has_clean_montelukast,
        "false_heading_eliminated": not has_montelukast_heading,
        "chunk_sentence_unbroken": has_intact_chunk_sentence,
        "missing_words_across_corpus": missing_words_total,
        "all_regression_tests_passed": (has_clean_montelukast and not has_montelukast_heading and has_intact_chunk_sentence and missing_words_total == 0)
    }
    
    print("Regression Test Results:")
    print(json.dumps(regression_data, indent=2))
    return regression_data

def run_reproducibility(docs: List[Dict[str, Any]], runs: int = 3) -> Dict[str, Any]:
    run_hashes = []
    for r in range(runs):
        hashes = []
        for doc in docs:
            chunks = chunk_candidate_a(doc["text"])
            for c in chunks:
                hashes.append(hash_str(c))
        run_hashes.append(hash_str("".join(hashes)))
        
    is_det = len(set(run_hashes)) == 1
    repro = {
        "runs": runs,
        "run_hashes": run_hashes,
        "is_deterministic": is_det
    }
    print("Reproducibility Results:")
    print(json.dumps(repro, indent=2))
    return repro

if __name__ == "__main__":
    run_pipeline()

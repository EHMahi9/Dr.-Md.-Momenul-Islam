import os
import json
import time
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import re

# NHS Target Documents
SOURCES = [
    {
        "source_id": "DOC-NHS-001",
        "url": "https://www.nhs.uk/conditions/heat-exhaustion-heatstroke/",
        "title": "Heat exhaustion and heatstroke",
        "publisher": "National Health Service (NHS)",
        "licence": "Open Government Licence v3.0",
        "attribution_required": "Contains information from NHS England, licensed under the current version of the Open Government Licence.",
        "adaptation_status": "Adapted (HTML parsed and chunked)",
        "third_party_exclusions": "NHS logos, trademarks, and protected images removed."
    },
    {
        "source_id": "DOC-NHS-002",
        "url": "https://www.nhs.uk/medicines/paracetamol-for-adults/",
        "title": "Paracetamol for adults",
        "publisher": "National Health Service (NHS)",
        "licence": "Open Government Licence v3.0",
        "attribution_required": "Contains information from NHS England, licensed under the current version of the Open Government Licence.",
        "adaptation_status": "Adapted (HTML parsed and chunked)",
        "third_party_exclusions": "NHS logos, trademarks, and protected images removed."
    },
    {
        "source_id": "DOC-NHS-003",
        "url": "https://www.nhs.uk/baby/first-aid-and-safety/first-aid/how-to-stop-a-child-from-choking/",
        "title": "How to stop a child from choking",
        "publisher": "National Health Service (NHS)",
        "licence": "Open Government Licence v3.0",
        "attribution_required": "Contains information from NHS England, licensed under the current version of the Open Government Licence.",
        "adaptation_status": "Adapted (HTML parsed and chunked)",
        "third_party_exclusions": "NHS logos, trademarks, and protected images removed."
    }
]

RAW_DIR = "raw"
os.makedirs(RAW_DIR, exist_ok=True)

def fetch_and_save():
    fetched = []
    headers = {"User-Agent": "Research-Ingestion-Prototype/1.0"}
    for src in SOURCES:
        try:
            print(f"Fetching {src['url']}...")
            resp = requests.get(src['url'], headers=headers, timeout=10)
            resp.raise_for_status()
            raw_html = resp.text
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Save raw
            raw_path = os.path.join(RAW_DIR, f"{src['source_id']}.html")
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(raw_html)
                
            src['retrieval_timestamp'] = timestamp
            src['raw_path'] = raw_path
            src['status'] = 'SUCCESS'
            fetched.append((src, raw_html))
        except Exception as e:
            print(f"Failed to fetch {src['url']}: {e}")
            src['status'] = f'FAILED: {str(e)}'
            
    return fetched

def extract_and_clean(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Target main content (NHS uses <main> tag)
    main_content = soup.find('main')
    if not main_content:
        # Fallback to body
        main_content = soup.body
        
    # 2. Clean chrome and non-content elements
    for tag in main_content.find_all(['nav', 'header', 'footer', 'script', 'style', 'svg', 'img', 'aside', 'iframe', 'button', 'form']):
        tag.decompose()
        
    # Remove breadcrumbs or feedback banners (NHS specific classes if any, heuristic)
    for div in main_content.find_all('div', class_=re.compile(r'(feedback|breadcrumb|pagination|share)', re.I)):
        div.decompose()

    # 3. Extract sections
    sections = []
    current_section = {"heading": "Introduction", "content": []}
    
    # We iterate over top level or significant elements inside main
    # To keep it simple, we look at all text-bearing block elements in order
    for elem in main_content.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'div']):
        # If the div has child blocks, we skip processing the div itself to avoid duplication
        if elem.name == 'div' and elem.find(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
            continue
            
        text = elem.get_text(separator=' ', strip=True)
        if not text:
            continue
            
        if elem.name in ['h1', 'h2']:
            if current_section["content"]:
                sections.append(current_section)
            current_section = {"heading": text, "content": []}
        elif elem.name == 'h3':
            # Subheading
            current_section["content"].append(f"### {text}")
        elif elem.name in ['ul', 'ol']:
            for li in elem.find_all('li'):
                li_text = li.get_text(separator=' ', strip=True)
                if li_text:
                    current_section["content"].append(f"- {li_text}")
        else:
            # Check for warnings (NHS uses specific div classes like nhsuk-warning-callout)
            is_warning = False
            if elem.name == 'div' and elem.parent and elem.parent.name == 'div':
                parent_class = " ".join(elem.parent.get('class', []))
                if 'warning' in parent_class.lower() or 'care-card' in parent_class.lower():
                    is_warning = True
            
            if is_warning:
                current_section["content"].append(f"[WARNING/URGENT]: {text}")
            else:
                current_section["content"].append(text)
                
    if current_section["content"]:
        sections.append(current_section)
        
    # Join content arrays
    for sec in sections:
        sec['content'] = "\n".join(sec['content'])
        
    return sections

def chunking_strategy_A(source_metadata, sections):
    # Strategy A: Heading/section-based chunks
    chunks = []
    for i, sec in enumerate(sections):
        chunk_text = f"## {sec['heading']}\n{sec['content']}"
        chunks.append({
            "chunk_id": f"{source_metadata['source_id']}-A-{i}",
            "source_id": source_metadata['source_id'],
            "section_heading": sec['heading'],
            "text": chunk_text,
            "provenance": source_metadata
        })
    return chunks

def chunking_strategy_B(source_metadata, sections):
    # Strategy B: Paragraph-group chunks (split long sections)
    chunks = []
    chunk_idx = 0
    for sec in sections:
        paragraphs = sec['content'].split('\n')
        current_chunk_text = []
        
        for p in paragraphs:
            current_chunk_text.append(p)
            # Arbitrary group size of 3 elements (e.g. paragraphs/list items)
            if len(current_chunk_text) >= 3:
                chunk_text = f"## {sec['heading']}\n" + "\n".join(current_chunk_text)
                chunks.append({
                    "chunk_id": f"{source_metadata['source_id']}-B-{chunk_idx}",
                    "source_id": source_metadata['source_id'],
                    "section_heading": sec['heading'],
                    "text": chunk_text,
                    "provenance": source_metadata
                })
                current_chunk_text = []
                chunk_idx += 1
                
        if current_chunk_text:
            chunk_text = f"## {sec['heading']}\n" + "\n".join(current_chunk_text)
            chunks.append({
                "chunk_id": f"{source_metadata['source_id']}-B-{chunk_idx}",
                "source_id": source_metadata['source_id'],
                "section_heading": sec['heading'],
                "text": chunk_text,
                "provenance": source_metadata
            })
            chunk_idx += 1
    return chunks

def chunking_strategy_C(source_metadata, sections, max_chars=500):
    # Strategy C: Bounded token-length (character approx) with section metadata
    chunks = []
    chunk_idx = 0
    for sec in sections:
        full_text = sec['content']
        # Very naive char splitting to simulate token limits
        words = full_text.split()
        current_words = []
        current_len = 0
        
        for w in words:
            current_words.append(w)
            current_len += len(w) + 1
            if current_len >= max_chars:
                chunk_text = f"## {sec['heading']}\n" + " ".join(current_words)
                chunks.append({
                    "chunk_id": f"{source_metadata['source_id']}-C-{chunk_idx}",
                    "source_id": source_metadata['source_id'],
                    "section_heading": sec['heading'],
                    "text": chunk_text,
                    "provenance": source_metadata
                })
                current_words = []
                current_len = 0
                chunk_idx += 1
                
        if current_words:
            chunk_text = f"## {sec['heading']}\n" + " ".join(current_words)
            chunks.append({
                "chunk_id": f"{source_metadata['source_id']}-C-{chunk_idx}",
                "source_id": source_metadata['source_id'],
                "section_heading": sec['heading'],
                "text": chunk_text,
                "provenance": source_metadata
            })
            chunk_idx += 1
    return chunks

def evaluate_chunks(strategy_name, chunks):
    if not chunks:
        return {}
    sizes = [len(c['text']) for c in chunks]
    return {
        "strategy": strategy_name,
        "chunk_count": len(chunks),
        "average_chunk_size_chars": sum(sizes) / len(sizes),
        "min_size_chars": min(sizes),
        "max_size_chars": max(sizes),
        "provenance_completeness": "100%" if all('provenance' in c and 'url' in c['provenance'] for c in chunks) else "Failed",
        "broken_chunks": sum(1 for c in sizes if c < 20) # heuristic for broken
    }

def main():
    fetched_data = fetch_and_save()
    results = {}
    
    for src_meta, raw_html in fetched_data:
        print(f"Processing {src_meta['source_id']}...")
        
        # Extract and Clean
        sections = extract_and_clean(raw_html)
        
        # Save structured document
        doc_representation = {
            "metadata": src_meta,
            "sections": sections
        }
        with open(f"{src_meta['source_id']}_structured.json", "w", encoding="utf-8") as f:
            json.dump(doc_representation, f, indent=2)
            
        # Chunking
        chunks_a = chunking_strategy_A(src_meta, sections)
        chunks_b = chunking_strategy_B(src_meta, sections)
        chunks_c = chunking_strategy_C(src_meta, sections)
        
        # Save sample chunks
        with open(f"{src_meta['source_id']}_chunks_A.json", "w", encoding="utf-8") as f:
            json.dump(chunks_a, f, indent=2)
            
        stats_a = evaluate_chunks("A_Section_Based", chunks_a)
        stats_b = evaluate_chunks("B_Paragraph_Group", chunks_b)
        stats_c = evaluate_chunks("C_Bounded_Chars", chunks_c)
        
        results[src_meta['source_id']] = {
            "metadata": src_meta,
            "stats": [stats_a, stats_b, stats_c]
        }
        
    with open("evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    main()

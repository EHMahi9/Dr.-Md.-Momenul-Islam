import os
import time
import hashlib
import json
import requests
from bs4 import BeautifulSoup
import datetime

# Configuration
URLS = [
    ("DOC-NHS-004", "https://www.nhs.uk/conditions/asthma/"),
    ("DOC-NHS-005", "https://www.nhs.uk/conditions/burns-and-scalds/"),
    ("DOC-NHS-006", "https://www.nhs.uk/conditions/cuts-and-grazes/"),
    ("DOC-NHS-007", "https://www.nhs.uk/conditions/dehydration/"),
    ("DOC-NHS-008", "https://www.nhs.uk/conditions/diarrhoea-and-vomiting/"),
    ("DOC-NHS-009", "https://www.nhs.uk/conditions/headaches/"),
    ("DOC-NHS-010", "https://www.nhs.uk/conditions/fever-in-children/"),
    ("DOC-NHS-011", "https://www.nhs.uk/conditions/anaphylaxis/")
]

BASE_DIR = os.path.join(os.path.dirname(__file__), "research", "gate_4e_ingestion")
DIRS = {
    "raw": os.path.join(BASE_DIR, "raw"),
    "processed": os.path.join(BASE_DIR, "processed"),
    "chunks": os.path.join(BASE_DIR, "chunks")
}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 Gate-4E-Bot'}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

def hash_str(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def clean_html(soup):
    # Keep only the main content area if available
    main = soup.find('main')
    if main:
        content = main
    else:
        content = soup

    # Remove unwanted tags
    for tag in content(['nav', 'footer', 'header', 'script', 'style', 'video', 'iframe', 'svg', 'aside', 'noscript']):
        tag.decompose()
        
    # Remove elements by class that are typically boilerplate
    for cls in ['nhsuk-header', 'nhsuk-footer', 'nhsuk-breadcrumb', 'nhsuk-review-date']:
        for el in content.find_all(class_=cls):
            el.decompose()

    return content.get_text(separator='\n\n', strip=True)

def create_chunks(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks

def main():
    ingestion_manifest = []
    provenance_manifest = []

    for source_id, requested_url in URLS:
        print(f"Fetching {source_id}: {requested_url}")
        
        utc_now = datetime.datetime.utcnow().isoformat() + "Z"
        
        try:
            r = requests.get(requested_url, headers=HEADERS, allow_redirects=True, timeout=10)
            status = r.status_code
            redirect_chain = [resp.url for resp in r.history]
            final_url = r.url
            
            raw_html = r.text
            html_hash = hash_str(raw_html)
            
            # Save raw HTML
            raw_path = os.path.join(DIRS["raw"], f"{source_id}.html")
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(raw_html)
                
            soup = BeautifulSoup(raw_html, 'html.parser')
            title = soup.title.string.strip() if soup.title else "NONE"
            canon = soup.find('link', rel='canonical')
            canonical_url = canon['href'] if canon else "NONE"
            
            # Extract Text
            clean_text = clean_html(soup)
            text_hash = hash_str(clean_text)
            
            processed_path = os.path.join(DIRS["processed"], f"{source_id}.txt")
            with open(processed_path, 'w', encoding='utf-8') as f:
                f.write(clean_text)
                
            ingestion_manifest.append({
                "source_id": source_id,
                "requested_url": requested_url,
                "final_url": final_url,
                "canonical_url": canonical_url,
                "status_code": status,
                "redirect_chain": redirect_chain,
                "title": title,
                "retrieval_timestamp_utc": utc_now,
                "html_hash": html_hash,
                "text_hash": text_hash,
                "extraction_version": "1.0",
                "rights_classification": "APPROVED_FOR_PLANNED_TEXT_REUSE",
                "attribution_requirement": "Must exclude logos; standard OGL attribution required",
                "status": "SUCCESS"
            })
            
            # Chunking
            chunks = create_chunks(clean_text, CHUNK_SIZE, CHUNK_OVERLAP)
            for idx, chunk_text in enumerate(chunks):
                chunk_id = f"{source_id}-C{idx:03d}"
                provenance_manifest.append({
                    "chunk_id": chunk_id,
                    "parent_source_id": source_id,
                    "source_title": title,
                    "requested_url": requested_url,
                    "final_url": final_url,
                    "canonical_url": canonical_url,
                    "retrieval_timestamp_utc": utc_now,
                    "html_hash": html_hash,
                    "text_hash": text_hash,
                    "extraction_version": "1.0",
                    "chunk_hash": hash_str(chunk_text),
                    "rights_classification": "APPROVED_FOR_PLANNED_TEXT_REUSE",
                    "text": chunk_text
                })
                
        except Exception as e:
            print(f"FAILED on {source_id}: {str(e)}")
            ingestion_manifest.append({
                "source_id": source_id,
                "requested_url": requested_url,
                "status": "FAILED",
                "error": str(e)
            })

    with open(os.path.join(BASE_DIR, "ingestion_manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(ingestion_manifest, f, indent=2)

    with open(os.path.join(BASE_DIR, "provenance_manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(provenance_manifest, f, indent=2)
        
    print("Ingestion and Provenance Mapping Complete.")

if __name__ == "__main__":
    main()

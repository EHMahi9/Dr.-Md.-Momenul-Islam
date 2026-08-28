import requests
import re
import urllib3
import json

urllib3.disable_warnings()

candidates = [
    'https://www.nhs.uk/conditions/asthma/',
    'https://www.nhs.uk/conditions/burns-and-scalds/',
    'https://www.nhs.uk/conditions/cuts-and-grazes/',
    'https://www.nhs.uk/conditions/dehydration/',
    'https://www.nhs.uk/conditions/diarrhoea-and-vomiting/',
    'https://www.nhs.uk/conditions/headaches/',
    'https://www.nhs.uk/conditions/fever-in-children/',
    'https://www.nhs.uk/conditions/anaphylaxis/',
    'https://www.nhs.uk/conditions/bleeding/'
]

headers = {'User-Agent': 'Mozilla/5.0'}

title_re = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
canon_re = re.compile(r'<link[^>]*rel=[\"\']canonical[\"\'][^>]*href=[\"\'](.*?)[\"\']', re.IGNORECASE)
h1_re = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
img_re = re.compile(r'<img[^>]+>', re.IGNORECASE)
iframe_re = re.compile(r'<iframe[^>]+>', re.IGNORECASE)
video_re = re.compile(r'<video[^>]+>', re.IGNORECASE)

print("=== CANDIDATE AUDIT ===")
results = []
for u in candidates:
    try:
        r = requests.get(u, headers=headers, allow_redirects=True, timeout=10)
        
        status = r.status_code
        chain = [resp.url for resp in r.history]
        final = r.url
        domain = final.split('/')[2] if '//' in final else final
        
        t_match = title_re.search(r.text)
        title = t_match.group(1).strip() if t_match else 'NONE'
        
        c_match = canon_re.search(r.text)
        canon_url = c_match.group(1) if c_match else 'NONE'
        
        h1_match = h1_re.search(r.text)
        h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else 'NONE'
        
        imgs = img_re.findall(r.text)
        iframes = iframe_re.findall(r.text)
        videos = video_re.findall(r.text)
        
        text_lower = r.text.lower()
        has_copyright = 'copyright' in text_lower or '©' in text_lower
        has_st_john = 'st john ambulance' in text_lower
        has_red_cross = 'red cross' in text_lower
        
        results.append({
            'original': u,
            'status': status,
            'chain': chain,
            'final': final,
            'domain': domain,
            'canonical': canon_url,
            'title': title,
            'h1': h1_text,
            'imgs': len(imgs),
            'iframes': len(iframes),
            'videos': len(videos),
            'has_st_john': has_st_john,
            'has_red_cross': has_red_cross,
        })
        print(f"Done: {u} -> Status: {status}")
    except Exception as e:
        print(f"Error on {u}: {e}")

with open('audit_4d2_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("=== BLEEDING NHS SEARCH ===")
try:
    search_url = 'https://www.nhs.uk/search/results?q=severe+bleeding'
    r_search = requests.get(search_url, headers=headers, timeout=10)
    link_re = re.compile(r'href=[\"\'](/conditions/[^\'\"]+)[\"\']')
    links = list(set(link_re.findall(r_search.text)))[:5]
    print(f"Search results for bleeding conditions: {links}")
except Exception as e:
    print(f"Search failed: {e}")

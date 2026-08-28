import requests
import re
import urllib3
urllib3.disable_warnings()

urls = [
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

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

title_re = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
canon_re = re.compile(r'<link[^>]*rel=[\"\']canonical[\"\'][^>]*href=[\"\'](.*?)[\"\']', re.IGNORECASE)
h1_re = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
desc_re = re.compile(r'<meta[^>]*name=[\"\']description[\"\'][^>]*content=[\"\'](.*?)[\"\']', re.IGNORECASE)

print("=== 1. URL & REDIRECT AUDIT ===")
for u in urls:
    try:
        r = requests.get(u, headers=headers, allow_redirects=True, timeout=10)
        
        t_match = title_re.search(r.text)
        title = t_match.group(1).strip() if t_match else 'NONE'
        
        c_match = canon_re.search(r.text)
        canon_url = c_match.group(1) if c_match else 'NONE'
        
        h1_match = h1_re.search(r.text)
        h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else 'NONE'
        
        desc_match = desc_re.search(r.text)
        desc = desc_match.group(1).strip() if desc_match else 'NONE'
        
        print(f"Input URL: {u}")
        print(f"Final URL: {r.url}")
        print(f"Status Code: {r.status_code}")
        print(f"Redirect Chain: {[resp.url for resp in r.history]}")
        print(f"Canonical: {canon_url}")
        print(f"Title: {title}")
        print(f"H1: {h1_text}")
        print(f"Desc: {desc}")
        print("-" * 50)
    except Exception as e:
        print(f"Error on {u}: {e}")

print("\n=== 2. /svg SUFFIX INVESTIGATION ===")
test_svg_url = 'https://www.nhs.uk/conditions/asthma/svg'
try:
    r_svg = requests.get(test_svg_url, headers=headers, allow_redirects=True, timeout=10)
    print(f"Testing {test_svg_url}")
    print(f"Status Code: {r_svg.status_code}")
    print(f"Final URL: {r_svg.url}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== 3. BLEEDING ALTERNATIVE SEARCH ===")
alt_urls = [
    'https://www.nhs.uk/conditions/first-aid/severe-bleeding/',
    'https://www.nhs.uk/conditions/severe-bleeding/',
    'https://www.nhs.uk/common-health-questions/accidents-first-aid-and-treatments/how-do-i-clean-a-wound/',
    'https://www.nhs.uk/search/results?q=severe+bleeding'
]
for au in alt_urls:
    try:
        r_alt = requests.get(au, headers=headers, allow_redirects=True, timeout=10)
        print(f"URL: {au} | Status: {r_alt.status_code} | Final: {r_alt.url}")
    except Exception as e:
        pass

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
    'https://www.nhs.uk/conditions/insect-bites-and-stings/',
    'https://www.nhs.uk/conditions/bleeding/',
    'https://www.nhs.uk/conditions/allergies/',
    'https://www.nhs.uk/conditions/food-poisoning/'
]

title_re = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
canon_re = re.compile(r'<link[^>]*rel=[\"\']canonical[\"\'][^>]*href=[\"\'](.*?)[\"\']', re.IGNORECASE)

for u in urls:
    try:
        r = requests.get(u, timeout=10, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        t_match = title_re.search(r.text)
        title = t_match.group(1).strip() if t_match else 'No Title'
        
        c_match = canon_re.search(r.text)
        canon_url = c_match.group(1) if c_match else 'No Canonical'
        
        print(f'Original: {u}')
        print(f'Final URL: {r.url}')
        print(f'Title: {title}')
        print(f'Canonical: {canon_url}')
        print('-'*40)
    except Exception as e:
        print(f'Error on {u}: {e}')

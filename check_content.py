import requests
import re
import urllib3
urllib3.disable_warnings()

urls = [
    'https://www.nhs.uk/conditions/asthma/',
    'https://www.nhs.uk/conditions/burns-and-scalds/',
    'https://www.nhs.uk/conditions/cuts-and-grazes/',
    'https://www.nhs.uk/conditions/dehydration/',
    'https://www.nhs.uk/symptoms/diarrhoea-and-vomiting/',
    'https://www.nhs.uk/symptoms/headaches/',
    'https://www.nhs.uk/symptoms/fever-in-children/',
    'https://www.nhs.uk/conditions/anaphylaxis/',
    'https://www.nhs.uk/conditions/insect-bites-and-stings/',
    'https://www.nhs.uk/conditions/allergies/',
    'https://www.nhs.uk/conditions/food-poisoning/'
]

video_re = re.compile(r'<iframe[^>]*src=[\"\']([^\"\']+)[\"\'][^>]*>', re.IGNORECASE)
stjohn_re = re.compile(r'st[ \.]?john ambulance', re.IGNORECASE)
copyright_re = re.compile(r'copyright|©', re.IGNORECASE)

for u in urls:
    try:
        r = requests.get(u, timeout=10, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        text = r.text
        
        videos = video_re.findall(text)
        has_stjohn = stjohn_re.search(text) is not None
        has_copyright = copyright_re.search(text) is not None
        
        print(f'URL: {u}')
        if videos:
            print(f'  Found Videos: {len(videos)} -> {videos[:2]}')
        if has_stjohn:
            print('  Found St John Ambulance references!')
        if has_copyright:
            print('  Found copyright symbols/text. Needs manual review for 3rd party content.')
        print('-'*40)
    except Exception as e:
        print(f'Error on {u}: {e}')

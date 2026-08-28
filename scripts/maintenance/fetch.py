import urllib.request
import json
import re

try:
    # First, get the dataset webpage to find the actual API link or schema
    url = 'https://data.mendeley.com/public-api/datasets/bwrhzbk326/files'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    for item in data:
        print("Filename:", item.get('filename'))
        print("Download URL:", item.get('content_details', {}).get('download_url'))
except Exception as e:
    print(e)

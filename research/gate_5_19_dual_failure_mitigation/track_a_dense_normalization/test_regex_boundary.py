import re

q = "হাত পুড়ে গেলে কতক্ষণ ঠাণ্ডা পানির নিচে রাখতে হবে?"

pat_b = r'\b(পুড়ে)\b'
pat_clean = r'(?:^|\s|[^\w\u0980-\u09FF])(পুড়ে|পোড়া|ফোস্কা)(?:$|\s|[^\w\u0980-\u09FF])'
pat_direct = r'(পুড়ে|পোড়া|ফোস্কা)'

print("re.search with \\b:", bool(re.search(pat_b, q)))
print("re.search with pat_clean:", bool(re.search(pat_clean, q)))
print("re.search with pat_direct:", bool(re.search(pat_direct, q)))

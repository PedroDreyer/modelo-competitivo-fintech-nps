import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,pt;q=0.7',
}

query = "Nubank Mexico octubre noviembre diciembre 2025"

# Test DDG HTML
print("=== DDG HTML ===")
try:
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    r = requests.get(url, headers=headers, timeout=12)
    print(f"Status: {r.status_code}")
    print(f"Length: {len(r.text)}")
    # Check for result classes
    if 'result__a' in r.text:
        print("FOUND result__a class")
    elif 'result__snippet' in r.text:
        print("FOUND result__snippet class")
    else:
        print("NO result classes found")
    # Show first 2000 chars
    print(f"Content[:500]: {r.text[:500]}")
    # Save for analysis
    with open('_ddg_html_test.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print("Saved to _ddg_html_test.html")
except Exception as e:
    print(f"ERROR: {e}")

print()

# Test DDG Lite
print("=== DDG LITE ===")
try:
    url2 = f"https://lite.duckduckgo.com/lite/?q={requests.utils.quote(query)}"
    r2 = requests.get(url2, headers=headers, timeout=12)
    print(f"Status: {r2.status_code}")
    print(f"Length: {len(r2.text)}")
    if '<a' in r2.text and 'http' in r2.text:
        print("FOUND links")
    else:
        print("NO links found")
    with open('_ddg_lite_test.html', 'w', encoding='utf-8') as f:
        f.write(r2.text)
    print("Saved to _ddg_lite_test.html")
except Exception as e:
    print(f"ERROR: {e}")

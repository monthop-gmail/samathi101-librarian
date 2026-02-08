import os
import requests

# List of manual links found on samathi101.com
MANUALS = [
    {"name": "WP-Life_Dev_Manual.pdf", "url": "https://www.dropbox.com/s/ytj8ei9yrgz46af/4%20%E0%B8%84%E0%B8%B9%E0%B9%88%E0%B8%A1%E0%B8%B7%E0%B8%AD%E0%B8%AB%E0%B8%A5%E0%B8%B1%E0%B8%81%E0%B8%AA%E0%B8%B9%E0%B8%95%E0%B8%A3%AA%E0%B8%A1%E0%B8%B2%E0%B8%98%E0%B8%B4%E0%B9%80%E0%B8%9E%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%9E%E0%B8%B1%E0%B8%92%E0%B8%99%E0%B8%B2%E0%B8%8A%E0%B8%B5%E0%B8%A7%E0%B8%B4%E0%B8%95.%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%81.pdf?dl=1"},
]

INBOX = "00_INBOX_UNPROCESSED"

def download_manuals():
    if not os.path.exists(INBOX):
        os.makedirs(INBOX)
        
    for manual in MANUALS:
        print(f"Downloading {manual['name']}...")
        try:
            r = requests.get(manual['url'], allow_redirects=True)
            r.raise_for_status()
            with open(os.path.join(INBOX, manual['name']), 'wb') as f:
                f.write(r.content)
            print(f"Success: {manual['name']}")
        except Exception as e:
            print(f"Failed to download {manual['name']}: {e}")

if __name__ == "__main__":
    download_manuals()

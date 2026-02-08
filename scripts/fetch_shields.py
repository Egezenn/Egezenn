import urllib.request

badges = [
    ("badge_tuta.svg", "https://img.shields.io/badge/tuta-840010?style=for-the-badge&logo=tuta&logoColor=white"),
    (
        "badge_github.svg",
        "https://img.shields.io/badge/github-000000.svg?&style=for-the-badge&logo=github&logoColor=white",
    ),
    (
        "badge_bluesky.svg",
        "https://img.shields.io/badge/bluesky-0285FF.svg?&style=for-the-badge&logo=bluesky&logoColor=white",
    ),
]

for filename, url in badges:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = response.read()
            with open(f"../assets/{filename}", "wb") as f:
                f.write(data)
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

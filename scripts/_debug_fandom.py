from wwe_data.collectors.http_client import HttpClient
from bs4 import BeautifulSoup

c = HttpClient()
API = "https://prowrestling.fandom.com/api.php"
pages = [
    "Saturday Night's Main Event XXXIV",
    "Tribute to the Troops 2007",
]
for p in pages:
    data = c.get_json(
        API,
        params={"action": "parse", "page": p, "prop": "text", "format": "json"},
        use_cache=False,
    )
    html = data["parse"]["text"]["*"]
    soup = BeautifulSoup(html, "lxml")
    print("====", p)
    print("tables", len(soup.find_all("table")))
    for i, t in enumerate(soup.find_all("table")[:10]):
        first = t.find("tr")
        headers = (
            [c.get_text(" ", strip=True)[:50] for c in first.find_all(["th", "td"])]
            if first
            else []
        )
        print(i, t.get("class"), headers)
    for line in soup.get_text("\n", strip=True).splitlines():
        if "defeated" in line.lower() or "def." in line.lower():
            print("LINE", line[:160])

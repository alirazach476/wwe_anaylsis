from wwe_data.collectors.http_client import HttpClient
import re

c = HttpClient()
API = "https://prowrestling.fandom.com/api.php"
for p in [
    "Saturday Night's Main Event XXXIV",
    "Saturday Night's Main Event XXXVI",
    "Tribute to the Troops 2007",
    "Tribute to the Troops 2010",
]:
    data = c.get_json(
        API,
        params={"action": "parse", "page": p, "prop": "wikitext", "format": "json"},
        use_cache=False,
    )
    wt = data["parse"]["wikitext"]["*"]
    print("====", p, "len", len(wt))
    # print results section
    m = re.search(r"==\s*Results\s*==(.+?)(?:\n==|\Z)", wt, re.S | re.I)
    chunk = m.group(1) if m else wt[:2500]
    print(chunk[:2000])
    print("---")

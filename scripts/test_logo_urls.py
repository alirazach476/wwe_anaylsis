import urllib.request
from urllib.parse import quote

urls = [
    "http://127.0.0.1:5173/logos/files/" + quote("John Cena's Final SmackDown.svg"),
    "http://127.0.0.1:5173/logos/files/WrestleMania%20(2002).jpg",
    "http://127.0.0.1:5173/logos/logo_index.json",
]
for u in urls:
    try:
        r = urllib.request.urlopen(u)
        print(r.status, r.headers.get("content-type"), u)
    except Exception as e:
        print("FAIL", u, e)

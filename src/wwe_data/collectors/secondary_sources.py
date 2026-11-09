"""Secondary source collectors (stubs / robots-aware placeholders).

Match scraping and deep HTML harvest are intentionally deferred until the
event inventory and coverage audit are reviewed.

These modules document intended sources and provide robots.txt checks only.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from wwe_data.collectors.http_client import HttpClient

SECONDARY_SOURCES = [
    {
        "name": "the_smackdown_hotel",
        "base_url": "https://www.thesmackdownhotel.com/",
        "events_url": "https://www.thesmackdownhotel.com/events-results/ppv-special/wwe/",
        "notes": "JS-heavy interactive DB; prefer permitted exports / static schedule pages.",
    },
    {
        "name": "online_world_of_wrestling",
        "base_url": "https://www.onlineworldofwrestling.com/",
        "events_url": "https://www.onlineworldofwrestling.com/results/",
        "notes": "Historical results archive; respect robots.txt before scraping.",
    },
    {
        "name": "wrestling_oracle",
        "base_url": "https://www.wrestlingoracle.com/",
        "events_url": "https://www.wrestlingoracle.com/",
        "notes": "Event listings; verify ToS and robots before automated access.",
    },
    {
        "name": "wwe_official",
        "base_url": "https://www.wwe.com/",
        "events_url": "https://www.wwe.com/events",
        "notes": "Official pages for announced future events; no paywall bypass.",
    },
]


@dataclass
class RobotsCheck:
    source_name: str
    robots_url: str
    can_fetch: bool | None
    detail: str


def check_robots(source_name: str, url: str, user_agent: str) -> RobotsCheck:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(user_agent, url)
        return RobotsCheck(source_name, robots_url, allowed, "ok")
    except Exception as exc:  # noqa: BLE001
        return RobotsCheck(source_name, robots_url, None, str(exc))


def audit_secondary_robots(client: HttpClient | None = None) -> list[RobotsCheck]:
    client = client or HttpClient()
    results = []
    for src in SECONDARY_SOURCES:
        results.append(
            check_robots(src["name"], src["events_url"], client.settings.user_agent)
        )
    return results

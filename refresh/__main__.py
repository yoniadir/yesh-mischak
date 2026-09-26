import sys
from datetime import datetime
from pathlib import Path

import httpx

from refresh.config import FIXTURES_URL, TEL_AVIV_CLUBS, TZ, USER_AGENT, VENUE_CALENDARS, VENUE_ICAL_URL
from refresh.model import SourceError
from refresh.transform import Payloads, build


def fetch(client: httpx.Client, url: str) -> str:
    response = client.get(url)
    if response.status_code != 200:
        raise SourceError(f"{url} answered HTTP {response.status_code}")
    return response.text


def main(out_dir: Path) -> None:
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        payloads = Payloads(
            venue={cid: fetch(client, VENUE_ICAL_URL.format(calendar_id=cid)) for cid in VENUE_CALENDARS},
            fixtures={club: fetch(client, FIXTURES_URL.format(club_id=club)) for club in TEL_AVIV_CLUBS},
        )
    artifacts = build(payloads, datetime.now(TZ))

    # Both artifacts exist in memory before either file is touched.
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in (("events.json", artifacts.events_json), ("bloomfield.ics", artifacts.ics)):
        tmp = out_dir / f".{name}.tmp"
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(out_dir / name)
    print(f"wrote {out_dir}/events.json and {out_dir}/bloomfield.ics")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("site"))

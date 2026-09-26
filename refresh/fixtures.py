"""365scores fixtures adapter.

Designated replacement if this endpoint breaks: the Israel Football
Association's official fixture PDF. Swapping sources means replacing this
module only; it must keep returning tentative football Events.
"""

import json
from datetime import datetime

from refresh.config import TEL_AVIV_CLUBS, TZ
from refresh.model import Event, SourceError


def parse_fixtures(json_text: str) -> list[Event]:
    try:
        games = json.loads(json_text)["games"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise SourceError(f"fixtures feed is not the expected JSON: {e}") from e
    if not isinstance(games, list):
        raise SourceError("fixtures feed 'games' is not a list")

    events = []
    for game in games:
        try:
            home, away = game["homeCompetitor"], game["awayCompetitor"]
            if home["id"] not in TEL_AVIV_CLUBS:
                continue
            start = datetime.fromisoformat(game["startTime"])
            if start.tzinfo is None:
                start = start.replace(tzinfo=TZ)
            start = start.astimezone(TZ)
            game_id = game["id"]
        except (KeyError, TypeError, ValueError) as e:
            raise SourceError(f"fixtures feed game is malformed: {e}") from e
        events.append(
            Event(
                id=f"365scores:{game_id}",
                date=start.date(),
                time=start.strftime("%H:%M"),
                title=f"{home['name']} – {away['name']}",
                kind="football",
                status="tentative",
                source="365scores",
                url=None,
            )
        )
    return events

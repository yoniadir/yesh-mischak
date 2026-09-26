from dataclasses import dataclass
from datetime import date


class SourceError(Exception):
    """A source responded with something we cannot trust."""


@dataclass(frozen=True)
class Event:
    id: str
    date: date
    time: str | None
    title: str
    kind: str  # football | concert | other
    status: str  # confirmed | tentative
    source: str  # sportpalace | 365scores
    url: str | None

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "time": self.time,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "source": self.source,
            "url": self.url,
        }

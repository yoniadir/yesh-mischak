from datetime import timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")

STADIUM_NAME = "אצטדיון בלומפילד"

VENUE_ICAL_URL = (
    "https://www.sportpalace.co.il/index.php"
    "?option=com_dpcalendar&task=ical.download&id={calendar_id}"
)
# DPCalendar calendar id -> event kind
VENUE_CALENDARS = {"10": "football", "11": "concert"}

FIXTURES_URL = (
    "https://webws.365scores.com/web/games/fixtures/"
    "?appTypeId=5&langId=2&timezoneName=Asia/Jerusalem&competitors={club_id}"
)
TEL_AVIV_CLUBS = {566: "מכבי תל אביב", 567: "הפועל תל אביב"}

PAST_DAYS = 7
# A night event only counts on the following day if still running at this hour.
DAY_ROLLOVER = timedelta(hours=6)

USER_AGENT = "yesh-mischak/1.0 (+https://github.com/yoniadir/yesh-mischak)"

SOURCES = [
    {
        "id": "sportpalace",
        "name": "היכלי הספורט תל אביב",
        "url": "https://www.sportpalace.co.il/tlv-faclities/sport-halls/new-blumfield/blumfield-events",
    },
    {"id": "365scores", "name": "365Scores", "url": "https://www.365scores.com/he"},
]

"""Test data for the Single Tournament creation wizard.

Form values come from tournament_data.json. Dates are relative to the day the
tests run so the calendar pickers always offer them. Officials are chosen only
from dedicated test accounts.
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

# Safety rule, deliberately kept in code rather than editable data:
# only test accounts named like "user102" may be invited as referees/scorers.
# Real users of the app (e.g. "Chandra") must never be selected.
OFFICIAL_TEST_USER = re.compile(r"user\d+")
PROTECTED_OFFICIALS = ("Chandra",)

_DEFAULTS = json.loads(
    Path(__file__).with_name("tournament_data.json").read_text(encoding="utf-8")
)["tournament_defaults"]


@dataclass(frozen=True)
class TournamentData:
    name: str
    sport: str = _DEFAULTS["sport"]
    tournament_type: str = "Knockout"
    match_type: str = _DEFAULTS["match_type"]
    age_group: str = _DEFAULTS["age_group"]
    category: str = _DEFAULTS["category"]
    level: str = _DEFAULTS["level"]
    state: str = _DEFAULTS["state"]
    district: str = _DEFAULTS["district"]
    city: str = _DEFAULTS["city"]
    first_prize: str = _DEFAULTS["first_prize"]
    second_prize: str = _DEFAULTS["second_prize"]
    start: date = field(
        default_factory=lambda: date.today() + timedelta(days=_DEFAULTS["start_in_days"])
    )
    duration_days: int = _DEFAULTS["duration_days"]
    playing_days: str = _DEFAULTS["playing_days"]
    match_minutes: str = _DEFAULTS["match_minutes"]
    players_per_side: str = _DEFAULTS["players_per_side"]
    expected_teams: str = _DEFAULTS["expected_teams"]
    ground_opens: tuple = tuple(_DEFAULTS["ground_opens"])
    ground_closes: tuple = tuple(_DEFAULTS["ground_closes"])
    grounds: int = _DEFAULTS["grounds"]
    referees: int = _DEFAULTS["referees"]
    scorers: int = _DEFAULTS["scorers"]
    entry_fee: str = _DEFAULTS["entry_fee"]
    rules: tuple = tuple(_DEFAULTS["rules"])

    @property
    def end(self):
        return self.start + timedelta(days=self.duration_days)

    @property
    def registration_opens(self):
        return min(date.today() + timedelta(days=2), self.start)

    @property
    def registration_closes(self):
        return self.start - timedelta(days=1)


def new_tournament(tournament_type="Knockout", **overrides):
    """Return unique tournament data; the name stays within the 60-character limit."""
    name = f"QA Auto {tournament_type} {int(time.time())}"
    return TournamentData(name=name, tournament_type=tournament_type, **overrides)


def playing_days_between(start, end, option):
    """Expected 'Playing days' figure for a schedule option."""
    days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    if option == "Weekends":
        return sum(day.weekday() >= 5 for day in days)
    if option == "Weekdays":
        return sum(day.weekday() < 5 for day in days)
    return len(days)

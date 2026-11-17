"""Test data for the Single Tournament creation wizard.

Form values come from tournament_data.json. Dates are relative to the day the
tests run so the calendar pickers always offer them. Officials are chosen only
from dedicated test accounts.
"""

import json
import os
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

_DATA = json.loads(Path(__file__).with_name("tournament_data.json").read_text(encoding="utf-8"))
_DEFAULTS = _DATA["tournament_defaults"]


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
    # Team sports (e.g. FootBall) have a match duration and players per side;
    # set-based sports (e.g. Badminton) have a number of sets instead.
    match_minutes: str | None = _DEFAULTS["match_minutes"]
    players_per_side: str | None = _DEFAULTS["players_per_side"]
    sets: str | None = None
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


def new_tournament(tournament_type="Knockout", name=None, **overrides):
    """Return FootBall tournament data.

    Without a name, a unique one is generated (within the 60-character limit).
    """
    name = name or f"QA Auto {tournament_type} {int(time.time())}"
    return TournamentData(name=name, tournament_type=tournament_type, **overrides)


def badminton_singles_tournament(**overrides):
    """Badminton Singles Knockout data from tournament_data.json (published by its test)."""
    values = {**_DATA["badminton_singles"], **overrides}
    values["rules"] = tuple(values["rules"])
    return TournamentData(**values)


@dataclass(frozen=True)
class RegistrationData:
    """Tournament and the pool of numbered test accounts for the registration flow.

    How many accounts register is not stored here: it is the expected number
    of players shown by the tournament itself. Accounts are tried in order.
    """

    tournament: str
    first_account: int
    last_account: int

    @property
    def accounts(self):
        return list(range(self.first_account, self.last_account + 1))


def registration_data():
    return RegistrationData(**_DATA["registration"])


@dataclass(frozen=True)
class FixturesData:
    """Tournament, organizer and schedule for the fixtures flow.

    Values are taken, first match wins, from: pytest options (--tournament,
    --organizer), environment / pipeline variables (SPORTZDOM_FIXTURES_TOURNAMENT,
    SPORTZDOM_FIXTURES_ORGANIZER), then tournament_data.json "fixtures".
    """

    tournament: str
    organizer_account: int
    league_group_start_times: tuple
    minutes_between_matches: int
    knockout_gap_days: int
    knockout_start_time: str
    third_place_time: str
    final_time: str


def fixtures_data(tournament=None, organizer=None):
    values = dict(_DATA["fixtures"])
    values["league_group_start_times"] = tuple(values["league_group_start_times"])
    values["tournament"] = tournament or os.getenv("SPORTZDOM_FIXTURES_TOURNAMENT") or values["tournament"]
    values["organizer_account"] = int(
        organizer or os.getenv("SPORTZDOM_FIXTURES_ORGANIZER") or values["organizer_account"]
    )
    return FixturesData(**values)


def account_credentials(number):
    """(email, password) of numbered test account number, e.g. user 2.

    The formats come from environment variables (.env locally, secret
    pipeline variables in Azure DevOps), with {n} replaced by the number:
        SPORTZDOM_PLAYER_EMAIL_TEMPLATE, SPORTZDOM_PLAYER_PASSWORD_TEMPLATE
    Returns None when either is not set.
    """
    email = os.getenv("SPORTZDOM_PLAYER_EMAIL_TEMPLATE", "")
    password = os.getenv("SPORTZDOM_PLAYER_PASSWORD_TEMPLATE", "")
    if not (email and password):
        return None
    return email.format(n=number), password.format(n=number)


def playing_days_between(start, end, option):
    """Expected 'Playing days' figure for a schedule option."""
    days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    if option == "Weekends":
        return sum(day.weekday() >= 5 for day in days)
    if option == "Weekdays":
        return sum(day.weekday() < 5 for day in days)
    return len(days)

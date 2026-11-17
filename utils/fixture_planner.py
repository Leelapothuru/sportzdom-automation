"""Plan a tournament's fixtures from its groups, without a device.

The tournament fixtures test reads the groups the app made (Auto-split) and
asks this module what to create:

* League: every pair of players in a group meets once (round robin), one
  round per day, each group in its own time block.
* Knockout stages, chosen from the number of qualifiers: 2 -> Final;
  4 -> Semi Final, Third Place, Final; 8 -> Quarter Final, Semi Final,
  Third Place, Final. The app offers no earlier knockout round.
* First knockout round: group positions ("Group A · 1st"), best against
  worst so that group winners meet runners-up of another group
  (2 groups: A1 v B2, B1 v A2).
* Later rounds: "Winner/Loser of <stage> · Match N" positions. Match numbers
  are only known in the app, so they are planned by order (ResultSlot.index)
  and resolved by the page object.

The schedule follows the manual run of 11 Nov 2026: Group A from 9 AM,
Group B from 4 PM, one hour apart, the knockout rounds two days apart.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from itertools import count

LEAGUE = "League"
QUARTER_FINAL = "Quarter Final"
SEMI_FINAL = "Semi Final"
THIRD_PLACE = "Third Place"
FINAL = "Final"

# Knockout stages for a number of qualifiers.
KNOCKOUT_STAGES = {
    2: (FINAL,),
    4: (SEMI_FINAL, THIRD_PLACE, FINAL),
    8: (QUARTER_FINAL, SEMI_FINAL, THIRD_PLACE, FINAL),
}


class PlanError(ValueError):
    """The tournament cannot be planned with these settings."""


def ordinal(number):
    """1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th', 11 -> '11th'."""
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


@dataclass(frozen=True)
class Player:
    """A registered player (a team in team sports), as named in the app."""

    name: str

    @property
    def label(self):
        return self.name


@dataclass(frozen=True)
class GroupSlot:
    """A group position filled in when the group finishes, e.g. 'Group A · 1st'."""

    group: str
    position: int

    @property
    def label(self):
        return f"{self.group} · {ordinal(self.position)}"


@dataclass(frozen=True)
class ResultSlot:
    """The winner or loser of the index-th match (by match number) of a stage."""

    outcome: str  # "Winner" or "Loser"
    stage: str
    index: int

    @property
    def prefix(self):
        """Start of the app's label, e.g. 'Winner of Semi Final · Match '."""
        return f"{self.outcome} of {self.stage} · Match "

    @property
    def label(self):
        return f"{self.outcome} of {self.stage} #{self.index + 1}"


@dataclass(frozen=True)
class Fixture:
    stage: str
    group: str | None  # only League fixtures belong to a group
    first: Player | GroupSlot | ResultSlot
    second: Player | GroupSlot | ResultSlot
    start: datetime

    def __str__(self):
        where = f" {self.group}" if self.group else ""
        return f"{self.stage}{where}: {self.first.label} vs {self.second.label} at {self.start:%d %b %H:%M}"


@dataclass(frozen=True)
class ScheduleSettings:
    # League: one start time per group, in group order (A, B, C, ...).
    league_group_start_times: tuple = ("09:00", "16:00")
    minutes_between_matches: int = 60
    # Days from the last League day to the first knockout day, and between knockout days.
    knockout_gap_days: int = 2
    knockout_start_time: str = "10:00"
    # Start times on the final day; the Third Place match is played before the Final.
    third_place_time: str = "09:00"
    final_time: str = "11:00"


@dataclass(frozen=True)
class FixturePlan:
    stages: tuple
    league: tuple
    knockout: tuple

    @property
    def fixtures(self):
        return self.league + self.knockout

    @property
    def total(self):
        return len(self.league) + len(self.knockout)

    @property
    def last_day(self):
        return max(fixture.start.date() for fixture in self.fixtures)


def _clock(text):
    hours, minutes = map(int, text.split(":"))
    return time(hours, minutes)


def round_robin(players):
    """Rounds of pairings in which every pair meets once (circle method).

    Each round has every player at most once; with an odd number of players
    one player rests each round.
    """
    players = list(players)
    if len(players) < 2:
        return []
    if len(players) % 2:
        players.append(None)  # rest
    rounds = []
    for _ in range(len(players) - 1):
        half = len(players) // 2
        pairs = [
            (players[i], players[-1 - i])
            for i in range(half)
            if players[i] is not None and players[-1 - i] is not None
        ]
        rounds.append(pairs)
        players = [players[0], players[-1], *players[1:-1]]
    return rounds


def knockout_stages(qualifiers):
    try:
        return KNOCKOUT_STAGES[qualifiers]
    except KeyError:
        raise PlanError(
            f"{qualifiers} players qualify from the groups; the app's knockout stages "
            f"support {sorted(KNOCKOUT_STAGES)} qualifiers"
        ) from None


def first_round_slots(qualifiers_per_group):
    """Pairings of group positions for the first knockout round.

    Positions are ranked 1st places first (A1, B1, ...), then 2nd places, and
    the best meets the worst, so winners meet runners-up of another group.
    """
    seeds = [
        GroupSlot(group, position)
        for position in range(1, max(qualifiers_per_group.values()) + 1)
        for group, qualifying in qualifiers_per_group.items()
        if position <= qualifying
    ]
    return [(seeds[i], seeds[-1 - i]) for i in range(len(seeds) // 2)]


def plan_fixtures(groups, qualifiers_per_group, first_day, last_allowed_day, settings=ScheduleSettings()):
    """Plan every fixture.

    groups: {"Group A": [player names], ...} in the app's order.
    qualifiers_per_group: {"Group A": 2, ...} from the group cards.
    first_day / last_allowed_day: the days fixtures may be played on.
    """
    if not groups or any(len(players) < 2 for players in groups.values()):
        raise PlanError(f"Every group needs at least 2 players: {groups}")
    if len(groups) > len(settings.league_group_start_times):
        raise PlanError(
            f"{len(groups)} groups but only {len(settings.league_group_start_times)} "
            "league_group_start_times are configured"
        )
    step = timedelta(minutes=settings.minutes_between_matches)

    league = []
    league_days = 0
    for group_index, (group, names) in enumerate(groups.items()):
        block_start = _clock(settings.league_group_start_times[group_index])
        rounds = round_robin([Player(name) for name in names])
        league_days = max(league_days, len(rounds))
        for day_offset, pairs in enumerate(rounds):
            day = first_day + timedelta(days=day_offset)
            for match_index, (first, second) in enumerate(pairs):
                start = datetime.combine(day, block_start) + step * match_index
                league.append(Fixture(LEAGUE, group, first, second, start))

    qualifiers = sum(qualifiers_per_group.values())
    stages = knockout_stages(qualifiers)
    knockout = []
    day = first_day + timedelta(days=league_days - 1)
    previous_round = None
    for stage in stages:
        if stage == THIRD_PLACE:
            continue  # played on the final day, with the Final
        day += timedelta(days=settings.knockout_gap_days)
        if stage == FINAL:
            if THIRD_PLACE in stages:
                knockout.append(Fixture(
                    THIRD_PLACE, None,
                    ResultSlot("Loser", previous_round, 0), ResultSlot("Loser", previous_round, 1),
                    datetime.combine(day, _clock(settings.third_place_time)),
                ))
            first, second = (
                first_round_slots(qualifiers_per_group)[0] if previous_round is None
                else (ResultSlot("Winner", previous_round, 0), ResultSlot("Winner", previous_round, 1))
            )
            knockout.append(Fixture(FINAL, None, first, second, datetime.combine(day, _clock(settings.final_time))))
            break
        if previous_round is None:
            pairs = first_round_slots(qualifiers_per_group)
        else:
            winners = len([f for f in knockout if f.stage == previous_round])
            pairs = [
                (ResultSlot("Winner", previous_round, i), ResultSlot("Winner", previous_round, i + 1))
                for i in range(0, winners, 2)
            ]
        start = datetime.combine(day, _clock(settings.knockout_start_time))
        for index, (first, second) in zip(count(), pairs):
            knockout.append(Fixture(stage, None, first, second, start + step * index))
        previous_round = stage

    plan = FixturePlan(stages=(LEAGUE, *stages), league=tuple(league), knockout=tuple(knockout))
    if plan.last_day > last_allowed_day:
        raise PlanError(
            f"The fixtures need {first_day:%d %b} - {plan.last_day:%d %b %Y}, "
            f"but the tournament ends on {last_allowed_day:%d %b %Y}"
        )
    return plan


def tournament_dates(text):
    """(start, end) from the details page's date line.

    Seen as '13 Nov – 23 Nov 2026'; also accepts '28 Dec 2026 – 3 Jan 2027'
    and a plain hyphen.
    """
    import re

    match = re.fullmatch(
        r"\s*(\d{1,2}) ([A-Za-z]{3})(?: (\d{4}))?\s*[–-]\s*(\d{1,2}) ([A-Za-z]{3}) (\d{4})\s*", text
    )
    if not match:
        raise PlanError(f"Unrecognised tournament dates: {text!r}")
    start_day, start_month, start_year, end_day, end_month, end_year = match.groups()
    end = datetime.strptime(f"{end_day} {end_month} {end_year}", "%d %b %Y").date()
    start = datetime.strptime(f"{start_day} {start_month} {start_year or end_year}", "%d %b %Y").date()
    if start > end:  # e.g. '28 Dec – 3 Jan 2027' without the start year
        start = start.replace(year=start.year - 1)
    return start, end


def first_playable_day(tournament_start: date, today: date) -> date:
    """Fixtures start on the tournament's first day, but never today or earlier."""
    return max(tournament_start, today + timedelta(days=1))

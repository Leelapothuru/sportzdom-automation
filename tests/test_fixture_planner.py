"""Unit tests for utils/fixture_planner.py (no device or Appium needed).

Run on their own with: pytest tests/test_fixture_planner.py
"""

from datetime import date, datetime
from itertools import combinations

import pytest

from utils.fixture_planner import (
    FINAL,
    LEAGUE,
    QUARTER_FINAL,
    SEMI_FINAL,
    THIRD_PLACE,
    GroupSlot,
    PlanError,
    ResultSlot,
    first_playable_day,
    ordinal,
    plan_fixtures,
    round_robin,
    tournament_dates,
)

FEATURE = "fixture_planner"
pytestmark = pytest.mark.planner

START, END = date(2026, 11, 13), date(2026, 11, 23)


def players(prefix, n):
    return [f"{prefix}{i}" for i in range(1, n + 1)]


def groups_of(*sizes):
    return {f"Group {chr(65 + i)}": players(chr(97 + i), size) for i, size in enumerate(sizes)}


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7, 8])
def test_round_robin_meets_every_pair_once(n):
    rounds = round_robin(players("p", n))
    pairs = [frozenset(pair) for matches in rounds for pair in matches]

    assert len(pairs) == n * (n - 1) // 2
    assert set(pairs) == {frozenset(pair) for pair in combinations(players("p", n), 2)}
    for matches in rounds:
        playing = [name for pair in matches for name in pair]
        assert len(playing) == len(set(playing)), f"A player plays twice in one round: {matches}"


@pytest.mark.parametrize("number, text", [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"), (11, "11th"), (22, "22nd")])
def test_ordinal(number, text):
    assert ordinal(number) == text


def test_eight_players_in_two_groups_matches_the_manual_run():
    plan = plan_fixtures(groups_of(4, 4), {"Group A": 2, "Group B": 2}, START, END)

    assert plan.stages == (LEAGUE, SEMI_FINAL, THIRD_PLACE, FINAL)
    assert len(plan.league) == 12
    assert plan.total == 16
    group_a = [f for f in plan.league if f.group == "Group A"]
    group_b = [f for f in plan.league if f.group == "Group B"]
    assert {f.start for f in group_a} == {
        datetime(2026, 11, d, h) for d in (13, 14, 15) for h in (9, 10)
    }
    assert {f.start for f in group_b} == {
        datetime(2026, 11, d, h) for d in (13, 14, 15) for h in (16, 17)
    }

    semis = [f for f in plan.knockout if f.stage == SEMI_FINAL]
    assert [(f.first.label, f.second.label) for f in semis] == [
        ("Group A · 1st", "Group B · 2nd"),
        ("Group B · 1st", "Group A · 2nd"),
    ]
    assert [f.start for f in semis] == [datetime(2026, 11, 17, 10), datetime(2026, 11, 17, 11)]

    third, final = plan.knockout[-2:]
    assert third.stage == THIRD_PLACE and final.stage == FINAL
    assert (third.first, third.second) == (ResultSlot("Loser", SEMI_FINAL, 0), ResultSlot("Loser", SEMI_FINAL, 1))
    assert (final.first, final.second) == (ResultSlot("Winner", SEMI_FINAL, 0), ResultSlot("Winner", SEMI_FINAL, 1))
    assert third.start == datetime(2026, 11, 19, 9) and final.start == datetime(2026, 11, 19, 11)


def test_every_player_plays_each_group_rival_once():
    groups = groups_of(4, 5)
    plan = plan_fixtures(groups, {"Group A": 2, "Group B": 2}, START, END)

    for group, names in groups.items():
        pairs = [frozenset((f.first.name, f.second.name)) for f in plan.league if f.group == group]
        assert sorted(map(sorted, pairs)) == sorted(map(sorted, combinations(names, 2)))


def test_one_group_two_qualifiers_plays_a_final_only():
    plan = plan_fixtures(groups_of(4), {"Group A": 2}, START, END)

    assert plan.stages == (LEAGUE, FINAL)
    (final,) = plan.knockout
    assert (final.first, final.second) == (GroupSlot("Group A", 1), GroupSlot("Group A", 2))


def test_four_groups_play_quarter_finals():
    settings_groups = groups_of(4, 4, 4, 4)
    from utils.fixture_planner import ScheduleSettings

    settings = ScheduleSettings(league_group_start_times=("09:00", "11:00", "14:00", "16:00"))
    plan = plan_fixtures(settings_groups, {g: 2 for g in settings_groups}, START, END, settings)

    assert plan.stages == (LEAGUE, QUARTER_FINAL, SEMI_FINAL, THIRD_PLACE, FINAL)
    quarters = [f for f in plan.knockout if f.stage == QUARTER_FINAL]
    assert len(quarters) == 4
    for fixture in quarters:
        assert fixture.first.position == 1 and fixture.second.position == 2
        assert fixture.first.group != fixture.second.group
    semis = [f for f in plan.knockout if f.stage == SEMI_FINAL]
    assert [(f.first.index, f.second.index) for f in semis] == [(0, 1), (2, 3)]
    assert plan.total == 24 + 4 + 2 + 2


def test_too_many_qualifiers_is_refused():
    groups = groups_of(*[4] * 8)
    from utils.fixture_planner import ScheduleSettings

    settings = ScheduleSettings(league_group_start_times=tuple(f"{h:02d}:00" for h in range(8, 16)))
    with pytest.raises(PlanError, match="16 players qualify"):
        plan_fixtures(groups, {g: 2 for g in groups}, START, END, settings)


def test_more_groups_than_time_blocks_is_refused():
    with pytest.raises(PlanError, match="league_group_start_times"):
        plan_fixtures(groups_of(4, 4, 4), {"Group A": 2, "Group B": 1, "Group C": 1}, START, END)


def test_fixtures_must_fit_in_the_tournament():
    with pytest.raises(PlanError, match="tournament ends"):
        plan_fixtures(groups_of(4, 4), {"Group A": 2, "Group B": 2}, START, date(2026, 11, 18))


def test_a_group_needs_two_players():
    with pytest.raises(PlanError, match="at least 2 players"):
        plan_fixtures({"Group A": ["solo"]}, {"Group A": 1}, START, END)


@pytest.mark.parametrize("text, expected", [
    ("13 Nov – 23 Nov 2026", (date(2026, 11, 13), date(2026, 11, 23))),
    ("28 Dec 2026 – 3 Jan 2027", (date(2026, 12, 28), date(2027, 1, 3))),
    ("28 Dec – 3 Jan 2027", (date(2026, 12, 28), date(2027, 1, 3))),
    ("1 Dec - 5 Dec 2026", (date(2026, 12, 1), date(2026, 12, 5))),
])
def test_tournament_dates(text, expected):
    assert tournament_dates(text) == expected


def test_first_playable_day_is_never_today_or_earlier():
    assert first_playable_day(date(2026, 11, 13), date(2026, 11, 11)) == date(2026, 11, 13)
    assert first_playable_day(date(2026, 11, 13), date(2026, 11, 15)) == date(2026, 11, 16)

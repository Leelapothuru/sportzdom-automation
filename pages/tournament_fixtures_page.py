"""Page object for setting up a tournament's fixtures (organizer only).

Flow (inspected with Appium Inspector on 11 Nov 2026; evidence in
inspect_output/fixtures/ and reports/manual/tournament_fixtures_manual_tests.md):

Tournament Details -> "Matches" tab -> "Tournament setup" card:
  1 League rules   2 Groups & stages   3 Generate Fixtures
(Step 4 "Confirm Fixtures" is being removed from the app, 12 Nov 2026, and is
not automated.) A step that is done shows a tick instead of its number, so the card's label
reads "...\\nGroups & stages\\n..." instead of "...\\n2\\nGroups & stages\\n...".
Step 3 only appears once stages exist.

Groups & stages: "Auto-split" opens a sheet ("8 teams → 2 groups · 4 teams
each", "Split into 2 groups"); group cards read "A\\nGroup A\\n4 teams · 2 qualify\\n...";
tapping a card opens its member list (rows "L\\nLisa\\nTelangana" with a Move
button). "Add stages" opens chips (League, Quarter Final, Semi Final, Third
Place, Final) and an "Add N stages" button.

Create Fixtures: a "Fixtures Creation" dialog (Manual Selection / Smart
Auto-Generate, NEXT) that the app sometimes skips. The manual form has
Tournament stage, Group (League only), First player, Opponent and Match start
fields; each opens a bottom-sheet picker with "Confirm selection". Knockout
pickers offer positions such as "Group A · 1st" and "Winner of Semi Final ·
Match 13". "Review fixture" -> "Confirm & create fixture" -> "<a> vs <b> is
scheduled for Fri, 13 Nov · 9:00 AM."

Most labels here span several lines ("First player\\nLisa"). Rows are
therefore found in the page source by their label and tapped at their centre
(tap_row), which proved reliable during the manual run, instead of putting
line breaks into UiAutomator or XPath selectors.
"""

import logging
import re
import time
import xml.etree.ElementTree as ElementTree

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from pages.tournament_registration_page import TournamentRegistrationPage
from utils.fixture_planner import GroupSlot, Player, ResultSlot
from utils.helpers import by_label, by_uia, by_xpath, calendar_label

log = logging.getLogger(__name__)

BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
SCHEDULED_COUNT = re.compile(r"^Scheduled \((\d+)\)$")
GROUP_CARD = re.compile(r"^[A-Z]\n(Group [A-Z])\n(?:(\d+) teams?|Empty) · (\d+) qualify")
GROUP_MEMBER = re.compile(r"^[^\n]{1,3}\n([^\n]+)\n[^\n]+$")
AUTO_SPLIT_SUMMARY = re.compile(r"^(\d+) teams → (\d+) groups?")
STAGE_ROW = re.compile(r"^(\d+)\n(League|Quarter Final|Semi Final|Third Place|Final)\n")
MATCH_NUMBER = re.compile(r"· Match (\d+)$")
DATE_LINE = re.compile(r"^\d{1,2} [A-Z][a-z]{2}( \d{4})? [–-] \d{1,2} [A-Z][a-z]{2} \d{4}$")
STAGE_ORDER = ("League", "Quarter Final", "Semi Final", "Third Place", "Final")


def scheduled_text(when):
    """The app's start-time format, e.g. 'Fri, 13 Nov · 9:00 AM'."""
    hour = when.hour % 12 or 12
    return f"{when:%a}, {when.day} {when:%b} · {hour}:{when:%M} {when:%p}"


def button(label):
    """A Button with this exact label (screen titles can share the label)."""
    return by_xpath(f'//android.widget.Button[@content-desc="{label}"]')


def _bounds(node):
    match = BOUNDS.match(node.get("bounds", ""))
    return tuple(map(int, match.groups())) if match else None


class TournamentFixturesPage(TournamentRegistrationPage):
    """Matches tab setup, Groups & stages and the manual fixture form."""

    # -- Tournament Details, Matches tab -----------------------------------
    MATCHES_TAB = by_xpath("//*[starts-with(@content-desc, 'Matches') and contains(@content-desc, 'Tab ')]")
    SETUP_CARD = by_uia('new UiSelector().descriptionStartsWith("Tournament setup")')
    GROUPS_AND_STAGES = button("Groups & stages")
    CREATE_FIXTURES = button("Create Fixtures")
    SCHEDULED_TAB = by_xpath("//*[starts-with(@content-desc, 'Scheduled')]")

    # -- Groups & stages ---------------------------------------------------
    BACK = by_label("Back")
    AUTO_SPLIT = by_label("Auto-split")
    AUTO_SPLIT_TITLE = by_label("Auto-split into groups")
    AUTO_SPLIT_SUMMARY = by_xpath("//*[contains(@content-desc, ' teams → ')]")
    SPLIT_BUTTON = by_xpath("//android.widget.Button[starts-with(@content-desc, 'Split into ')]")
    ASSIGN_TEAMS = by_xpath("//*[starts-with(@content-desc, 'Assign teams')]")
    # Progress popup while a split is saved, e.g. "Splitting into 2 groups…".
    SPLITTING = by_xpath("//*[starts-with(@content-desc, 'Splitting into')]")
    ADD_STAGES = by_label("Add stages")
    ADD_N_STAGES = by_xpath(
        "//android.widget.Button[starts-with(@content-desc, 'Add ') and contains(@content-desc, ' stage')"
        " and @content-desc != 'Add stage' and @content-desc != 'Add stages']"
    )

    # -- Create Fixtures ---------------------------------------------------
    CREATION_DIALOG = by_label("Fixtures Creation")
    MANUAL_SELECTION = by_xpath("//*[starts-with(@content-desc, 'Manual Selection')]")
    SMART_AUTO_GENERATE = by_xpath("//*[starts-with(@content-desc, 'Smart Auto-Generate')]")
    DIALOG_NEXT = by_label("NEXT")
    COMING_SOON = by_label("COMING")
    SCRIM = by_label("Scrim")
    FORM_TITLE = by_label("Build your next fixture")
    REVIEW_FIXTURE = by_label("Review fixture")
    READY_TO_REVIEW = by_xpath("//*[starts-with(@content-desc, 'Ready to review')]")
    CONFIRM_CREATE_FIXTURE = by_label("Confirm & create fixture")
    CREATED_MESSAGE = by_xpath("//*[contains(@content-desc, 'is scheduled for')]")

    # Form fields: labels start with these lines, followed by the value.
    STAGE_FIELD = "Tournament stage"
    GROUP_FIELD = "Group"
    FIRST_PLAYER_FIELD = "First player"
    OPPONENT_FIELD = "Opponent"
    MATCH_START_FIELD = "Match start · Required"

    # -- bottom-sheet pickers ----------------------------------------------
    CONFIRM_SELECTION = by_label("Confirm selection")
    CANCEL_SELECTION = by_label("Cancel selection")
    CLEAR_SELECTION = by_label("Clear selection")
    ONE_SELECTED = by_xpath("//*[starts-with(@content-desc, '1 selected')]")
    PICKER_AVAILABLE = by_xpath("//*[contains(@content-desc, ' available')]")

    # -- date / time ---------------------------------------------------------
    DIALOG_OK = by_label("OK")
    DIALOG_CANCEL = by_label("CANCEL")

    # -- page-source rows ----------------------------------------------------

    def rows(self, source=None):
        """[(label, bounds, clickable)] for every labelled node in the page source."""
        root = ElementTree.fromstring((source or self.driver.page_source).encode("utf-8"))
        return [
            (node.get("content-desc"), _bounds(node), node.get("clickable") == "true")
            for node in root.iter()
            if node.get("content-desc") and _bounds(node)
        ]

    def labels(self, source=None):
        return [label for label, _, _ in self.rows(source)]

    def _screen_height(self):
        if getattr(self, "_height", None) is None:
            self._height = self.driver.get_window_size()["height"]
        return self._height

    def _visible(self, box):
        """Tall enough to tap and above the form's fixed footer (hint + Review fixture).

        Rows sliding under the footer or the screen edge report clipped bounds;
        the footer starts at about 86% of the screen height (11 Nov 2026).
        """
        return box[3] - box[1] >= 40 and box[3] <= self._screen_height() * 0.85

    # -- gestures --------------------------------------------------------------
    # UiAutomator2 sometimes rejects a gesture with "Unable to perform W3C
    # actions" (run of 11 Nov 2026, also seen in the logout drawer); the same
    # gesture succeeds a moment later, so rejected gestures are retried.

    def _gesture(self, perform, what, attempts=3, pause=1.5):
        for attempt in range(1, attempts + 1):
            try:
                return perform()
            except WebDriverException as error:
                if "W3C actions" not in (error.msg or "") or attempt == attempts:
                    raise
                log.warning("%s rejected by the device (attempt %s of %s); retrying", what, attempt, attempts)
                time.sleep(pause)

    def tap_at(self, x, y):
        self._gesture(lambda: self.driver.tap([(x, y)]), f"Tap at ({x}, {y})")

    def _drag(self, direction, percent=0.4):
        """Drag the content (finger up for 'down'); falls back to a scroll command if drags keep failing."""
        height = self._screen_height()
        x = self.driver.get_window_size()["width"] // 2
        low, high = int(height * 0.7), int(height * (0.7 - 0.5 * percent))
        start, end = (low, high) if direction == "down" else (high, low)
        try:
            self._gesture(lambda: self.driver.swipe(x, start, x, end, 800), f"Swipe {direction}")
        except WebDriverException as error:
            log.warning("Swipe %s keeps failing (%s); using a scroll command instead", direction, error.msg)
            self.driver.execute_script("mobile: scrollGesture", {
                "left": int(x * 0.2), "top": int(height * 0.3), "width": int(x * 1.6), "height": int(height * 0.4),
                "direction": direction, "percent": percent,
            })

    def _swipe(self, direction, percent=0.7):
        """Scroll; returns False once the screen stops changing (used by scroll_to and friends)."""
        before = self.driver.page_source
        self._drag(direction, percent)
        return self.driver.page_source != before

    def tap_row(self, matches, what, max_swipes=6, directions=("down", "up")):
        """Tap the centre of the first visible row whose label satisfies matches(label).

        Reads the screen once per scroll position (one page-source fetch per
        step) and checks it after every drag, including the last one.
        """
        source = self.driver.page_source
        for direction in directions:
            for swipe in range(max_swipes + 1):
                for label, box, _ in self.rows(source):
                    if matches(label) and self._visible(box):
                        self.tap_at((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
                        time.sleep(0.6)
                        return label
                if swipe == max_swipes:
                    break
                self._drag(direction, 0.4)
                time.sleep(0.4)
                after = self.driver.page_source
                if after == source:
                    break  # nothing more in this direction
                source = after
        raise NoSuchElementException(f"No visible row for {what}")

    def field_value(self, field, source=None):
        """Value shown in a form field, e.g. 'Lisa' for 'First player\\nLisa'."""
        prefix = f"{field}\n"
        for label in self.labels(source):
            if label.startswith(prefix):
                return label[len(prefix):]
        return None

    def tap_field(self, field):
        """Tap a form field, scrolling towards it: fields further down the form than the
        ones on screen are searched downwards first, earlier ones upwards."""
        order = [self.STAGE_FIELD, self.GROUP_FIELD, self.FIRST_PLAYER_FIELD,
                 self.OPPONENT_FIELD, self.MATCH_START_FIELD]
        labels = self.labels()
        shown = [i for i, name in enumerate(order) if any(label.startswith(f"{name}\n") for label in labels)]
        downwards = not shown or order.index(field) >= max(shown)
        self.tap_row(lambda label: label.startswith(f"{field}\n"), f"form field {field!r}",
                     directions=("down", "up") if downwards else ("up", "down"))

    # -- Matches tab -------------------------------------------------------

    def open_tournament(self, name, timeout=30, max_back_presses=5):
        """Open the tournament from wherever the app is.

        The Tournaments list is reached through the bottom navigation, which
        a tournament's details page and its sub-screens do not have (run of
        11 Nov 2026), so step back until the navigation shows first.
        """
        for _ in range(max_back_presses):
            if self.is_present(self.HOME_NAV):
                break
            self.driver.back()
            self.wait_until_stable(2, interval=0.5)
        super().open_tournament(name, timeout)

    def open_matches_tab(self):
        self.scroll_to(self.MATCHES_TAB, directions=("down", "up")).click()
        self.wait_for(self.SETUP_CARD)
        self.wait_until_stable(3)

    def tournament_dates_text(self, max_swipes=6):
        """The tournament's dates, e.g. '13 Nov – 23 Nov 2026'.

        Read from the header's date line (above the "8/8 Players" card) or,
        when the page is scrolled past it, from the Overview tab's "Timeline &
        location" card ("...\\nTournament dates\\n13 Nov 2026 – 23 Nov 2026\\n...").
        Otherwise scrolls up, checking after every swipe, until the page stops
        moving (run of 12 Nov 2026: the page opened scrolled past the header).
        """
        for swipe in range(max_swipes + 1):
            for label in self.labels():
                if DATE_LINE.match(label):
                    return label
                lines = label.split("\n")
                if "Tournament dates" in lines[:-1]:
                    line = lines[lines.index("Tournament dates") + 1]
                    if DATE_LINE.match(line):
                        return line
            if swipe == max_swipes or not self._swipe("up", percent=0.5):
                break
        raise AssertionError("Tournament dates not found on the details page")

    def setup_text(self):
        return self.scroll_to(self.SETUP_CARD, directions=("up", "down")).get_attribute("content-desc")

    def setup_step_done(self, title):
        """True when a setup step shows its tick rather than its number."""
        text = self.setup_text()
        assert title in text, f"Setup step {title!r} is not shown: {text!r}"
        return not re.search(rf"(^|\n)\d\n{re.escape(title)}(\n|$)", text)

    def scheduled_count(self):
        """N from 'Scheduled (N)'; 0 while the tab reads just 'Scheduled'."""
        label = self.scroll_to(self.SCHEDULED_TAB).get_attribute("content-desc")
        match = SCHEDULED_COUNT.match(label)
        return int(match.group(1)) if match else 0

    # -- Groups & stages ---------------------------------------------------

    def open_groups_and_stages(self):
        self.scroll_to(self.GROUPS_AND_STAGES, directions=("down", "up")).click()
        self.wait_for(self.AUTO_SPLIT)
        self.wait_until_stable(3)

    def back_to_matches_tab(self):
        """Back from Groups & stages or the fixture form to the Matches tab."""
        for _ in range(4):
            if self.is_present(self.MATCHES_TAB):
                break
            if self.is_present(self.BACK):
                self.click(self.BACK)
            else:
                self.driver.back()
            self.wait_until_stable(3)
        if not self.is_present(self.SETUP_CARD):
            self.open_matches_tab()

    def stages_listed(self, max_swipes=6):
        """Stage names under Stages, in the app's order (empty when none)."""
        found = {}
        for _ in range(max_swipes + 1):
            for label in self.labels():
                match = STAGE_ROW.match(label)
                if match:
                    found[match.group(2)] = int(match.group(1))
            if not self._swipe("down", percent=0.4):
                break
        return sorted(found, key=found.get)

    def auto_split(self):
        """Open Auto-split, keep the app's proposed group count, split; returns (teams, groups)."""
        self.scroll_to(self.AUTO_SPLIT, directions=("up", "down")).click()
        summary = self.wait_for(self.AUTO_SPLIT_SUMMARY).get_attribute("content-desc")
        teams, groups = map(int, AUTO_SPLIT_SUMMARY.match(summary).groups())
        log.info("Auto-split proposes: %s", summary)
        self.click(self.SPLIT_BUTTON)
        self.wait_until_gone(self.AUTO_SPLIT_TITLE)
        self.wait_until_split(timeout=30)
        self.wait_until_stable(3)
        return teams, groups

    def wait_until_split(self, timeout=30):
        """Wait until the app has saved the split and redrawn the groups.

        The sheet closes at once, but the app keeps showing "Splitting into 2
        groups…" while it saves, and the "Assign teams" card still reads "8
        teams are not in a group" until it has redrawn (seen after ~4 s on
        11 Nov 2026, 16:06), so wait for the card itself.
        """
        try:
            self.wait_until_gone(self.SPLITTING, timeout=timeout)
        except TimeoutException:
            raise AssertionError(f"Still 'Splitting into … groups' after {timeout}s") from None

        def card_text():
            found = self.driver.find_elements(*self.ASSIGN_TEAMS)
            return found[0].get_attribute("content-desc") if found else ""

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=1).until(
                lambda _: "Every team is in a group" in card_text()
            )
        except TimeoutException:
            raise AssertionError(
                f"Groups not updated {timeout}s after Auto-split; the card reads {card_text()!r}"
            ) from None

    def unassigned_message(self):
        return self.scroll_to(self.ASSIGN_TEAMS, directions=("up", "down")).get_attribute("content-desc")

    def group_cards(self, max_swipes=4):
        """{'Group A': (team count, qualifiers), ...} from the group cards."""
        self.scroll_to(self.ASSIGN_TEAMS, directions=("up", "down"))
        cards = {}
        for _ in range(max_swipes + 1):
            for label in self.labels():
                match = GROUP_CARD.match(label)
                if match:
                    cards[match.group(1)] = (int(match.group(2) or 0), int(match.group(3)))
            if not self._swipe("down", percent=0.3):
                break
        return dict(sorted(cards.items()))

    def group_members(self, group, max_swipes=5):
        """Player names in a group, read from its member sheet."""
        self.scroll_to(self.ASSIGN_TEAMS, directions=("up", "down"))
        self.tap_row(lambda label: label.startswith(f"{group[-1]}\n{group}\n"), group)
        self.wait_for(by_label(group))
        names = []
        for _ in range(max_swipes + 1):
            for label in self.labels():
                match = GROUP_MEMBER.match(label)
                if match and match.group(1) not in names:
                    names.append(match.group(1))
            if not self._swipe("down", percent=0.3):
                break
        self.driver.back()
        self.wait_until_gone(by_label(group))
        return names

    def add_stages(self, stages):
        """Tick each stage chip once and add them; returns the 'Add N stages' label used."""
        self.scroll_to(self.ADD_STAGES).click()
        self.wait_for(by_label(stages[0]))
        for stage in stages:
            chip = by_xpath(f'//android.widget.Button[@content-desc="{stage}"]')
            if self.wait_for(chip).get_attribute("selected") != "true":
                self.click(chip)
            WebDriverWait(self.driver, 5).until(
                lambda _: self.wait_for(chip).get_attribute("selected") == "true",
                message=f"The {stage!r} chip is not ticked after tapping it",
            )
        # The button reads "Add stage" for one stage and "Add N stages" for more
        # (run of 11 Nov 2026).
        label = "Add stage" if len(stages) == 1 else f"Add {len(stages)} stages"
        assert self.is_present(by_label(label)), (
            f"Expected the button to read {label!r} with {stages} ticked; "
            f"it reads {[e.get_attribute('content-desc') for e in self.driver.find_elements(*self.ADD_N_STAGES)]}"
        )
        self.click(by_label(label))
        # The sheet's title shares the "Add stages" label with the empty-state button,
        # and both are gone once the stages exist.
        self.wait_until_gone(self.ADD_STAGES)
        self.wait_until_stable(3)
        return label

    # -- Create Fixtures entry ----------------------------------------------

    def open_creation_choice(self):
        """Tap Create Fixtures; returns 'dialog' or 'form' (the app sometimes skips the dialog)."""
        self.scroll_to(self.CREATE_FIXTURES, directions=("down", "up")).click()
        WebDriverWait(self.driver, 20).until(
            lambda _: self.is_present(self.CREATION_DIALOG) or self.is_present(self.FORM_TITLE),
            message="Create Fixtures opened neither the creation dialog nor the form",
        )
        return "dialog" if self.is_present(self.CREATION_DIALOG) else "form"

    def smart_auto_generate_result(self):
        """Choose Smart Auto-Generate; returns 'coming soon' or 'opened', or None when the dialog was skipped."""
        if self.open_creation_choice() == "form":
            self.back_to_matches_tab()
            return None
        self.click(self.SMART_AUTO_GENERATE)
        self.click(self.DIALOG_NEXT)
        WebDriverWait(self.driver, 15).until(
            lambda _: self.is_present(self.COMING_SOON) or not self.is_present(self.CREATION_DIALOG),
            message="Nothing happened after choosing Smart Auto-Generate",
        )
        if not self.is_present(self.COMING_SOON):
            return "opened"
        # The popup's close (X) button has no label: tap the dimmed area above it,
        # or fall back to Back.
        self.click(self.SCRIM)
        try:
            self.wait_until_gone(self.COMING_SOON, timeout=5)
        except TimeoutException:
            self.driver.back()
            self.wait_until_gone(self.COMING_SOON, timeout=5)
        return "coming soon"

    def open_manual_form(self):
        if self.open_creation_choice() == "dialog":
            self.click(self.MANUAL_SELECTION)
            self.click(self.DIALOG_NEXT)
        self.wait_for(self.FORM_TITLE)
        self.wait_until_stable(2)

    # -- pickers -----------------------------------------------------------

    def _open_picker(self, field):
        """Open a field's picker. It can open with an option already selected
        (the form remembers earlier choices); pick() deals with that."""
        self.tap_field(field)
        self.wait_for(self.CANCEL_SELECTION)
        self.wait_until_stable(2, interval=0.5)

    def _selected_options(self):
        """First lines of the open picker's options marked selected."""
        root = ElementTree.fromstring(self.driver.page_source.encode("utf-8"))
        return [
            node.get("content-desc").split("\n")[0]
            for node in root.iter()
            if node.get("selected") == "true" and node.get("content-desc")
            and node.get("class") == "android.widget.Button"
        ]

    # Long pickers (the Final's lists every position, then the locked ones and
    # the players) need more than a handful of swipes; scrolling still stops
    # as soon as the list stops moving (run of 12 Nov 2026).
    PICKER_MAX_SWIPES = 20

    def _scroll_picker_to_top(self):
        # Drags start inside the option list (percent 0.4: 50% -> 70% of the
        # screen), never on the sheet's title or search box, so they scroll
        # the list rather than pulling the sheet down.
        for _ in range(self.PICKER_MAX_SWIPES):
            if not self._swipe("up", percent=0.4):
                break
        assert self.is_present(self.CANCEL_SELECTION), "The picker closed while scrolling it to the top"

    def picker_options(self):
        """{label: enabled} for the open picker's option rows, read top to bottom.

        Rows such as "Group A · 1st\\nAlready used in Match 13" are locked
        (enabled="false"); available ones read e.g. "Lisa\\n0 of 3 matches · Telangana".
        """
        self._scroll_picker_to_top()
        options = {}
        for _ in range(self.PICKER_MAX_SWIPES):
            root = ElementTree.fromstring(self.driver.page_source.encode("utf-8"))
            for node in root.iter():
                label = node.get("content-desc") or ""
                if "\n" in label and _bounds(node) and not label.startswith(("Choose ", "Pick ")):
                    options.setdefault(label, node.get("enabled") == "true")
            if not self._swipe("down", percent=0.3):
                break
        return options

    def picker_rows(self):
        """Labels of all the open picker's option rows, locked ones included,
        e.g. 'Lisa\\n0 of 3 matches · Telangana'."""
        return list(self.picker_options())

    def picker_availability(self):
        return self.wait_for(self.PICKER_AVAILABLE).get_attribute("content-desc")

    def pick(self, row_label, what):
        """Select the picker row whose first line is row_label and confirm.

        The picker's bottom button reads "Clear selection" (disabled) while
        nothing is selected and "Confirm selection" once an option is; a
        selected option is cleared by tapping it again ("Tap again to
        deselect"), never with that button (run of 11 Nov 2026).

        Rows are searched from the top of the list downwards: an earlier read
        of the picker can leave it scrolled to the bottom, and searching
        upwards from there ran out of swipes one row short of "Winner of Semi
        Final · Match 13" in the Final's long picker (run of 12 Nov 2026).
        """
        row = lambda label: label.split("\n")[0] == row_label  # noqa: E731
        if self.is_present(self.ONE_SELECTED):
            selected = self._selected_options()
            if row_label in selected:
                log.info("%s is already selected", what)
                self.click(self.CONFIRM_SELECTION)
                self.wait_until_gone(self.CONFIRM_SELECTION)
                return
            for other in selected:
                log.info("Deselecting %r before choosing %s", other, what)
                self._tap_picker_row(lambda label, other=other: label.split("\n")[0] == other, f"selected {other!r}")
        self._tap_picker_row(row, what)
        WebDriverWait(self.driver, 5).until(
            lambda _: self.is_present(self.CONFIRM_SELECTION),
            message=f"Choosing {what} did not enable 'Confirm selection'",
        )
        self.click(self.CONFIRM_SELECTION)
        self.wait_until_gone(self.CONFIRM_SELECTION)

    def _tap_picker_row(self, matches, what):
        self._scroll_picker_to_top()
        self.tap_row(matches, what, max_swipes=self.PICKER_MAX_SWIPES, directions=("down",))

    def _assert_field(self, field, expected):
        self.wait_until_stable(1, interval=0.5)
        actual = self.field_value(field)
        assert actual == expected, f"{field} shows {actual!r} after choosing {expected!r}"

    def open_first_player_picker(self, stage, group=None):
        self.choose_stage(stage)
        if group:
            self.choose_group(group)
        self._open_picker(self.FIRST_PLAYER_FIELD)

    def open_opponent_picker(self):
        self._open_picker(self.OPPONENT_FIELD)

    def cancel_picker(self):
        self.click(self.CANCEL_SELECTION)
        self.wait_until_gone(self.CANCEL_SELECTION)

    def choose_stage(self, stage):
        if self.field_value(self.STAGE_FIELD) == stage:
            return
        self._open_picker(self.STAGE_FIELD)
        self.pick(stage, f"stage {stage!r}")
        self._assert_field(self.STAGE_FIELD, stage)

    def choose_group(self, group):
        if self.field_value(self.GROUP_FIELD) == group:
            return
        self._open_picker(self.GROUP_FIELD)
        self.pick(group, group)  # group rows are labelled just "Group A"
        self._assert_field(self.GROUP_FIELD, group)

    def resolve_result_slot(self, slot):
        """'Winner of Semi Final · Match 13' for ResultSlot(Winner, Semi Final, 0), read from the open picker.

        Matches are numbered from every row (locked ones too), so slot.index
        keeps pointing at the same match; a locked match fails with the
        app's reason instead of a tap on a row that cannot be selected.
        """
        options = {
            label: enabled for label, enabled in self.picker_options().items() if label.startswith(slot.prefix)
        }
        names = sorted(
            {label.split("\n")[0] for label in options},
            key=lambda name: int(MATCH_NUMBER.search(name).group(1)),
        )
        assert len(names) > slot.index, f"Picker offers no {slot.label}; it lists {list(options)}"
        name = names[slot.index]
        locked = [label for label, enabled in options.items() if label.split("\n")[0] == name and not enabled]
        assert not locked, f"{name} is listed but cannot be selected: {locked[0]!r}"
        return name

    def choose_side(self, field, slot):
        """Pick a player or position for one side; returns the name shown in the app."""
        self._open_picker(field)
        if isinstance(slot, ResultSlot):
            name = self.resolve_result_slot(slot)
        elif isinstance(slot, (Player, GroupSlot)):
            name = slot.label
        else:
            raise TypeError(slot)
        self.pick(name, f"{field} {name!r}")
        self._assert_field(field, name)
        return name

    # -- date and time -------------------------------------------------------

    def open_start_date_picker(self):
        self.tap_field(self.MATCH_START_FIELD)
        self.wait_for(self.DIALOG_OK)

    def cancel_date_picker(self):
        self.click(self.DIALOG_CANCEL)
        self.wait_until_gone(self.DIALOG_CANCEL)

    def set_match_start(self, when):
        self.open_start_date_picker()
        cell = self._show_calendar_day(when.date())
        assert cell is not None, f"{calendar_label(when.date())} is not offered by the date picker"
        assert cell.get_attribute("enabled") == "true", f"{calendar_label(when.date())} cannot be picked"
        cell.click()
        self.click(self.DIALOG_OK)
        # The time picker opens next. A tap on "text input" while it is still
        # opening is lost, so retry until the Hour field appears.
        self.wait_for(self.TIME_TEXT_MODE)
        for _ in range(4):
            if self.is_present(self.TIME_HOUR):
                break
            self.click(self.TIME_TEXT_MODE)
            time.sleep(1)
        hour = when.hour % 12 or 12
        for locator, value in ((self.TIME_HOUR, f"{hour:02d}"), (self.TIME_MINUTE, f"{when.minute:02d}")):
            self.wait_for(locator).click()
            field = self.wait_for(locator)
            field.clear()
            field.send_keys(value)
        self.click(by_label(when.strftime("%p")))
        self.click(self.DIALOG_OK)
        self.wait_until_gone(self.DIALOG_OK)
        self.wait_until_stable(1, interval=0.5)
        expected = scheduled_text(when)
        actual = self.field_value(self.MATCH_START_FIELD)
        assert actual == expected, f"Match start shows {actual!r}, expected {expected!r}"

    # -- creating a fixture --------------------------------------------------

    def is_ready_to_review(self):
        return self.is_present(self.READY_TO_REVIEW)

    def create_fixture(self, fixture):
        """Fill and submit the manual form for a planned fixture; returns the app's message."""
        self.choose_stage(fixture.stage)
        if fixture.group:
            self.choose_group(fixture.group)
        first = self.choose_side(self.FIRST_PLAYER_FIELD, fixture.first)
        second = self.choose_side(self.OPPONENT_FIELD, fixture.second)
        self.set_match_start(fixture.start)
        assert self.is_ready_to_review(), f"Form not ready to review for {fixture}"

        self.scroll_to(self.REVIEW_FIXTURE).click()
        pairing = f"{first}  vs  {second}"
        self.wait_for(by_label(pairing))
        assert self.is_present(by_label(scheduled_text(fixture.start))), (
            f"Review does not show {scheduled_text(fixture.start)!r} for {pairing}"
        )
        self.click(self.CONFIRM_CREATE_FIXTURE)
        self.wait_until_gone(self.CONFIRM_CREATE_FIXTURE, timeout=30)

        expected = f"{first} vs {second} is scheduled for {scheduled_text(fixture.start)}."
        try:
            self.scroll_to(by_label(expected), max_swipes=4, directions=("up", "down"))
        except NoSuchElementException:
            shown = [e.get_attribute("content-desc") for e in self.driver.find_elements(*self.CREATED_MESSAGE)]
            raise AssertionError(f"No confirmation for {fixture}; messages shown: {shown}") from None
        log.info("Created: %s", expected)
        self._show_form_fields()
        return expected

    def _show_form_fields(self):
        """After a fixture is created the form is back at its top, under the
        "Fixture created" card; one deliberate scroll brings the fields up so
        the next fixture's lookups need no searching."""
        self.wait_until_stable(2, interval=0.5)
        self._drag("down", 0.7)
        time.sleep(0.5)

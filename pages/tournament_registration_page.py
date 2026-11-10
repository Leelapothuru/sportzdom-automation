"""Page object for registering a player in a published tournament.

Flow (verified with Appium Inspector on 6 Nov 2026, Sportzdom 1.4.6):
Tournaments -> Upcoming -> search by name -> "View tournament" -> Tournament
Details -> "Register now" -> Rules dialog ("Agree") -> "Successfully registered"
popup ("Ok"). Afterwards the button reads "Registered" and is disabled, and
the players count (e.g. "1/16") goes up by one.

An ineligible player gets a popup instead of the Rules dialog, e.g.
"Sorry, your age doesn't meet the requirement to register this tournament."

Officials (verified 6 Nov 2026) are listed at the bottom of the Overview tab,
one section per role, e.g. "Organizers\\n1", "Referees\\n2", "Scorers\\n1", each
with one image per official labelled with their profile name. "Grounds" is
listed in the same way but is not a role. The app does not stop officials from
registering, so callers must skip them.
"""

import logging
import re
import xml.etree.ElementTree as ElementTree

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from pages.tournament_page import TournamentsPage
from utils.helpers import by_label, by_uia, by_xpath, description_contains

log = logging.getLogger(__name__)

PLAYERS_REGISTERED = re.compile(r"^(\d+) players? registered$")
# An officials section on the Overview tab: its title and how many it lists.
ROLE_SECTION = re.compile(r"^([A-Za-z][A-Za-z &]*)\n(\d+)$")
NOT_A_ROLE = ("Grounds",)
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def _bounds(node):
    match = BOUNDS.match(node.get("bounds", ""))
    return tuple(map(int, match.groups())) if match else None


def _inside(inner, outer):
    """True when the centre of the inner bounds lies within the outer bounds."""
    x, y = (inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2
    return outer[0] <= x <= outer[2] and outer[1] <= y <= outer[3]


def officials_on_screen(page_source):
    """{role: {names}} for the officials sections drawn in this page source."""
    nodes = list(ElementTree.fromstring(page_source.encode("utf-8")).iter())
    images = [
        (node.get("content-desc"), _bounds(node)) for node in nodes
        if node.get("class") == "android.widget.ImageView" and node.get("content-desc") and _bounds(node)
    ]
    found = {}
    for node in nodes:
        match = ROLE_SECTION.match(node.get("content-desc") or "")
        if not match or match.group(1) in NOT_A_ROLE or not _bounds(node):
            continue
        section = _bounds(node)
        found.setdefault(match.group(1), {"count": int(match.group(2)), "names": set()})
        found[match.group(1)]["names"].update(name for name, box in images if _inside(box, section))
    return found


class TournamentRegistrationPage(TournamentsPage):
    """Tournament details and registration; list navigation comes from TournamentsPage."""

    VIEW_TOURNAMENT = by_label("View tournament")
    DETAILS_TITLE = by_label("Tournament Details")
    # Players count on the details page, e.g. "0/16".
    PLAYER_COUNT = by_uia('new UiSelector().descriptionMatches("[0-9]+/[0-9]+")')
    # The registration button sits directly below the players progress bar. Its
    # label is the registration state ("Register now", "Registered", ...).
    REGISTRATION_BUTTON = by_xpath("(//android.widget.ProgressBar/following::android.widget.Button)[1]")
    REGISTER_NOW = by_label("Register now")
    REGISTERED = by_label("Registered")
    PLAYERS_REGISTERED_LABEL = by_uia('new UiSelector().descriptionMatches("[0-9]+ players? registered")')
    # Details tabs are labelled e.g. "Teams\nTab 4 of 8".
    TEAMS_TAB = by_xpath("//*[starts-with(@content-desc, 'Teams') and contains(@content-desc, 'Tab ')]")

    # Rules dialog shown after "Register now".
    RULES_DIALOG = description_contains("Do you agree to the Rules?")
    RULES_AGREE = by_label("Agree")
    RULES_CANCEL = by_label("Cancel")
    VIEW_RULES = by_label("View rules")

    # Result popup: a full-screen "Dismiss" scrim, a message and an "Ok" button.
    POPUP_OK = by_label("Ok")
    POPUP_SCRIM = "Dismiss"
    # While a popup is open only its own nodes are in the hierarchy.
    DESCRIBED = by_xpath("//*[string-length(@content-desc) > 0]")
    SUCCESS_MESSAGE = "Successfully registered"

    def _swipe(self, direction, percent=0.7):
        """Scroll with a plain finger drag; returns False once the screen stops changing.

        The Upcoming results and the details page ignore "mobile: scrollGesture"
        (6 Nov 2026), but a drag from 70% to 35% of the screen height scrolls them.
        Starting lower (80%) lands on the list's bottom edge and does nothing.
        """
        before = self.driver.page_source
        size = self.driver.get_window_size()
        x = size["width"] // 2
        low, high = int(size["height"] * 0.7), int(size["height"] * (0.7 - 0.35 * percent / 0.7))
        start, end = (low, high) if direction == "down" else (high, low)
        self.driver.swipe(x, start, x, end, 800)
        return self.driver.page_source != before

    # -- finding the tournament -------------------------------------------

    def open_tournament(self, name, timeout=30):
        """Open the details page of the Upcoming tournament called name."""
        self.open_tab("Upcoming")
        self.search_tournaments(name)
        self.wait_until_stable(5)
        try:
            title = self.scroll_to(by_label(name), max_swipes=6)
        except NoSuchElementException:
            raise AssertionError(f"{name!r} not found in Upcoming") from None
        # Tapping the title only opens a "Tournament Name" popup; the card opens
        # from its "View tournament" button. After scrolling, UiAutomator often
        # leaves that button out of the hierarchy although it is drawn, so when
        # it is not reported, tap it where it sits relative to the title:
        # title top + 308 px, x 709 px, measured on a 1080 px wide screen
        # (6 Nov 2026) and scaled to this screen's width for other devices.
        try:
            self.wait_for(self.VIEW_TOURNAMENT, 5)
            self.click(self.VIEW_TOURNAMENT)
        except TimeoutException:
            rect = title.rect
            scale = self.driver.get_window_size()["width"] / 1080
            log.info("'View tournament' not in the hierarchy; tapping it below the title")
            self.driver.tap([(int(709 * scale), rect["y"] + int(308 * scale))])
        try:
            self.wait_for(self.DETAILS_TITLE, timeout)
        except TimeoutException:
            raise AssertionError(f"'View tournament' on the {name!r} card did not open its details") from None
        self.wait_for(by_label(name), timeout)
        self.wait_for(self.REGISTRATION_BUTTON, timeout)

    # -- details page state ----------------------------------------------

    def player_count(self):
        """(registered, capacity) from the details page, e.g. (1, 16)."""
        registered, capacity = self.scroll_to(self.PLAYER_COUNT, directions=("up", "down")) \
            .get_attribute("content-desc").split("/")
        return int(registered), int(capacity)

    def registration_state(self):
        """Label and enabled state of the registration button, e.g. ('Registered', False)."""
        button = self.scroll_to(self.REGISTRATION_BUTTON, directions=("up", "down"))
        return button.get_attribute("content-desc"), button.get_attribute("enabled") == "true"

    def officials(self, max_swipes=10):
        """{role: [profile names]} from the Overview tab of the open details page.

        Scrolls down through the Overview, collecting every officials section,
        then back to the top. Fails when a section lists fewer names than its
        count (e.g. a row that scrolls sideways), so an official is never
        mistaken for a player.
        """
        found = officials_on_screen(self.driver.page_source)
        for _ in range(max_swipes):
            if not self._swipe("down"):
                break
            for role, section in officials_on_screen(self.driver.page_source).items():
                found.setdefault(role, {"count": section["count"], "names": set()})["names"].update(section["names"])
        for role, section in found.items():
            if len(section["names"]) < section["count"]:
                raise AssertionError(
                    f"Read {len(section['names'])} of {section['count']} {role}: {sorted(section['names'])}"
                )
        self.scroll_to(self.PLAYER_COUNT, directions=("up",))
        return {role: sorted(section["names"]) for role, section in found.items()}

    def players_listed_on_teams_tab(self, timeout=20):
        """Open the Teams tab and return N from its 'N player(s) registered' line."""
        self.scroll_to(self.TEAMS_TAB).click()
        self.wait_for(self.PLAYERS_REGISTERED_LABEL, timeout)
        return self.players_registered_label()

    def players_registered_label(self):
        """Number from 'N player(s) registered' under the tabs, or None when not shown."""
        found = self.driver.find_elements(*self.PLAYERS_REGISTERED_LABEL)
        if not found:
            return None
        match = PLAYERS_REGISTERED.match(found[0].get_attribute("content-desc"))
        return int(match.group(1)) if match else None

    # -- registering ------------------------------------------------------

    def popup_message(self):
        """Text of the open result popup (everything except the scrim and Ok)."""
        texts = [element.get_attribute("content-desc") for element in self.driver.find_elements(*self.DESCRIBED)]
        return " ".join(text for text in texts if text not in (self.POPUP_SCRIM, "Ok")).strip()

    def _wait_for_rules_or_popup(self, timeout):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda _: self.is_present(self.RULES_DIALOG) or self.is_present(self.POPUP_OK),
                message="Neither the Rules dialog nor a result popup appeared",
            )
        except TimeoutException as error:
            raise AssertionError(str(error.msg)) from None

    def register(self, timeout=30):
        """Tap Register now, agree to the rules, and return the result popup's message.

        The popup is closed with Ok afterwards. When the app shows a popup
        instead of the Rules dialog (e.g. an eligibility message), that
        message is returned without agreeing to anything.
        """
        self.scroll_to(self.REGISTER_NOW, directions=("up", "down"))
        self.click(self.REGISTER_NOW)
        self._wait_for_rules_or_popup(timeout)
        if self.is_present(self.RULES_DIALOG):
            self.click(self.RULES_AGREE)
            self.wait_for(self.POPUP_OK, timeout)
        message = self.popup_message()
        log.info("Registration result: %s", message)
        self.click(self.POPUP_OK)
        self.wait_until_gone(self.POPUP_OK)
        self.wait_until_stable(3)
        return message

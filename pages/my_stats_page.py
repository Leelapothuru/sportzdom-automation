"""Page object for the Profile drawer's My Stats screen."""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree import ElementTree

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.myprofile_page import MyProfilePage
from utils.configuration import get_wait_timeout_seconds


@dataclass(frozen=True)
class StatCount:
    """A visible statistics label and its displayed count, when exposed together."""

    label: str
    value: int | None


class MyStatsPage:
    """Interact with and validate the My Stats tabs for a signed-in user."""

    MATCHES_TAB = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionStartsWith("Sports")',
    )
    TEAMS_TAB = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionStartsWith("Teams")',
    )
    STATS_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Stats")')
    BADGES_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("Badges")')
    FIRST_MATCH_BADGE = (AppiumBy.ACCESSIBILITY_ID, "\u00d718\nFirst match")
    CERTIFICATE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().description("Certificate").instance(0)',
    )
    CERTIFICATE_CLOSE_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().description("Close")',
    )
    PROFILE_SEASON_LABEL = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Season")',
    )
    METRIC_LABELS = ("Played", "Won", "Lost", "Drawn")
    PROFILE_STAT_LABELS = ("Matches", "Wins", "Win rate", "Tournaments")

    def __init__(self, driver, timeout: float | None = None):
        self.driver = driver
        self.timeout = get_wait_timeout_seconds() if timeout is None else timeout
        self.wait = WebDriverWait(driver, self.timeout)
        self.profile = MyProfilePage(driver, timeout=self.timeout)

    def _click(self, locator) -> None:
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def open(self) -> None:
        """Open Profile, then the My Stats item in its end drawer."""
        source = self.driver.page_source
        if 'pane-title="Player Statistics"' in source and 'content-desc="Teams (' in source:
            return
        self.profile.open_my_stats()
        self.wait.until(EC.visibility_of_element_located(self.MATCHES_TAB))

    def select_matches(self) -> None:
        """Select the Sports section containing the user's match totals."""
        self._click(self.MATCHES_TAB)

    def select_teams(self) -> None:
        self._click(self.TEAMS_TAB)

    def select_stats(self) -> None:
        self._click(self.STATS_TAB)

    def select_badges(self) -> None:
        self._click(self.BADGES_TAB)

    def _visible_ui_signatures(self) -> set[str]:
        """Read a fresh UIAutomator snapshot without caching native elements.

        The app redraws while records and adverts load.  Calling ``get_attribute``
        on an element returned by a prior ``//*`` query then raises
        ``StaleElementReferenceException``.  Page source is an atomic snapshot,
        so it is safe to use for the scroll audit.
        """
        root = ElementTree.fromstring(self.driver.page_source)
        signatures = set()
        for node in root.iter():
            attributes = node.attrib
            if attributes.get("displayed", "true").lower() != "true":
                continue
            signatures.add(
                "|".join(
                    attributes.get(attribute, "")
                    for attribute in ("text", "content-desc", "resource-id", "class", "bounds")
                )
            )
        return signatures

    def audit_visible_ui_to_end(self, max_swipes: int = 12) -> set[str]:
        """Assert a tab has UI and record every distinct visible item to scroll end.

        The source snapshot is used to detect the end of a list, avoiding a fixed
        device-size assumption.  A short upward swipe deliberately leaves the tab
        header reachable for the next tab selection.
        """
        seen: set[str] = set()
        unchanged_swipes = 0

        for _ in range(max_swipes):
            visible = self._visible_ui_signatures()
            assert visible, "No UI elements are visible in the selected My Stats tab"
            before = len(seen)
            seen.update(visible)

            window = self.driver.get_window_size()
            x = window["width"] // 2
            self.driver.swipe(x, int(window["height"] * 0.82), x, int(window["height"] * 0.30), 500)

            # Some views animate after a swipe, so inspect the next screen before
            # deciding that the scroll position did not change.
            new_visible = self._visible_ui_signatures()
            seen.update(new_visible)
            unchanged_swipes = unchanged_swipes + 1 if len(seen) == before else 0
            if unchanged_swipes >= 2:
                break

        assert seen, "No My Stats UI was collected during the scroll audit"
        return seen

    def scroll_to_top(self, max_swipes: int = 12) -> None:
        """Scroll to the profile summary without repeatedly dumping the full hierarchy."""
        window = self.driver.get_window_size()
        x = window["width"] // 2
        for swipe_count in range(max_swipes + 1):
            if any(
                element.is_displayed()
                for element in self.driver.find_elements(*self.PROFILE_SEASON_LABEL)
            ):
                return
            if swipe_count == max_swipes:
                break
            self.driver.swipe(x, int(window["height"] * 0.30), x, int(window["height"] * 0.82), 500)
        raise TimeoutException("The My Stats profile summary was not visible after scrolling to the top")

    @staticmethod
    def _bounds(node) -> tuple[int, int, int, int] | None:
        match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.attrib.get("bounds", ""))
        return tuple(map(int, match.groups())) if match else None

    def assert_profile_header_and_stats_visible(self) -> str:
        """Verify the profile name, display picture, and four summary metrics."""
        root = ElementTree.fromstring(self.driver.page_source)
        visible_nodes = [
            node
            for node in root.iter()
            if node.attrib.get("displayed", "true").lower() == "true"
        ]
        season_node = next(
            (
                node
                for node in visible_nodes
                if "Season" in node.attrib.get("content-desc", "")
            ),
            None,
        )
        assert season_node is not None, "Profile season summary is not visible"
        season_bounds = self._bounds(season_node)
        assert season_bounds is not None, "Profile season summary has no screen bounds"

        name_candidates = []
        for node in visible_nodes:
            description = node.attrib.get("content-desc", "").strip()
            bounds = self._bounds(node)
            if (
                node.attrib.get("class") == "android.view.View"
                and description
                and bounds
                and abs(bounds[0] - season_bounds[0]) <= 4
                and bounds[3] <= season_bounds[1]
            ):
                name_candidates.append((bounds[3], description, bounds))
        assert name_candidates, "Profile name is not visible beside the display picture"
        _, profile_name, name_bounds = max(name_candidates)
        assert profile_name.strip(), "Profile name is empty"

        has_profile_image = any(
            node.attrib.get("class") == "android.widget.ImageView"
            and (bounds := self._bounds(node)) is not None
            and bounds[0] < name_bounds[0]
            and bounds[1] < name_bounds[3]
            and bounds[3] > name_bounds[1]
            for node in visible_nodes
        )
        assert has_profile_image, "Profile display picture is not visible"

        described_nodes = [
            (node.attrib.get("content-desc", "").strip(), self._bounds(node))
            for node in visible_nodes
            if node.attrib.get("content-desc", "").strip()
        ]
        numeric_nodes = [
            (description, bounds)
            for description, bounds in described_nodes
            if bounds and re.fullmatch(r"\d+(?:\.\d+)?%?", description)
        ]
        stat_values = {}
        for label in self.PROFILE_STAT_LABELS:
            label_bounds = next(
                (bounds for description, bounds in described_nodes if description == label),
                None,
            )
            assert label_bounds is not None, f"{label} summary label is not visible"
            label_center = (label_bounds[0] + label_bounds[2]) / 2
            candidates = [
                (bounds[3], value)
                for value, bounds in numeric_nodes
                if abs((bounds[0] + bounds[2]) / 2 - label_center) <= 30
                and bounds[3] <= label_bounds[1]
            ]
            assert candidates, f"{label} summary value is not visible"
            stat_values[label] = max(candidates)[1]

        matches = int(stat_values["Matches"])
        wins = int(stat_values["Wins"])
        win_rate = float(stat_values["Win rate"].rstrip("%"))
        expected_win_rate = round(wins * 100 / matches) if matches else 0
        assert win_rate == expected_win_rate, (
            f"Displayed win rate {win_rate}% does not match {wins} wins "
            f"from {matches} matches"
        )
        return profile_name

    def assert_all_badges_displayed(self, max_swipes: int = 12) -> None:
        """Verify the earned count and every badge card in the Achievements list."""
        badge_cards = set()
        previous_frame = None
        unchanged_swipes = 0
        summary_pattern = re.compile(r"Achievements\s+(\d+)\s+of\s+(\d+)")
        summary_counts = None
        excluded_descriptions = {"Player Statistics", "Badges", "2026", "2025"}

        window = self.driver.get_window_size()
        x = window["width"] // 2
        for swipe_count in range(max_swipes + 1):
            root = ElementTree.fromstring(self.driver.page_source)
            current_frame = set()
            for node in root.iter():
                attributes = node.attrib
                if attributes.get("displayed", "true").lower() != "true":
                    continue
                description = attributes.get("content-desc", "").strip()
                if description.startswith("Achievements"):
                    match = summary_pattern.search(description)
                    if match:
                        summary_counts = (int(match.group(1)), int(match.group(2)))
                if (
                    attributes.get("clickable") == "true"
                    and attributes.get("class")
                    in {"android.view.View", "android.widget.ProgressBar"}
                    and description
                    and description not in excluded_descriptions
                    and not description.startswith(("Sports (", "Teams ("))
                    and not re.fullmatch(r"20\d{2}", description)
                ):
                    current_frame.add((attributes.get("class"), description, attributes.get("bounds", "")))

            for _element_class, description, _bounds in current_frame:
                badge_cards.add(description)

            if swipe_count == max_swipes:
                break
            unchanged_swipes = unchanged_swipes + 1 if current_frame == previous_frame else 0
            if unchanged_swipes >= 2:
                break
            previous_frame = current_frame
            self.driver.swipe(
                x,
                int(window["height"] * 0.82),
                x,
                int(window["height"] * 0.30),
                500,
            )

        assert summary_counts is not None, "Achievements earned/total summary is not visible"
        earned_count, total_count = summary_counts
        assert 0 <= earned_count <= total_count, "Achievements summary has invalid counts"
        assert len(badge_cards) == total_count, (
            f"Achievements reports {total_count} badges, but "
            f"{len(badge_cards)} unique badge cards were visible"
        )

    def open_first_match_badge(self) -> tuple[str, str]:
        """Open First match and return the first certificate's sport and date."""
        self._click(self.FIRST_MATCH_BADGE)
        self.wait.until(
            EC.visibility_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID, "Played your first match")
            )
        )
        self.wait.until(EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, "History")))

        root = ElementTree.fromstring(self.driver.page_source)
        certificate_nodes = [
            node
            for node in root.iter()
            if node.attrib.get("class") == "android.widget.Button"
            and node.attrib.get("content-desc") == "Certificate"
            and node.attrib.get("displayed", "true").lower() == "true"
        ]
        certificate_rows = [
            (bounds[1], node, bounds)
            for node in certificate_nodes
            if (bounds := self._bounds(node)) is not None
        ]
        assert certificate_rows, "No certificate is available in the First match history"
        _, _first_button, button_bounds = min(certificate_rows)

        row_descriptions = []
        date_pattern = re.compile(r"\d{1,2}\s+[A-Za-z]{3}\s+\d{4}")
        for node in root.iter():
            description = node.attrib.get("content-desc", "").strip()
            bounds = self._bounds(node)
            if (
                node.attrib.get("class") == "android.view.View"
                and description
                and bounds
                and bounds[2] < button_bounds[0]
                and bounds[1] >= button_bounds[1] - 8
                and bounds[3] <= button_bounds[3] + 8
            ):
                row_descriptions.append(description)

        expected_date = next(
            (description for description in row_descriptions if date_pattern.fullmatch(description)),
            None,
        )
        expected_sport = next(
            (
                description
                for description in row_descriptions
                if not date_pattern.fullmatch(description)
            ),
            None,
        )
        assert expected_sport, "Sport was not shown for the first certificate"
        assert expected_date, "Date was not shown for the first certificate"
        return expected_sport, expected_date

    def open_first_certificate(self) -> None:
        """Open the first Certificate action shown in the selected badge history."""
        self._click(self.CERTIFICATE_BUTTON)
        self.wait.until(
            EC.visibility_of_element_located(
                (AppiumBy.ACCESSIBILITY_ID, "CERTIFICATE")
            )
        )
        self.wait.until(EC.element_to_be_clickable(self.CERTIFICATE_CLOSE_BUTTON))

    def assert_certificate_details(
        self,
        profile_name: str,
        expected_sport: str,
        expected_date: str,
    ) -> None:
        """Verify the certificate UI and that it belongs to the signed-in profile."""
        root = ElementTree.fromstring(self.driver.page_source)
        descriptions = [
            node.attrib.get("content-desc", "").strip()
            for node in root.iter()
            if node.attrib.get("displayed", "true").lower() == "true"
            and node.attrib.get("content-desc", "").strip()
        ]
        required_details = (
            "SPORTZDOM",
            "CERTIFICATE",
            "OF ACHIEVEMENT",
            "This certificate is proudly presented to",
            "for",
            "First match",
            "Played your first match",
            "Date",
            "Certificate no.",
            "sportzdom.com",
            "Close",
            "Share",
        )
        for detail in required_details:
            assert detail in descriptions, f"Certificate UI is missing {detail!r}"

        normalize_name = lambda value: re.sub(r"\s+", "", value).rstrip(".").casefold()
        assert any(
            normalize_name(description) == normalize_name(profile_name)
            for description in descriptions
        ), "Certificate recipient does not match the signed-in profile"
        assert expected_sport.casefold() in {
            description.casefold() for description in descriptions
        }, "Certificate sport does not match the selected history entry"
        assert expected_date in descriptions, "Certificate date does not match the selected history entry"
        assert any(re.fullmatch(r"SZD-\d+", description) for description in descriptions), (
            "Certificate number is missing or malformed"
        )

    def close_certificate(self) -> None:
        """Close the certificate and verify the badge history is visible again."""
        self._click(self.CERTIFICATE_CLOSE_BUTTON)
        self.wait.until(EC.invisibility_of_element_located(self.CERTIFICATE_CLOSE_BUTTON))
        self.wait.until(EC.visibility_of_element_located((AppiumBy.ACCESSIBILITY_ID, "History")))

    def visible_match_counts(self) -> dict[str, StatCount]:
        """Confirm the Played, Won, Lost and Drawn metrics are displayed.

        Match rows are data-dependent.  For a player with no loaded records, the
        app renders only the ``P=Played W=Won L=Lost D=Drawn`` legend, not four
        zero values.  That is a valid empty-state UI, so values are recorded as
        ``None`` instead of failing the whole tab test.
        """
        counts: dict[str, StatCount] = {}
        for label in self.METRIC_LABELS:
            locator = (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().descriptionContains("{label}")',
            )
            elements = self.driver.find_elements(*locator)
            if not elements:
                elements = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{label}")',
                )
            visible = next((element for element in elements if element.is_displayed()), None)
            assert visible is not None, f"{label} match statistic is not visible"

            text = " ".join(
                str(visible.get_attribute(attribute) or "")
                for attribute in ("text", "content-desc")
            )
            match = re.search(r"\\d+", text)
            counts[label] = StatCount(label, int(match.group()) if match else None)

        return counts

    def assert_coming_soon(self) -> None:
        """Verify the selected unfinished tab presents its Coming Soon state."""
        try:
            self.wait.until(
                lambda driver: any(
                    element.is_displayed()
                    for locator in (
                        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Coming Soon")'),
                        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("Coming Soon")'),
                    )
                    for element in driver.find_elements(*locator)
                )
            )
        except TimeoutException as exc:
            raise AssertionError("The selected My Stats tab does not show 'Coming Soon'") from exc

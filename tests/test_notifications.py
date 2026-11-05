"""End-to-end coverage for all home Notifications tabs."""

from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException

from pages.Notifications_page import NotificationsPage


SCREENSHOTS = Path("screenshots")


def _screenshot(driver, name: str) -> None:
    SCREENSHOTS.mkdir(exist_ok=True)
    driver.save_screenshot(str(SCREENSHOTS / name))


class _TabElement:
    def __init__(self, driver, label: str):
        self.driver = driver
        self.label = label

    def is_displayed(self) -> bool:
        return True

    def click(self) -> None:
        self.driver.selected = self.label


class _TabDriver:
    def __init__(self, label):
        self.label = label
        self.selected = None

    def find_elements(self, _by, selector: str):
        if self.label and f'"{self.label}"' in selector:
            return [_TabElement(self, self.label)]
        return []

    def get_window_size(self):
        return {"width": 720, "height": 1570}

    def swipe(self, *_args) -> None:
        pass

    def execute_script(self, *_args, **_kwargs) -> None:
        pass


class _UiSnapshotDriver:
    def __init__(self, page_source: str):
        self.page_source = page_source

    def get_window_size(self):
        return {"width": 720, "height": 1570}


@pytest.mark.parametrize(
    ("method_name", "tab_label"),
    [
        ("select_match_requests", "Requests"),
        ("select_match_requests", "Match Request"),
        ("select_connections", "Connections"),
        ("select_team_request", "Teams"),
        ("select_team_request", "Team Request"),
        ("select_general", "Updates"),
        ("select_general", "General"),
    ],
)
def test_tab_selection_supports_current_and_legacy_labels(method_name, tab_label):
    driver = _TabDriver(tab_label)
    notifications = NotificationsPage(driver, timeout=0.1)

    getattr(notifications, method_name)()

    assert driver.selected == tab_label


def test_match_requests_tab_supports_count_badge():
    class CountedRequestsDriver(_TabDriver):
        def find_elements(self, by, selector: str):
            if 'textContains("Requests")' in selector:
                return [_TabElement(self, "Requests 3")]
            return super().find_elements(by, selector)

    driver = CountedRequestsDriver("Requests 3")
    notifications = NotificationsPage(driver, timeout=0.1)

    notifications.select_match_requests()

    assert driver.selected == "Requests 3"


def test_missing_notification_tab_fails_explicitly():
    notifications = NotificationsPage(_TabDriver(None), timeout=0)

    with pytest.raises(TimeoutException, match="Connections tab is not visible"):
        notifications.select_connections()


def test_tab_selection_scrolls_horizontally_when_tab_is_offscreen():
    class HorizontallyScrollableTabDriver(_TabDriver):
        def __init__(self):
            super().__init__("Connections")
            self.scrolled = False

        def find_elements(self, by, selector: str):
            if not self.scrolled:
                return []
            return super().find_elements(by, selector)

        def swipe(self, *_args) -> None:
            self.scrolled = True

    driver = HorizontallyScrollableTabDriver()
    notifications = NotificationsPage(driver, timeout=0.1)

    notifications.select_connections()

    assert driver.scrolled
    assert driver.selected == "Connections"


def test_accept_first_requests_accepts_at_most_two(monkeypatch):
    notifications = NotificationsPage(_TabDriver(None), timeout=0.1)
    rows = [
        (400, "Match Request user1"),
        (600, "Match Request user2"),
        (800, "Match Request user3"),
    ]
    clicked = []
    monkeypatch.setattr(notifications, "_request_notification_rows", lambda: rows)
    monkeypatch.setattr(notifications, "_click", lambda locator: clicked.append(locator))
    monkeypatch.setattr("pages.Notifications_page.time.sleep", lambda _seconds: None)

    accepted = notifications.accept_first_requests_if_present()

    assert accepted == 2
    assert len(clicked) == 2


def test_accept_first_requests_skips_empty_tab():
    notifications = NotificationsPage(_TabDriver(None), timeout=0.1)
    notifications._request_notification_rows = lambda: []

    assert notifications.accept_first_requests_if_present() == 0


def test_request_row_detection_skips_connection_empty_state():
    driver = _UiSnapshotDriver(
        '<hierarchy><node bounds="[0,0][720,1570]">'
        '<node class="android.view.ViewGroup" bounds="[20,330][700,468]">'
        '<node text="you dont have any connection requests yet."/></node>'
        '</node></hierarchy>'
    )

    assert NotificationsPage(driver)._request_notification_rows() == []


def test_request_row_detection_finds_notification_card():
    driver = _UiSnapshotDriver(
        '<hierarchy><node bounds="[0,0][720,1570]">'
        '<node class="android.view.ViewGroup" bounds="[20,309][700,464]">'
        '<node text="Match Request"/><node text="user134"/></node>'
        '</node></hierarchy>'
    )

    rows = NotificationsPage(driver)._request_notification_rows()

    assert len(rows) == 1
    assert rows[0][0] == 405
    assert "Match Request" in rows[0][1]


@pytest.mark.integration
def test_notifications_tabs_and_accept_first_requests(driver):
    """Audit notification tabs and accept up to two requests in each request tab."""
    notifications = NotificationsPage(driver)
    notifications.open()

    notifications.select_match_requests()
    _screenshot(driver, "notifications_match_request.png")
    notifications.scroll_to_top()
    notifications.accept_first_requests_if_present(max_requests=2)
    assert notifications.audit_recent_notifications(max_notifications=10)
    notifications.scroll_to_top()

    notifications.select_connections()
    _screenshot(driver, "notifications_connections.png")
    notifications.scroll_to_top()
    notifications.accept_first_requests_if_present(max_requests=2)
    assert notifications.audit_recent_notifications(max_notifications=10)
    notifications.scroll_to_top()

    notifications.select_team_request()
    _screenshot(driver, "notifications_team_request.png")
    assert notifications.audit_recent_notifications(max_notifications=10)
    notifications.scroll_to_top()

    notifications.select_general()
    _screenshot(driver, "notifications_general.png")
    assert notifications.audit_recent_notifications(max_notifications=10)

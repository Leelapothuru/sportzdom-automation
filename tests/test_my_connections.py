"""End-to-end coverage for Profile drawer > My Connections."""

import os
import random
from pathlib import Path

import pytest

from pages.my_connections import MyConnectionsPage


SCREENSHOTS = Path("screenshots")


@pytest.mark.parametrize(
    ("request_count", "expected_actions"),
    [
        (0, []),
        (1, ["accept"]),
        (2, ["accept", "decline"]),
    ],
)
def test_pending_requests_are_handled_by_count(
    monkeypatch,
    request_count,
    expected_actions,
):
    connections = MyConnectionsPage.__new__(MyConnectionsPage)
    actions = []
    monkeypatch.setattr(connections, "pending_request_count", lambda: request_count)
    monkeypatch.setattr(
        connections,
        "accept_one_request_if_present",
        lambda: actions.append("accept") or True,
    )
    monkeypatch.setattr(
        connections,
        "decline_one_request_if_present",
        lambda: actions.append("decline") or True,
    )

    assert connections.handle_pending_requests() == request_count
    assert actions == expected_actions


def test_search_field_scrolls_into_view_before_lookup():
    class SearchField:
        def is_displayed(self):
            return True

        def is_enabled(self):
            return True

    class Driver:
        def __init__(self):
            self.swipes = 0
            self.search_field = SearchField()

        def get_window_size(self):
            return {"width": 720, "height": 1570}

        def find_elements(self, *_locator):
            return [self.search_field] if self.swipes else []

        def swipe(self, *_coordinates):
            self.swipes += 1

    connections = MyConnectionsPage.__new__(MyConnectionsPage)
    connections.driver = Driver()

    assert connections._find_search_field_after_scrolling() is connections.driver.search_field
    assert connections.driver.swipes == 1


def _screenshot(driver, name: str) -> None:
    SCREENSHOTS.mkdir(exist_ok=True)
    driver.save_screenshot(str(SCREENSHOTS / name))


@pytest.mark.integration
@pytest.mark.destructive
@pytest.mark.skipif(
    os.getenv("SPORTZDOM_RUN_DESTRUCTIVE", "false").lower() != "true",
    reason="Set SPORTZDOM_RUN_DESTRUCTIVE=true to allow sending connection requests",
)
def test_my_connections_ui_and_send_two_requests(driver):
    """Audit connections, process pending requests, and discover two users."""
    connections = MyConnectionsPage(driver)
    connections.open()

    connections.select_my_connections()
    _screenshot(driver, "my_connections_before_connect.png")
    assert connections.audit_visible_ui_to_end()
    connections.scroll_to_top()

    connections.select_requests()
    _screenshot(driver, "my_connections_requests_before_connect.png")
    assert connections.audit_visible_ui_to_end()
    connections.scroll_to_top()
    connections.handle_pending_requests()
    _screenshot(driver, "my_connections_requests_after_actions.png")

    connections.select_add_connections()
    _screenshot(driver, "my_connections_discover_before_connect.png")
    assert connections.audit_visible_ui_to_end()
    connections.scroll_to_top()

    user_numbers = random.sample(range(100, 901), 2)
    target_users = [f"user2026.{number}" for number in user_numbers]
    users = connections.send_connection_requests(target_users)
    _screenshot(driver, "my_connections_after_connect.png")
    assert users == target_users

"""Test the gear sort option (distance or recent) for ha_strava."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.config_flow import OptionsFlowHandler
from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_GEAR_ENABLED,
    CONF_GEAR_SORT,
    CONF_GEAR_SORT_DEFAULT,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_NUM_GEAR_SENSORS,
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_PHOTOS,
    DOMAIN,
    GEAR_SORT_DISTANCE,
    GEAR_SORT_RECENT,
)
from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator

# Distance order (most used first): b2, s1, b1, b3
ATHLETE = {
    "bikes": [
        {"id": "b1", "distance": 1000},
        {"id": "b2", "distance": 5000},
        {"id": "b3", "distance": 500},
    ],
    "shoes": [{"id": "s1", "distance": 2000}],
}

# b1 was used most recently, then b2; s1 and b3 do not appear at all.
ACTIVITIES = [
    {"gear_id": "b1", "start_date": "2026-11-20T22:14:10Z"},
    {"gear_id": "b2", "start_date": "2026-10-12T16:57:40Z"},
    {"gear_id": "b1", "start_date": "2026-09-01T12:00:00Z"},
    {"gear_id": None, "start_date": "2026-11-21T08:00:00Z"},
    {"start_date": "2026-11-21T09:00:00Z"},
]


def _make_coordinator(hass: HomeAssistant, **options) -> StravaDataUpdateCoordinator:
    """Return a coordinator whose entry has gear enabled plus the given options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_CLIENT_ID: "test_client_id",
            CONF_CLIENT_SECRET: "test_client_secret",
            "token": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": 4102444800,
                "token_type": "Bearer",
            },
        },
        options={CONF_GEAR_ENABLED: True, CONF_NUM_GEAR_SENSORS: 10, **options},
        title="Strava: Test User",
    )
    with patch("homeassistant.helpers.frame.report_usage"):
        return StravaDataUpdateCoordinator(hass, entry=entry)


async def _fetch_gear_ids(coordinator: StravaDataUpdateCoordinator) -> list[str]:
    """Run _fetch_gear against a mocked Strava API and return the gear ids in order."""
    athlete_response = MagicMock()
    athlete_response.status = 200
    athlete_response.json = AsyncMock(return_value=ATHLETE)

    async def fake_request(method, url):
        if url.endswith("/athlete"):
            return athlete_response
        gear_id = url.rsplit("/", 1)[-1]
        resp = MagicMock()
        resp.status = 200
        resp.json = AsyncMock(return_value={"id": gear_id, "name": gear_id})
        return resp

    with patch.object(
        coordinator.oauth_session, "async_request", side_effect=fake_request
    ):
        gear = await coordinator._fetch_gear("12345")
    return [g["id"] for g in gear]


class TestRecordGearLastUsed:
    """Test _record_gear_last_used."""

    async def test_keeps_newest_start_date_per_gear(self, hass: HomeAssistant):
        """Each gear id maps to its newest activity start date."""
        coordinator = _make_coordinator(hass)
        coordinator._record_gear_last_used(ACTIVITIES)
        assert coordinator._gear_last_used == {
            "b1": "2026-11-20T22:14:10Z",
            "b2": "2026-10-12T16:57:40Z",
        }

    async def test_ignores_activities_without_gear_and_resets_between_calls(
        self, hass: HomeAssistant
    ):
        """Activities without gear are skipped and each call replaces the previous map."""
        coordinator = _make_coordinator(hass)
        coordinator._record_gear_last_used(ACTIVITIES)
        coordinator._record_gear_last_used([{"start_date": "2026-11-21T09:00:00Z"}])
        assert coordinator._gear_last_used == {}


class TestFetchGearSort:
    """Test the gear_sort option in _fetch_gear."""

    async def test_default_is_distance(self, hass: HomeAssistant):
        """With no gear_sort option the order is by distance, whatever the recency."""
        assert CONF_GEAR_SORT_DEFAULT == GEAR_SORT_DISTANCE
        coordinator = _make_coordinator(hass)
        coordinator._record_gear_last_used(ACTIVITIES)
        assert await _fetch_gear_ids(coordinator) == ["b2", "s1", "b1", "b3"]

    async def test_recent_orders_by_last_use(self, hass: HomeAssistant):
        """Recent puts the most recently used gear first; unused gear follows by distance."""
        coordinator = _make_coordinator(hass, **{CONF_GEAR_SORT: GEAR_SORT_RECENT})
        coordinator._record_gear_last_used(ACTIVITIES)
        assert await _fetch_gear_ids(coordinator) == ["b1", "b2", "s1", "b3"]

    async def test_recent_limit_keeps_most_recent(self, hass: HomeAssistant):
        """The gear sensor limit is applied after sorting, so recent gear survives it."""
        coordinator = _make_coordinator(
            hass, **{CONF_GEAR_SORT: GEAR_SORT_RECENT, CONF_NUM_GEAR_SENSORS: 1}
        )
        coordinator._record_gear_last_used(ACTIVITIES)
        # Lowest-distance-but-most-recent b1 wins; by distance it would be b2.
        assert await _fetch_gear_ids(coordinator) == ["b1"]

    async def test_recent_without_activity_data_falls_back_to_distance(
        self, hass: HomeAssistant
    ):
        """If no activity used any gear, recent order equals distance order."""
        coordinator = _make_coordinator(hass, **{CONF_GEAR_SORT: GEAR_SORT_RECENT})
        assert await _fetch_gear_ids(coordinator) == ["b2", "s1", "b1", "b3"]


class TestGearSortOptionsFlow:
    """Test that the options flow stores gear_sort."""

    async def _submit(self, hass: HomeAssistant, mock_config_entry, **extra) -> dict:
        mock_config_entry.add_to_hass(hass)
        flow = OptionsFlowHandler()
        flow.hass = hass
        flow.handler = mock_config_entry.entry_id
        user_input = {
            CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride"],
            CONF_PHOTOS: False,
            CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
            CONF_DISTANCE_UNIT_OVERRIDE: "metric",
            CONF_NUM_RECENT_ACTIVITIES: 1,
            CONF_GEAR_ENABLED: True,
            CONF_NUM_GEAR_SENSORS: 5,
            **extra,
        }
        with patch("custom_components.ha_strava.config_flow.async_get"), patch(
            "custom_components.ha_strava.config_flow.async_entries_for_config_entry",
            return_value=[],
        ):
            result = await flow.async_step_init(user_input)
        assert result["type"] == FlowResultType.CREATE_ENTRY
        return result["data"]

    async def test_gear_sort_is_saved(self, hass: HomeAssistant, mock_config_entry):
        """The selected gear order ends up in the saved options."""
        data = await self._submit(
            hass, mock_config_entry, **{CONF_GEAR_SORT: GEAR_SORT_RECENT}
        )
        assert data[CONF_GEAR_SORT] == GEAR_SORT_RECENT

    async def test_gear_sort_defaults_to_distance(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Without a selection the saved option is the default."""
        data = await self._submit(hass, mock_config_entry)
        assert data[CONF_GEAR_SORT] == GEAR_SORT_DISTANCE

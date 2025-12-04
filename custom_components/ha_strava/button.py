"""Button platform for HA Strava."""

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ATTR_SPORT_TYPE,
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
    CONF_SENSOR_ID,
    DOMAIN,
    generate_device_id,
    generate_device_name,
    generate_recent_activity_device_id,
    generate_recent_activity_device_name,
    get_athlete_name_from_title,
    normalize_activity_type,
)
from .coordinator import StravaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StravaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    athlete_id = entry.unique_id
    athlete_name = get_athlete_name_from_title(entry.title)

    buttons: list[ButtonEntity] = []

    activities = (coordinator.data or {}).get("activities") or []

    # Get number of recent activities from config, default to 1
    num_recent_activities = entry.options.get(
        CONF_NUM_RECENT_ACTIVITIES, CONF_NUM_RECENT_ACTIVITIES_DEFAULT
    )

    per_type_added: set[str] = set()
    for activity in activities:
        sport_type = activity.get(CONF_ATTR_SPORT_TYPE)
        activity_id = activity.get(CONF_SENSOR_ID)
        if not sport_type or activity_id is None:
            continue

        normalized_type = normalize_activity_type(sport_type)
        if normalized_type in per_type_added:
            continue

        per_type_added.add(normalized_type)
        buttons.append(
            StravaActivityRefreshButton(
                coordinator=coordinator,
                athlete_id=athlete_id,
                athlete_name=athlete_name,
                activity_type=sport_type,
            )
        )

    # Only create buttons for the configured number of recent activities
    for index in range(num_recent_activities):
        buttons.append(
            StravaRecentActivityRefreshButton(
                coordinator=coordinator,
                athlete_id=athlete_id,
                athlete_name=athlete_name,
                activity_index=index,
            )
        )

    if buttons:
        async_add_entities(buttons)


class StravaActivityRefreshButton(CoordinatorEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        athlete_id: str,
        athlete_name: str,
        activity_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._athlete_id = athlete_id
        self._athlete_name = athlete_name
        self._activity_type = activity_type
        self._normalized_activity_type = normalize_activity_type(activity_type)
        self._attr_unique_id = (
            f"strava_{athlete_id}_{self._normalized_activity_type}_refresh"
        )
        self._attr_name = "Refresh Activity"

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {
                (
                    DOMAIN,
                    generate_device_id(
                        self._athlete_id,
                        self._normalized_activity_type,
                    ),
                )
            },
            "name": generate_device_name(self._athlete_name, self._activity_type),
            "manufacturer": "Powered by Strava",
            "model": f"{self._activity_type} Activity",
        }

    @property
    def available(self) -> bool:
        return self._get_latest_activity() is not None

    def _get_latest_activity(self) -> dict | None:
        data = self.coordinator.data or {}
        activities = data.get("activities") or []
        for activity in activities:
            if activity.get(CONF_ATTR_SPORT_TYPE) == self._activity_type:
                return activity
        return None

    async def async_press(self) -> None:
        activity = self._get_latest_activity()
        if not activity:
            return

        activity_id = activity.get(CONF_SENSOR_ID)
        if not activity_id:
            return

        await self.coordinator.async_refresh_activity(activity_id)


class StravaRecentActivityRefreshButton(CoordinatorEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        athlete_id: str,
        athlete_name: str,
        activity_index: int,
    ) -> None:
        super().__init__(coordinator)
        self._athlete_id = athlete_id
        self._athlete_name = athlete_name
        self._activity_index = activity_index
        self._attr_unique_id = (
            f"strava_{athlete_id}_recent_{activity_index + 1}_refresh"
        )
        self._attr_name = "Refresh Activity"

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {
                (
                    DOMAIN,
                    generate_recent_activity_device_id(
                        self._athlete_id,
                        self._activity_index,
                    ),
                )
            },
            "name": generate_recent_activity_device_name(
                self._athlete_name,
                self._activity_index,
            ),
            "manufacturer": "Powered by Strava",
            "model": "Recent Activity",
        }

    @property
    def available(self) -> bool:
        return self._get_activity() is not None

    def _get_activity(self) -> dict | None:
        data = self.coordinator.data or {}
        activities = data.get("activities") or []
        if activities and len(activities) > self._activity_index:
            return activities[self._activity_index]
        return None

    async def async_press(self) -> None:
        activity = self._get_activity()
        if not activity:
            return

        activity_id = activity.get(CONF_SENSOR_ID)
        if not activity_id:
            return

        await self.coordinator.async_refresh_activity(activity_id)

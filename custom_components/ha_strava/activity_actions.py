"""Explicit account-scoped activity actions, independent of the recent sensor cache."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .activity_api import ActivityError
from .const import (
    ACTIVITY_ACTION_FIELDS,
    DOMAIN,
    SERVICE_EDIT_ACTIVITY,
    SERVICE_GET_ACTIVITY,
)


@callback
def async_register_activity_actions(hass: HomeAssistant) -> None:
    """Register shared actions once; all account selection is explicit."""

    async def handle(call: ServiceCall) -> dict[str, Any]:
        entry_id = call.data["config_entry_id"]
        entry = hass.config_entries.async_get_entry(entry_id)
        coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
        if (
            entry is None
            or entry.domain != DOMAIN
            or entry.disabled_by is not None
            or coordinator is None
        ):
            raise ServiceValidationError("source_not_loaded")
        try:
            if call.service == SERVICE_GET_ACTIVITY:
                activity = await coordinator.activity_client.get(
                    call.data["activity_id"]
                )
                return {
                    **{
                        key: activity[key]
                        for key in ACTIVITY_ACTION_FIELDS
                        if key in activity
                    },
                    "athlete_id": str(activity["athlete"]["id"]),
                }
            changes = dict(call.data["changes"])
            if "append_description" in call.data:
                if changes or "expected_description" in call.data:
                    raise ActivityError("invalid_changes")
                return await coordinator.activity_client.append(
                    call.data["activity_id"],
                    call.data["append_description"],
                    call.data["dry_run"],
                )
            kwargs = (
                {"expected": {"description": call.data["expected_description"]}}
                if "expected_description" in call.data
                else {}
            )
            return await coordinator.activity_client.update(
                call.data["activity_id"], changes, call.data["dry_run"], **kwargs
            )
        except ActivityError as err:
            raise ServiceValidationError(err.category) from None

    common = {
        vol.Required("config_entry_id"): str,
        vol.Required("activity_id"): cv.string,
    }
    for name, extra in {
        SERVICE_GET_ACTIVITY: {},
        SERVICE_EDIT_ACTIVITY: {
            vol.Optional("changes", default={}): dict,
            vol.Optional("dry_run", default=True): bool,
            vol.Optional("append_description"): str,
            vol.Optional("expected_description"): str,
        },
    }.items():
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(
                DOMAIN,
                name,
                handle,
                schema=vol.Schema({**common, **extra}),
                supports_response=SupportsResponse.OPTIONAL,
            )

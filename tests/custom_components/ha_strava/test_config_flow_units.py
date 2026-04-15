"""Tests for distance unit override persistence in the options flow (Issue #289)."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from custom_components.ha_strava.config_flow import OptionsFlowHandler
from custom_components.ha_strava.const import (
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
)


def _get_schema_default(data_schema, key_name):
    """Extract the default value for a named key from a voluptuous schema."""
    for key in data_schema.schema:
        if hasattr(key, "schema") and key.schema == key_name:
            default = key.default
            return default() if callable(default) else default
    return None


def _make_mock_entry(data: dict, options: dict):
    """Create a minimal mock config entry."""
    entry = MagicMock()
    entry.data = data
    entry.options = options
    entry.title = "Strava: Test User"
    return entry


async def _show_form_with_entry(data: dict, options: dict):
    """Instantiate OptionsFlowHandler, inject a mock config_entry, and return the form."""
    mock_entry = _make_mock_entry(data, options)
    flow = OptionsFlowHandler()

    # HA's OptionsFlow.config_entry is a read-only property backed by hass.
    # We patch it on the *class* for the duration of this call so that
    # show_form_init() can access self.config_entry without the full HA runtime.
    with patch.object(
        OptionsFlowHandler, "config_entry", new_callable=PropertyMock
    ) as mock_prop:
        mock_prop.return_value = mock_entry
        return await flow.show_form_init()


class TestDistanceUnitOverrideDefault:
    """Verify that the options form defaults correctly honour both options and data."""

    @pytest.mark.asyncio
    async def test_form_defaults_to_data_metric_when_options_empty(self):
        """When options is empty and data has 'metric', the form should default to 'metric'.

        This is the regression for Issue #289: previously the form fell back to
        CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT ('default') instead of reading entry.data,
        silently overwriting the user's metric preference on first options submission.
        """
        result = await _show_form_with_entry(
            data={CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_METRIC},
            options={},
        )
        default = _get_schema_default(
            result["data_schema"], CONF_DISTANCE_UNIT_OVERRIDE
        )
        assert default == CONF_DISTANCE_UNIT_OVERRIDE_METRIC, (
            f"Expected form default '{CONF_DISTANCE_UNIT_OVERRIDE_METRIC}' "
            f"from entry.data, got '{default}'"
        )

    @pytest.mark.asyncio
    async def test_form_defaults_to_data_imperial_when_options_empty(self):
        """When options is empty and data has 'imperial', form should default to 'imperial'."""
        result = await _show_form_with_entry(
            data={CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL},
            options={},
        )
        default = _get_schema_default(
            result["data_schema"], CONF_DISTANCE_UNIT_OVERRIDE
        )
        assert default == CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL

    @pytest.mark.asyncio
    async def test_form_options_takes_precedence_over_data(self):
        """When both options and data have a value, options takes precedence."""
        result = await _show_form_with_entry(
            data={CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_METRIC},
            options={CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL},
        )
        default = _get_schema_default(
            result["data_schema"], CONF_DISTANCE_UNIT_OVERRIDE
        )
        assert default == CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL

    @pytest.mark.asyncio
    async def test_form_falls_back_to_default_when_neither_options_nor_data_set(self):
        """When neither options nor data have the key, fall back to the built-in default."""
        result = await _show_form_with_entry(data={}, options={})
        default = _get_schema_default(
            result["data_schema"], CONF_DISTANCE_UNIT_OVERRIDE
        )
        assert default == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT

    @pytest.mark.asyncio
    async def test_form_options_metric_preserved(self):
        """When options already has 'metric', it is shown correctly."""
        result = await _show_form_with_entry(
            data={},
            options={CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_METRIC},
        )
        default = _get_schema_default(
            result["data_schema"], CONF_DISTANCE_UNIT_OVERRIDE
        )
        assert default == CONF_DISTANCE_UNIT_OVERRIDE_METRIC

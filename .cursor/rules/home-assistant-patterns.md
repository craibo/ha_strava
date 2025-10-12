---
description: Home Assistant custom component development patterns and best practices
globs: ["custom_components/ha_strava/**/*.py"]
alwaysApply: false
---

# Home Assistant Integration Patterns

This file contains specific patterns and best practices for developing Home Assistant custom components, based on the ha_strava implementation.

## Component Structure

### Required Files
- `__init__.py` - Main entry point with setup functions
- `manifest.json` - Component metadata and dependencies
- `config_flow.py` - OAuth2 and options configuration flows
- `const.py` - All constants and configuration keys
- `coordinator.py` - Data update coordinator for API management
- `sensor.py` - Sensor platform implementation
- `camera.py` - Camera platform implementation
- `translations/` - Internationalization support

### Entry Point Functions

```python
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    # Initialize coordinator
    # Register webhook views
    # Forward to platforms
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Clean up webhook subscriptions
    # Unload platforms
    return True
```

## OAuth2 Implementation

### Config Flow Pattern
```python
class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow for OAuth2 authentication."""
    
    @property
    def extra_authorize_data(self) -> dict:
        """Extra data for authorize URL."""
        return {
            "scope": "activity:read_all",
            "approval_prompt": "force",
            "response_type": "code",
        }
    
    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create entry after OAuth success."""
        # Fetch athlete info
        # Set unique ID
        # Create config entry
        pass
```

### OAuth2 Session Usage
```python
self.oauth_session = config_entry_oauth2_flow.OAuth2Session(
    hass,
    entry,
    config_entry_oauth2_flow.LocalOAuth2Implementation(
        hass, DOMAIN, client_id, client_secret, authorize_url, token_url
    ),
)
```

## Data Update Coordinator

### Coordinator Pattern
```python
class StravaDataUpdateCoordinator(DataUpdateCoordinator):
    """Managing fetching data from the Strava API."""
    
    def __init__(self, hass, *, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),
        )
    
    async def _async_update_data(self):
        """Fetch data from the API."""
        # Implement data fetching logic
        # Return structured data dictionary
        pass
```

## Entity Implementation

### Sensor Entity Pattern
```python
class StravaStatsSensor(CoordinatorEntity, SensorEntity):
    """A sensor for Strava data."""
    
    def __init__(self, coordinator, **kwargs):
        super().__init__(coordinator)
        self._attr_unique_id = f"strava_{athlete_id}_{index}"
    
    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"strava_activity_{athlete_id}")},
            "name": f"Strava Activity: {title}",
            "manufacturer": "Powered by Strava",
            "model": "Activity",
            "configuration_url": f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
        }
    
    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if entity should be enabled by default."""
        return self._activity_index < DEFAULT_NB_ACTIVITIES
```

### Camera Entity Pattern
```python
class StravaCamera(CoordinatorEntity, Camera):
    """A camera for Strava photos."""
    
    _attr_should_poll = False
    
    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        """Return image response."""
        # Fetch and return image data
        pass
```

## Webhook Implementation

### Webhook View Pattern
```python
class StravaWebhookView(HomeAssistantView):
    """API endpoint for Strava webhooks."""
    
    url = "/api/strava/webhook"
    name = "api:strava:webhook"
    requires_auth = False
    cors_allowed = True
    
    async def get(self, request: Request) -> Response:
        """Handle webhook challenge."""
        challenge = request.query.get("hub.challenge")
        if challenge:
            return json_response({"hub.challenge": challenge})
        return Response(status=HTTPStatus.OK)
    
    async def post(self, request: Request) -> Response:
        """Handle webhook data updates."""
        # Process webhook data
        # Trigger coordinator refresh
        return Response(status=HTTPStatus.OK)
```

## Options Flow

### Options Flow Pattern
```python
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for runtime configuration changes."""
    
    async def async_step_init(self, user_input=None):
        """Initial options step."""
        if user_input is not None:
            # Update entity registry based on options
            # Store new options
            return self.async_create_entry(title=title, data=options)
        return self.async_show_form(step_id="init", data_schema=schema)
```

## Constants Management

### Constants File Pattern
```python
# Domain and basic config
DOMAIN = "ha_strava"
CONFIG_ENTRY_TITLE = "Strava"

# OAuth configuration
OAUTH2_AUTHORIZE = "https://www.strava.com/oauth/authorize"
OAUTH2_TOKEN = "https://www.strava.com/oauth/token"

# Configuration keys
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_PHOTOS = "conf_photos"

# Sensor definitions
CONF_SENSORS = {
    CONF_SENSOR_DISTANCE: {"icon": "mdi:map-marker-distance"},
    CONF_SENSOR_ELEVATION: {"icon": "mdi:elevation-rise"},
    # ... more sensors
}
```

## Event Handling

### Event-Based Updates
```python
# Fire events after data updates
self.hass.bus.async_fire(EVENT_ACTIVITIES_UPDATE, {"activities": activities})
self.hass.bus.async_fire(EVENT_SUMMARY_STATS_UPDATE, {"stats": summary_stats})

# Listen for events in entities
self.async_on_remove(
    self.hass.bus.async_listen(EVENT_ACTIVITIES_UPDATE, self._handle_update)
)
```

## Error Handling

### API Error Handling
```python
try:
    response = await self.oauth_session.async_request(method="GET", url=url)
    response.raise_for_status()
    data = await response.json()
except aiohttp.ClientError as err:
    raise UpdateFailed(f"Error communicating with API: {err}") from err
```

## Multi-User Support

### User-Specific Data
```python
# Use unique_id from config entry for user identification
athlete_id = config_entry.unique_id

# Store user-specific data in coordinator
hass.data[DOMAIN][entry.entry_id] = coordinator

# Handle webhook updates for specific users
for entry in self.hass.config_entries.async_entries(DOMAIN):
    if entry.unique_id == str(owner_id):
        coordinator = self.hass.data[DOMAIN][entry.entry_id]
        self.hass.async_create_task(coordinator.async_request_refresh())
        break
```

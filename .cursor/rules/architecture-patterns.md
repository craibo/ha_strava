---
description: Architecture patterns for OAuth2, webhooks, coordinators, and multi-user support
globs: ["custom_components/ha_strava/**/*.py"]
alwaysApply: false
---

# Architecture Patterns

This file defines the architectural patterns used in the ha_strava project, including OAuth2 authentication, webhook handling, data coordination, and multi-user support.

## OAuth2 Authentication Architecture

### OAuth2 Flow Implementation
The component uses Home Assistant's built-in OAuth2 flow for secure authentication with Strava.

```python
class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow for OAuth2 authentication."""
    
    @property
    def extra_authorize_data(self) -> dict:
        """Extra data appended to authorize URL."""
        return {
            "scope": "activity:read_all",
            "approval_prompt": "force",
            "response_type": "code",
        }
    
    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create config entry after successful OAuth."""
        # Fetch athlete information
        # Set unique ID based on athlete ID
        # Store OAuth credentials securely
        pass
```

### OAuth2 Session Management
```python
self.oauth_session = config_entry_oauth2_flow.OAuth2Session(
    hass,
    entry,
    config_entry_oauth2_flow.LocalOAuth2Implementation(
        hass, DOMAIN, client_id, client_secret, authorize_url, token_url
    ),
)

# Ensure token validity before API calls
await self.oauth_session.async_ensure_token_valid()
```

## Webhook Architecture

### Webhook Subscription Management
```python
async def renew_webhook_subscription(hass: HomeAssistant, entry: ConfigEntry):
    """Subscribe to Strava webhooks for real-time updates."""
    # Get Home Assistant public URL
    ha_host = get_url(hass, allow_internal=False, allow_ip=False)
    callback_url = f"{ha_host}/api/strava/webhook"
    
    # Check for existing subscriptions
    # Delete outdated subscriptions
    # Create new subscription if needed
    # Store webhook ID in config entry
```

### Webhook Endpoint Implementation
```python
class StravaWebhookView(HomeAssistantView):
    """API endpoint for Strava webhook callbacks."""
    
    url = "/api/strava/webhook"
    name = "api:strava:webhook"
    requires_auth = False
    cors_allowed = True
    
    async def get(self, request: Request) -> Response:
        """Handle webhook challenge verification."""
        challenge = request.query.get("hub.challenge")
        if challenge:
            return json_response({"hub.challenge": challenge})
        return Response(status=HTTPStatus.OK)
    
    async def post(self, request: Request) -> Response:
        """Handle webhook data updates."""
        data = await request.json()
        owner_id = data.get("owner_id")
        
        # Find coordinator for this user
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == str(owner_id):
                coordinator = self.hass.data[DOMAIN][entry.entry_id]
                self.hass.async_create_task(coordinator.async_request_refresh())
                break
        
        return Response(status=HTTPStatus.OK)
```

## Data Update Coordinator Architecture

### Coordinator Pattern
The coordinator manages data fetching, caching, and updates for a single user.

```python
class StravaDataUpdateCoordinator(DataUpdateCoordinator):
    """Managing fetching data from the Strava API for a single user."""
    
    def __init__(self, hass, *, entry):
        """Initialize coordinator with OAuth session."""
        self.hass = hass
        self.entry = entry
        self.oauth_session = config_entry_oauth2_flow.OAuth2Session(...)
        self.image_updates = {}  # Track image update timestamps
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),
        )
    
    async def _async_update_data(self):
        """Fetch and process data from Strava API."""
        try:
            await self.oauth_session.async_ensure_token_valid()
            
            athlete_id, activities = await self._fetch_activities()
            summary_stats = await self._fetch_summary_stats(athlete_id)
            images = await self._fetch_images(activities)
            
            return {
                "activities": activities,
                "summary_stats": summary_stats,
                "images": images,
            }
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
```

### Data Processing Pipeline
```python
async def _fetch_activities(self) -> Tuple[str, list[dict]]:
    """Fetch and process activities from Strava API."""
    # 1. Fetch activities list
    response = await self.oauth_session.async_request(
        method="GET",
        url=f"https://www.strava.com/api/v3/athlete/activities?per_page={MAX_NB_ACTIVITIES}",
    )
    activities_json = await response.json()
    
    # 2. Process each activity
    activities = []
    for activity in activities_json:
        # Fetch detailed activity data
        activity_response = await self.oauth_session.async_request(
            method="GET",
            url=f"https://www.strava.com/api/v3/activities/{activity_id}",
        )
        activity_dto = await activity_response.json()
        
        # Process and geocode activity
        processed_activity = self._sensor_activity(
            activity,
            await self._geocode_activity(activity, activity_dto, auth)
        )
        activities.append(processed_activity)
    
    # 3. Sort by date (newest first)
    return athlete_id, sorted(activities, key=lambda x: x[CONF_SENSOR_DATE], reverse=True)
```

## Multi-User Architecture

### User Isolation
Each user has their own config entry and coordinator instance.

```python
# In __init__.py
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Strava integration for a single user."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create user-specific coordinator
    coordinator = StravaDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator by entry ID
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up webhook (shared across all users)
    hass.http.register_view(StravaWebhookView(hass))
    await renew_webhook_subscription(hass, entry)
    
    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
```

### User-Specific Data Storage
```python
# Each user's data is isolated
hass.data[DOMAIN][entry.entry_id] = coordinator

# Webhook routing to correct user
for entry in self.hass.config_entries.async_entries(DOMAIN):
    if entry.unique_id == str(owner_id):
        coordinator = self.hass.data[DOMAIN][entry.entry_id]
        self.hass.async_create_task(coordinator.async_request_refresh())
        break
```

### Entity Naming and Identification
```python
# Use athlete ID in unique identifiers
self._attr_unique_id = f"strava_{athlete_id}_{activity_index}_{sensor_index}"

# Device information includes user context
@property
def device_info(self):
    return {
        "identifiers": {(DOMAIN, f"strava_activity_{self._athlete_id}_{self._activity_index}")},
        "name": f"Strava Activity {self._activity_index}: {self.coordinator.entry.title}",
        "manufacturer": "Powered by Strava",
        "model": "Activity",
        "configuration_url": f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
    }
```

## Event-Driven Architecture

### Event Publishing
```python
# Fire events after data updates
self.hass.bus.async_fire(EVENT_ACTIVITIES_UPDATE, {
    "activities": activities,
    "athlete_id": athlete_id
})

self.hass.bus.async_fire(EVENT_SUMMARY_STATS_UPDATE, {
    "summary_stats": summary_stats,
    "athlete_id": athlete_id
})
```

### Event Listening
```python
# Entities listen for relevant events
self.async_on_remove(
    self.hass.bus.async_listen(EVENT_ACTIVITIES_UPDATE, self._handle_activities_update)
)

def _handle_activities_update(self, event):
    """Handle activities update event."""
    if event.data.get("athlete_id") == self._athlete_id:
        self.async_write_ha_state()
```

## Options Flow Architecture

### Runtime Configuration
```python
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle runtime configuration changes."""
    
    async def async_step_init(self, user_input=None):
        """Handle options flow initialization."""
        if user_input is not None:
            # Update entity registry based on new options
            await self._update_entity_registry(user_input)
            
            # Store new options
            return self.async_create_entry(
                title=self.config_entry.title,
                data=user_input
            )
        
        return self.async_show_form(step_id="init", data_schema=self._get_schema())
    
    async def _update_entity_registry(self, user_input):
        """Update entity registry based on new options."""
        entity_registry = async_get(hass=self.hass)
        entities = async_entries_for_config_entry(
            registry=entity_registry,
            config_entry_id=self.config_entry.entry_id,
        )
        
        for entity in entities:
            # Enable/disable entities based on new options
            if self._should_enable_entity(entity, user_input):
                entity_registry.async_update_entity(entity.entity_id, disabled_by=None)
            else:
                entity_registry.async_update_entity(
                    entity.entity_id,
                    disabled_by=RegistryEntryDisabler.INTEGRATION
                )
```

## Error Handling Architecture

### Coordinated Error Handling
```python
async def _async_update_data(self):
    """Fetch data with proper error handling."""
    try:
        # API calls
        pass
    except aiohttp.ClientError as err:
        _LOGGER.error("API communication error: %s", err)
        raise UpdateFailed(f"Error communicating with API: {err}") from err
    except Exception as err:
        _LOGGER.error("Unexpected error during data update: %s", err)
        raise UpdateFailed(f"Unexpected error: {err}") from err
```

### Graceful Degradation
```python
@property
def available(self):
    """Return if entity is available."""
    return self.coordinator.data is not None and self._data is not None

@property
def native_value(self):
    """Return the state with fallback handling."""
    if not self.available:
        return None
    
    try:
        return self._calculate_value()
    except (KeyError, TypeError, ValueError) as err:
        _LOGGER.warning("Error calculating value: %s", err)
        return None
```

## Resource Management

### Cleanup on Unload
```python
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Clean up resources on unload."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clean up webhook subscription
        if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
            await self._delete_webhook_subscription(webhook_id)
        
        # Remove coordinator from data store
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
```

### Memory Management
```python
# Limit image cache size
self._urls = dict(
    sorted(self._urls.items(), key=lambda item: item[1]["date"])[-CONF_MAX_NB_IMAGES:]
)

# Track image update timestamps to avoid unnecessary API calls
if (dt.now() - self.image_updates.get(activity_id, dt(1990, 1, 1))).days <= 0:
    continue
```

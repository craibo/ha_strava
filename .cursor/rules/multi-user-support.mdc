---
description: Multi-user support patterns and architecture for the ha_strava project
globs: ["custom_components/ha_strava/**/*.py"]
alwaysApply: false
---

# Multi-User Support Patterns

This file defines patterns for supporting multiple Strava users in the ha_strava Home Assistant custom component, based on the current implementation.

## Multi-User Architecture Overview

The ha_strava component supports multiple Strava users through:

- **Unique Strava app credentials per user** (client_id, client_secret)
- Separate config entries for each user
- User-specific coordinators and data storage
- **Individual webhook registration per user** with shared endpoint
- Webhook routing to correct user instances based on owner_id
- Isolated entity namespaces
- **Automatic migration from single-user to multi-user** (version 1 to 2)

## User Identification and Isolation

### Unique User Identification

```python
# Each user is identified by their Strava athlete ID
athlete_id = config_entry.unique_id

# Each user must have unique Strava app credentials
client_id = entry.data[CONF_CLIENT_ID]  # Must be unique per user
client_secret = entry.data[CONF_CLIENT_SECRET]  # Must be unique per user

# Store user-specific data using entry ID as key
hass.data[DOMAIN][entry.entry_id] = coordinator

# Entity unique IDs include athlete ID
self._attr_unique_id = f"strava_{athlete_id}_{activity_index}_{sensor_index}"
```

### Credential Uniqueness Validation

```python
async def async_step_user(self, user_input=None):
    """Validate that Strava app credentials are unique across all users."""
    if user_input is not None:
        client_id = user_input[CONF_CLIENT_ID]

        # Check if these credentials are already in use by another user
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_CLIENT_ID) == client_id:
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(data_schema),
                    errors={"base": "credentials_already_used"}
                )

        # Proceed with OAuth2 flow for unique credentials
        return await self.async_step_pick_implementation()
```

### Config Entry Management

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Strava integration for a single user."""
    hass.data.setdefault(DOMAIN, {})

    # Create user-specific coordinator
    coordinator = StravaDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator by entry ID (not athlete ID)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up webhook (shared endpoint, individual registration per user)
    hass.http.register_view(StravaWebhookView(hass))
    await renew_webhook_subscription(hass, entry)  # Each user registers their own webhook

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
```

## Webhook Routing for Multiple Users

### Webhook User Resolution

```python
class StravaWebhookView(HomeAssistantView):
    """API endpoint for Strava webhook callbacks."""

    async def post(self, request: Request) -> Response:
        """Handle webhook data updates for specific users."""
        try:
            data = await request.json()
            owner_id = data.get("owner_id")
        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON received in webhook")
            return Response(status=HTTPStatus.BAD_REQUEST)

        if not owner_id:
            _LOGGER.warning("Webhook received without owner_id")
            return Response(status=HTTPStatus.OK)

        # Find the coordinator for this specific user
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == str(owner_id):
                coordinator = self.hass.data[DOMAIN][entry.entry_id]
                self.hass.async_create_task(coordinator.async_request_refresh())
                _LOGGER.debug(f"Triggered refresh for user {owner_id}")
                break
        else:
            _LOGGER.warning(f"Webhook received for unknown user: {owner_id}")

        return Response(status=HTTPStatus.OK)
```

### Webhook Security and Validation

```python
class StravaWebhookView(HomeAssistantView):
    """Secure webhook endpoint with user-specific validation."""

    def __init__(self, hass: HomeAssistant):
        """Initialize webhook view with security measures."""
        self.hass = hass
        self._user_coordinator_cache = {}  # Cache for performance
        self._rate_limits = {}  # Per-user rate limiting

    async def post(self, request: Request) -> Response:
        """Handle webhook with security validation."""
        try:
            data = await request.json()
            owner_id = data.get("owner_id")
        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON received in webhook")
            return Response(status=HTTPStatus.BAD_REQUEST)

        if not owner_id:
            _LOGGER.warning("Webhook received without owner_id")
            return Response(status=HTTPStatus.OK)

        # Rate limiting per user
        if not await self._check_rate_limit(owner_id):
            _LOGGER.warning(f"Rate limit exceeded for user {owner_id}")
            return Response(status=HTTPStatus.TOO_MANY_REQUESTS)

        # Validate webhook signature (if implemented)
        if not await self._validate_webhook_signature(request, data):
            _LOGGER.warning(f"Invalid webhook signature for user {owner_id}")
            return Response(status=HTTPStatus.UNAUTHORIZED)

        # Use cached lookup for performance
        coordinator = self._user_coordinator_cache.get(owner_id)
        if not coordinator:
            # Fallback to iteration and cache result
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.unique_id == str(owner_id):
                    coordinator = self.hass.data[DOMAIN][entry.entry_id]
                    self._user_coordinator_cache[owner_id] = coordinator
                    break

        if coordinator:
            self.hass.async_create_task(coordinator.async_request_refresh())
            _LOGGER.debug(f"Triggered refresh for user {owner_id}")
        else:
            _LOGGER.warning(f"Webhook received for unknown user: {owner_id}")

        return Response(status=HTTPStatus.OK)

    async def _check_rate_limit(self, owner_id: str) -> bool:
        """Check rate limiting for specific user."""
        now = time.time()
        last_call = self._rate_limits.get(owner_id, 0)

        # Allow one call per 5 seconds per user
        if now - last_call < 5:
            return False

        self._rate_limits[owner_id] = now
        return True

    async def _validate_webhook_signature(self, request: Request, data: dict) -> bool:
        """Validate webhook signature from Strava (placeholder for implementation)."""
        # TODO: Implement webhook signature validation
        # This would verify the request is actually from Strava
        return True
```

### Webhook Subscription Management

```python
async def renew_webhook_subscription(hass: HomeAssistant, entry: ConfigEntry):
    """Subscribe to Strava webhooks for a specific user with unique credentials."""
    try:
        ha_host = get_url(hass, allow_internal=False, allow_ip=False)
    except NoURLAvailableError:
        _LOGGER.error("Home Assistant instance does not have a public URL")
        return

    callback_url = f"{ha_host}/api/strava/webhook"
    websession = async_get_clientsession(hass, verify_ssl=False)

    # Each user has unique credentials, so only manage their own subscriptions
    try:
        async with websession.get(
            WEBHOOK_SUBSCRIPTION_URL,
            params={
                "client_id": entry.data[CONF_CLIENT_ID],  # User-specific credentials
                "client_secret": entry.data[CONF_CLIENT_SECRET],  # User-specific credentials
            },
        ) as response:
            response.raise_for_status()
            subscriptions = await response.json()

        # Delete any existing subscriptions for this user's app that are not current
        for sub in subscriptions:
            if sub["callback_url"] != callback_url:
                _LOGGER.debug(f"Deleting outdated webhook subscription for user {entry.unique_id}: {sub['id']}")
                async with websession.delete(
                    f"{WEBHOOK_SUBSCRIPTION_URL}/{sub['id']}",
                    data={
                        "client_id": entry.data[CONF_CLIENT_ID],
                        "client_secret": entry.data[CONF_CLIENT_SECRET],
                    },
                ) as delete_response:
                    delete_response.raise_for_status()

        # Create new subscription if needed for this user
        if not any(sub["callback_url"] == callback_url for sub in subscriptions):
            await _create_webhook_subscription(websession, entry, callback_url)
            _LOGGER.info(f"Created webhook subscription for user {entry.unique_id}")

    except aiohttp.ClientError as err:
        _LOGGER.error(f"Error managing webhook subscriptions for user {entry.unique_id}: {err}")
```

## User-Specific Data Storage

### Coordinator Per User

```python
class StravaDataUpdateCoordinator(DataUpdateCoordinator):
    """Managing fetching data from the Strava API for a single user."""

    def __init__(self, hass, *, entry):
        """Initialize coordinator for a specific user."""
        self.hass = hass
        self.entry = entry  # Contains user-specific config
        self.oauth_session = config_entry_oauth2_flow.OAuth2Session(
            hass,
            entry,
            config_entry_oauth2_flow.LocalOAuth2Implementation(
                hass, DOMAIN,
                entry.data[CONF_CLIENT_ID],
                entry.data[CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
            ),
        )
        self.image_updates = {}  # User-specific image update tracking
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),
        )
```

### User-Specific Image Management

```python
class UrlCam(CoordinatorEntity, Camera):
    """Camera that cycles through images for a specific user."""

    def __init__(self, coordinator: StravaDataUpdateCoordinator, athlete_id: str, default_enabled=True):
        """Initialize camera for a specific user."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self._athlete_id = athlete_id
        self._attr_unique_id = f"{CONF_PHOTOS_ENTITY}_{self._athlete_id}"

        # User-specific pickle file for image URLs
        self._url_dump_filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"{self._athlete_id}_{CONFIG_URL_DUMP_FILENAME}",
        )
        self._urls = {}
        self._url_index = 0
        self._attr_entity_registry_enabled_default = default_enabled
```

## Entity Naming and Namespace Isolation

### User-Specific Entity IDs

```python
class StravaStatsSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a specific user's Strava data."""

    def __init__(self, coordinator, activity_index: int, sensor_index: int, athlete_id: str):
        """Initialize sensor for specific user and activity."""
        super().__init__(coordinator)
        self._sensor_index = sensor_index
        self._activity_index = activity_index
        self._athlete_id = athlete_id

        # Include athlete ID in unique ID for namespace isolation
        self._attr_unique_id = f"strava_{self._athlete_id}_{self._activity_index}_{self._sensor_index}"
```

### Device Information Per User

```python
@property
def device_info(self):
    """Return device information for this user's entities."""
    if not self.available:
        return None

    activity_id = self._data.get(CONF_SENSOR_ID, "")
    return {
        "identifiers": {
            (DOMAIN, f"strava_activity_{self._athlete_id}_{self._activity_index}")
        },
        "name": f"Strava Activity {self._activity_index}: {self.coordinator.entry.title}",
        "manufacturer": "Powered by Strava",
        "model": "Activity",
        "configuration_url": f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
    }
```

## User-Specific Configuration

### Options Flow Per User

```python
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for runtime configuration changes per user."""

    def __init__(self, config_entry):
        """Initialize options flow for specific user."""
        self.config_entry = config_entry
        self._athlete_id = config_entry.unique_id
        # ... other user-specific options

    async def async_step_init(self, user_input=None):
        """Handle options for this specific user."""
        if user_input is not None:
            # Update entity registry for this user's entities only
            entity_registry = async_get(hass=self.hass)
            entities = async_entries_for_config_entry(
                registry=entity_registry,
                config_entry_id=self.config_entry.entry_id,  # User-specific
            )

            # Update entities based on user's preferences
            for entity in entities:
                if self._should_enable_entity(entity, user_input):
                    entity_registry.async_update_entity(entity.entity_id, disabled_by=None)
                else:
                    entity_registry.async_update_entity(
                        entity.entity_id,
                        disabled_by=RegistryEntryDisabler.INTEGRATION
                    )

            return self.async_create_entry(
                title=self.config_entry.title,
                data=user_input
            )

        return self.async_show_form(step_id="init", data_schema=self._get_schema())
```

## Event Handling for Multiple Users

### User-Specific Event Publishing

```python
# Fire events with user context
self.hass.bus.async_fire(EVENT_ACTIVITIES_UPDATE, {
    "activities": activities,
    "athlete_id": athlete_id,
    "user_name": self.entry.title
})

self.hass.bus.async_fire(EVENT_SUMMARY_STATS_UPDATE, {
    "summary_stats": summary_stats,
    "athlete_id": athlete_id,
    "user_name": self.entry.title
})
```

### User-Specific Event Listening

```python
# Entities listen for events from their specific user
self.async_on_remove(
    self.hass.bus.async_listen(EVENT_ACTIVITIES_UPDATE, self._handle_activities_update)
)

def _handle_activities_update(self, event):
    """Handle activities update event for this user only."""
    if event.data.get("athlete_id") == self._athlete_id:
        self.async_write_ha_state()
```

## User Management and Cleanup

### User-Specific Unload

```python
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a specific user's integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up webhook subscription for this user
        if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
            try:
                websession = async_get_clientsession(hass)
                async with websession.delete(
                    f"{WEBHOOK_SUBSCRIPTION_URL}/{webhook_id}",
                    data={
                        "client_id": entry.data[CONF_CLIENT_ID],
                        "client_secret": entry.data[CONF_CLIENT_SECRET],
                    },
                ) as response:
                    response.raise_for_status()
                    _LOGGER.debug(f"Successfully deleted webhook subscription for user {entry.unique_id}")
            except aiohttp.ClientError as err:
                _LOGGER.error(f"Failed to delete webhook subscription for user {entry.unique_id}: {err}")

        # Remove user's coordinator from data store
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info(f"Unloaded Strava integration for user {entry.unique_id}")

    return unload_ok
```

### User-Specific Resource Cleanup

```python
async def _cleanup_user_resources(self, athlete_id: str):
    """Clean up resources for a specific user."""
    # Remove user-specific image files
    image_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{athlete_id}_{CONFIG_URL_DUMP_FILENAME}",
    )
    if os.path.exists(image_file):
        try:
            os.remove(image_file)
            _LOGGER.debug(f"Removed image cache file for user {athlete_id}")
        except OSError as err:
            _LOGGER.warning(f"Failed to remove image cache file for user {athlete_id}: {err}")
```

## User-Specific Error Handling

### User Context in Error Messages

```python
async def _async_update_data(self):
    """Fetch data with user-specific error handling."""
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
        _LOGGER.error(f"API error for user {self.entry.unique_id}: {err}")
        raise UpdateFailed(f"Error communicating with API for user {self.entry.title}: {err}") from err
```

## User-Specific Logging

### User Context in Logs

```python
# Include user context in log messages
_LOGGER.debug(f"Fetching activities for user {athlete_id}")
_LOGGER.info(f"Successfully updated {len(activities)} activities for user {athlete_id}")
_LOGGER.warning(f"Webhook received for unknown user: {owner_id}")
_LOGGER.error(f"API error for user {self.entry.unique_id}: {err}")
```

## Testing Multi-User Support

### Multi-User Test Patterns

```python
async def test_multiple_users_with_unique_credentials(hass: HomeAssistant):
    """Test multiple users can be configured with unique credentials."""
    # Create first user with unique credentials
    user1_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            "client_id": "client1_unique",
            "client_secret": "secret1_unique",
            "webhook_id": "webhook1"
        }
    )
    user1_entry.add_to_hass(hass)

    # Create second user with different unique credentials
    user2_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="67890",
        data={
            "client_id": "client2_unique",
            "client_secret": "secret2_unique",
            "webhook_id": "webhook2"
        }
    )
    user2_entry.add_to_hass(hass)

    # Set up both users
    await hass.config_entries.async_setup(user1_entry.entry_id)
    await hass.config_entries.async_setup(user2_entry.entry_id)
    await hass.async_block_till_done()

    # Verify both coordinators exist
    assert user1_entry.entry_id in hass.data[DOMAIN]
    assert user2_entry.entry_id in hass.data[DOMAIN]

    # Verify webhook routing works for both users
    webhook_view = StravaWebhookView(hass)

    # Test webhook for user 1
    request1 = make_mocked_request('POST', '/api/strava/webhook', json={"owner_id": 12345})
    response1 = await webhook_view.post(request1)
    assert response1.status == 200

    # Test webhook for user 2
    request2 = make_mocked_request('POST', '/api/strava/webhook', json={"owner_id": 67890})
    response2 = await webhook_view.post(request2)
    assert response2.status == 200

async def test_credential_uniqueness_validation(hass: HomeAssistant):
    """Test that duplicate credentials are rejected."""
    # Create first user
    user1_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={"client_id": "shared_client", "client_secret": "shared_secret"}
    )
    user1_entry.add_to_hass(hass)

    # Try to create second user with same credentials
    config_flow = OAuth2FlowHandler()
    config_flow.hass = hass

    result = await config_flow.async_step_user({
        "client_id": "shared_client",  # Same as user1
        "client_secret": "shared_secret"  # Same as user1
    })

    # Should show error about credentials already in use
    assert result["type"] == "form"
    assert "credentials_already_used" in result["errors"]["base"]

async def test_webhook_security_and_rate_limiting(hass: HomeAssistant):
    """Test webhook security features."""
    webhook_view = StravaWebhookView(hass)

    # Test rate limiting
    request1 = make_mocked_request('POST', '/api/strava/webhook', json={"owner_id": 12345})
    response1 = await webhook_view.post(request1)
    assert response1.status == 200

    # Immediate second request should be rate limited
    request2 = make_mocked_request('POST', '/api/strava/webhook', json={"owner_id": 12345})
    response2 = await webhook_view.post(request2)
    assert response2.status == 429  # Too Many Requests

    # Test invalid JSON
    request3 = make_mocked_request('POST', '/api/strava/webhook', data=b"invalid json")
    response3 = await webhook_view.post(request3)
    assert response3.status == 400  # Bad Request
```

## Performance Considerations for Multiple Users

### Resource Management

```python
# Limit resources per user
MAX_ACTIVITIES_PER_USER = 10
MAX_IMAGES_PER_USER = 100

# User-specific rate limiting
self._user_rate_limits = {}

async def _rate_limited_request_for_user(self, user_id: str, method: str, url: str, **kwargs):
    """Make rate-limited request for specific user."""
    now = time.time()
    last_call = self._user_rate_limits.get(user_id, 0)

    if now - last_call < self._rate_limit_delay:
        await asyncio.sleep(self._rate_limit_delay - (now - last_call))

    self._user_rate_limits[user_id] = time.time()
    return await self.oauth_session.async_request(method, url, **kwargs)
```

### Memory Management

```python
# Clean up old user data
async def _cleanup_old_user_data(self):
    """Clean up data for users that are no longer configured."""
    active_user_ids = {entry.unique_id for entry in self.hass.config_entries.async_entries(DOMAIN)}

    for user_id in list(self._user_rate_limits.keys()):
        if user_id not in active_user_ids:
            del self._user_rate_limits[user_id]
```

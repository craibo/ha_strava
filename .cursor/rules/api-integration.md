---
description: API integration patterns for Strava API and external services
globs: ["custom_components/ha_strava/**/*.py"]
alwaysApply: false
---

# API Integration Patterns

This file defines patterns for integrating with external APIs, specifically the Strava API and geocoding services, based on the ha_strava implementation.

## Strava API Integration

### API Rate Limits

**CRITICAL**: The Strava API has strict rate limits that must be respected:

- **Read Operations**: 100 requests every 15 minutes, 1000 requests per day
- **Write Operations**: 100 requests every 15 minutes, 1000 requests per day

**Implementation Requirements**:

- Only poll for data during initialization
- Use webhooks for all subsequent updates
- Never implement continuous polling
- Implement exponential backoff for failed requests
- Monitor API usage to stay within limits

### API Endpoints and Authentication

```python
# OAuth2 endpoints
OAUTH2_AUTHORIZE = "https://www.strava.com/oauth/authorize"
OAUTH2_TOKEN = "https://www.strava.com/oauth/token"

# API endpoints
STRAVA_ACTIVITY_BASE_URL = "https://www.strava.com/activities/"
STRAVA_ACTHLETE_BASE_URL = "https://www.strava.com/dashboard"
WEBHOOK_SUBSCRIPTION_URL = "https://www.strava.com/api/v3/push_subscriptions"

# API request patterns
_PHOTOS_URL_TEMPLATE = "https://www.strava.com/api/v3/activities/%s/photos?size={CONFIG_IMG_SIZE}"
_STATS_URL_TEMPLATE = "https://www.strava.com/api/v3/athletes/%s/stats"
```

### OAuth2 Session Management

```python
class StravaDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator with OAuth2 session management."""

    def __init__(self, hass, *, entry):
        self.oauth_session = config_entry_oauth2_flow.OAuth2Session(
            hass,
            entry,
            config_entry_oauth2_flow.LocalOAuth2Implementation(
                hass, DOMAIN, client_id, client_secret, authorize_url, token_url
            ),
        )

    async def _make_api_request(self, method: str, url: str, **kwargs):
        """Make authenticated API request."""
        await self.oauth_session.async_ensure_token_valid()
        response = await self.oauth_session.async_request(method=method, url=url, **kwargs)
        response.raise_for_status()
        return response
```

### Activities API Integration

```python
async def _fetch_activities(self) -> Tuple[str, list[dict]]:
    """Fetch activities from Strava API."""
    _LOGGER.debug("Fetching activities")

    # Fetch activities list
    response = await self.oauth_session.async_request(
        method="GET",
        url=f"https://www.strava.com/api/v3/athlete/activities?per_page={MAX_NB_ACTIVITIES}",
    )
    response.raise_for_status()
    activities_json = await response.json()

    # Process each activity with detailed data
    activities = []
    for activity in activities_json:
        athlete_id = int(activity["athlete"]["id"])
        activity_id = int(activity["id"])

        # Fetch detailed activity data
        activity_response = await self.oauth_session.async_request(
            method="GET",
            url=f"https://www.strava.com/api/v3/activities/{activity_id}",
        )
        activity_dto = (
            await activity_response.json()
            if activity_response.status == 200
            else None
        )

        # Process and geocode activity
        processed_activity = self._sensor_activity(
            activity,
            await self._geocode_activity(activity, activity_dto, auth)
        )
        activities.append(processed_activity)

    return athlete_id, sorted(activities, key=lambda x: x[CONF_SENSOR_DATE], reverse=True)
```

### Summary Stats API Integration

```python
async def _fetch_summary_stats(self, athlete_id: str) -> dict:
    """Fetch summary statistics from Strava API."""
    _LOGGER.debug("Fetching summary stats")

    response = await self.oauth_session.async_request(
        method="GET",
        url=_STATS_URL_TEMPLATE % (athlete_id,)
    )
    response.raise_for_status()
    summary_stats = self._sensor_summary_stats(await response.json())
    summary_stats[CONF_SENSOR_ID] = athlete_id
    return summary_stats
```

### Photos API Integration

```python
async def _fetch_images(self, activities: list[dict]):
    """Fetch photos from Strava API."""
    if not self.entry.options.get(CONF_PHOTOS, False):
        _LOGGER.debug("Fetch photos DISABLED")
        return

    _LOGGER.debug("Fetching images")
    img_urls = []

    for activity in activities:
        activity_id = activity.get(CONF_SENSOR_ID)

        # Check if we need to update images for this activity
        if (dt.now() - self.image_updates.get(activity_id, dt(1990, 1, 1))).days <= 0:
            continue

        response = await self.oauth_session.async_request(
            method="GET",
            url=_PHOTOS_URL_TEMPLATE % (activity_id,)
        )
        if response.status != 200:
            continue

        self.image_updates[activity_id] = dt.now()

        for image in await response.json():
            img_date = dt.strptime(
                image.get("created_at_local", "2000-01-01T00:00:00Z"),
                "%Y-%m-%dT%H:%M:%SZ",
            )
            img_url = list(image.get("urls").values())[0]
            img_urls.append({"date": img_date, "url": img_url})

    return img_urls
```

## Webhook-First Architecture

### Core Principle

**The integration MUST use webhooks for all data updates after initialization. Polling should only occur during the initial setup.**

```python
class StravaDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator that only polls on initialization, then relies on webhooks."""

    def __init__(self, hass, *, entry):
        # Set update_interval to None to disable automatic polling
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # CRITICAL: Disable automatic polling
        )

    async def async_config_entry_first_refresh(self):
        """Only poll during initial setup."""
        await self._async_update_data()

    # No automatic polling - all updates come via webhooks
```

### Webhook-Triggered Updates

```python
# In webhook handler
async def post(self, request: Request) -> Response:
    """Handle webhook data updates."""
    # ... validation code ...

    # Find coordinator and trigger manual refresh
    for entry in self.hass.config_entries.async_entries(DOMAIN):
        if entry.unique_id == str(owner_id):
            coordinator = self.hass.data[DOMAIN][entry.entry_id]
            # Manual refresh triggered by webhook
            self.hass.async_create_task(coordinator.async_request_refresh())
            break
```

## Webhook Integration

### Webhook Subscription Management

```python
async def renew_webhook_subscription(hass: HomeAssistant, entry: ConfigEntry):
    """Subscribe to Strava webhooks for real-time updates."""
    try:
        ha_host = get_url(hass, allow_internal=False, allow_ip=False)
    except NoURLAvailableError:
        _LOGGER.error("Home Assistant instance does not have a public URL")
        return

    callback_url = f"{ha_host}/api/strava/webhook"
    websession = async_get_clientsession(hass, verify_ssl=False)

    # Check for existing subscriptions
    try:
        async with websession.get(
            WEBHOOK_SUBSCRIPTION_URL,
            params={
                "client_id": entry.data[CONF_CLIENT_ID],
                "client_secret": entry.data[CONF_CLIENT_SECRET],
            },
        ) as response:
            response.raise_for_status()
            subscriptions = await response.json()

        # Delete outdated subscriptions
        for sub in subscriptions:
            if sub["callback_url"] != callback_url:
                _LOGGER.debug(f"Deleting outdated webhook subscription: {sub['id']}")
                async with websession.delete(
                    f"{WEBHOOK_SUBSCRIPTION_URL}/{sub['id']}",
                    data={
                        "client_id": entry.data[CONF_CLIENT_ID],
                        "client_secret": entry.data[CONF_CLIENT_SECRET],
                    },
                ) as delete_response:
                    delete_response.raise_for_status()

        # Create new subscription if needed
        if not any(sub["callback_url"] == callback_url for sub in subscriptions):
            await _create_webhook_subscription(websession, entry, callback_url)

    except aiohttp.ClientError as err:
        _LOGGER.error(f"Error managing webhook subscriptions: {err}")

async def _create_webhook_subscription(websession, entry, callback_url):
    """Create a new webhook subscription."""
    _LOGGER.debug(f"Creating new webhook subscription for {callback_url}")
    async with websession.post(
        WEBHOOK_SUBSCRIPTION_URL,
        data={
            CONF_CLIENT_ID: entry.data[CONF_CLIENT_ID],
            CONF_CLIENT_SECRET: entry.data[CONF_CLIENT_SECRET],
            CONF_CALLBACK_URL: callback_url,
            "verify_token": "HA_STRAVA",
        },
    ) as response:
        response.raise_for_status()
        new_sub = await response.json()

        # Store webhook ID in config entry
        mutable_data = {**entry.data}
        mutable_data[CONF_WEBHOOK_ID] = new_sub["id"]
        hass.config_entries.async_update_entry(entry, data=mutable_data)
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
        _LOGGER.debug(f"Strava Endpoint got a GET request from {request.headers.get('Host', None)}")
        challenge = request.query.get("hub.challenge")
        if challenge:
            return json_response({"hub.challenge": challenge})
        return Response(status=HTTPStatus.OK)

    async def post(self, request: Request) -> Response:
        """Handle webhook data updates."""
        request_host = request.headers.get("Host", None)
        _LOGGER.debug(f"Strava Webhook Endpoint received a POST request from: {request_host}")

        try:
            data = await request.json()
            owner_id = data.get("owner_id")
        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON received in webhook")
            return Response(status=HTTPStatus.BAD_REQUEST)

        if not owner_id:
            _LOGGER.warning("Webhook received without owner_id")
            return Response(status=HTTPStatus.OK)

        # Find coordinator for this user and trigger refresh
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == str(owner_id):
                coordinator = self.hass.data[DOMAIN][entry.entry_id]
                self.hass.async_create_task(coordinator.async_request_refresh())
                break
        else:
            _LOGGER.warning(f"Webhook received for unknown user: {owner_id}")

        return Response(status=HTTPStatus.OK)
```

## Geocoding Integration

### Geocoding Service Integration

```python
async def _geocode_activity(
    self, activity: dict, activity_dto: dict, auth: str
) -> str:
    """Fetch the best geocode possible from the activity's start location."""
    # Try segment efforts first (most accurate)
    if activity_dto and (segment_efforts := activity_dto.get("segment_efforts")):
        if segment := segment_efforts[0].get("segment"):
            if city := segment.get("city"):
                return city

    # Try Strava's location data
    if city := activity.get("location_city"):
        return city
    if state := activity.get("location_state"):
        return state

    # Fall back to external geocoding service
    if start_latlng := activity.get("start_latlng"):
        geo_location = await self._make_geocode_request(
            start_latlng=start_latlng, auth=auth
        )
        if city := geo_location.get("city"):
            return city if city != GEOCODE_XYZ_THROTTLED else UNKNOWN_AREA
        return geo_location.get("region", UNKNOWN_AREA)

    return UNKNOWN_AREA

async def _make_geocode_request(self, start_latlng: list, auth: str) -> dict:
    """Make geocoding request to external service."""
    request_url = (
        f"https://geocode.xyz/{start_latlng[0]},{start_latlng[1]}?geoit=json"
    )
    if auth:
        request_url += f"&auth={auth}"

    response = await self.oauth_session.async_request("GET", request_url)
    return await response.json()
```

## Error Handling Patterns

### API Error Handling

```python
async def _async_update_data(self):
    """Fetch data with comprehensive error handling."""
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
        _LOGGER.error(f"API communication error: {err}")
        raise UpdateFailed(f"Error communicating with API: {err}") from err
    except json.JSONDecodeError as err:
        _LOGGER.error(f"Invalid JSON response: {err}")
        raise UpdateFailed("Invalid response format") from err
    except Exception as err:
        _LOGGER.error(f"Unexpected error during data update: {err}")
        raise UpdateFailed(f"Unexpected error: {err}") from err
```

### Rate Limiting and Throttling

```python
# Track API call timestamps to implement rate limiting
self._last_api_call = {}
self._rate_limit_delay = 1.0  # seconds between calls

async def _rate_limited_request(self, method: str, url: str, **kwargs):
    """Make rate-limited API request."""
    now = time.time()
    last_call = self._last_api_call.get(url, 0)

    if now - last_call < self._rate_limit_delay:
        await asyncio.sleep(self._rate_limit_delay - (now - last_call))

    self._last_api_call[url] = time.time()
    return await self.oauth_session.async_request(method, url, **kwargs)
```

## Data Processing Patterns

### Activity Data Processing

```python
def _sensor_activity(self, activity: dict, geocode: str) -> dict:
    """Process raw activity data into sensor format."""
    return {
        CONF_SENSOR_ID: activity.get("id"),
        CONF_SENSOR_TITLE: activity.get("name", "Strava Activity"),
        CONF_SENSOR_CITY: geocode,
        CONF_SENSOR_ACTIVITY_TYPE: activity.get("type", "Ride").lower(),
        CONF_SENSOR_DISTANCE: float(activity.get("distance", -1)),
        CONF_SENSOR_DATE: dt.strptime(
            activity.get("start_date_local", "2000-01-01T00:00:00Z"),
            "%Y-%m-%dT%H:%M:%SZ",
        ),
        CONF_SENSOR_ELAPSED_TIME: int(activity.get("elapsed_time", -1)),
        CONF_SENSOR_MOVING_TIME: int(activity.get("moving_time", -1)),
        CONF_SENSOR_KUDOS: int(activity.get("kudos_count", -1)),
        CONF_SENSOR_CALORIES: int(
            activity.get(
                CONF_SENSOR_CALORIES,
                activity.get("kilojoules", (-1 / FACTOR_KILOJOULES_TO_KILOCALORIES))
                * FACTOR_KILOJOULES_TO_KILOCALORIES,
            )
        ),
        CONF_SENSOR_ELEVATION: int(activity.get("total_elevation_gain", -1)),
        CONF_SENSOR_POWER: int(activity.get("average_watts", -1)),
        CONF_SENSOR_TROPHIES: int(activity.get("achievement_count", -1)),
        CONF_SENSOR_HEART_RATE_AVG: float(activity.get("average_heartrate", -1)),
        CONF_SENSOR_HEART_RATE_MAX: float(activity.get("max_heartrate", -1)),
        CONF_SENSOR_CADENCE_AVG: float(
            activity.get("average_cadence", (-1 / 2)) * 2
        ),
        CONF_ATTR_START_LATLONG: activity.get("start_latlng"),
        CONF_ATTR_END_LATLONG: activity.get("end_latlng"),
        CONF_ATTR_SPORT_TYPE: activity.get("sport_type"),
        CONF_ATTR_COMMUTE: activity.get("commute", False),
        CONF_ATTR_PRIVATE: activity.get("private", False),
        CONF_ATTR_POLYLINE: activity.get("map", {}).get("summary_polyline", ""),
    }
```

### Summary Stats Processing

```python
def _sensor_summary_stats(self, summary_stats: dict) -> dict:
    """Process summary statistics into structured format."""
    athlete_id = str(summary_stats.get(CONF_SENSOR_ID, ""))

    return {
        CONF_ACTIVITY_TYPE_RIDE: {
            CONF_SUMMARY_RECENT: {
                CONF_SENSOR_ID: athlete_id,
                CONF_SENSOR_DISTANCE: float(
                    summary_stats.get("recent_ride_totals", {}).get("distance", 0)
                ),
                CONF_SENSOR_ACTIVITY_COUNT: int(
                    summary_stats.get("recent_ride_totals", {}).get("count", 0)
                ),
                CONF_SENSOR_MOVING_TIME: int(
                    summary_stats.get("recent_ride_totals", {}).get("moving_time", 0)
                ),
                CONF_SENSOR_ELEVATION: float(
                    summary_stats.get("recent_ride_totals", {}).get("elevation_gain", 0)
                ),
            },
            # ... YTD and ALL time periods
        },
        # ... RUN and SWIM activity types
    }
```

## Caching and Performance

### Image URL Caching

```python
async def _update_urls(self):
    """Update and cache image URLs."""
    if self.coordinator.data and self.coordinator.data.get("images"):
        for img_url in self.coordinator.data["images"]:
            self._urls[md5(img_url["url"].encode()).hexdigest()] = img_url

        # Limit cache size
        self._urls = dict(
            sorted(self._urls.items(), key=lambda item: item[1]["date"])[-CONF_MAX_NB_IMAGES:]
        )
        await self._store_pickle_urls()

async def _store_pickle_urls(self):
    """Store image URLs to persistent storage."""
    try:
        async with aiofiles.open(self._url_dump_filepath, "wb") as file:
            await file.write(pickle.dumps(self._urls))
    except (OSError, pickle.PickleError) as err:
        _LOGGER.error(f"Error storing pickled URLs: {err}")
```

### API Response Caching

```python
# Cache API responses to avoid unnecessary calls
self._api_cache = {}
self._cache_ttl = 300  # 5 minutes

async def _cached_api_request(self, cache_key: str, url: str, **kwargs):
    """Make cached API request."""
    now = time.time()

    if cache_key in self._api_cache:
        cached_data, timestamp = self._api_cache[cache_key]
        if now - timestamp < self._cache_ttl:
            return cached_data

    response = await self.oauth_session.async_request(url, **kwargs)
    data = await response.json()

    self._api_cache[cache_key] = (data, now)
    return data
```

## Security Considerations

### API Key Management

```python
# Never log sensitive information
_LOGGER.debug("Making API request to %s", url)  # OK
_LOGGER.debug("API key: %s", api_key)  # NEVER DO THIS

# Validate API responses
def _validate_api_response(self, response_data: dict) -> bool:
    """Validate API response structure."""
    required_fields = ["id", "name", "distance"]
    return all(field in response_data for field in required_fields)
```

### Input Sanitization

```python
def _sanitize_activity_data(self, raw_data: dict) -> dict:
    """Sanitize activity data from API."""
    sanitized = {}
    for key, value in raw_data.items():
        if isinstance(value, str):
            # Remove potential XSS or injection attempts
            sanitized[key] = value.strip()[:1000]  # Limit length
        elif isinstance(value, (int, float)):
            sanitized[key] = value
        elif isinstance(value, dict):
            sanitized[key] = self._sanitize_activity_data(value)
    return sanitized
```

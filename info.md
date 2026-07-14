# Strava integration for Home Assistant (Unofficial)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/craibo/ha_strava?color=41BDF5&style=for-the-badge)](https://github.com/craibo/ha_strava/releases/latest)
[![Integration Usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&style=for-the-badge&logo=home-assistant&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.ha_strava.total)](https://analytics.home-assistant.io/)

<img src="https://raw.githubusercontent.com/craibo/ha_strava/main/img/api_logo_pwrdBy_strava_stack_light.png">

The unofficial Strava intregration for Home Assistant. Adds a custom component to integrate Strava activity data into Home Assistant.

## Support this project

[![Sponsor me on GitHub](https://img.shields.io/badge/Sponsor-craibo%20on%20GitHub-blue.svg?logo=github)](https://github.com/sponsors/craibo)
[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?logo=paypal)](https://paypal.me/craibo?country.x=AU&locale.x=en_AU)

## Important Notes:

> ⚠️ **Strava subscription required from 1 July 2026**
> Strava now requires a paid Strava subscription to use the API as a Standard Tier developer. Without an active subscription, the integration will stop receiving updates after this date. Visit your [API settings dashboard](https://www.strava.com/settings/api) to check your subscription status.

When configuring the Strava API, the **Authorization Callback Domain** must be set to: **my.home-assistant.io**

## Features

- Gives you access to **your most recent activities** in Strava.
- Pulls Recent (last 4 weeks), Year-to-Date (YTD) and All-Time **summary statistics**
- Creates a **camera entity** in Home Assistant to **feature recent Strava pictures** as a photo-carousel
- Supports both the **metric and the imperial** unit system
- Activity data in Home Assistant **auto-updates** whenever you add, modify, or delete activities on Strava
- **Activity Type Selection**: Choose which of the 50 supported activity types to track
- **Device Source Tracking**: Automatically detects and displays the device used for each activity
- **Gear Sensors**: Track your bikes and shoes with distance and detailed information (brand, model, etc.)
- **Multi-User Support**: Add up to 10 Strava accounts sharing a single API app (Standard Tier), or each with their own app credentials
- **Easy set-up**: only enter your Strava Client-ID and Client-Secret and you're ready to go

<img src="https://raw.githubusercontent.com/craibo/ha_strava/main/img/strava_activity_device.png" width="50%"><img src="https://raw.githubusercontent.com/craibo/ha_strava/main/img/strava_summary_device.png" width="50%">

The Strava Home Assistant Integration creates **sensor entities** for each activity type you choose to track. For each selected activity type, you get:

**Activity Sensors:**

- **Latest Activity**: Shows the name of your most recent activity of that type
- **Activity Details**: Includes distance, time, elevation, heart rate, power, and more
- **Device Information**: Automatically detects and displays the device used (Garmin, Apple Watch, etc.)

**Summary Statistics Sensors:**

- **Recent** (last 4 weeks): Distance, activity count, and other metrics
- **Year-to-Date**: Cumulative statistics for the current year
- **All-Time**: Lifetime statistics for each activity type

**Gear Sensors:**

- **Gear Name**: Shows the name of each gear item (bike or shoe) with attributes including brand, model, and description
- **Gear Distance**: Tracks the total distance for each gear item with proper unit conversion
- Configure the number of gear sensors to display (1-20, default: 3)

**Supported Activity Types:**
The integration supports all 50 Strava activity types including Run, Ride, Walk, Swim, Hike, AlpineSki, BackcountrySki, Badminton, Canoeing, Crossfit, EBikeRide, Elliptical, Golf, GravelRide, Handcycle, HighIntensityIntervalTraining, IceSkate, InlineSkate, Kayaking, Kitesurf, MountainBikeRide, NordicSki, Pickleball, Pilates, Racquetball, RockClimbing, RollerSki, Rowing, Sail, Skateboard, Snowboard, Snowshoe, Soccer, Squash, StairStepper, StandUpPaddling, Surfing, TableTennis, Tennis, TrailRun, Velomobile, VirtualRide, VirtualRow, VirtualRun, WeightTraining, Wheelchair, Windsurf, Workout, and Yoga.

You can use all sensor data in your **Dashboards and Automations**, just as you'd use any other sensor data in Home Assistant.

## Installation

### 1. Set up remote access to your Home Assistant Installation

To use the Strava Home Assistant integration, your Home Assistant Instance must be accessible from an **External URL** (i.e. Remote Access). Without remote access, the integration won't be able to pull data from Strava. To learn how to set up Remote Access for Home Assistant, please visit the [Official Documentation](https://www.home-assistant.io/docs/configuration/remote/)

_If you use **Nabu Casa** then do this configuration from your **Nabu Casa URL**. You can find this under Configuration -> "Home Assistant Cloud"_

### 2. Obtain your Strava API credentials

**For Single User Setup:**

After you've set up remote access for your Home Assistant instance, click [here](https://www.strava.com/settings/api) **or** head over to your **Strava Profile** and go to `Settings` > `My API Application`.

Follow the steps in the configuration wizard, and eventually obtain your Strava API credentials (ID + secret). We need those credentials during the final installation step.

**!!! IMPORTANT !!!** The **Authorization Callback Domain** must be set to: **my.home-assistant.io**

**Strava API tiers — how many users can share one app?**

Strava's Standard Tier allows up to 10 athletes per API app (self-upgrade in your [API settings dashboard](https://www.strava.com/settings/api), no review required). For a single user or a household, one set of credentials is all you need. See "Adding Multiple Strava Accounts" below.

### 3. Add the Strava Home Assistant Integration to your Home Assistant Installation

As of now, the Strava Home Assistant Integration can only be installed as a custom repository through the Home Assistant Community Store (HACS). The installation process is super easy

1. Install [HACS](#hacs) follwing the instructions [here](https://hacs.xyz/docs/setup/download)
2. [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=craibo&repository=ha_strava&category=integration)
3. Press the Download button
4. Restart Home Assistant
5. [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_strava)

### 4. Make a connection between your Strava account and Home Assistant

Now is the time to fire up the Strava Home Assistant Integration for the first time and make a connection between Strava and your Home Assistant Instance.

From within Home Assistant, head over to `Configuration` > `Integrations` and hit the "+" symbol at the bottom. Search for "Strava Home Assistant" and click on the icon to add the Integration to Home Assistant. You'll automatically be prompted to enter your Strava API credentials. It'll take a few seconds to complete the set-up process after you've granted all the required permissions.

### 5. Adding Multiple Strava Accounts

The integration supports multiple Strava users in a single Home Assistant instance. Each user gets their own separate integration entry and fully isolated data. There are two ways to set this up:

---

#### Option A — Shared API app (Standard Tier, up to 10 athletes) ✅ Recommended

One person creates a Strava API app and shares the credentials. The integration handles webhook deduplication automatically.

1. The app owner self-upgrades to Standard Tier in the [API settings dashboard](https://www.strava.com/settings/api) (no review needed)
2. Ensure **Authorization Callback Domain** is set to: **my.home-assistant.io**
3. Share the **Client ID** and **Client Secret** with each additional user
4. For each user: `Settings` > `Devices & Services` > `Add Integration` > "Strava Home Assistant"
5. Enter the **same** Client ID and Client Secret
6. Each user completes OAuth2 with **their own Strava account**

> Add users one at a time to avoid a race condition on webhook registration.

---

#### Option B — Separate API app per user

Each user creates their own app at [strava.com/settings/api](https://www.strava.com/settings/api) with unique credentials. Use this if you need more than 10 users or users prefer independent apps.

## ⚠️ Breaking Changes in v4.0.0

**This is a major version update with significant architectural changes:**

- **New Architecture**: Complete rewrite from individual activity devices to activity type-based sensors
- **Activity Type Selection**: Choose which of the 50 supported activity types to track
- **Device Source Detection**: Automatically detects and displays the device used for each activity
- **Improved Performance**: More efficient data fetching and processing
- **Enhanced Statistics**: Better summary statistics for each activity type

**Migration Required**: Existing installations will need to be reconfigured. The old individual activity devices are no longer supported.

## Configuration/Customization

Upon completion of the installation process, the Strava Home Assistant integration **automatically creates sensor entities** for the activity types you select. By default, the integration tracks **Run, Ride, and Swim** activities.

### 1. Select Activity Types to Track

You can **choose which activity types to track** from within Home Assistant. The integration supports all 50 Strava activity types.

Just locate the Strava Home Assistant Integration under `Configuration` > `Integrations`, click on `CONFIGURE`, and select the activity types you want to track. After you've saved your settings, it might take a few minutes for Home Assistant to create the corresponding sensor entities and fetch the underlying data.

### 2. Specifying the Distance unit system to use

Three configurations for the **_distance unit system_** are available.

- `Default` uses the Home Assistant `Unit System` configuration
- `Metric` uses kilometers (km) and meters (m) for distances
- `Imperial` uses miles (mi) and feet (ft) for distances

This setting is selectable on configuration of the Strava integration and from the Strava Home Assistant Integration under `Configuration` > `Integrations`, click on `CONFIGURE`.

### 3. Photo Import Settings

You can configure whether to import photos from your Strava activities and set the rotation interval for the camera entity.

### 4. Gear Sensors

You can enable gear sensors to track your bikes and shoes from Strava. When enabled, the integration will:

- Fetch your most recently used gear items (bikes and shoes combined)
- Create a device for each gear item
- Create two sensors per gear:
  - **Gear Name**: Shows the gear name with attributes (id, brand_name, model_name, primary, description)
  - **Gear Distance**: Shows the total distance for the gear with proper unit conversion

**Configuration Options:**

- **Enable Gear Sensors**: Checkbox to enable/disable gear sensors
- **Number of Gear Sensors**: Slider to select how many gear items to track (1-20, default: 3)

The gear items are sorted by distance (most used first), and the integration respects API rate limits by caching gear details.

**_NOTES_**

1. Changing the unit system setting will require a restart of Home Assistant to be fully applied.
2. The new architecture provides more reliable and efficient data processing compared to previous versions.

## Displaying an Activity Route/Map

Activity sensors expose a `polyline` attribute containing the route as a Google-encoded polyline string. Since that string isn't directly usable by map cards, the integration provides the `ha_strava.get_activity_route` service to decode it into a list of `{lat, lon}` coordinates on demand — keeping the raw encoded string in sensor attributes (recorder-friendly) while giving you real coordinates when you need to render a map.

**Calling the service:**

```yaml
service: ha_strava.get_activity_route
data:
  activity_id: "1234567890"
```

The service returns a response shaped like:

```yaml
route:
  - lat: 38.5
    lon: -120.2
  - lat: 40.7
    lon: -120.95
```

**Rendering the route on a map card:**

The [journey-viewer-card](https://github.com/nledenyi/journey-viewer-card) Lovelace card can render Strava-style per-activity maps using this service. It reads activity data from any sensor matching its [data contract](https://github.com/nledenyi/journey-viewer-card/blob/main/README.md#data-contract) and lazily loads the route via a configurable `route_service` hook, which you can point at `ha_strava.get_activity_route`. See the card's documentation for full setup instructions.

## Contributors

- [@craibo](https://github.com/craibo)
- [@jlapenna](https://github.com/jlapenna)
- [@madmic1314](https://github.com/madmic1314)
- [@codingcyclist](https://github.com/codingcyclist)

## Acknowledgments

Forked from <https://github.com/madmic1314/ha_strava> (project abandoned).

Originally forked from <https://github.com/codingcyclist/ha_strava> (project abandoned).

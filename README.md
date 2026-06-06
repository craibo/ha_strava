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
- **Webhook-First Architecture**: Uses Strava webhooks for real-time updates, respecting API rate limits
- **Easy set-up**: only enter your Strava Client-ID and Client-Secret and you're ready to go

## How It Works

This integration uses a **webhook-first architecture** to respect Strava's API rate limits:

- **Initial Setup**: Fetches your data once during configuration
- **Real-Time Updates**: Uses Strava webhooks to receive updates instantly when you add/modify activities
- **No Continuous Polling**: Never continuously polls the API, preventing rate limit issues
- **API Rate Limit Compliance**: Stays well within Strava's limits (100 requests/15min, 1000/day)

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

Head over to your **Strava Profile** and go to `Settings` > `My API Application` (or click [here](https://www.strava.com/settings/api)).

Follow the steps in the configuration wizard to obtain your Strava API credentials (Client ID + Client Secret).

**!!! IMPORTANT !!!** The **Authorization Callback Domain** must be set to: **my.home-assistant.io**

**Strava API tiers — how many users can share one app?**

| Tier               | Athletes per app | How to get it                                                                                         |
| ------------------ | ---------------- | ----------------------------------------------------------------------------------------------------- |
| Standard (default) | Up to 10         | Self-upgrade in your [API settings dashboard](https://www.strava.com/settings/api) — no review needed |
| Extended Access    | Higher limits    | Apply via Strava developer program                                                                    |

For a **single user** or a **household sharing one Strava API app** (up to 10 athletes), one set of credentials is all you need. See "Adding Multiple Strava Accounts" below.

### 3. Add the Strava Home Assistant Integration to your Home Assistant

As of now, the Strava Home Assistant Integration can only be installed as a custom repository through the Home Assistant Community Store (HACS). The installation process is super easy

1. Install [HACS](#hacs) follwing the instructions [here](https://hacs.xyz/docs/setup/download)
2. [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=craibo&repository=ha_strava&category=integration)
3. Press the Download button
4. Restart Home Assistant
5. [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_strava)

### 4. Make a connection between your Strava account and Home Assistant

Now is the time to fire up the Strava Home Assistant Integration for the first time and make a connection between Strava and your Home Assistant Instance.

From within Home Assistant, head over to `Configuration` > `Integrations` and hit the `+` symbol at the bottom. Search for "Strava Home Assistant" and click on the icon to add the Integration to Home Assistant. You'll automatically be prompted to enter your Strava API credentials. It'll take a few seconds to complete the set-up process after you've granted all the required permissions.

### 5. Adding Multiple Strava Accounts

The integration supports multiple Strava users in a single Home Assistant instance. Each user gets their own separate integration entry and fully isolated data.

There are two ways to set this up depending on your Strava API tier:

---

#### Option A — Shared API app (Standard Tier, up to 10 athletes) ✅ Recommended

One person creates a single Strava API app and shares the Client ID and Client Secret with everyone who needs access. The integration handles webhook deduplication automatically — only one webhook subscription is ever registered regardless of how many users are added.

**Setup:**

1. The app owner self-upgrades their Strava app to Standard Tier in the [API settings dashboard](https://www.strava.com/settings/api) (no review required, supports up to 10 athletes)
2. Ensure the **Authorization Callback Domain** is set to: **my.home-assistant.io**
3. Share the **Client ID** and **Client Secret** with each user who needs to be added
4. For each additional user, in Home Assistant go to `Settings` > `Devices & Services` and click `Add Integration`
5. Search for "Strava Home Assistant" and enter the **same** Client ID and Client Secret
6. Each user completes the OAuth2 flow with **their own Strava account** — this is what links their personal data

> **Note:** Add users one at a time, not simultaneously, to avoid a race condition on webhook registration.

---

#### Option B — Separate API app per user

Each user creates their own Strava app at [strava.com/settings/api](https://www.strava.com/settings/api) with a unique Client ID and Client Secret. Follow the same steps 3–6 above, entering each user's own credentials.

Use this approach if you need more than 10 users, or if users prefer to manage their own API apps independently.

## Configuration/Customization

Upon completion of the installation process, the Strava Home Assistant integration **automatically creates sensor entities** for the activity types you select. By default, the integration tracks **Run, Ride, and Swim** activities.

### 1. Select Activity Types to Track

You can **choose which activity types to track** from the 50 supported Strava activity types.

1. Go to `Configuration` > `Integrations`
2. Find the Strava Home Assistant Integration and click `CONFIGURE`
3. Select the activity types you want to track from the multi-select list
4. Save your settings

The integration will create sensors for each selected activity type, showing your latest activity and summary statistics.

### 2. Distance Unit System

Three configurations for the **_distance unit system_** are available.

- `Default` uses the Home Assistant `Unit System` configuration
- `Metric` uses kilometers (km) and meters (m) for distances
- `Imperial` uses miles (mi) and feet (ft) for distances

This setting is selectable during initial setup and can be changed later under `Configuration` > `Integrations` > `CONFIGURE`.

### 3. Photo Updates

You can enable or disable automatic photo updates for the camera entity. When enabled, the integration will fetch new photos from your activities and update the camera entity accordingly.

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
2. The integration now fetches up to 200 activities instead of being limited to 10.
3. Device source tracking automatically detects the device used for each activity (Garmin, Apple Watch, etc.).

## Contributors

- [@craibo](https://github.com/craibo)
- [@jlapenna](https://github.com/jlapenna)
- [@madmic1314](https://github.com/madmic1314)
- [@codingcyclist](https://github.com/codingcyclist)

## Acknowledgments

Forked from <https://github.com/madmic1314/ha_strava> (project abandoned).

Originally forked from <https://github.com/codingcyclist/ha_strava> (project abandoned).

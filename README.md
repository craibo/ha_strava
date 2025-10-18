[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/craibo/ha_strava?color=41BDF5&style=for-the-badge)](https://github.com/craibo/ha_strava/releases/latest)
[![Integration Usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&style=for-the-badge&logo=home-assistant&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.ha_strava.total)](https://analytics.home-assistant.io/)

---

## ⚠️ Breaking Changes in v4.0.0

**This is a major version update with significant architectural changes:**

1. **Complete Sensor Restructure**: All existing sensors will be removed and replaced with a new architecture
2. **Activity Type Selection**: You must now select which activity types to track (defaults to Run, Ride, Walk, Swim)
3. **Entity ID Changes**: All sensor entity IDs will change
4. **No Migration Path**: You must manually reconfigure the integration after updating
5. **Device Source Tracking**: New feature that automatically detects the device used for each activity
6. **Removed Dependencies**: No longer requires geocode.xyz API key

**Before updating to v4.0.0:**

- Note down your current sensor entity IDs if you have automations or dashboards using them
- Plan to reconfigure the integration after the update
- Consider backing up your Home Assistant configuration

A maintenance mode 3.2 release branch will be maintained for a period of time for those that do not want to upgrade to
4.0.0.

---

# Strava integration for Home Assistant (Unofficial)

<img src="https://raw.githubusercontent.com/craibo/ha_strava/main/img/api_logo_pwrdBy_strava_stack_light.png">

The unofficial Strava intregration for Home Assistant. Adds a custom component to integrate Strava activity data into Home Assistant.

## Important Notes:

When configuring the Strava API, the **Authorization Callback Domain** must be set to: **my.home-assistant.io**

## Features

- Gives you access to **your most recent activities** in Strava.
- Pulls Recent (last 4 weeks), Year-to-Date (YTD) and All-Time **summary statistics**
- Creates a **camera entity** in Home Assistant to **feature recent Strava pictures** as a photo-carousel
- Supports both the **metric and the imperial** unit system
- Activity data in Home Assistant **auto-updates** whenever you add, modify, or delete activities on Strava
- **Activity Type Selection**: Choose which of the 50 supported activity types to track
- **Device Source Tracking**: Automatically detects and displays the device used for each activity
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

**Supported Activity Types:**
The integration supports all 50 Strava activity types including Run, Ride, Walk, Swim, Hike, AlpineSki, BackcountrySki, Badminton, Canoeing, Crossfit, EBikeRide, Elliptical, Golf, GravelRide, Handcycle, HighIntensityIntervalTraining, IceSkate, InlineSkate, Kayaking, Kitesurf, MountainBikeRide, NordicSki, Pickleball, Pilates, Racquetball, RockClimbing, RollerSki, Rowing, Sail, Skateboard, Snowboard, Snowshoe, Soccer, Squash, StairStepper, StandUpPaddling, Surfing, TableTennis, Tennis, TrailRun, Velomobile, VirtualRide, VirtualRow, VirtualRun, WeightTraining, Wheelchair, Windsurf, Workout, and Yoga.

You can use all sensor data in your **Dashboards and Automations**, just as you'd use any other sensor data in Home Assistant.

## Installation

### 1. Set up remote access to your Home Assistant Installation

To use the Strava Home Assistant integration, your Home Assistant Instance must be accessible from an **External URL** (i.e. Remote Access). Without remote access, the integration won't be able to pull data from Strava. To learn how to set up Remote Access for Home Assistant, please visit the [Official Documentation](https://www.home-assistant.io/docs/configuration/remote/)

_If you use **Nabu Casa** then do this configuration from your **Nabu Casa URL**. You can find this under Configuration -> "Home Assistant Cloud"_

### 2. Obtain your Strava API credentials

After you've set up remote access for your Home Assistant instance, click [here](https://www.strava.com/settings/api) **or** head over to your **Strava Profile** and go to `Settings` > `My API Application`.

Follow the steps in the configuration wizard, and eventually obtain your Strava API credentials (ID + secret). We need those credentials during the final installation step.

**!!! IMPORTANT !!!** The **Authorization Callback Domain** must be set to: **my.home-assistant.io**

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

## Configuration/Customization

Upon completion of the installation process, the Strava Home Assistant integration **automatically creates sensor entities** for the activity types you select. By default, the integration tracks **Run, Ride, Walk, and Swim** activities.

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

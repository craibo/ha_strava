[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/craibo/ha_strava?color=41BDF5&style=for-the-badge)](https://github.com/craibo/ha_strava/releases/latest)
[![Integration Usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&style=for-the-badge&logo=home-assistant&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.ha_strava.total)](https://analytics.home-assistant.io/)

# Strava Home Assistant Integration

Custom Component to integrate Activity Data from Strava into Home Assistant.

## Important Notes:

When configuring the Strava API, the **Authorization Callback Domain** must be set to: **my.home-assistant.io**

## Features

- Gives you access to **up to 10 of your most recent activities** in Strava.
- Pulls Recent (last 4 weeks), Year-to-Date (YTD) and All-Time **summary statistics for Run, Ride, and Swim activities**
- Creates a **camera entity** in Home Assistant to **feature recent Strava pictures** as a photo-carousel
- Supports both the **metric and the imperial** unit system
- Activity data in Home Assistant **auto-updates** whenever you add, modify, or delete activities on Strava
- Exposes **13 sensor entities** for each Strava activity
- **Easy set-up**: only enter your Strava Client-ID and Client-Secret and you're ready to go

<img src="https://raw.githubusercontent.com/craibo/ha_strava/main/img/strava_activity_device.png" width="50%"><img src="https://raw.githubusercontent.com/craibo/ha_strava/main/img/strava_summary_device.png" width="50%">

For every Strava activity, the Strava Home Assistant Integration creates a **device entity** in Home Assistant (max 10 activities). Each of these virtual device entities exposes **thirteen sensor entities**:

- Date & Title
  - Activity type
  - Start geo co-ordinates
- Elapsed Time
- Moving Time
- Pace
- Speed
- Distance
- Heart Rate (Average)
- Heart Rate (Max)
- Calories
- Cadence (Average)
- Elevation Gain
- Power
- Kudos
- Trophies

Since every Strava activity gets its own virtual device, you can use the underlying sensor data in your **Dashboards and Automations**, just as you'd use any other sensor data in Home Assistant.

## Installation

### 1. Set up remote access to your Home Assistant Installation

To use the Strava Home Assistant integration, your Home Assistant Instance must be accessible from an **External URL** (i.e. Remote Access). Without remote access, the integration won't be able to pull data from Strava. To learn how to set up Remote Access for Home Assistant, please visit the [Official Documentation](https://www.home-assistant.io/docs/configuration/remote/)

_If you use **Nabu Casa** then do this configuration from your **Nabu Casa URL**. You can find this under Configuration -> "Home Assistant Cloud"_

### 2. Obtain your Strava API credentials

After you've set up remote access for your Home Assistant instance, click [here](https://www.strava.com/settings/api) **or** head over to your **Strava Profile** and go to `Settings` > `My API Application`.

Follow the steps in the configuration wizard, and eventually obtain your Strava API credentials (ID + secret). We need those credentials during the final installation step.

**!!! IMPORTANT !!!** The **Authorization Callback Domain** must be set to: **my.home-assistant.io**

### 3. Add the Strava Home Assistant Integration to your Home Assistant Installation

As of now, the Strava Home Assistant Integration can only be installed as a custom repository through the Home Assistant Community Store (HACS). The installation process is super easy

- Install HACS follwing the instructions [here](https://hacs.xyz/docs/setup/download)
- Add this repository **https://github.com/craibo/ha_strava** in `HACS` > `Integrations` as a Custom Repository
- Add the HA Strava integration using the `+Explore & Download Respoitories` button

### 4. Make a connection between your Strava account and Home Assistant

Now is the time to fire up the Strava Home Assistant Integration for the first time and make a connection between Strava and your Home Assistant Instance.

From within Home Assistant, head over to `Configuration` > `Integrations` and hit the "+" symbol at the bottom. Search for "Strava Home Assistant" and click on the icon to add the Integration to Home Assistant. You'll automatically be prompted to enter your Strava API credentials. It'll take a few seconds to complete the set-up process after you've granted all the required permissions.

## Configuration/Customization

Upon completion of the installation process, the Strava Home Assistant integration **automatically creates device- and sensor entities** for you to access data from your most recent Strava activities. Per default, only sensor entities for the **two most recent Strava activities** are visible in Home Assistant. Please read the section below to learn how to change the number of visible sensor entities for Strava Home Assistant.

### 1. Increase/Decrease the number of Strava activities available in Home Assistant

You can always **adjust the number of Strava activities you wish to track** from within Home Assistant (min 1; max 10).

Just locate the Strava Home Assistant Integration under `Configuration` > `Integrations`, click on `CONFIGURE`, and use the slider to adjust the number of activities. After you've saved your settings, it might take a few minutes for Home Assistant to create the corresponding sensor entities and fetch the underlying data. The activities available in Home Assistant always correspond to the most recent ones under your Strava profile.

### 2. Specifying the Distance unit system to use

Three configurations for the **_distance unit system_** are available.

- `Default` uses the Home Assistant `Unit System` configuration
- `Metric` uses kilometers (km) and meters (m) for distances
- `Imperial` uses miles (mi) and feet (ft) for distances

This setting is selectable on configuration of the Strava integration and from the Strava Home Assistant Integration under `Configuration` > `Integrations`, click on `CONFIGURE`.

### 3. Geocode.xyz API Key

An initial attempt to get the location from the detailed strava activity is made, however if this is not present the geocode.xyz service is used. If your activity titles are constantly showing the area as **Unknown Area**, this is likely a result of the geocode.xyz api throttling. You are able to register for a free geocode.xyz account which will provide you with an API key. This key will reduce the throttling applied your geocoding queries.

1. Go to https://geocode.xyz/new_account to register your account. 
2. Copy the provided API key
3. Paste the API Key in the configuration of the Strava Home Assistant Integration found here: `Configuration` > `Integrations`, click on `CONFIGURE`.

**_NOTES_**

1. Changing the unit system setting will require a restart of Home Assistant to be fully applied.
2. Due to the way that some sensors track statistical data, changing this after the initial integration setup may result in some staticstical data not showing correctly.

## Contributors

- [@craibo](https://github.com/craibo)
- [@jlapenna](https://github.com/jlapenna)
- [@madmic1314](https://github.com/madmic1314)
- [@codingcyclist](https://github.com/codingcyclist)

## Acknowledgments

Forked from <https://github.com/madmic1314/ha_strava> (project abandoned).

Originally forked from <https://github.com/codingcyclist/ha_strava> (project abandoned).

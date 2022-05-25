[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
# Picking up the Pieces
An abandoned project which needs a home, so hopefully I can keep it alive for a little longer.

This is a fork from @madmic1314 <https://github.com/madmic1314/ha_strava> after they abandoned the project

# Strava Home Assistant Integration

NOTE: You MUST remove the HA_Strava integration from Home Assistant integration, HACS Integration, HACS Custom Repository and reboot HA before adding this.

Custom Component to integrate Activity Data from Strava into Home Assistant.

This is a fork from Codingcyclist <https://github.com/codingcyclist/ha_strava> in an attempt to keep the integration alive - I take no credit for his hard work. I'm not a coder and the best you'll get from me is copy + paste, but happy to accept contributions and help from the community.

## Features
* Gives you access to statistics for **up to 10 of your most recent activities** in Strava.
* Pulls Year-to-Date (YTD) and All-Time **summary statistics for Run, Ride, and Swimm activities**
* Exposes **5 customizeable sensor entities** for each Strava activity + 18 additional entities for summary statistics
* Creates a **camera entity** in Home Assistant to **feature recent Strava pictures** as a photo-carousel
* Supports both the **metric and the imperial** unit system
* Activity data in Home Assistant **auto-updates** whenever you add, modify, or delete activities on Strava
* **Easy set-up**: only enter your Strava Client-ID and -secret and you're ready to go

![](sensor_overview.png)

For every Strava activity, the Strava Home Assistant Integration creates a **device entity** in Home Assistant (max 10 activities). Each of these virtual device entities exposes **five sensor entities** which you can fully customize to display one of the following **activity KPIs**:
* Duration (Minutes),
* Pace (Minutes/Mile ; Minutes/Km)
* Speed (Miles/Hour; Km/Hour)
* Distance (Miles; Km)
* \# Kudos
* Kalories (cKal),
* Elevation Gain (Feet, Meter)
* Power (Watts)
* \# Trophies

Since every Strava activity gets its own virtual device, you can use the underlying sensor data in your **Dashboards and Automations**, just as you'd use any other sensor data in Home Assistant. 

The Strava Home Assistant Integration also creates a **device entity** for both **Year-to-Date and All-Time** summary statistics. Each of these virtual device entities exposes **nine sensor entities**:
* Moving Time
* Distance
* Activity Count
...for **Ride, Run, and Swim** activities

## Installation
For much more detailed guidelines on how to configure Strava Home Assitant, check out the (README) https://github.com/madmic1314/ha_strava

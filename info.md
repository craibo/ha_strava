# Integration Abandonded - do not add to Home Assistant, it will fail
With the last set of changes required, I've decided to no longer try and maintain integration. There will be no fixes or replies to issues - I leave this here in case anyone wants to fork it and take over.

I used the original integration as I makde a gadget for my wife's running that sat on her desk at home as a bit of fun. She no longer works from home often, so this has fallen into disuse, especially with the drive to save as much electricity as possible, this now sits in a drawer.

I'm a technologist by day, but never learnt to code beyond VBA and a bit of VB - was also pretty good at the OPL Language used on the Psion devices - so dropping into this integration at this level is too much a learning curve. Unfortunately, I have too much else to do outside of work to learn try and Python to the level of understanding required to carry this integration on. The rate of breaking changes that come from the rapid pace of HA means I simply can't keep up - I did try.

Hopefully someone will pick this up and run with it (see what I did there?) - else so long, thanks for all the fish.

# Strava Home Assistant Integration
Custom Component to integrate Activity Data from Strava into Home Assistant.


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

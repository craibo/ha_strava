# Project Overview

This project is a custom integration for Home Assistant that brings Strava activity data into the Home Assistant ecosystem. It allows users to track their recent activities, view summary statistics, and even display photos from their Strava activities.

**Key Technologies:**

- Home Assistant
- Python 3
- Strava API
- HACS (Home Assistant Community Store)

**Architecture:**

The integration follows the standard Home Assistant custom component architecture. It uses a `config_flow` to handle user authentication and configuration via the Home Assistant UI. The core logic is within the `custom_components/ha_strava` directory, with `sensor.py` and `camera.py` creating the entities that expose Strava data to Home Assistant. Data is fetched from the Strava API and updated via a webhook.

# Building and Running

This is a Home Assistant integration and is not intended to be run as a standalone application. To use this integration, you need a running instance of Home Assistant.

**Installation:**

1.  **HACS:** The primary installation method is through the Home Assistant Community Store (HACS).
2.  **Manual:** Users can also manually copy the `custom_components/ha_strava` directory into their Home Assistant `custom_components` directory.

**Running:**

Once installed, the integration is configured through the Home Assistant UI. Users need to provide their Strava Client ID and Client Secret to authenticate with the Strava API.

**Testing:**

The project uses `pre-commit` hooks to enforce code quality and style. The following tools are used:

- `black`: for code formatting
- `flake8`: for linting
- `isort`: for sorting imports
- `pylint`: for static analysis

To run the tests locally, you can use the following command:

```bash
pre-commit run --all-files
```

# Development Conventions

- **Code Style:** The project uses `black` for code formatting and follows PEP 8 guidelines.
- **Linting:** `flake8` and `pylint` are used for linting and static analysis.
- **Imports:** `isort` is used to sort imports automatically.
- **Commits:** There are no explicit commit message conventions, but the project uses `pre-commit` to ensure code quality before committing.
- **Contributing:** The `CONTRIBUTING.md` file is empty, but the use of `pre-commit` suggests that contributions should follow the same code quality standards.

from __future__ import annotations
from homeassistant.helpers import config_entry_oauth2_flow

API_BASE = "https://www.strava.com/api/v3"

class StravaApi:
    def __init__(self, session: config_entry_oauth2_flow.OAuth2Session):
        self._session = session

    async def get_athlete(self) -> dict:
        return await self._session.async_request("GET", f"{API_BASE}/athlete")

    async def set_activity_gear(self, activity_id: int | str, gear_id: str) -> dict:
        # PUT /activities/{id} with { gear_id }
        return await self._session.async_request(
            "PUT",
            f"{API_BASE}/activities/{activity_id}",
            json={"gear_id": gear_id},
        )


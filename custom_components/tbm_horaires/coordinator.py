from datetime import timedelta, datetime, timezone
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from .const import DOMAIN, DEFAULT_INTERVAL_SEC
from .api import SiriLiteClient
import unicodedata

import logging
import httpx

LOGGER = logging.getLogger(__name__)

class TBMCoordinator(DataUpdateCoordinator):
    def __init__(self, 
            hass: HomeAssistant, 
            name: str,
            stop_point_ref: str,
            line_ref: str | None,
            destination_ref: str | None,
            real_destination: str | None,
            preview: str):
        self.hass = hass
        self.stop_point_ref = stop_point_ref
        self.line_ref = line_ref
        self.destination_ref = destination_ref
        self.real_destination = real_destination
        self.preview = preview
        self._session = httpx.AsyncClient(headers={"Accept":"application/json"})
        self.client = SiriLiteClient(self._session,
                                     api_base=hass.data[DOMAIN]["api_base"],
                                     api_key=hass.data[DOMAIN]["api_key"])
        super().__init__(hass, LOGGER, name=name, update_interval=timedelta(seconds=DEFAULT_INTERVAL_SEC))
        # super().__init__(hass, hass.helpers.event.async_call_later.__self__,  # logger
        #                  name=name,
        #                  update_interval=timedelta(seconds=DEFAULT_INTERVAL_SEC))

    async def _async_update_data(self):
        visits = await self.client.stop_monitoring(
            self.stop_point_ref, self.line_ref, self.destination_ref, self.preview, max_visits=10
        )
        if not self.real_destination:
            return visits

        def _normalize(text: str | None) -> str:
            raw = (text or "").strip().casefold()
            return "".join(c for c in unicodedata.normalize("NFKD", raw) if not unicodedata.combining(c))

        target = _normalize(self.real_destination)
        return [visit for visit in visits if _normalize(visit.get("destination")) == target]

    async def async_shutdown(self):
        await self._session.aclose()


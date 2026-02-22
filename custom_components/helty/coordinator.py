"""Data update coordinator for Helty VMC."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HeltyCloudAPI, HeltyAuthError, HeltyConnectionError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class HeltyDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that polls sensor data from the Helty cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: HeltyCloudAPI,
        board_serial: str,
        product_serial: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{board_serial}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api
        self.board_serial = board_serial
        self.product_serial = product_serial

    async def _async_update_data(self) -> dict:
        """Fetch sensor data from the API."""
        try:
            data = await self.api.read_sensors(
                self.board_serial, self.product_serial
            )
        except HeltyAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except HeltyConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        if not data:
            raise UpdateFailed("No sensor data received")

        return data

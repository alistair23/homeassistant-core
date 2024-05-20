"""Demo platform that has a couple fake lawn mowers."""

from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from datetime import datetime

from .const import DOMAIN
from .coordinator import Coordinator, HusqvarnaAutomowerBleEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutomowerLawnMower integration from a config entry."""
    coordinator: Coordinator = hass.data[DOMAIN][config_entry.entry_id]
    model = coordinator.model
    address = coordinator.address

    async_add_entities(
        [
            AutomowerLawnMower(
                coordinator,
                "automower" + model + "_" + address,
                model,
                LawnMowerEntityFeature.PAUSE
                | LawnMowerEntityFeature.START_MOWING
                | LawnMowerEntityFeature.DOCK,
            ),
            BatterySensor(
                coordinator,
                "automower" + model + "_" + address + "_battery_level",
                "Battery Level",
            ),
            MowerNextStart(
                coordinator,
                "automower" + model + "_" + address + "_next_start_time",
                "Next Start Time",
            ),
        ]
    )


class AutomowerLawnMower(HusqvarnaAutomowerBleEntity, LawnMowerEntity):
    """Husqvarna Automower."""

    def __init__(
        self,
        coordinator: Coordinator,
        unique_id: str,
        name: str,
        features: LawnMowerEntityFeature = LawnMowerEntityFeature(0),
    ) -> None:
        """Initialize the lawn mower."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_supported_features = features
        self._attr_activity = LawnMowerActivity.ERROR

    def _get_activity(self) -> LawnMowerActivity | None:
        """Return the current lawn mower activity."""
        if self.coordinator.data is None:
            return None

        state = str(self.coordinator.data["state"])
        activity = str(self.coordinator.data["activity"])

        _LOGGER.debug("mower state = " + state)
        _LOGGER.debug("mower activity = " + activity)

        state = state[state.find('.')+1:].lower()
        activity = activity[activity.find('.')+1:].lower()

        _LOGGER.debug("mower (fixed) state = " + state)
        _LOGGER.debug("mower (fixed) activity = " + activity)

        if state is None:
            return None

        if activity is None:
            return None

        if state == "paused":
            return LawnMowerActivity.PAUSED
        if state in ("stopped", "off", "waitForSafetyPin"):
            # This is actually stopped, but that isn't an option
            return LawnMowerActivity.ERROR
        if state in (
            "restricted",
            "inOperation",
            "in_operation",
            "unknown",
            "checkSafety",
            "pendingStart",
        ):
            if activity in ("charging", "parked", "none"):
                return LawnMowerActivity.DOCKED
            if activity in ("goingOut", "mowing", "goingHome", "going_home"):
                return LawnMowerActivity.MOWING
        return LawnMowerActivity.ERROR

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("AutomowerLawnMower: _handle_coordinator_update")

        self._attr_activity = self._get_activity()
        self._attr_available = self._attr_activity is not None
        self.async_write_ha_state()

    async def async_start_mowing(self) -> None:
        """Start mowing."""
        _LOGGER.debug("Starting mower")

        if not self.coordinator.mower.is_connected():
            device = bluetooth.async_ble_device_from_address(
                self.coordinator.hass, self.coordinator.address, connectable=True
            )
            if not await self.coordinator.mower.connect(device):
                return

        await self.coordinator.mower.mower_resume()
        if self._attr_activity == LawnMowerActivity.DOCKED:
            await self.coordinator.mower.mower_override()
        await self.coordinator.async_request_refresh()

        self._attr_activity = self._get_activity()
        self.async_write_ha_state()

    async def async_dock(self) -> None:
        """Start docking."""
        _LOGGER.debug("Start docking")

        if not self.coordinator.mower.is_connected():
            device = bluetooth.async_ble_device_from_address(
                self.coordinator.hass, self.coordinator.address, connectable=True
            )
            if not await self.coordinator.mower.connect(device):
                return

        await self.coordinator.mower.mower_park()
        await self.coordinator.async_request_refresh()

        self._attr_activity = self._get_activity()
        self.async_write_ha_state()

    async def async_pause(self) -> None:
        """Pause mower."""
        _LOGGER.debug("Pausing mower")

        if not self.coordinator.mower.is_connected():
            device = bluetooth.async_ble_device_from_address(
                self.coordinator.hass, self.coordinator.address, connectable=True
            )
            if not await self.coordinator.mower.connect(device):
                return

        await self.coordinator.mower.mower_pause()
        await self.coordinator.async_request_refresh()

        self._attr_activity = self._get_activity()
        self.async_write_ha_state()


class BatterySensor(HusqvarnaAutomowerBleEntity, SensorEntity):
    """Husqvarna Automower Battery Status."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: Coordinator,
        unique_id: str,
        name: str,
    ) -> None:
        """Initialize the lawn mower."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("BatterySensor: _handle_coordinator_update")

        self._attr_native_value = int(self.coordinator.data["battery_level"])
        self._attr_available = self._attr_native_value is not None
        self.async_write_ha_state()

class MowerNextStart(HusqvarnaAutomowerBleEntity, SensorEntity):
    """Husqvarna Automower Next Start Time"""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_native_unit_of_measurement = None

    def __init__(
        self,
        coordinator: Coordinator,
        unique_id: str,
        name: str,
    ) -> None:
        """Initialize the lawn mower."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("MowerNextStart: _handle_coordinator_update")

        self.retrieve_value = str(self.coordinator.data["next_start_time"])
        if self.retrieve_value:
            self._attr_native_value = datetime.strptime(self.retrieve_value, '%Y-%m-%d %H:%M:%S%z')
        self._attr_available = self._attr_native_value is not None
        self.async_write_ha_state()

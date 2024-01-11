"""Tests for the Husqvarna Automower Bluetooth integration."""

from unittest.mock import patch

from homeassistant.const import CONF_ADDRESS, CONF_CLIENT_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.service_info.bluetooth import BluetoothServiceInfo

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info

AUTOMOWER_SERVICE_INFO = BluetoothServiceInfo(
    name="305",
    address="00000000-0000-0000-0000-000000000001",
    rssi=-63,
    service_data={},
    manufacturer_data={1062: b"\x05\x04\xbf\xcf\xbb\r"},
    service_uuids=["98bd0001-0b0e-421a-84e5-ddbf75dc6de4"],
    source="local",
)

AUTOMOWER_UNNAMED_SERVICE_INFO = BluetoothServiceInfo(
    name=None,
    address="00000000-0000-0000-0000-000000000002",
    rssi=-63,
    service_data={},
    manufacturer_data={1062: b"\x05\x04\xbf\xcf\xbb\r"},
    service_uuids=["98bd0001-0b0e-421a-84e5-ddbf75dc6de4"],
    source="local",
)

AUTOMOWER_MISSING_SERVICE_SERVICE_INFO = BluetoothServiceInfo(
    name="Missing Service Info",
    address="00000000-0000-0000-0001-000000000000",
    rssi=-63,
    service_data={},
    manufacturer_data={1062: b"\x05\x04\xbf\xcf\xbb\r"},
    service_uuids=[],
    source="local",
)

AUTOMOWER_MISSING_MANUFACTURER_DATA_SERVICE_INFO = BluetoothServiceInfo(
    name="Missing Manufacturer Data",
    address="00000000-0000-0000-0001-000000000001",
    rssi=-63,
    service_data={},
    manufacturer_data={},
    service_uuids=["98bd0001-0b0e-421a-84e5-ddbf75dc6de4"],
    source="local",
)

AUTOMOWER_UNSUPPORTED_GROUP_SERVICE_INFO = BluetoothServiceInfo(
    name="Unsupported Group",
    address="00000000-0000-0000-0001-000000000002",
    rssi=-63,
    service_data={},
    manufacturer_data={1062: b"\x05\x04\xbf\xcf\xbb\r"},
    service_uuids=["98bd0001-0b0e-421a-84e5-ddbf75dc6de4"],
    source="local",
)


def create_mock_entry(no_meters=False):
    """Create a mock config entry for a RAVEn device."""
    return MockConfigEntry(
        domain="husqvarna_automower_ble",
        data={
            CONF_ADDRESS: AUTOMOWER_SERVICE_INFO.address,
            CONF_CLIENT_ID: 1197489078,
        },
    )


async def setup_entry(
    hass: HomeAssistant, mock_entry: MockConfigEntry, platforms: list[Platform]
) -> None:
    """Make sure the device is available."""

    inject_bluetooth_service_info(hass, AUTOMOWER_SERVICE_INFO)

    entry = create_mock_entry()

    with patch("homeassistant.components.husqvarna_automower_ble.PLATFORMS", platforms):
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

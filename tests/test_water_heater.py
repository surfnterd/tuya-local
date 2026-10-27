"""Tests for the water heater entity."""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.water_heater import WaterHeaterEntity
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tuya_local.const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL_VERSION,
    CONF_TYPE,
    DOMAIN,
)
from custom_components.tuya_local.helpers.device_config import get_config
from custom_components.tuya_local.water_heater import (
    TuyaLocalWaterHeater,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_init_entry(hass):
    """Test the initialisation."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "geyserwise_water_heater",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device

    await async_setup_entry(hass, entry, m_add_entities)
    assert type(hass.data[DOMAIN]["dummy"]["water_heater"]) is TuyaLocalWaterHeater
    m_add_entities.assert_called_once()


@pytest.mark.asyncio
async def test_init_entry_fails_if_device_has_no_water_heater(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "smartplugv1",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


@pytest.mark.asyncio
async def test_init_entry_fails_if_config_is_missing(hass):
    """Test initialisation when device has no matching entity"""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "non_existing",
            CONF_DEVICE_ID: "dummy",
            CONF_PROTOCOL_VERSION: "auto",
        },
    )
    # although async, the async_add_entities function passed to
    # async_setup_entry is called truly asynchronously. If we use
    # AsyncMock, it expects us to await the result.
    m_add_entities = Mock()
    m_device = AsyncMock()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["dummy"] = {}
    hass.data[DOMAIN]["dummy"]["device"] = m_device
    try:
        await async_setup_entry(hass, entry, m_add_entities)
        assert False
    except ValueError:
        pass
    m_add_entities.assert_not_called()


def _kettle(mocker, dps):
    """A water heater whose temperature range depends on a unit dp."""
    device = mocker.MagicMock()
    device.get_property.side_effect = lambda dp_id: dps.get(dp_id)
    cfg = get_config("weeket_kes5211tece_kettle")
    ecfg = next(e for e in cfg.all_entities() if e.entity == "water_heater")
    return TuyaLocalWaterHeater(device, ecfg)


def test_temp_range_falls_back_while_unit_unknown(mocker):
    """Before the unit dp is reported (offline, startup) there is no range."""
    subject = _kettle(mocker, {})
    assert subject.min_temp == WaterHeaterEntity.min_temp.fget(subject)
    assert subject.max_temp == WaterHeaterEntity.max_temp.fget(subject)


def test_temp_range_follows_unit(mocker):
    subject = _kettle(mocker, {"6": "c"})
    assert subject.min_temp == 70
    assert subject.max_temp == 100

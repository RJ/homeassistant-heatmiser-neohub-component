"""Platform for Heatmiser Neohub"""
import asyncio
from datetime import timedelta
import logging

from aiohttp import ClientConnectionError
from async_timeout import timeout
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, NEOHUB_PORT
from .util import get_mac_from_host

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_HOSTS
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import Throttle

from homeassistant.helpers import device_registry as dr

import ipaddress
from . import config_flow  # noqa  pylint_disable=unused-import

_LOGGER = logging.getLogger(__name__)

COMPONENT_TYPES = ['climate']  #, 'switch']  #, 'sensor', 'switch']

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(
            #CONF_HOST
            CONF_HOST, default="10.0.0.125"
        ): vol.All(ipaddress.ip_address, cv.string)
    })
}, extra=vol.ALLOW_EXTRA)



async def async_setup(hass, config):
    """Set up neohub config"""
    if DOMAIN not in config:
        return True

    host = config[DOMAIN].get(CONF_HOST)

    if not host:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={'source': SOURCE_IMPORT}))

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={'source': SOURCE_IMPORT},
            data={
                CONF_HOST: host,
            }))

    return True



async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    """Establish connection with Neohub"""
    conf = entry.data
    hub = await neohub_api_setup(hass, conf[CONF_HOST])

    hass.data.setdefault(DOMAIN, {}).update({entry.entry_id: hub})

    # determining mac address is only possible on local subnet
    # not if running in a non-bridged docker container, for example.
    mac = get_mac_from_host(conf[CONF_HOST])
    _LOGGER.info("neohub host: %s mac: %s" % (conf[CONF_HOST], mac))
    if mac is None:
        conns = {('hub_ip', conf[CONF_HOST])}
        idents = {(DOMAIN, conf[CONF_HOST])}
    else:
        conns = {(CONNECTION_NETWORK_MAC, mac)}
        idents = {(DOMAIN, mac)}

    _LOGGER.info("Adding neohub to device registry, entry_id: %s" % entry.entry_id)
    # add to device registry
    dev_reg = await dr.async_get_registry(hass)
    dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            connections=conns,
            identifiers=idents,
            manufacturer='Heatmiser',
            name='NeoHub',
            model=hub.dcb.get('DEVICE_ID'),
            sw_version=hub.dcb.get('Firmware version'),
    )

    # set up devices for: climate. switch, sensor?
    for component in COMPONENT_TYPES:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                entry, component))
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await asyncio.wait([
        hass.config_entries.async_forward_entry_unload(config_entry, component)
        for component in COMPONENT_TYPES
    ])
    hass.data[DOMAIN].pop(config_entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


async def neohub_api_setup(hass, host):
    # TODO if hub unreachable, error nicely
    _LOGGER.info("neohub_api_setup for %s" % host)
    from .neohub import NeoHub
    hub = NeoHub(host, NEOHUB_PORT)
    await hub.async_setup()
    _LOGGER.info("neohub async_setup completed")
    return hub


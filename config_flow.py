"""Config flow for the Neohub platform."""
import asyncio
import logging

from aiohttp import ClientError
from async_timeout import timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST

from .const import KEY_IP, KEY_MAC, DOMAIN, NEOHUB_PORT
from .util import get_mac_from_host

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def _create_entry(self, host):
        """Register new entry."""
        # determining mac address is only possible on local subnet
        # not if running in a non-bridged docker container, for example.
        mac = get_mac_from_host(host)
        if mac is not None:
            data_key = 'hub_ip'
            data_val = host
        else:
            data_key = KEY_MAC
            data_val = mac
        # Check if mac already is registered
        for entry in self._async_current_entries():
            if entry.data[data_key] == data_val:
                return self.async_abort(reason='already_configured')

        return self.async_create_entry(
            title=host,
            data={
                CONF_HOST: host,
                data_key: data_val
            })

    async def _create_device(self, host):
        """Create device."""
        from .neohub import NeoHub
        hub = NeoHub(host, NEOHUB_PORT)
        await hub.async_setup()

        return await self._create_entry(host)

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self.async_show_form(
                step_id='user',
                data_schema=vol.Schema({
                    vol.Required(CONF_HOST): str
                })
            )
        return await self._create_device(user_input[CONF_HOST])

    async def async_step_import(self, user_input):
        """Import a config entry."""
        host = user_input.get(CONF_HOST)
        if not host:
            return await self.async_step_user()
        return await self._create_device(host)

    async def async_step_discovery(self, user_input):
        """Initialize step from discovery - deprecated?"""
        _LOGGER.info("Discovered device: %s", user_input)
        return await self._create_entry(user_input[KEY_IP], user_input[KEY_MAC])

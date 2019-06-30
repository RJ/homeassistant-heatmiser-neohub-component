"""Support for neohub thermostat devices"""
import re
import logging
import asyncio
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateDevice
from homeassistant.components.climate.const import (
        STATE_IDLE, STATE_HEAT, SUPPORT_ON_OFF,
        SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE_LOW
    )
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT, STATE_ON, STATE_OFF, ATTR_TEMPERATURE,
    TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE, CONF_PORT, CONF_HOST
    )

from .const import DOMAIN

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_LOW |
                 SUPPORT_ON_OFF)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string
})


async def async_setup_platform(hass, config, async_add_entities, disco=None):
    """Old way of setting up the platform.
    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """
    pass


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up neohub climate device based on config_entry."""
    _LOGGER.info("async_setup_entry, asking neohub for stats. entry: %s" % repr(entry))
    hub = hass.data[DOMAIN].get(entry.entry_id)
    stats = hub.neostats()
    _LOGGER.info("neohub lists %s NeoStats" % (len(stats)))
    neostats = [NeoStatDevice(stats[name]) for name in stats]
    async_add_entities(neostats)


class NeoStatDevice(ClimateDevice):
    def __init__(self, n):
        self._neo = n
        self._temp_unit = TEMP_FAHRENHEIT
        if n.hub.corf() == "C":
            self._temp_unit = TEMP_CELSIUS

    @property
    def device_info(self):
        """Return a device description for device registry."""
        _LOGGER.info("device info called on neohub NeoStatDevice")
        return {
            'name': self.name,
            'identifiers':{(DOMAIN, self.unique_id)},
           # 'connections': {('hub_ip', self._neo.hub.host)},
            'manufacturer': 'Heatmiser',
            'via_device': (DOMAIN, self._neo.hub.host),
        }

    @property
    def unique_id(self):
        """Form unique ID by adding name to neohub ip"""
        return "NeoStat %s" % (self.name)
    
    @property
    def is_on(self):
        """We co-opt frost mode as on/off, see README"""
        return not self.is_away_mode_on

    async def async_turn_off(self):
        return await self.async_turn_away_mode_on()

    async def async_turn_on(self):
        return await self.async_turn_away_mode_off()

    @property
    def should_poll(self):
        return True

    @property
    def name(self):
        return self._neo.name

    @property
    def current_operation(self):
        """ Returns current operation"""
        if self._neo.currently_heating():
            return STATE_HEAT
        else:
            return STATE_IDLE

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return [STATE_ON, STATE_OFF]

    @property
    def temperature_unit(self):
        """ Returns the unit of measurement. """
        return self._temp_unit

    @property
    def current_temperature(self):
        """ Returns the current temperature. """
        return self._neo.current_temperature()

    @property
    def target_temperature(self):
        """ Returns the temperature we try to reach. """
        return self._neo.set_temperature()

    @property
    def min_temp(self):
        return self._neo.frost_temperature()

    @property
    def is_away_mode_on(self):
        """ Returns if away mode is on. """
        return self._neo.is_frosted()

    def update_after(self, secs):
        async def wait_and_update():
            await asyncio.sleep(secs)
            _LOGGER.info("updating after delay of %s" % (secs))
            await self.async_update()
            #self.async_schedule_update_ha_state()

        asyncio.ensure_future(wait_and_update())

    async def async_set_temperature(self, **kwargs):
        """ Set new target temperature. """
        new_temp = int(kwargs.get(ATTR_TEMPERATURE))
        await self._neo.set_set_temperature(new_temp)
        self.update_after(1.5)

    async def async_turn_away_mode_on(self):
        """ Turns away mode on. """
        await self._neo.set_frost_on()
        self.update_after(1.5)

    async def async_turn_away_mode_off(self):
        """ Turns away mode off. """
        await self._neo.set_frost_off()
        self.update_after(1.5)

    async def async_update(self):
        await self._neo.update()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

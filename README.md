# Heatmiser Neohub for Home Assistant

This works in the `custom_components` dir for now.
I'm using a hack to monkey patch hass to support config flows from custom components.
However this has been disabled recently. Considering submitting upstream.


## Usage

Give your neohub a static IP or fixed DHCP lease on your router!
There isn't a reliable way to uniquely identify the hub otherwise.


* Clone into hass configdir/custom\_components/heatmiser\_neohub
* Add to `configuration.yaml`
```yaml
heatmiser_neohub:
    host: 192.168.0.123
```
* Restart hass


## Handling the Neohub/Hass Impedance Mismatch 

I set my neohub to not have any timed or scheduled programs.
I do all schedules and programming via home assistant.

My neohub component simplifies the thermostat in hass by supporting a target
temperature, and on/off mode.

When the climate device is "off" in hass, it enables frost mode on the neostat.
Turning the device "on" simply disables frost mode, so the neostat will maintain
the target temperature.

### TODO - update neohub pypy module

I'm bundling neohub module in this repo for now. Need to polish and submit
to pypy to comply with hass guidelines.

### TODO - Minimum temp

Neostats support a minimum frost temp, so even when frosted (aka "off"), they
will not allow the temperature to drop below this point.

* `SUPPORT_TARGET_TEMPERATURE_LOW` The device supports a lower bound target temperature.

I'm not sure how this works in the UI. Could add it as a service?


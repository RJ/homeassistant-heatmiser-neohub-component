import ipaddress
from getmac import get_mac_address


def get_mac_from_host(host):
    """Tries to get mac from host, only works on local subnet ofc.."""
    # so yeah, not going to work if you are running in a docker container
    # without bridged networking.
    try:
        if ipaddress.ip_address(host).version == 6:
            mode = 'ip6'
        else:
            mode = 'ip'
    except ValueError:
        mode = 'hostname'
    return get_mac_address(**{mode: host})

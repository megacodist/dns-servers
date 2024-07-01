#
# 
#
"""This module offers network APIs for this application and contains:

#### Types
1. `NetInt`

#### Functions
1. `enumNetInts`
"""

from ipaddress import IPv4Address, IPv6Address
from typing import Any


class NetInt:
    def __init__(
            self,
            net_conn_id: str,
            description: str,
            dhcp_enabled: bool,
            dns_order: tuple[IPv4Address | IPv6Address, ...] | None,
            default_gateway: tuple[str, ...] | None,
            ) -> None:
        self.NetConnectionID = net_conn_id
        """The name of the network interface in the shell."""
        self.Description = description
        self.DHCPEnabled = dhcp_enabled
        self.DNSServerSearchOrder = dns_order
        self.DefaultIPGateway = default_gateway
    
    def __repr__(self) -> str:
        return (f"<{self.__class__.__qualname__} "
            f"NetConnectionID={self.NetConnectionID} "
            f"Description={self.Description} "
            f"DHCPEnabled={self.DHCPEnabled} "
            f"DNSServerSearchOrder={self.DNSServerSearchOrder} "
            f"DefaultIPGateway={self.DefaultIPGateway}>")


def enumNetInts() -> list[NetInt]:
    """Enumerates network interfaces on this Windows platform."""
    import win32com.client
    wmi = win32com.client.GetObject("winmgmts:")
    # Querying network adapter configurations...
    configQuery = """
        SELECT
            Index, InterfaceIndex, MACAddress, SettingID, Description,
            DHCPEnabled, DNSServerSearchOrder, DefaultIPGateway
        FROM
            Win32_NetworkAdapterConfiguration"""
    results = wmi.ExecQuery(configQuery)
    configs: dict[str, Any] = {
        item.Description: item
        for item in results}
    # Querying network adapters...
    adaptersQuery = """
        SELECT
            Index, InterfaceIndex, MACAddress, GUID, Description,
            NetConnectionID, NetEnabled
        FROM
            Win32_NetworkAdapter
        WHERE
            PhysicalAdapter=True"""
    adapters = wmi.ExecQuery(adaptersQuery)
    # Merging results...
    netInts = list[NetInt]()
    for adap in adapters:
    return [
        NetInt(
            adap.NetConnectionID,
            adap.Name,
            configs[adap.Name].DHCPEnabled,
            _toIpList(configs[adap.Name].DNSServerSearchOrder),
            _toIpList(onfigs[adap.Name].DefaultIPGateway))
        for adap in adapters
        if adap.Name in configs]


def _toIpList(
        ips: tuple[str, ...] | None,
        ) -> tuple[IPv4Address | IPv6Address, ...] | None:
    """Converts a tuple of strings representing IP addresses to
    `IPv4Address` or `IPv6Address`. It raises `TypeError` if not possible.
    """
    from ipaddress import AddressValueError
    if ips is None:
        return None
    res = list[IPv4Address | IPv6Address]()
    for ip in ips:
        try:
            res.append(IPv4Address(ip))
            continue
        except AddressValueError:
            pass
        try:
            res.append(IPv6Address(ip))
            continue
        except AddressValueError:
            pass
        raise TypeError(f'expected IPv4 or IPv6 but got {ip}')
    return tuple(res)

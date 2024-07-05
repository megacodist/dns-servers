#
# 
#
"""This module offers network APIs for this application and contains:

#### Types
1. `NetInt`

#### Functions
1. `enumNetInts`
"""

from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import logging
import re
from typing import Any
from uuid import UUID


class MAC:
    """This class encapsulate MAC addresses."""
    _MAC_REGEX = '^[0-9A-F]{2}(?:[:][0-9A-F]{2}){5}$'

    _macPat = re.compile(_MAC_REGEX)

    def __init__(self, mac_addr: str):
        """
        Initializes a MAC object.

        :param mac_addr: a string representing the MAC address in the format XX:XX:XX:XX:XX:XX
        """
        self._macAddr = self._validate(mac_addr)
        """The MAC address string."""

    def _validate(self, mac_addr: str) -> str:
        """Validates the MAC address string. If it is valid, it normalizes it
        and returns it; otherwise raises `ValueError` exception.

        :param `mac_addr`: a string representing the MAC address
        :return: the validated MAC address string
        :raises `ValueError`: if the MAC address format is invalid
        """
        mac_addr = mac_addr.strip().replace('-', ':').replace('.', ':').upper()
        mtch = self._macPat.match(mac_addr)
        if mtch is None:
            raise ValueError(f'{mac_addr} is not a valid MAC address')
        return mac_addr

    def __str__(self):
        """Returns a string representation of the MAC address.

        :return: a string in the format XX:XX:XX:XX:XX:XX
        """
        return self._macAddr
    
    def __repr__(self):
        return f"<{self.__class__.__qualname__}('{self._macAddr}')>"

    def __eq__(self, other: object) -> bool:
        """Compares two MAC objects for equality.

        :param other: another MAC object
        :return: `True` if the MAC addresses are equal, `False` otherwise.
        """
        if not isinstance(other, MAC):
            return NotImplemented
        return self._macAddr == other._macAddr

    def __hash__(self) -> int:
        """Returns a hash value for the MAC object.

        :return: an integer hash value
        """
        return hash(self._macAddr)

    @property
    def OUI(self):
        """Returns the Organizationally Unique Identifier (OUI) part of
        the MAC address.

        :return: a string representing the OUI (first 3 bytes of the MAC
        address)
        """
        return self._macAddr[:8]

    @property
    def NIC(self):
        """
        Return the Network Interface Controller (NIC) part of the MAC
        address.

        :return: a string representing the NIC (last 3 bytes of the MAC
        address)
        """
        return self._macAddr[9:]
    
    def isUnicast(self) -> bool:
        """Checks if the MAC address is a unicast address"""
        first_octet = int(self._macAddr[0:2], 16)
        return (first_octet & 0x01) == 0

    def isMulticast(self) -> bool:
        """Checks if the MAC address is a multicast address"""
        first_octet = int(self._macAddr[0:2], 16)
        return (first_octet & 0x01) == 1

    def isBroadcast(self):
        """Checks if the MAC address is a broadcast address"""
        return self._macAddr == "FF:FF:FF:FF:FF:FF"


class NetInt:
    def __init__(
            self,
            index: int,
            interface_idx: int,
            net_conn_id: str,
            description: str,
            ip_enabled: bool,
            dhcp_enabled: bool,
            ip_addr: tuple[IPv4 | IPv6, ...] | None,
            dns_order: tuple[IPv4 | IPv6, ...] | None,
            default_gateway: tuple[IPv4 | IPv6, ...] | None,
            guid: UUID,
            mac_addr: MAC | None,
            ) -> None:
        self.NetConnectionID = net_conn_id
        """The name of the network interface in the shell."""
        self.Description = description
        self.DHCPEnabled = dhcp_enabled
        self.DNSServerSearchOrder = dns_order
        self.DefaultIPGateway = default_gateway
        self.Index = index
        self.InterfaceIndex = interface_idx
        self.MACAddress = mac_addr
        self.GUID = guid
        self.IPEnabled = ip_enabled
        self.IPAddress = ip_addr
    
    def __repr__(self) -> str:
        return (f"<{self.__class__.__qualname__} "
            f"Index={self.Index} "
            f"InterfaceIndex={self.InterfaceIndex} "
            f"NetConnectionID={self.NetConnectionID} "
            f"Description={self.Description} "
            f"MACAddress={self.MACAddress} "
            f"GUID={self.GUID} "
            f"DHCPEnabled={self.DHCPEnabled} "
            f"DNSServerSearchOrder={self.DNSServerSearchOrder} "
            f"DefaultIPGateway={self.DefaultIPGateway}>")
    
    def connectivity(self) -> bool:
        """Specifies whether this network interface has the potential
        interner connectivity.
        """
        return self.IPEnabled and bool(self.IPAddress) and \
            bool(self.MACAddress) and bool(self.DefaultIPGateway) and (
            self.DHCPEnabled or bool(self.DNSServerSearchOrder))
    
    def dhcpEnabled(self) -> bool:
        """Specifies whether DHCP is enabled for this network interface
        or not.
        """
        return self.DHCPEnabled


def enumNetInts() -> list[NetInt]:
    """Enumerates network interfaces on this Windows platform."""
    from uuid import UUID
    import pythoncom
    import win32com.client
    from win32com.client import CDispatch
    #
    pythoncom.CoInitialize()
    wmi = win32com.client.GetObject("winmgmts:")
    # Querying network adapter configurations...
    configQuery = """
        SELECT
            Index, InterfaceIndex, MACAddress, SettingID, Description,
            DHCPEnabled, DNSServerSearchOrder, DefaultIPGateway, IPEnabled,
            IPAddress
        FROM
            Win32_NetworkAdapterConfiguration"""
    configs = wmi.ExecQuery(configQuery)
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
    results = list[NetInt]()
    # Firstly, combining using GUID (SettingID)....
    mpConfigs = dict[UUID, CDispatch]()
    missCfgs = list[CDispatch]()
    for cfg in configs:
        try:
            mpConfigs[UUID(cfg.SettingID)] = cfg
        except Exception:
            missCfgs.append(cfg)
    mpAdapters = dict[UUID, CDispatch]()
    missAdaps = list[CDispatch]()
    for adap in adapters:
        try:
            mpAdapters[UUID(adap.GUID)] = adap
        except Exception:
            missAdaps.append(adap)
    cmnKeys = set(mpConfigs.keys()).intersection(mpAdapters.keys())
    for key in cmnKeys:
        try:
            ipAddr = _toIpList(mpConfigs[key].IPAddress)
        except TypeError:
            logging.error('Invalid IP Address in '
                f'{mpConfigs[key].SettingID} adapter configuration')
            continue
        try:
            dnses = _toIpList(mpConfigs[key].DNSServerSearchOrder)
        except TypeError:
            logging.error('Invalid DNS server search order in '
                f'{mpConfigs[key].SettingID} adapter configuration')
            continue
        try:
            gateway = _toIpList(mpConfigs[key].DefaultIPGateway)
        except TypeError:
            logging.error('Invalid default IP Gateway in '
                f'{mpConfigs[key].SettingID} adapter configuration')
            continue
        try:
            mac = mpConfigs[key].MACAddress
            if mac is not None:
                mac = MAC(mac)
        except TypeError:
            logging.error('Invalid MAC address in '
                f'{mpConfigs[key].SettingID} adapter configuration')
            continue
        results.append(NetInt(
            mpConfigs[key].Index,
            mpConfigs[key].InterfaceIndex,
            mpAdapters[key].NetConnectionID,
            mpConfigs[key].Description,
            mpConfigs[key].IPEnabled,
            mpConfigs[key].DHCPEnabled,
            ipAddr,
            dnses,
            gateway,
            key,
            mac))
        obj = mpConfigs[key]
        del obj
        obj = mpAdapters[key]
        del obj
        del mpConfigs[key]
        del mpAdapters[key]
    #
    pythoncom.CoUninitialize()
    return results


def _toIpList(
        ips: tuple[str, ...] | None,
        ) -> tuple[IPv4 | IPv6, ...] | None:
    """Converts a tuple of strings representing IP addresses to
    `IPv4Address` or `IPv6Address`. It raises `TypeError` if not possible.
    """
    from ipaddress import AddressValueError
    if ips is None:
        return None
    res = list[IPv4 | IPv6]()
    for ip in ips:
        try:
            res.append(IPv4(ip))
            continue
        except AddressValueError:
            pass
        try:
            res.append(IPv6(ip))
            continue
        except AddressValueError:
            pass
        raise TypeError(f'expected IPv4 or IPv6 but got {ip}')
    return tuple(res)

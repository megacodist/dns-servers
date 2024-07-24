#
# 
#
"""This module offers network APIs for this application and contains:

#### Types
1. `NetInt`

#### Functions
1. `enumNetInts`
"""

from __future__ import annotations
import enum
from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import logging
import re
from typing import Iterable
from uuid import UUID


class NetConfigCode(enum.IntEnum):
    SUCCESSFUL = 0
    """Successful completion"""
    SUCCESSFUL_REBOOT = 1
    """Successful completion, but a reboot is required"""
    NOT_SUPPORTED = 64
    """Method not supported on this platform"""
    ERR_UNKNOWN = 65
    """Unknown failure"""
    BAD_SUBNET_MASK = 66
    """Invalid subnet mask"""
    ERR_PROCESSING_IP = 67
    """An error occurred while processing an IP address"""
    BAD_IP = 68
    """Invalid IP address"""
    BAD_GATEWAY_IP = 69
    """Invalid gateway IP address"""
    BAD_DOMAIN_NAME = 70
    """Invalid domain name"""
    BAD_HOST_NAME = 71
    """Invalid host name"""
    NO_PRIM_SECON_WINS = 72
    """No primary or secondary WINS server defined"""
    BAD_FILE = 73
    """Invalid file"""
    BAD_SYSTEM_PATH = 74
    """Invalid system path"""
    ERR_COPYING_FILE = 75
    """File copy failed"""
    BAD_SECURITY_PARAM = 76
    """Invalid security parameter"""
    ERR_CONFIG_TCPIP = 77
    """Unable to configure TCP/IP service"""
    ERR_CONFIG_DHCP = 78
    """Unable to configure DHCP service"""
    ERR_RENEW_DHCP_LEASE = 79
    """Unable to renew DHCP lease"""
    ERR_RELEASE_DHCP_LEASE = 80
    """Unable to release DHCP lease"""
    IP_NOT_ENABLED = 81
    """IP not enabled on adapter"""
    IPX_NOT_ENABLED = 82
    """IPX not enabled on adapter"""
    ERR_FRAME_NET_NUM_BOUNDS = 83
    """Frame or network number bounds error"""
    BAD_FRAME_TYPE = 84
    """Invalid frame type"""
    BAD_NET_NUM = 85
    """Invalid network number"""
    DUP_NET_NUM = 86
    """Duplicate network number"""
    PARAM_OUT_OF_BOUNDS = 87
    """Parameter out of bounds"""
    ACCESS_DENIED = 88
    """Access denied"""
    OUT_OF_MEMORY = 89
    """Out of memory"""
    ALREADY_EXISTS = 90
    """Already exists"""
    PATH_FILE_OBJECT_NOT_FOUND = 91
    """Path, file, or object not found"""
    UNSUPPORTED_CONFIGU = 92
    """Unsupported configuration"""
    BAD_PARAM = 93
    """Invalid parameter"""
    MORE_5_GATEWAYS = 94
    """More than five gateways specified"""
    NON_STATIC_IP = 95
    """Non-static IP addresses detected"""
    DHCP_NOT_ENABLED = 96
    """DHCP not enabled on the adapter"""
    OTHER = 97


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
    """Encapsulates a network interface on Microsot Windows. This class
    current supports IP-based network communication.
    """

    @ classmethod
    def enumAllNetInts(cls) -> list[NetInt]:
        """Enumerates all network interfaces on this Windows platform."""
        return _enumNetInts()

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
            dhcp_server: IPv4 | IPv6 | None
            ) -> None:
        self.NetConnectionID = net_conn_id
        """The name of this network interface in the shell."""
        self.Description = description
        self.DHCPEnabled = dhcp_enabled
        """Whether this network interface is configured to obtain obtain
        its network configuration settings, such as IP address, subnet mask,
        default gateway, and DNS server addresses; automatically through DHCP.
        """
        self.DHCPServer = dhcp_server
        """Specifies the IP address of the DHCP server that will provide the
        necessary network configurations."""
        self.DNSServerSearchOrder = dns_order
        self.DefaultIPGateway = default_gateway
        self.Index = index
        self.InterfaceIndex = interface_idx
        self.MACAddress = mac_addr
        self.GUID = guid
        self.IPEnabled = ip_enabled
        """Specifies whether this network interface can use IP protocol for
        its network communicatiopns.
        """
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
        # Checking whether this network interface uses IP-based
        # communication...
        if self.IPEnabled:
            return bool(self.IPAddress) and bool(self.MACAddress) and \
                bool(self.DefaultIPGateway) and (self.dnsProvided() or
                self.dhcpAccess())
        else:
            return False
    
    def dnsProvided(self) -> bool:
        """Specifies whether this network interface is provided with DNS
        servers or not.
        """
        return bool(self.DNSServerSearchOrder)
    
    def dhcpAccess(self) -> bool:
        """Specifies whether this network interface has access to DHCP
        server.
        """
        return self.DHCPEnabled and bool(self.DHCPServer)
    
    def setDnsSearchOrder(self, ips: Iterable[IPv4 | IPv6]) -> NetConfigCode:
        import pythoncom
        import win32com.client
        #
        pythoncom.CoInitialize()
        wmi = win32com.client.GetObject("winmgmts:")
        configQuery = f"""
            SELECT
                *
            FROM
                Win32_NetworkAdapterConfiguration
            WHERE
                Index = {self.Index}
                AND InterfaceIndex = {self.InterfaceIndex}
                AND MACAddress = '{self.MACAddress}'
                AND SettingID = '{self.GUID}'
                AND Description = '{self.Description}'"""
        print(configQuery)
        configs = wmi.ExecQuery(configQuery)
        print(len(configs))
        if len(configs) != 1:
            print(NetConfigCode.ERR_UNKNOWN)
            code = NetConfigCode.ERR_UNKNOWN
        else:
            code = configs[0].SetDNSServerSearchOrder(ips)
        #
        pythoncom.CoUninitialize()
        return code


def _enumNetInts() -> list[NetInt]:
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
            IPAddress, DHCPServer
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
        try:
            dhcpServer = _strToIp(mpConfigs[key].DHCPServer)
        except TypeError:
            logging.error('Invalid DHCP server in '
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
            mac,
            dhcpServer))
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
        raise TypeError(
            f'expected IPv4 or IPv6 but got {ip.__class__.__qualname__}')
    return tuple(res)


def _strToIp(ip: str | None) -> IPv4 | IPv6 | None:
    from ipaddress import AddressValueError
    if ip is None:
        return None
    try:
        return IPv4(ip)
    except AddressValueError:
        pass
    try:
        return IPv6(ip)
    except AddressValueError:
        raise TypeError(
            f'expected IPv4 or IPv6 but got {ip.__class__.__qualname__}')

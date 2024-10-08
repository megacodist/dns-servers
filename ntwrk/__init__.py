#
# 
#
"""This module offers network APIs for this application and contains:

#### Types
1. `NetAdap`

#### Functions
1. `enumNetInts`
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import enum
from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import logging
from os import PathLike
import re
from typing import Any, Iterable, Iterator, TypeVar, overload
from uuid import UUID


class ACIdx:
    """This class specifies the index of a `NetAdap` or `NetConfig` object
    in a `AdapCfgBag` container. The `adapIdx` must always be an integer
    but the `cfgIdx` can be `int` or `None`:
    * `cfgIdx is None`: the index is called to be an adapter index
    * `cfgIdx: int`: the index is called to be a config index
    """

    def __init__(self, a_idx: int, c_idx: int | None,) -> None:
        self.adapIdx = a_idx
        self.cfgIdx = c_idx
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ACIdx):
            return NotImplemented
        if self.adapIdx != value.adapIdx:
            return False
        try:
            return self.cfgIdx == value.cfgIdx
        except Exception:
            return False
    
    def __hash__(self) -> int:
        return hash(self.toTuple())
    
    def __repr__(self) -> str:
        return (f'<{self.__class__.__qualname__}(adapIdx={self.adapIdx}, '
            f'cfgIdx={self.cfgIdx})>')
    
    def nextIdx(self) -> ACIdx:
        """Returns next index in a `Sequence[NetAdap]`."""
        aIdx = self.adapIdx
        cIdx = 0 if self.cfgIdx is None else self.cfgIdx + 1
        return ACIdx(aIdx, cIdx)
    
    def isAdap(self) -> bool:
        """Specifies whether this index is an adapter index or not."""
        return self.cfgIdx is None
    
    def isConfig(self) -> bool:
        """Specifies whether this index is a config index or not."""
        return self.cfgIdx is not None
    
    def isConfigOf(self, other: ACIdx) -> bool:
        """Specifies whether this index is a config index of the provided
        index.
        """
        if self.adapIdx != other.adapIdx:
            return False
        return (self.cfgIdx is not None) and (other.cfgIdx is None)
    
    def isAdapOf(self, other: ACIdx) -> bool:
        """Specifies whether this index is a adapter index of the provided
        index.
        """
        if self.adapIdx != other.adapIdx:
            return False
        return (self.cfgIdx is None) and (other.cfgIdx is not None)
    
    def getAdap(self) -> ACIdx:
        """Gets the adapter version of this index. If it is already an
        adapter index, it will returned unchanged.
        """
        return ACIdx(self.adapIdx, None)
    
    def toTuple(self) -> tuple[int, int | None]:
        return (self.adapIdx, self.cfgIdx,)


class AdapCfgBag:
    def __init__(self) -> None:
        self._adaps = dict[int, NetAdap]()
    
    def __getitem__(self, idx: ACIdx) -> NetAdap | NetConfig:
        try:
            adap = self._adaps[idx.adapIdx]
        except KeyError:
            raise IndexError(f'no network adapter with Index={idx.adapIdx}')
        if idx.cfgIdx is None:
            return adap
        try:
            return adap._configs[idx.cfgIdx]
        except KeyError:
            raise IndexError(
                f'no network adapter config with Index={idx.cfgIdx}')
    
    def indexAdap(self, adap: NetAdap) -> ACIdx:
        """Get the index of the provided `NetAdap` in the bag. It raises:
        * `IndexError`: if it has not been found.
        * `ValueError`: it found but with contradictory determinant
        attributes.
        """
        try:
            a = self._adaps[adap.Index]
        except KeyError:
            raise IndexError(f'{adap} not found in the bag')
        if adap.equalIdentityTo(a):
            return ACIdx(adap.Index, None)
        else:
            raise ValueError(
                f'contradictory determinants of {adap} in the bag')
    
    def indexConfig(
            self,
            config: NetConfig,
            ) -> ACIdx:
        """Searches for a specified config in the bag. It raises:
        * `IndexError`: there is no config with the same identity (the
        same determinant attributes).
        * `ValueError`: there is a contradictory peer (the same index
        but not completely equal determinant attributes).
        """
        for adap in self._adaps.values():
            if config.Index in adap._configs:
                if config.equalIdentityTo(adap._configs[config.Index]):
                    return ACIdx(adap.Index, config.Index)
                else:
                    raise ValueError('a contradictory peer found')
        raise IndexError('config does not exist')
    
    def delIdx(self, idx: ACIdx) -> None:
        """Deletes the specified index from the bag. Raises `IndexError`
        if index does not exist.
        """
        try:
            if idx.isAdap():
                del self._adaps[idx.adapIdx]
                return
            else:
                adap = self._adaps[idx.adapIdx]
        except KeyError:
            raise IndexError(f'{idx} does not exist in the bag')
        try:
            del adap._configs[idx.cfgIdx] # type: ignore
        except KeyError:
            raise IndexError(f'{idx} does not exist in the bag')
    
    def addAdap(self, adap: NetAdap) -> None:
        """Adds the provided `NetAdap` object to this bag. Raises
        `ValueError` if an adapter object with the same `Index` alreadt
        exists.
        """
        if adap.Index in self._adaps:
            raise ValueError(
                f'a NetAdap with `Index` of {adap.Index} already exists')
        self._adaps[adap.Index] = adap
    
    def addConfig(self, config: NetConfig) -> None:
        """Adds a config to the bag.
        #### Excepitons:
        * `ValueError`: no corresponding adapter found
        * `IndexError`: a config with the same index already exists in the 
        corresponding adapter.
        """
        for adap in self._adaps.values():
            if adap._Caption == config._Caption:
                if config.Index in adap._configs:
                    raise IndexError(
                        'the config index already exists in the '
                        'corresponding adap')
                else:
                    adap._configs[config.Index] = config
                    return
        raise ValueError(f'unable to add {config} to the bag')
    
    def iterAdaps(self) -> Iterator[tuple[ACIdx, NetAdap]]:
        """Returns an iterator to iterate through all network adapters
        alongside their `ACIdx`.
        """
        return (
            (ACIdx(adap.Index, None,), adap)
            for adap in self._adaps.values())
    
    def iterConfigs(
            self,
            adap_idx: ACIdx,
            ) -> Iterator[tuple[ACIdx, NetConfig]]:
        """Returns an iterator to iterate through all network adapter
        configurations alongside their `ACIdx` for the specified network
        adapter. Raises `IndexError` if the provided index is not an
        adapter index or it does not exist in the bag.
        """
        if adap_idx.cfgIdx is not None:
            raise IndexError(f'{adap_idx} is not an adapter index')
        try:
            adap = self._adaps[adap_idx.adapIdx]
        except KeyError:
            raise IndexError(
                f'the adapter index does not exist in this bag: {adap_idx}')
        return (
            (ACIdx(adap_idx.adapIdx, i), cfg,)
            for i, cfg in adap._configs.items())


class ConnStatus(enum.Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    DISCONNECTING = 3
    HARDWARE_NOT_PRESENT = 4
    HARDWARE_DISABLED = 5
    HARDWARE_MALFUNCTION = 6
    MEDIA_DISCONNECTED = 7
    AUTHENTICATING = 8
    AUTH_SUCCEEDED = 9
    """Authentication succeeded"""
    AUTH_FAILED = 10
    """Authentication failed"""
    INVALID_ADDRESS = 11
    CREDENTIALS_REQUIRED = 12


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
    ERR_OCCURRED_INSTANCE = 67
    """An error occurred while processing an Instance that was returned"""
    BAD_PARAM = 68
    """Invalid input parameter"""
    MORE_5_GATEWAYS = 69
    """More than five gateways specified"""
    BAD_IP = 70
    """Invalid IP address"""
    BAD_GATEWAY_IP = 71
    """Invalid gateway IP address"""
    ERR_OCCURRED_REGISTRY = 72
    """An error occurred while accessing the Registry for the requested information"""
    BAD_DOMAIN_NAME = 73
    """Invalid domain name"""
    BAD_HOST_NAME = 74
    """Invalid host name"""
    NO_PRIM_SECON_WINS = 75
    """No primary or secondary WINS server defined"""
    BAD_FILE = 76
    """Invalid file"""
    BAD_SYSTEM_PATH = 77
    """Invalid system path"""
    ERR_COPYING_FILE = 78
    """File copy failed"""
    BAD_SECURITY_PARAM = 79
    """Invalid security parameter"""
    ERR_CONFIG_TCPIP = 80
    """Unable to configure TCP/IP service"""
    ERR_CONFIG_DHCP = 81
    """Unable to configure DHCP service"""
    ERR_RENEW_DHCP_LEASE = 82
    """Unable to renew DHCP lease"""
    ERR_RELEASE_DHCP_LEASE = 83
    """Unable to release DHCP lease"""
    IP_NOT_ENABLED = 84
    """IP not enabled on adapter"""
    IPX_NOT_ENABLED = 85
    """IPX not enabled on adapter"""
    ERR_FRAME_NET_NUM_BOUNDS = 86
    """Frame/network number bounds error"""
    BAD_FRAME_TYPE = 87
    """Invalid frame type"""
    BAD_NET_NUM = 88
    """Invalid network number"""
    DUP_NET_NUM = 89
    """Duplicate network number"""
    PARAM_OUT_OF_BOUNDS = 90
    """Parameter out of bounds"""
    ACCESS_DENIED = 91
    """Access denied"""
    OUT_OF_MEMORY = 92
    """Out of memory"""
    ALREADY_EXISTS = 93
    """Already exists"""
    PATH_FILE_OBJECT_NOT_FOUND = 94
    """Path, file, or object not found"""
    ERR_NOTIFYING_SERVICE = 95
    """Unable to notify service"""
    ERR_NOTIFYING_DNS = 96
    """Unable to notify DNS service"""
    NON_CONFIG = 97
    """Interface not configurable"""
    ERR_ALL_DHCP_LEASES = 98
    """Not all DHCP leases could be released/renewed"""
    DHCP_NOT_ENABLED = 100
    """DHCP not enabled on the adapter"""
    OTHER = 101


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


_T = TypeVar('_T', bound='AbsNetItem')


class AbsNetItem(ABC):
    @classmethod
    @abstractmethod
    def readAll(cls: type[_T], **kwargs) -> tuple[_T, ...]:
        """Reads all instances from WMI which satisfy the conditions."""
        pass

    def __repr__(self) -> str:
        attrValues = list[str]()
        for attr in self.getDeterminant(leading_under=True):
            value = getattr(self, attr)
            if isinstance(value, str):
                attrValues.append(f'{attr[1:]}="{getattr(self, attr)}"')
            else:
                attrValues.append(f'{attr[1:]}={getattr(self, attr)}')
        msg = ', '.join(attrValues)
        return f"<{self.__class__.__qualname__} {msg}>"
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented
        return self.equalIdentityTo(value)
    
    def equalIdentityTo(self, value: AbsNetItem) -> bool:
        """Checks whether the identity (deteminant attributes) of this
        object is equal to the provided object or not. It is an alias for
        equality operator (`==`).
        """
        selfDet = set(self.getDeterminant(leading_under=True))
        valueDet = set(value.getDeterminant(leading_under=True))
        if selfDet != valueDet:
            return False
        for attr in selfDet:
            if getattr(self, attr) != getattr(value, attr):
                return False
        return True
    
    def equalValueTo(self, value: AbsNetItem) -> bool:
        """Checks whther this object has the same value as the provided
        object (checks all the attributes including determinants).
        """
        selfAttrs = set(self.getAttrs(leading_under=True))
        valueAttrs = set(value.getAttrs(leading_under=True))
        if selfAttrs != valueAttrs:
            return False
        for attr in selfAttrs:
            if getattr(self, attr) != getattr(value, attr):
                return False
        return True
    
    @abstractmethod
    def getDeterminant(self, leading_under: bool = False) -> tuple[str, ...]:
        """Gets attributes which determine the nature of the object and
        should not change while a system runs.
        """
        pass
    
    def getAttrs(self, leading_under: bool = False) -> tuple[str, ...]:
        """The attributes of interest of `Win32_NetworkAdapterConfiguration`
        class.
        """
        attrs = [
            attr
            for attr in dir(self)
            if attr.startswith('_') and attr[1].isupper() and not \
                attr.startswith('__') and not callable(getattr(self, attr))]
        if leading_under:
            return tuple(attrs)
        else:
            return self._removeUnder(attrs)
    
    def update(self, wmi_obj: Any | None = None) -> bool:
        """Updates this `AbsNetItem` object with the provided WMI object.
        If nothing is provided, this `AbsNetItem` object updates itself
        from the WMI.
        
        In case of reading WMI (`None`), if results are unexpected, it
        raises `RuntimeError`.
        """
        if wmi_obj is None:
            mpKeyValue = {
                attr[1:]:getattr(self, attr)
                for attr in self.getDeterminant(leading_under=True)}
            objs = self.readAll(**mpKeyValue)
            nObjs = len(objs)
            if nObjs != 1:
                raise RuntimeError(f'expected one WMI object but got {nObjs}')
            wmi_obj = objs[0]
        selfChanges = dict[str, Any]()
        changed = False
        for attr in self.getAttrs(leading_under=True):
            selfAttr = getattr(self, attr)
            try:
                objAttr = getattr(wmi_obj, attr)
            except AttributeError:
                break
            if selfAttr != objAttr:
                setattr(self, attr, objAttr)
                selfChanges[attr] = objAttr
                changed = True
        else:
            return changed
        # The provided `obj` does not have required attributes
        # Rolling back changes...
        for attr in selfChanges.keys():
            setattr(self, attr, selfChanges[attr])
        return False
    
    def _removeUnder(self, attrs: Iterable[str]) -> tuple[str, ...]:
        """Removes leading underscore from the specified iterable of
        attribute names.
        """
        return tuple([attr[1:] for attr in attrs])


class NetAdap(AbsNetItem):
    """Instances of this class represent instances of `Win32_NetworkAdapter`
    class on WMI.
    """
    @classmethod
    def readAll(cls, **kwargs) -> tuple[NetAdap, ...]:
        import wmi
        import pythoncom
        pythoncom.CoInitialize()
        wmi_ = wmi.WMI()
        kwargs['PhysicalAdapter'] = True
        wmiAdaps = wmi_.Win32_NetworkAdapter(**kwargs)
        # Converting COM objects into `NetAdap` objects...
        adaps = list[NetAdap]()
        badWmiAdaps = False
        for adap in wmiAdaps:
            try:
                adap = NetAdap(adap)
            except TypeError:
                badWmiAdaps = True
            else:
                adaps.append(adap)
        if badWmiAdaps:
            logging.error(
                'some COM objects cannot be converted into "NetAdap"')
        pythoncom.CoUninitialize()
        return tuple(adaps)

    @ classmethod
    def anumWinNetAdaps(cls) -> AdapCfgBag:
        """Enumerates all network interfaces on this Windows platform."""
        return _enumNetAdaps()

    def __init__(self, obj: Any) -> None:
        """Initializes an instance of `NetAdap` class with an object that
        provide necessary attributes. It raises `TypeError` if `obj` lacks
        some attributes or exposes type mismatch.
        """
        try:
            # Setting `Description` attribute...
            try:
                _assertAsStr(obj.Description)
            except AssertionError:
                raise TypeError(f'expected `Description` as `str` but got '
                    f'`{obj.Description.__class__.__qualname__}`')
            self._Description: str = obj.Description
            # Setting `DeviceID` attribute...
            try:
                _assertAsStr(obj.DeviceID)
            except AssertionError:
                raise TypeError(f'expected `DeviceID` as `str` but got '
                    f'`{obj.DeviceID.__class__.__qualname__}`')
            self._DeviceID: str = obj.DeviceID
            """The Unique identifier of the network adapter from other
            devices on the system.
            """
            # Setting `Caption` attribute...
            try:
                _assertAsStr(obj.Caption)
            except AssertionError:
                raise TypeError(f'expected `Caption` as `str` but got '
                    f'`{obj.Caption.__class__.__qualname__}`')
            self._Caption: str = obj.Caption
            """A short description of the instance, a one-line string."""
            # Setting `Index` attribute...
            try:
                _assertAsInt(obj.Index)
            except AssertionError:
                raise TypeError(f'expected `Index` as `int` but got '
                    f'`{obj.Index.__class__.__qualname__}`')
            self._Index: int = obj.Index
            """Index number of the network adapter, stored in the system
            registry.
            """
            # Setting `InterfaceIndex` attribute...
            try:
                _assertAsInt(obj.InterfaceIndex)
            except AssertionError:
                raise TypeError(f'expected `InterfaceIndex` as `int` but got '
                    f'`{obj.InterfaceIndex.__class__.__qualname__}`')
            self._InterfaceIndex: int = obj.InterfaceIndex
            # Setting `NetConnectionID` attribute...
            try:
                _assertAsStr(obj.NetConnectionID)
            except AssertionError:
                raise TypeError(f'expected `NetConnectionID` as `str` but got '
                    f'`{obj.NetConnectionID.__class__.__qualname__}`')
            self._NetConnectionID: str = obj.NetConnectionID
            """The name of this network interface in the shell."""
            self._NetConnectionStatus: int = obj.NetConnectionStatus
            # Setting `GUID` attribute...
            try:
                _assertAsStr(obj.GUID)
            except AssertionError:
                raise TypeError(f'expected `GUID` as `str` but got '
                    f'`{obj.GUID.__class__.__qualname__}`')
            self._GUID: str = obj.GUID
            # Setting `MACAddress` attribute...
            try:
                _assertAsStrNone(obj.MACAddress)
            except AssertionError:
                raise TypeError(f'expected `MACAddress` as `str` or `None`'
                    f' but got `{obj.MACAddress.__class__.__qualname__}`')
            self._MACAddress: str | None = obj.MACAddress
        except AttributeError as err:
            raise TypeError(err.args)
        else:
            self._configs = dict[int, NetConfig]()
    
    @property
    def Configs(self) -> tuple[NetConfig, ...]:
        return tuple(self._configs.values())
    
    @property
    def DeviceID(self) -> str:
        return self._DeviceID
    
    @property
    def Caption(self) -> str:
        return self._Caption
    
    @property
    def Index(self) -> int:
        return self._Index
    
    @property
    def InterfaceIndex(self) -> int:
        return self._InterfaceIndex
    
    @property
    def NetConnectionID(self) -> str:
        return self._NetConnectionID
    
    @property
    def NetConnectionStatus(self) -> ConnStatus:
        return ConnStatus(self._NetConnectionStatus)
    
    @property
    def Description(self) -> str:
        return self._Description
    
    @property
    def MACAddress(self) -> MAC | None:
        return _toMac(self._MACAddress)
    
    @property
    def GUID(self) -> UUID:
        return UUID(self._GUID)
    
    def getDeterminant(self, leading_under: bool = False) -> tuple[str, ...]:
        det = ['_Index', '_DeviceID', '_Description', '_Caption',]
        if leading_under:
            return tuple(det)
        else:
            return self._removeUnder(det)
    
    def connectivity(self) -> bool:
        """Specifies whether this network adapter has the potential
        internet connectivity.
        """
        return any(config.connectivity() for config in self._configs.values())
    
    def dnsProvided(self) -> bool:
        """Specifies whether this network interface is provided with DNS
        servers or not.
        """
        return any(config.dnsProvided() for config in self._configs.values())
    
    def dhcpAccess(self) -> bool:
        """Specifies whether this network interface has access to DHCP
        server.
        """
        return any(config.dhcpAccess() for config in self._configs.values())


class NetConfig(AbsNetItem):
    """Instances of this class represent instances of
    `Win32_NetworkAdapterConfiguration` class on WMI.
    """
    @classmethod
    def readAll(cls, **kwargs) -> tuple[NetConfig, ...]:
        import wmi
        import pythoncom
        pythoncom.CoInitialize()
        wmi_ = wmi.WMI()
        wmiAdaps = wmi_.Win32_NetworkAdapterConfiguration(**kwargs)
        # Converting COM objects into `NetAdap` objects...
        configs = list[NetConfig]()
        badWmiConfigs = False
        for adap in wmiAdaps:
            try:
                adap = NetConfig(adap)
            except TypeError:
                badWmiConfigs = True
            else:
                configs.append(adap)
        if badWmiConfigs:
            logging.error(
                'some COM objects cannot be converted into "NetAdap"')
        pythoncom.CoUninitialize()
        return tuple(configs)

    def __init__(self, obj: Any) -> None:
        """Initializes an instance of `NetConfig` class with an object
        that provide necessary attributes. It raises `TypeError` if `obj` 
        lacks some attributes or exposes type mismatch.
        """
        try:
            # Setting `Caption` attribute...
            try:
                _assertAsStr(obj.Caption)
            except AssertionError:
                raise TypeError(f'expected `Caption` as `str` but got '
                    f'`{obj.Caption.__class__.__qualname__}`')
            self._Caption: str = obj.Caption
            """A short description of the instance, a one-line string."""
            # Setting `SettingID` attribute...
            try:
                _assertAsStr(obj.SettingID)
            except AssertionError:
                raise TypeError(f'expected `SettingID` as `str` but got '
                    f'`{obj.SettingID.__class__.__qualname__}`')
            self._SettingID: str = obj.SettingID
            # Setting `Index` attribute...
            try:
                _assertAsInt(obj.Index)
            except AssertionError:
                raise TypeError(f'expected `Index` as `int` but got '
                    f'`{obj.Index.__class__.__qualname__}`')
            self._Index: int = obj.Index
            """A network adapter (an instance of `NetAdap`) can
            have multiple configuration and each of them has a unique `Index`.
            """
            # Setting `InterfaceIndex` attribute...
            try:
                _assertAsInt(obj.InterfaceIndex)
            except AssertionError:
                raise TypeError(f'expected `InterfaceIndex` as `int` but got '
                    f'`{obj.InterfaceIndex.__class__.__qualname__}`')
            self._InterfaceIndex: int = obj.InterfaceIndex
            # Setting `IPEnabled` attribute...
            try:
                _assertAsBool(obj.IPEnabled)
            except AssertionError:
                raise TypeError(f'expected `IPEnabled` as `bool` but got '
                    f'`{obj.IPEnabled.__class__.__qualname__}`')
            self._IPEnabled: bool = obj.IPEnabled
            """Specifies whether this network interface can use IP protocol
            for its network communicatiopns.
            """
            # Setting `IPAddress` attribute...
            try:
                _assertAsTupleStrNone(obj.IPAddress)
            except AssertionError:
                raise TypeError(f'expected `IPAddress` as `tuple[str, ...] | '
                    f'None` but got `{obj.IPAddress.__class__.__qualname__}`')
            self._IPAddress: tuple[str, ...] | None = obj.IPAddress
            """The optional IP addresses assigned to this network interface.
            It's a crucial property for identifying and communicating with a
            device on a network.
            """
            # Setting `DHCPEnabled` attribute...
            try:
                _assertAsBool(obj.DHCPEnabled)
            except AssertionError:
                raise TypeError(f'expected `DHCPEnabled` as `bool` but got '
                    f'`{obj.DHCPEnabled.__class__.__qualname__}`')
            self._DHCPEnabled: bool = obj.DHCPEnabled
            """Whether this network interface is configured to obtain obtain
            its network configuration settings, such as IP address, subnet
            mask, default gateway, and DNS server addresses; automatically
            through DHCP.
            """
            # Setting `DHCPServer` attribute...
            try:
                _assertAsStrNone(obj.DHCPServer)
            except AssertionError:
                raise TypeError(f'expected `DHCPServer` as `str` or `None`'
                    f' but got `{obj.DHCPServer.__class__.__qualname__}`')
            self._DHCPServer: str | None = obj.DHCPServer
            """Specifies the IP address of the DHCP server that will provide
            the necessary network configurations.
            """
            # Setting `DNSServerSearchOrder` attribute...
            try:
                _assertAsTupleStrNone(obj.DNSServerSearchOrder)
            except AssertionError:
                raise TypeError(f'expected `DNSServerSearchOrder` as '
                    '`tuple[str, ...] | None` but got '
                    f'`{obj.DNSServerSearchOrder.__class__.__qualname__}`')
            self._DNSServerSearchOrder: tuple[str, ...] | None = \
                obj.DNSServerSearchOrder
            # Setting `DefaultIPGateway` attribute...
            try:
                _assertAsTupleStrNone(obj.DefaultIPGateway)
            except AssertionError:
                raise TypeError(f'expected `DefaultIPGateway` as '
                    '`tuple[str, ...] | None` but got '
                    f'`{obj.DefaultIPGateway.__class__.__qualname__}`')
            self._DefaultIPGateway: tuple[str, ...] | None = \
                obj.DefaultIPGateway
            """An optional tuple of IP addresses of default gateways that the
            computer system uses.
            """
            # Setting `MACAddress` attribute...
            try:
                _assertAsStrNone(obj.MACAddress)
            except AssertionError:
                raise TypeError(f'expected `MACAddress` as `str` or `None`'
                    f' but got `{obj.MACAddress.__class__.__qualname__}`')
            self._MACAddress: str | None = obj.MACAddress
        except AttributeError as err:
            raise TypeError(err.args)
    
    @property
    def Caption(self) -> str:
        return self._Caption
    
    @property
    def SettingID(self) -> UUID:
        return UUID(self._SettingID)
    
    @property
    def Index(self) -> int:
        return self._Index
    
    @property
    def InterfaceIndex(self) -> int:
        return self._InterfaceIndex
    
    @property
    def IPEnabled(self) -> bool:
        return self._IPEnabled
    
    @property
    def IPAddress(self) -> tuple[IPv4 | IPv6, ...] | None:
        return _toIpTuple(self._IPAddress)
    
    @property
    def DHCPEnabled(self) -> bool:
        return self._DHCPEnabled
    
    @property
    def DHCPServer(self) -> IPv4 | IPv6 | None:
        return _strToIp(self._DHCPServer)
    
    @property
    def DNSServerSearchOrder(self) -> tuple[IPv4 | IPv6, ...] | None:
        return _toIpTuple(self._DNSServerSearchOrder)
    
    @property
    def DefaultIPGateway(self) -> tuple[IPv4 | IPv6, ...] | None:
        return _toIpTuple(self._DefaultIPGateway)
    
    @property
    def MACAddress(self) -> MAC | None:
        return _toMac(self._MACAddress)
    
    def getDeterminant(self, leading_under: bool = False) -> tuple[str, ...]:
        det = ['_Index', '_InterfaceIndex', '_Caption', '_SettingID',]
        if leading_under:
            return tuple(det)
        else:
            return self._removeUnder(det)
    
    def connectivity(self) -> bool:
        """Specifies whether this network interface has the potential
        interner connectivity.
        """
        # Checking whether this network interface uses IP-based
        # communication...
        if self.IPEnabled:
            return bool(self._IPAddress) and bool(self._MACAddress) and \
                bool(self._DefaultIPGateway) and (self.dnsProvided() or
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
    
    def setDnsSearchOrder(
            self,
            ips: Iterable[IPv4 | IPv6],
            ) -> NetConfigCode:
        import wmi
        import pythoncom
        pythoncom.CoInitialize()
        wmi_ = wmi.WMI()
        configs = wmi_.Win32_NetworkAdapterConfiguration(Index=self._Index)
        ips_ = [ip.exploded for ip in ips]
        logging.debug(ips)
        code: tuple[int] = configs[0].SetDNSServerSearchOrder(ips_)
        pythoncom.CoUninitialize()
        return NetConfigCode(code[0])


def _enumNetAdaps() -> AdapCfgBag:
    adaps = NetAdap.readAll()
    configs = NetConfig.readAll()
    acbag = AdapCfgBag()
    for adap in adaps:
        try:
            acbag.addAdap(adap)
        except ValueError:
            pass
    for config in configs:
        try:
            acbag.addConfig(config)
        except (ValueError, IndexError,):
            pass
    return acbag


def _assertAsStr(obj: Any) -> None:
    """Asserts that the argument is `str`."""
    assert isinstance(obj, str), \
        f'expected str but got {obj.__class__.__qualname__}'


def _assertAsInt(obj: Any) -> None:
    """Asserts that the argument is `int``."""
    assert isinstance(obj, int), \
        f'expected int but got {obj.__class__.__qualname__}'


def _assertAsBool(obj: Any) -> None:
    """Asserts that the argument is `int``."""
    assert isinstance(obj, bool), \
        f'expected bool but got {obj.__class__.__qualname__}'


def _assertAsStrNone(obj: Any) -> None:
    """Asserts that the argument is `str | None``."""
    assert (isinstance(obj, str) or obj is None), \
        f'expected str or None but got {obj.__class__.__qualname__}'


def _assertAsTupleStrNone(obj: Any) -> None:
    """Asserts that the argument is `tuple[str, ...] | None``."""
    assert obj is None or (isinstance(obj, tuple) and all(
        isinstance(item, str) for item in obj)), \
        f'{obj} is neither a tuple of strings nor None'


def _toIpTuple(
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


def _toMac(mac: str | None) -> MAC | None:
    """Converts an optional MAC address string to `MAC` object."""
    return mac if mac is None else MAC(mac)


def _saveWmiObj(wmi_objs: Iterable[Any], file_name: PathLike[str]) -> None:
    from os import fspath
    with open(fspath(file_name), mode='wt') as fileObj:
        for adap in wmi_objs:
            mpNameValue = _objToNameValue(adap)
            width = max(len(name) for name in mpNameValue.keys())
            fileObj.write('\n\n' + ('=' * 40))
            for name, value in mpNameValue.items():
                fileObj.write(f'\n{name:>{width}}  {value}')


def _objToNameValue(obj: Any) -> dict[str, Any]:
    mpNameValue = dict[str, Any]()
    for attrName in dir(obj):
        if not attrName.startswith('_'):
            attrValue = getattr(obj, attrName)
            if not callable(attrValue):
                mpNameValue[attrName] = attrValue
    names = list(mpNameValue.keys())
    sorted(names, key=lambda x: x.lower())
    return {name:mpNameValue[name] for name in names}

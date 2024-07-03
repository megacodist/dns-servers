#
# 
#

from __future__ import annotations
from abc import ABC, abstractmethod
import enum
from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
from typing import Iterable


class IPRole(enum.IntEnum):
    PRIM_4 = 1
    SECON_4 = 2
    PRIM_6 = 3
    SECON_6 = 4


class DnsServer:
    def __init__(
            self,
            name: str,
            ips: Iterable[IPv4 | IPv6]
            ) -> None:
        """Initializes a new instance of `DnsServer`. Arguments are as
        follow:

        :param `name`: the name of the DNS server.
        :param `ips`: a list of IPv4 and IPv6. This list must contain at
        least one IP and up to two IPv4 and up to two IPv6 addresses,
        otherwise `ValueError` will be raised. `TypeError` is raised if
        there is at least one object of different type.
        """
        self._name = name
        self._prim_4: IPv4 | None = None
        self._secon_4: IPv4 | None = None
        self._prim_6: IPv6| None = None
        self._secon_6: IPv6 | None = None
        # Processing `ips` list...
        n4 = 0
        n6 = 0
        for ip in ips:
            if isinstance(ip, IPv4):
                if n4 == 0:
                    self._prim_4 = ip
                    n4 = 1
                elif n4 == 1:
                    self._secon_4 = ip
                    n4 = 2
                else:
                    raise ValueError(
                        'expected up to two IPv4 addresses but got 3')
            elif isinstance(ip, IPv6):
                if n6 == 0:
                    self._prim_6 = ip
                    n6 = 1
                elif n6 == 1:
                    self._secon_6 = ip
                    n6 = 2
                else:
                    raise ValueError(
                        'expected up to two IPv6 addresses but got 3')
            else:
                raise TypeError('expected IPv4 or IPv6 but got '
                    f'{ip.__class__.__qualname__}')
        if n4 == 0 and n6 == 0:
            raise ValueError('no IP is provided')
    
    @property
    def name(self) -> str:
        """Gets the name of the DNS server."""
        return self._name
    
    @property
    def prim_4(self) -> IPv4 | None:
        """Gets the primary IPv4 of this DNS server."""
        return self._prim_4
    
    @property
    def secon_4(self) -> IPv4 | None:
        """Gets the secondary IPv4 of this DNS server."""
        return self._secon_4
    
    @property
    def prim_6(self) -> IPv6 | None:
        """Gets the primary IPv6 of this DNS server."""
        return self._prim_6
    
    @property
    def secon_6(self) -> IPv6 | None:
        """Gets the secondary IPv6 of this DNS server."""
        return self._secon_6
    
    def toSet(self) -> frozenset[IPv4 | IPv6]:
        """Returns IPs as a `frozenset` object."""
        return frozenset(filter(
            None,
            (self._prim_4, self._secon_4, self._prim_6, self._secon_6)))
    
    def toTuple(self) -> tuple[IPv4 | IPv6, ...]:
        return tuple(filter(
            None,
            (self._prim_4, self._secon_4, self._prim_6, self._secon_6)))
    
    def ipsEqual(self, dns: DnsServer) -> bool:
        """Specifies whether IP set of this object equals the provided
        one.
        """
        if not isinstance(dns, DnsServer):
            return NotImplemented
        return self.toSet() == dns.toSet()
    
    def __repr__(self) -> str:
        ips = list[str]()
        if self._prim_4:
            ips.append(f"primary IPv4='{str(self._prim_4)}'")
        if self._secon_4:
            ips.append(f"secondary IPv4='{str(self._secon_4)}'")
        if self._prim_6:
            ips.append(f"primary IPv6='{str(self._prim_6)}'")
        if self._secon_6:
            ips.append(f"secondary IPv6='{str(self._secon_6)}'")
        return (f'<{self.__class__.__qualname__} name={self._name}, '
            f'{' '.join(ips)}')
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DnsServer):
            return NotImplemented
        return (self._name == value._name) and (self.toSet() == 
            value.toSet())


class IDatabase(ABC):
    @abstractmethod
    def close(self) -> None:
        """Closes the connection to the database."""
        pass

    @abstractmethod
    def selectDns(self, dns_name: str) -> DnsServer | None:
        """Selects and returns DNS server from the database with the
        specified name. Returns `None` if it does not exist."""
        pass

    @abstractmethod
    def selctAllDnses(self) -> list[DnsServer]:
        """Returns a mutable sequence (typically a `list`) of all DNS
        servers in the database.
        """
        pass

    @abstractmethod
    def insertDns(self, dns: DnsServer) -> None:
        """Inserts the specified DNS server object into the database."""
        pass

    @abstractmethod
    def deleteDns(self, dns_spec: int | str) -> None:
        """Deletes the specified DNS server object from the database.
        The specifier can be either `int` (`id`) or `str` (`name`).
        """
        pass

    @abstractmethod
    def updateDns(self, old_name: str, new_dns: DnsServer) -> None:
        """Updates the specified DNS server object with the new one."""
        pass

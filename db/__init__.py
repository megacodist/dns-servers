#
# 
#

from __future__ import annotations
from abc import ABC, abstractmethod
from ipaddress import IPv4Address
from typing import MutableSequence


class DnsInfo:
    """This class is used when DNS servers information is not possible
    via `DnsServer`.
    """
    def __init__(
            self,
            name: str,
            primary: str,
            secondary: str,
            ) -> None:
        self.name = name
        self.primary = primary
        self.secondary = secondary


class DnsServer:
    def __init__(
            self,
            name: str,
            primary: IPv4Address,
            secondary: IPv4Address | None = None,
            ) -> None:
        self._name = name
        self._primary = primary
        self._secondary = secondary
    
    @property
    def name(self) -> str:
        """Gets the name of the DNS server."""
        return self._name
    
    @property
    def primary(self) -> IPv4Address:
        """Gets the primary IP of the DNS server."""
        return self._primary
    
    @property
    def secondary(self) -> IPv4Address | None:
        """Gets the secondary IP of the DNS server."""
        return self._secondary
    
    def ipsToSet(self) -> set[IPv4Address]:
        """Returns IPs as a set. If the secondary IP is `None`, the result
        only contains primary IP.
        """
        set_ = set[IPv4Address]()
        set_.add(self._primary)
        if self._secondary:
            set_.add(self._primary)
        return set_
    
    def ipsEqual(self, dns: DnsServer) -> bool:
        """Specifies whether IP set of this object equals the provided
        object.
        """
        if not isinstance(dns, DnsServer):
            return NotImplemented
        return self.ipsToSet() == dns.ipsToSet()
    
    def __repr__(self) -> str:
        second = f', secondary={str(self._secondary)}' if self._secondary \
            else ''
        return (f'<{self.__class__.__qualname__} name={self._name}, '
            f'primary={self._primary}{second}>')
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DnsServer):
            return NotImplemented
        return (self._name == value._name) and (self.ipsToSet() == 
            value.ipsToSet())


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
    def selctAllDnses(self) -> dict[int, DnsServer]:
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
    def updateDns(self, dns_name: str, new_dns: DnsServer) -> None:
        """Updates the specified DNS server object with the new one."""
        pass

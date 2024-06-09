#
# 
#

from __future__ import annotations
from abc import ABC, abstractmethod
from ipaddress import IPv4Address
from typing import MutableSequence


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
    
    def __repr__(self) -> str:
        second = f', secondary={str(self._secondary)}' if self._secondary \
            else ''
        return (f'<{self.__class__.__qualname__} name={self._name}, '
            f'primary={self._primary}{second}>')


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
    def selctAllDnses(self) -> MutableSequence[DnsServer]:
        """Returns a mutable sequence (typically a `list`) of all DNS
        servers in the database.
        """
        pass

    @abstractmethod
    def insertDns(self, dns: DnsServer) -> None:
        """Inserts the specified DNS server object into the database."""
        pass

    @abstractmethod
    def deleteDns(self, dns_name: str) -> None:
        """Deletes the specified DNS server object from the database."""
        pass

    @abstractmethod
    def updateDns(self, dns_name: str, new_dns: DnsServer) -> None:
        """Updates the specified DNS server object with the new one."""
        pass

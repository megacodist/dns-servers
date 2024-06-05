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

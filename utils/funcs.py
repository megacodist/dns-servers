#
# 
#


from ipaddress import IPv4Address
from queue import Queue
from typing import Callable, MutableSequence, TYPE_CHECKING

from db import DnsServer, IDatabase


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


def listInterfaces(q: Queue[str] | None) -> MutableSequence[str]:
    """List all network interfaces. Raises `TypeError` upon any failure."""
    from ntwrk import GetInterfacesNames
    if q:
        q.put(_('LOADING_INTERFACES'))
    return GetInterfacesNames()


def listDnses(
        q: Queue[str] | None,
        db: IDatabase,
        ) -> MutableSequence[DnsServer]:
    if q:
        q.put(_('LOADING_DNSES'))
    return db.selctAllDnses()

def dnsToSetIps(dns: DnsServer) -> set[IPv4Address]:
    """Converts a `DnsServer` object into a set of one or two IPv4
    objects.
    """
    return {dns.primary} if dns.secondary is None else \
        {dns.primary, dns.secondary}

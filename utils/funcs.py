#
# 
#


from ipaddress import IPv4Address
from queue import Queue
from typing import Callable, MutableSequence, TYPE_CHECKING

from db import DnsInfo, DnsServer, IDatabase
from ntwrk import InterfaceAttrs


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


def mergeMsgs(braced: str, embed: str) -> str:
    """Merges `embed` into `braced`. `braced` must contain `{}`."""
    words = embed.split()
    words[0] = words[0].lower()
    embed = ' '.join(words)
    return braced.format(embed)


def listInterfaces(q: Queue[str] | None) -> list[InterfaceAttrs]:
    """List all network interfaces. Raises `TypeError` upon any failure."""
    from ntwrk import parse_ipconfig
    if q:
        q.put(_('READING_INTERFACES'))
    return parse_ipconfig()


def listDnses(
        q: Queue[str] | None,
        db: IDatabase,
        ) -> tuple[dict[str, DnsServer], dict[
            frozenset[IPv4Address], DnsServer]]:
    if q:
        q.put(_('READING_DNSES'))
    dnses = db.selctAllDnses()
    if q:
        q.put(_('CONSTRUCTING_DATA'))
    mpNameDns = {dns.name:dns for dns in dnses}
    mpIpDns = {dns.ipsToSet():dns for dns in dnses}
    return mpNameDns, mpIpDns

def readDnsInfo(
        q: Queue[str] | None,
        inter_name: str,
        mp_ip_dns: dict[frozenset[IPv4Address], DnsServer],
        ) -> DnsInfo | DnsServer:
    from ntwrk import readDnsInfo
    if q:
        q.put(_('READING_DNS_INFO'))
    return readDnsInfo(inter_name, mp_ip_dns,)

def dnsToSetIps(dns: DnsServer) -> set[IPv4Address]:
    """Converts a `DnsServer` object into a set of one or two IPv4
    objects.
    """
    return {dns.primary} if dns.secondary is None else \
        {dns.primary, dns.secondary}

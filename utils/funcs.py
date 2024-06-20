#
# 
#


from ipaddress import IPv4Address
import logging
from queue import Queue
from typing import Callable, Literal, TYPE_CHECKING
from urllib.parse import ParseResult

from db import DnsServer, IDatabase
from ntwrk import InterfaceAttrs
from utils.types import DnsInfo


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class OpFailedError(Exception):
    """APIs of this module might raise this exception if their designated
    operation failed.
    """
    pass


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
        ) -> DnsInfo | Literal['DHCP']:
    from ntwrk import readDnsInfo
    if q:
        q.put(_('READING_DNS_INFO'))
    return readDnsInfo(inter_name)


def setDns(q: Queue | None, inter_name: str, dns: DnsServer | DnsInfo) -> None:
    """Sets DNS servers of the specified network interface.

    #### Exceptions:
    1. `OpFailedError`
    2. `subprocess.CalledProcessError`
    3. `ntwrk.ParsingError`
    """
    from ntwrk import setDns, readDnsInfo
    if q:
        if isinstance(dns, DnsServer):
            msg = _('SETTING_DNS').format(inter_name, dns.name)
        elif isinstance(dns, DnsInfo):
            msg = _('SETTING_DNS').format(inter_name, _('UNNAMED'))
        q.put(msg)
    setDns(inter_name, dns.primary, dns.secondary)
    dnsInfo = readDnsInfo(inter_name)
    try:
        logging.debug(dnsInfo)
        isEqual = dnsInfo.ipsToSet() == dns.ipsToSet() # type: ignore
    except Exception:
        isEqual = False
    if not isEqual:
        raise OpFailedError('cannot set dns as expected')


def dnsToSetIps(dns: DnsServer) -> set[IPv4Address]:
    """Converts a `DnsServer` object into a set of one or two IPv4
    objects.
    """
    return {dns.primary} if dns.secondary is None else \
        {dns.primary, dns.secondary}


def ipToStr(ip: IPv4Address | None) -> str:
    """Converts an optional IPv4 object to string."""
    return '' if ip is None else str(ip)


def parseUrl(url: str, scheme: str = '') -> ParseResult:
    """Parses a string containing URL and returns result. It raises
    `TypeError` if it fails.
    """
    import re
    from urllib.parse import urlparse
    NET_LOC_REGEX = r"""
        (?:(?P<username>\w+):(?P<password>\w+)@)?
        (?P<hostname>\w+(?:[.]\w+)+)(?:[:](?P<port>\d+))?
    """
    netLocPat = re.compile(NET_LOC_REGEX, re.VERBOSE)
    mtch = netLocPat.search(url)
    if not mtch:
        raise TypeError('cannot match network location')
    netloc = mtch.group()
    scheme_ = url[:mtch.start()]
    pathParamsFrag = url[mtch.end():]
    if scheme_:
        SCHEME_REGEX = r"^(?P<scheme>\w+)?:?/*$"
        schemePat = re.compile(SCHEME_REGEX, re.VERBOSE)
        mtch = schemePat.match(scheme_)
        if not mtch:
            raise TypeError(f'cannot match scheme: {scheme_}')
        scheme = mtch.group('scheme')
    if pathParamsFrag:
        PATH_PAR_FRAG_REGEX = r"""
            ^
            (?P<path>(?:/\w+)+)?
            (?:[?](?P<params>\w+=\w+(?:&\w+=\w+)*))?
            (?:[#](?P<fragment>\w+))?
            $
        """
        pathParFragPat = re.compile(PATH_PAR_FRAG_REGEX, re.VERBOSE)
        mtch = pathParFragPat.match(pathParamsFrag)
        if not mtch:
            raise TypeError('cannot match path, params, and/or '
                f'fragment: {pathParamsFrag}')
        path = mtch.group('path')
    else:
        path = ''
    temp = urlparse(url)
    return ParseResult(
        scheme=scheme,
        netloc=netloc,
        path=path,
        params=temp.params,
        query=temp.query,
        fragment=temp.fragment)

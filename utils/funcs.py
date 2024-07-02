#
# 
#


from ipaddress import IPv4Address
import logging
from queue import Queue
from typing import Callable, Literal, TYPE_CHECKING
from urllib.parse import ParseResult

from db import DnsServer, IDatabase
from ntwrk import NetInt
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


def readNetInts(q: Queue[str] | None) -> list[NetInt]:
    """Reads all network interfaces. Raises `TypeError` upon any failure."""
    from ntwrk import enumNetInts
    if q:
        q.put(_('READING_INTERFACES'))
    return enumNetInts()


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


def setDns(
        q: Queue | None,
        net_int: str,
        dns: DnsServer | DnsInfo | Literal['DHCP'],
        ) -> None:
    """Sets DNS servers of the specified network interface.

    #### Exceptions:
    1. `TypeError`
    2. `OpFailedError`
    3. `subprocess.CalledProcessError`
    4. `ntwrk.ParsingError`
    """
    from ntwrk import setDns, setDnsDhcp, readDnsInfo
    if q:
        try:
            dnsName = dns.name # type: ignore
        except AttributeError:
            dnsName = dns if isinstance(dns, str) else _('UNNAMED')
        q.put(_('SETTING_DNS').format(net_int, dnsName))
    # Setting DNS servers to DHCP if requested...
    if isinstance(dns, str):
        if dns == 'DHCP':
            setDnsDhcp(net_int)
            if not (readDnsInfo(net_int) is 'DCHP'):
                raise OpFailedError('cannot set DNS servers to DHCP')
            return
        raise TypeError(f'only DHCP is allowed not {dns}')
    # Setting DNS servers to provided IPs...
    setDns(net_int, dns.primary, dns.secondary)
    dnsInfo = readDnsInfo(net_int)
    try:
        isEqual = dnsInfo.ipsToSet() == dns.ipsToSet() # type: ignore
    except Exception:
        isEqual = False
    if not isEqual:
        raise OpFailedError('cannot set DNS servers as expected')


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


def floatToEngineering(num: float, short: bool = False) -> str:
    """Converts a float number to its engineering representation. It raises
    `ValueError` if prefix is smaller or larger that support.
    """
    from decimal import Decimal
    if short is True:
        idx = 0
    elif short is False:
        idx = 1
    else:
        raise TypeError("expected bool for 'short' but got "
            f"'{short.__class__.__qualname__}'")
    # Defining scientific prefixes and their corresponding powers of 10
    prefixes: dict[int, tuple[str, str]] = {
        24: ('Y', 'yotta'),
        21: ('Z', 'zetta'),
        18: ('E', 'exa'),
        15: ('P', 'peta'),
        12: ('T', 'tera'),
        9: ('G', 'giga'),
        6: ('M', 'mega'),
        3: ('k', 'kilo'),
        0: ('', ''),
        -3: ('m', 'milli'),
        -6: ('μ', 'micro'),
        -9: ('n', 'nano'),
        -12: ('p', 'pico'),
        -15: ('f', 'femto'),
        -18: ('a', 'atto'),
        -21: ('z', 'zepto'),
        -24: ('y', 'yocto'),}
    # Converting the number to a string in scientific notation
    sciNotation = f"{num:.2e}"
    # Spliting the scientific notation into the coefficient and the exponent
    coeff, exponent = sciNotation.split('e')
    exponent = int(exponent)
    #
    a = exponent % 3
    try:
        prefix = prefixes[exponent - a][idx]
    except KeyError:
        raise ValueError(f'no prefix for {exponent - a}')
    n = Decimal(coeff) * (10 ** a)
    return f'{float(n)} {prefix}'

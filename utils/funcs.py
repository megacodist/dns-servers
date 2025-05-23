#
# 
#


from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
from queue import Queue
from typing import Callable, Iterable, Literal, TYPE_CHECKING
from urllib.parse import ParseResult

from db import DnsServer, IDatabase
from ntwrk import AdapCfgBag, NetAdap, NetConfig


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


def getNetItemAttrs(net_item: NetAdap | NetConfig) -> Iterable[str]:
    return net_item.getAttrs()


def getNetItemHashable(net_item: NetAdap | NetConfig) -> tuple[int, int]:
    """Gets a hashable object for `NetAdap` or `NetConfig` objects."""
    if isinstance(net_item, NetAdap):
        return (0, net_item.Index,)
    elif isinstance(net_item, NetConfig):
        return (1, net_item.Index,)
    else:
        raise TypeError(
            'expected NetAdap or NetConfig but got '
            f'{net_item.__class__.__qualname__}')


def getNetItemTitle(net_item: NetAdap | NetConfig) -> str:
    """Gets a title for `NetAdap` or `NetConfig` objects."""
    if isinstance(net_item, NetAdap):
        return _('ADAP_TITLE').format(net_item.NetConnectionID)
    elif isinstance(net_item, NetConfig):
        return _('CONFIG_TITLE').format(net_item.Index)
    else:
        raise TypeError(
            'expected NetAdap or NetConfig but got '
            f'{net_item.__class__.__qualname__}')


def genSep(q: Queue[str] | None, names: Iterable[str]) -> str:
    from itertools import combinations
    import string
    allChars = string.punctuation + string.digits + string.ascii_letters
    for n in range(1, len(allChars)):
        for choice in combinations(allChars, n):
            perm = ''.join(choice)
            if not any(perm in name for name in names):
                return perm


def mergeMsgs(braced: str, embed: str) -> str:
    """Merges `embed` into `braced`. `braced` must contain `{}`."""
    words = embed.split()
    words[0] = words[0].lower()
    embed = ' '.join(words)
    return braced.format(embed)


def readNetAdaps(q: Queue[str] | None) -> AdapCfgBag:
    """Reads all network interfaces. Raises `TypeError` upon any failure."""
    if q:
        q.put(_('READING_ADAPS'))
    return NetAdap.anumWinNetAdaps()


def listDnses(
        q: Queue[str] | None,
        db: IDatabase,
        ) -> tuple[dict[str, DnsServer], dict[IPv4 | IPv6, DnsServer]]:
    if q:
        q.put(_('READING_DNSES'))
    dnses = db.selctAllDnses()
    if q:
        q.put(_('CONSTRUCTING_DATA'))
    mpNameDns = {dns.name:dns for dns in dnses}
    mpIpDns = {ip:dns for dns in dnses for ip in dns.toSet()}
    return mpNameDns, mpIpDns


def ipToStr(ip: IPv4 | IPv6 | None) -> str:
    """Converts an optional IPv4 or IPv6 object to string."""
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

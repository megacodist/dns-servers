#
# 
#

from collections import namedtuple
import re
from urllib.parse import ParseResult


UrlParts = namedtuple(
    'UrlParts',
    ('scheme', 'username', 'password', 'hostname', 'port', 'path', 'params', 'fragment'))


def parseUrl(url: str, scheme: str = '') -> ParseResult:
    """Parses a string containing URL and returns result. It raises
    `TypeError` if it fails.
    """
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


def urlparse_222(url: str) -> ParseResult | None:
    HOST_REGEX = r"""
        (?P<hostname>\w+(?:[.]\w+)+)(?:[:](?P<port>\d+))?
    """
    hostPat = re.compile(HOST_REGEX, re.VERBOSE)
    mtch = hostPat.search(url)
    if not mtch:
        print('a')
        return None
    hostname = mtch.group('hostname')
    port = mtch.group('port')
    preHost = url[:mtch.start()]
    postHost = url[mtch.end():]
    if preHost:
        print('preHost:', preHost)
        PRE_HOST_REGEX = r"""
            ^
            (?P<scheme>\w+)?(?:[:]?)/*  # Matches against optional `scheme` and a colon
            (?:(?P<username>\w+):(?P<password>\w+)@)?
            $
        """
        preHostPat = re.compile(PRE_HOST_REGEX, re.VERBOSE)
        mtch = preHostPat.match(preHost)
        if not mtch:
            print('b')
            return None
        scheme = mtch.group('scheme')
        username = mtch.group('username')
        password = mtch.group('password')
    else:
        scheme = None
        username = None
        password = None
    if postHost:
        print('postHost:', postHost)
        POST_HOST_REGEX = r"""
            ^
            (?P<path>(?:/\w+)+)?
            (?:[?](?P<params>\w+=\w+(?:&\w+=\w+)*))?
            (?:[#](?P<fragment>\w+))?
            $
        """
        postHostPat = re.compile(POST_HOST_REGEX, re.VERBOSE)
        mtch = postHostPat.match(postHost)
        if not mtch:
            print('c')
            return None
        path = mtch.group('path')
        params = mtch.group('params')
        fragment = mtch.group('fragment')
    else:
        path = None
        params = None
        fragment = None
    return ParseResult(
        scheme,
        username,
        password,
        hostname,
        port,
        path,
        params,
        fragment)


def main() -> None:
    from urllib.parse import ParseResult
    try:
        while True:
            url = parseUrl(input('Enter a URL: '))
            if url is None:
                print('Invalid URL')
                continue
            print('URL parts ======================')
            print('Scheme:', url.scheme)
            print('Username:', url.username)
            print('Password:', url.password)
            print('Host:', url.hostname)
            print('Port:', url.port)
            print('Path:', url.path)
            print('Params:', url.params)
            print('Fragment:', url.fragment)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

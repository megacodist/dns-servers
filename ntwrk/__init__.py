#
# 
#

from ipaddress import AddressValueError
import logging
from collections import namedtuple
import re
from typing import MutableSequence, ValuesView

from db import DnsInfo, DnsServer
from widgets.dns_win import IPv4Address


class ParsingError(Exception):
    pass


class NetOpFailedError(Exception):
    """Exception raised for errors in APIS of this module."""
    pass


type AttrValue = None | str | tuple[str, ...]
"""Possible types of adapter (network interface) values."""

type InterfaceAttrs = dict[str, AttrValue]


_ADAPTER_REGEX = r'''
    ^              # Start of the string
    (?P<type>.+)   # Capture group for the adapter type (alphanumeric characters)
    \s+adapter\s+  # Literal "adapter" surrounded by whitespace
    (?P<name>.+)   # Capture group for the adapter name (alphanumeric characters)
    :$'''          # Colon at the end of th

_intrfcPatt = re.compile(_ADAPTER_REGEX, re.VERBOSE)


def _matchInterface(line: str) -> tuple[str, str] | None:
    global _ADAPTER_REGEX
    global _intrfcPatt
    lineMatch = _intrfcPatt.match(line)
    if lineMatch:
        return (lineMatch['name'], lineMatch['type'])
    else:
        return None


def _matchAttr(line: str) -> tuple[str, str] | None:
    try:
        colonIdx = line.index(':')
        return line[:colonIdx].strip(' .'), line[(colonIdx + 1):]
    except ValueError:
        return None


def _addToAttr(attr: AttrValue, value: str) -> AttrValue:
    """Adds `value` to the `attr`."""
    value = value.strip()
    if not value:
        return attr
    match attr:
        case None:
            return value
        case str():
            temp = set([attr, value])
            return attr if len(temp) == 1 else tuple(temp)
        case tuple():
            temp = set(attr)
            temp.add(value)
            return tuple(temp)


def parse_ipconfig() -> list[InterfaceAttrs]:
    """Parses the output of `ipconfig` command in Windows and returns
    a list of network interfaces and their attributes.

    #### Exceptions:
    1. `subprocess.CalledProcessError`: something went wrong communicating
    with the `ipconfgi` process.
    2. `ParsingError`
    """
    import subprocess
    command = ['ipconfig']
    ipconfig = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,)
    output, error = ipconfig.communicate()
    if error:
        raise subprocess.CalledProcessError(
            returncode=ipconfig.returncode,
            cmd=command,
            output=error,
            stderr=error,)
    #
    interface: InterfaceAttrs | None = None
    attr: str | None = None
    result = list[InterfaceAttrs]()
    for line in output.splitlines():
        # Ignoring empty lines...
        line = line.strip()
        if not line:
            continue
        # Matching against interface...
        res = _matchInterface(line)
        if res is not None:
            if interface:
                result.append(interface)
            interface = {}
            interface['Name'] = res[0]
            interface['Type'] = res[0]
            attr = None
            continue
        # Matching against attribute...
        res = _matchAttr(line)
        if res is not None:
            if interface is None:
                raise ParsingError(
                    'attribute line before all adapter lines',
                    line,)
            attr = res[0]
            if attr in interface:
                interface[attr] = _addToAttr(interface[attr], res[1])
            else:
                interface[attr] = res[1] if res[1] else None
            continue
        # Eliminating leading, unstructured lines...
        if interface is None:
            continue
        #
        if attr is None:
            raise ParsingError(
                'Possibly second-value line before any attribute line',
                line,)
        else:
            interface[attr] = _addToAttr(interface[attr], line)
    if interface:
        result.append(interface)
    return result


def canConnect(adapter: InterfaceAttrs) -> bool:
    """Specifies whether the specified network interface can connect
    to the Internet or not.
    """
    if 'Default Gateway' in adapter and adapter['Default Gateway']:
        return True
    else:
        return False


def GetInterfacesAttrs() -> tuple[tuple[str, ...], ...]:
    import subprocess
    cmpl = subprocess.run(
        ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
        capture_output=True,
        text=True,
        check=True,)
    lines = cmpl.stdout.splitlines()
    lines = [line for line in lines if line.strip()]
    if lines[1].strip(' -'):
        raise TypeError('Cannot detect dashed line.')
    attrs = lines[0].split()
    # Getting columns boundaries...
    colsLimit = list[slice]()
    prev = 0
    while True:
        try:
            next = lines[1].index(' -', prev)
        except ValueError:
            colsLimit.append(slice(prev, None))
            break
        else:
            next += 1
            colsLimit.append(slice(prev, next))
            prev = next
    # Defining the named tuple...
    InterfaceAttrs = namedtuple(
        'InterfaceAttrs',
        [lines[0][slc].strip() for slc in colsLimit])
    #
    interfaces = list[InterfaceAttrs]()
    for line in lines[2:]:
        inter = InterfaceAttrs(*[line[slc].strip() for slc in colsLimit])
        interfaces.append(inter)
    return tuple(interfaces)


def GetInterfacesNames() -> MutableSequence[str]:
    """Gets all the available interfaces names. It raises `NetOpFailedError`
    upon any failure.
    """
    try:
        return [inter.Name for inter in GetInterfacesAttrs()] # type: ignore
    except AttributeError:
        raise NetOpFailedError('Unable to read network interface names.')


def readDnsInfo(
        inter_name: str,
        mp_ip_dns: dict[frozenset[IPv4Address], DnsServer],
        ) -> DnsInfo | DnsServer:
    """Gets DNS servers for the specified network interface.

    #### Exceptions:
    1. `subprocess.CalledProcessError`
    2. `ParsingError`
    """
    import subprocess
    command = ['netsh', 'interface', 'ip', 'show', 'dns', inter_name]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,)
    output, error = process.communicate()
    if error:
        raise subprocess.CalledProcessError(
            returncode=process.returncode,
            cmd=command,
            output=error,
            stderr=error,)
    # Parsing result...
    lines = [
        line.strip().lower()
        for line in output.splitlines()
        if line.strip()]
    logging.debug('\n'.join(lines))
    if not inter_name.lower() in lines[0]:
        raise ParsingError('Interface name did not find in output', lines)
    if 'dhcp' in lines[1]:
        return DnsInfo(name='DHCP',)
    if 'static' in lines[1]:
        try:
            colonIdx = lines[1].index(':')
        except ValueError:
            raise ParsingError('cannot parse primary IP', lines)
        try:
            primary = IPv4Address(lines[1][(colonIdx + 1):].strip())
        except AddressValueError:
            return DnsInfo()
        try:
            seconadry = IPv4Address(lines[2].strip())
        except AddressValueError:
            seconadry = None
        ipsSet = DnsServer.primSeconToSet(primary, seconadry)
        if ipsSet in mp_ip_dns:
            return mp_ip_dns[ipsSet]
        else:
            return DnsInfo(
                primary=str(primary),
                secondary=str(seconadry) if seconadry else '')
    raise ParsingError('cannot detect either DHCP or static IPs')


def setDns(inter_name: str, dns: DnsServer) -> None:
    """Sets the DNS servers of the specified interface names."""
    import subprocess
    primCmd = (f'netsh interface ip set dns "{inter_name}" '
        f'static {dns.primary}')
    res = subprocess.run(primCmd, shell=True, check=True, text=True)
    logging.debug(res.stdout)
    seconCmd = f'netsh interface ip add address name="{inter_name}" {dns.secondary}'
    res = subprocess.run(seconCmd, shell=True, check=True, text=True)
    logging.debug(res.stdout)
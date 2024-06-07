#
# 
#


from collections import namedtuple
from ipaddress import IPv4Address
from typing import MutableSequence


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
    """Gets all the available interfaces names. It raises `TypeError`
    upon any failure.
    """
    try:
        return [inter.Name for inter in GetInterfacesAttrs()] # type: ignore
    except AttributeError:
        raise TypeError('Unable to read network interfaces names.')


def GetDnsServersIPv4(name: str) -> tuple[IPv4Address, IPv4Address]:
    pass

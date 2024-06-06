#
# 
#


from queue import Queue
from typing import Callable, MutableSequence, TYPE_CHECKING

from db import DnsServer, IDatabase


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


def listInterfaces(q: Queue) -> MutableSequence[str]:
    """List all network interfaces. Raises `TypeError` upon any failure."""
    from ntwrk import GetInterfacesNames
    q.put(_('LOADING_INTERFACES'))
    return GetInterfacesNames()


def listDnses(q: Queue, db: IDatabase) -> MutableSequence[DnsServer]:
    pass

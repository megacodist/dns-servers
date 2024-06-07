#
# 
#


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

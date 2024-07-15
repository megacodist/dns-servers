#
# 
#

from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
from os import PathLike
import sqlite3

from . import DnsServer, IDatabase


class SqliteDb(IDatabase):
    def __init__(self, db_file: PathLike) -> None:
        """Initializes a new database instance from the provided path."""
        self._conn = sqlite3.connect(db_file, check_same_thread=False)
        """The connection object of the database."""
    
    def _tupleToDns(
            self,
            tpl: tuple[str, int | None, int | None, int | None, int | None],
            ) -> DnsServer:
        """Converts a 5-tuple into a `DnsServer` object."""
        ips = list[IPv4 | IPv6]()
        if tpl[1] is not None:
            ips.append(IPv4(tpl[1]))
        if tpl[2] is not None:
            ips.append(IPv4(tpl[2]))
        if tpl[3] is not None:
            ips.append(IPv6(tpl[3]))
        if tpl[4] is not None:
            ips.append(IPv6(tpl[4]))
        return  DnsServer(tpl[0], *ips)

    def _dnsToTuple(
            self,
            dns: DnsServer,
            ) -> tuple[str, int | None, int | None, int | None, int | None]:
        """Converts the `DnsServer` object into a 5-tuple compatible with
        the database.
        """
        return (
            dns.name,
            None if dns.prim_4 is None else int(dns.prim_4),
            None if dns.secon_4 is None else int(dns.secon_4),
            None if dns.prim_6 is None else int(dns.prim_6),
            None if dns.secon_6 is None else int(dns.secon_6),)
    
    def close(self) -> None:
        """Closes the database."""
        self._conn.close()
    
    def selectDns(self, dns_name: str) -> DnsServer | None:
        sql = """
            SELECT
                name, prim_4, secon_4, prim_6, secon_6
            FROM
                dns_servers
            WHERE
                name = ?;
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, (dns_name,))
        res = cur.fetchone()
        if res is None:
            return None
        return self._tupleToDns(res)
    
    def selctAllDnses(self) -> list[DnsServer]:
        sql = """
            SELECT
                id, name, prim_4, secon_4, prim_6, secon_6
            FROM
                dns_servers
            ORDER BY
                id;
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql)
        dnses = [
            self._tupleToDns(tplDns[1:])
            for tplDns in cur.fetchall()]
        return dnses
    
    def insertDns(self, dns: DnsServer) -> None:
        sql = """
            INSERT INTO
                dns_servers(name, prim_4, secon_4, prim_6, secon_6)
            VALUES
                (?, ?, ?, ?, ?);
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, self._dnsToTuple(dns))
        self._conn.commit()
    
    def deleteDns(self, dns_spec: int | str) -> None:
        match dns_spec:
            case int():
                specifier = 'id'
            case str():
                specifier = 'name'
            case _:
                raise TypeError(f"'dns_spec' must be either 'int' or 'str'")
        sql = """
            DELETE FROM
                dns_servers
            WHERE
                {} = ?;
        """.format(specifier)
        cur = self._conn.cursor()
        cur = cur.execute(sql, (dns_spec,))
        self._conn.commit()
    
    def updateDns(self, old_name: str, new_dns: DnsServer) -> None:
        sql = """
            UPDATE
                dns_servers
            SET
                name = ?, prim_4 = ?, secon_4 = ?, prim_6 = ?, secon_6 = ?
            WHERE
                name = ?;
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, (*self._dnsToTuple(new_dns), old_name,))
        self._conn.commit()

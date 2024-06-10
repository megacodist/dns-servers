#
# 
#

from os import PathLike
import sqlite3
from typing import MutableSequence

from db import DnsServer

from . import DnsServer, IDatabase, IPv4Address


class SqliteDb(IDatabase):
    def __init__(self, db_file: PathLike) -> None:
        """Initializes a new database instance from the provided path."""
        self._conn = sqlite3.connect(db_file, check_same_thread=False)
        """The connection object of the database."""
    
    def close(self) -> None:
        """Closes the database."""
        self._conn.close()
    
    def selectDns(self, dns_name: str) -> DnsServer | None:
        sql = """
            SELECT
                name, primary_, secondary
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
        return DnsServer(
            res[0],
            res[1],
            res[2],)
    
    def selctAllDnses(self) -> MutableSequence[DnsServer]:
        sql = """
            SELECT
                name, primary_, secondary
            FROM
                dns_servers;
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql)
        dnses = [
            DnsServer(
                tplDns[0],
                IPv4Address(tplDns[1]),
                None if tplDns[2] is None else IPv4Address(tplDns[2]))
            for tplDns in cur.fetchall()]
        return dnses
    
    def insertDns(self, dns: DnsServer) -> None:
        sql = """
            INSERT INTO
                dns_servers(name, primary_, secondary)
            VALUES
                (?, ?, ?)
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, self._dnsToTuple(dns))
        self._conn.commit()
    
    def deleteDns(self, dns_name: str) -> None:
        sql = """
            DELETE FROM
                dns_servers
            WHERE
                name = ?
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, (dns_name,))
        self._conn.commit()
    
    def updateDns(self, dns_name: str, new_dns: DnsServer) -> None:
        sql = """
            UPDATE
                dns_servers
            SET
                name = ?, primary_ = ?, secondary = ?
            WHERE
                name = ?
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, (*self._dnsToTuple(new_dns), dns_name,))
        self._conn.commit()

    def _dnsToTuple(self, dns: DnsServer) -> tuple[str, int, int | None]:
        """Converts the `DnsServer` object into a 3-tuple compatible with
        the database.
        """
        return (
            dns.name,
            int(dns.primary),
            int(dns.secondary) if dns.secondary else None)

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
        cur = cur.execute(
            sql,
            (
                dns.name,
                int(dns.primary),
                int(dns.secondary) if dns.secondary else None))
        self._conn.commit()

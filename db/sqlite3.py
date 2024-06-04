#
# 
#

from os import PathLike
import sqlite3

from db import DnsServer

from . import DnsServer, IDatabase


class SqliteDb(IDatabase):
    def __init__(self, db_file: PathLike) -> None:
        """Initializes a new database instance from the provided path."""
        self._conn = sqlite3.connect(db_file)
        """The connection object of the database."""
    
    def close(self) -> None:
        """Closes the database."""
        self._conn.close()
    
    def selectDns(self, dns_name: str) -> DnsServer | None:
        sql = """
            SELECT
                name, primary, secondary
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

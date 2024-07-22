#
# 
#

from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
from pathlib import Path
from db.sqlite3 import SqliteDb

sqliteDb = SqliteDb(Path('db.db3'))
dnses = sqliteDb.selctAllDnses()
sqliteDb.close()
allIps = set[IPv4 | IPv6]()
for dns in dnses:
    ips = dns.toSet()
    for ip in ips:
        if ip not in allIps:
            allIps.add(ip)
        else:
            print(f'Duplicate IP: {ip}')

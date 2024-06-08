#
# 
#


from collections import namedtuple
from typing import MutableSequence


def Foo(a: MutableSequence) -> None:
    a


def main() -> None:
    import sqlite3
    conn = sqlite3.connect(r'D:\Mohsen\Programming\Python\dns-servers\db.db3')
    sql = """
        SELECT
            name, primary_, secondary
        FROM
            dns_servers;
    """
    cur = conn.cursor()
    cur = cur.execute(sql)
    print(cur.fetchall())


if __name__ == '__main__':
    main()

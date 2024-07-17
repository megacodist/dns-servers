#
# 
#

import sqlite3

srcConn = sqlite3.connect('db.db3')
desConn = sqlite3.connect('new.db3')
#
srcQuery = """
    SELECT
        id, name, prim_4, secon_4, prim_6, secon_6
    FROM
        dns_servers
    ORDER BY
        id;
"""
desQuery = """
    INSERT INTO
        dns_servers(id, name, prim_4, secon_4, prim_6, secon_6)
    VALUES
        (?, ?, ?, ?, ?, ?);
"""
#
srcCur = srcConn.cursor()
desCur = desConn.cursor()
srcCur.execute(srcQuery)
for record in srcCur.fetchall():
    desCur.execute(desQuery, record)
srcCur.close()
desCur.close()
srcConn.commit()
desConn.commit()
srcConn.close()
desConn.close()

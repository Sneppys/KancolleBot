import sqlite3

def table_exists(conn, table_name):
    query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='%s';" % (table_name)
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()[0][0] == 1

def copy_table(conn, original_table, new_table_name):
    query = "SELECT sql FROM sqlite_master WHERE type='table' AND name='%s'" % original_table
    cur = conn.cursor()
    cur.execute(query)
    create_statement = cur.fetchall()[0][0]
    cur.close()

    new_statement = create_statement.replace(original_table, new_table_name)
    cur = conn.cursor()
    cur.execute(new_statement)
    cur.close()

    query = "INSERT INTO %s SELECT * FROM %s" % (new_table_name, original_table)
    cur = conn.cursor()
    cur.execute(query)
    cur.close()

    conn.commit()

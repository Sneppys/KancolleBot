import sqlite3

def table_exists(conn, table_name):
    query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?;"
    args = (table_name,)
    cur = conn.cursor()
    cur.execute(query, args)
    return cur.fetchone()[0] == 1

def copy_table(conn, original_table, new_table_name):
    query = "SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
    args = (original_table,)
    cur = conn.cursor()
    cur.execute(query, args)
    create_statement = cur.fetchone()[0]
    cur.close()

    new_statement = create_statement.replace(original_table, new_table_name)
    cur = conn.cursor()
    cur.execute(new_statement)
    cur.close()

    query = "INSERT INTO ? SELECT * FROM ?"
    args = (new_table_name, original_table)
    cur = conn.cursor()
    cur.execute(query, args)
    cur.close()

    conn.commit()

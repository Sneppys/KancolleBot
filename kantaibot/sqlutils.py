"""Miscellaneous utilities for SQLite."""


def table_exists(conn, table_name):
    """Return true if a table with the given name exists."""
    query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?"
    args = (table_name,)
    cur = conn.cursor()
    cur.execute(query, args)
    return cur.fetchone()[0] == 1


def copy_table(conn, original_table, new_table_name):
    """Copy a table to a new table with the given name."""
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

    query = "INSERT INTO %s SELECT * FROM %s" \
        % (new_table_name, original_table)
    cur = conn.cursor()
    cur.execute(query)
    cur.close()

    conn.commit()

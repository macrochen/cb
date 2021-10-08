import sqlite3

from prettytable import PrettyTable


def from_db(cursor, field_names, rows, **kwargs):
    if cursor.description:
        table = PrettyTable(**kwargs)
        table.field_names = [col[0] for col in cursor.description]
        if field_names is not None:
            table.field_names.extend(field_names)
        if rows is None:
            rows = cursor.fetchall()
        for row in rows:
            table.add_row(row)
        return table


def get_record(table, row):
    return dict(zip(table._field_names, row))


def get_dict_row(cursor, row):
    if cursor.description:
        field_names = [col[0] for col in cursor.description]
        return dict(zip(field_names, row))

    raise Exception('not convert to dict row')

def get_connect():
    return sqlite3.connect('db/cb.db3')
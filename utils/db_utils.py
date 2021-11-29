import os
import sqlite3

from prettytable import PrettyTable

from config import db_file_path, basedir, db_daily_file_path
from models import db


def from_db(cursor, ext_field_names=None, rows=None, **kwargs):
    if cursor.description:
        table = PrettyTable(**kwargs)
        table.field_names = [col[0] for col in cursor.description]
        if ext_field_names is not None:
            table.field_names.extend(ext_field_names)
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


local_con = {}


def get_db_file():
    return os.path.join(basedir, db_file_path)


def get_db_daily_file():
    return os.path.join(basedir, db_daily_file_path)


def get_connect():
    return sqlite3.connect(get_db_file())


def get_daily_connect():
    return sqlite3.connect(get_db_daily_file())


def get_cursor(sql, params=None):
    result = db.session.execute(sql, params)
    return result.cursor


def execute_sql_with_rowcount(sql, params=None):
    # fixme update这种sql语句不会返回cursor, 直接返回更新数
    result = None
    try:
        result = db.session.execute(sql, params)
        db.session.commit()
    except Exception as e:
        print('execute sql is failure. sql:' + sql + ', params:' + str(params), e)
        db.session.rollback()
        raise e
    # finally:
    #     db.session.close()

    return 0 if result is None else result.rowcount

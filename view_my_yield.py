
import sqlite3

from prettytable import from_db_cursor
from pyecharts.globals import ThemeType

import common

import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']


def draw_my_view():
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    cur = con_file.cursor()
    try:

        html = ''
        htmls = {}

        # 用来画收益曲线图的数据

        cur.execute("""
SELECT
date_string as 时间, 
all_yield as 累积收益率,
day_yield as 日收益率
from invest_yield 
order by date     --limit 2   
        """)

        rows = []
        dict_rows = []

        table = from_db_cursor(cur)

        table_height_style = """"""
        if len(table._rows) > 10:
            table_height_style += """ style="height:500px;width:800px"> """
        else:
            table_height_style += """ style="width:800px"> """

        table_html = table.get_html_string()

        for row in table._rows:
            rows.append(row)
            dict_row = common.get_dict_row(cur, row)
            dict_rows.append(dict_row)

        line_html = common.generate_line_html(dict_rows)

        html = """
            <br/>
            <br/>
            <br/>
            <br/>
                <center>
                    """ + line_html + "<br/>" + """<div class="outer_table"><div class="inner_table" """ + table_height_style + table_html + '</div></div>' + """
                </center>
        """

        con_file.close()

        return '我的可转债收益情况', '<li><a href="/">Home</a></li>', html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


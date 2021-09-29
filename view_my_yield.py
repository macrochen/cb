
import sqlite3

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
 --date
strftime('%Y-%m-%d', datetime(date, 'unixepoch', 'localtime'))
 as 时间, 
all_yield as 收益率
from invest_yield 
order by date     --limit 2   
        """)

        rows = []
        dict_rows = []

        for row in cur.fetchall():
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
                    """ + line_html + """
                </center>
        """

        con_file.close()

        return '我的账户', '<li><a href="/">Home</a></li>', html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


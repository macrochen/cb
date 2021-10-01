
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
all_yield || '%' as 累积收益率,
day_yield || '%' as 我的涨跌,
cb_day_yield || '%' as 等权涨跌,
hs_day_yield || '%' as 沪深300涨跌,
round(my_net_value-1, 2) as 我的净值,
round(cb_net_value-1, 2) as 等权指数净值,
round(hs_net_value-1, 2) as 沪深300净值
from invest_yield 
order by date  desc   --limit 2   
        """)

        # table_html = table.get_html_string()
        table, table_html = common.generate_table(None, cur, html, need_title=False,
                                                  remark_fields_color=['我的涨跌', '等权涨跌', '沪深300涨跌'],
                                                  ignore_fields=['我的净值', '等权指数净值','沪深300净值'],
                                                  htmls=htmls, table_width='800px')

        rows = []
        dict_rows = []
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
                    """ + line_html + "<br/>" + table_html + """
                </center>
        """

        con_file.close()

        return '我的可转债收益情况', '<li><a href="/">Home</a></li>', html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


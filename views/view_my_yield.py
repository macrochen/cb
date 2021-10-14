# import matplotlib.pyplot as plt
#
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
import utils.echarts_html_utils
import utils.table_html_utils
from utils import db_utils
from utils.db_utils import get_cursor
from views import view_utils


def draw_my_view():
    try:

        html = ''
        nav_html_list = {}

        # 用来画收益曲线图的数据

        cur = get_cursor("""
SELECT
date_string as 时间, 
all_yield || '%' as 累积收益率,
day_yield || '%' as 我的,
cb_day_yield || '%' as 可转债指数,
hs_day_yield || '%' as 沪深300,
round(my_net_value-1, 2) as 我的净值,
round(cb_net_value-1, 2) as 可转债指数净值,
round(hs_net_value-1, 2) as 沪深300净值
from invest_yield 
order by date  desc   --limit 2   
        """)

        # table_html = table.get_html_string()
        table, table_html = utils.table_html_utils.generate_table_html_with_data(None, cur, html, need_title=False,
                                                                                 remark_fields_color=['我的', '可转债指数', '沪深300'],
                                                                                 ignore_fields=['我的净值', '可转债指数净值', '沪深300净值'],
                                                                                 nav_html_list=nav_html_list, table_width='800px')

        rows = []
        dict_rows = []
        for row in table._rows:
            rows.append(row)
            dict_row = db_utils.get_dict_row(cur, row)
            dict_rows.append(dict_row)

        line_html = utils.echarts_html_utils.generate_line_html(dict_rows)

        html = """
            <br/>
            <br/>
            <br/>
            <br/>
                <center>
                    """ + line_html + "<br/>" + table_html + """
                </center>
        """

        return '我的可转债收益情况', ''.join(view_utils.build_personal_nav_html_list('/view_my_yield.html')), html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


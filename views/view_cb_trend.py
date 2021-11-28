# import matplotlib.pyplot as plt
#
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
import utils.echarts_html_utils
import utils.table_html_utils
from utils import db_utils
from utils.db_utils import get_cursor


def draw_view():
    try:

        html = ''
        nav_html_list = {}

        # 用来画收益曲线图的数据

        cur = get_cursor("""
SELECT
date, mid_price, avg_premium
from cb_index_history 
order by date  desc   --limit 2   
        """)

        rows = list(cur)
        dict_rows = []
        for row in rows:
            dict_row = db_utils.get_dict_row(cur, row)
            dict_rows.append(dict_row)


        html = """
                <center>
                    """ + utils.echarts_html_utils.generate_line_html2(dict_rows) + """<br/>
                    """ + utils.echarts_html_utils.generate_line_html3(dict_rows) + """
                </center>
        """

        return '可转债整体估值', '<li><a href="/">Home</a></li>', html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


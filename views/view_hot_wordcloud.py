# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
from pyecharts.charts import WordCloud
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

import views.nav_utils
from utils.db_utils import get_cursor
from utils.echarts_html_utils import generate_scatter_html_with_one_table
from utils.html_utils import env
from utils.table_html_utils import generate_table_html_with_data
from views.view_market import generate_strategy_html


# import matplotlib.pyplot as plt


def draw_view(url):
    try:

        sql = """SELECT cb_name_id, cb_hot from changed_bond where cb_hot > 5 order by cb_hot desc limit 1000"""
        cur = get_cursor(sql)
        rows = cur.fetchall()
        words = []
        for row in rows:
            words.append((row[0].replace('转债', ''), row[1]))

        chart = WordCloud(opts.InitOpts(height='1000px', width='1424px', theme=ThemeType.MACARONS,
                                      chart_id='cb_wordcloud'))
        chart.add(series_name="",
                # 添加数据
                data_pair=words,
                # 字间隙
                word_gap=5,
                # 调整字大小范围
                word_size_range=[5, 100],
                # shape="cardioid",
                is_draw_out_of_bound=True,
               rotate_step=1,
                #  选择背景图，也可以不加该参数，使用默认背景
                #  mask_image='购物车.jpg'
             )
        chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title="", title_textstyle_opts=opts.TextStyleOpts(font_size=23)
            ),
            tooltip_opts=opts.TooltipOpts(is_show=True),
        )
        html = """<br/><br/><br/><br/><br/><br/><br/>""" + chart.render_embed('template.html', env)

        return '可转债热度分析', views.nav_utils.build_analysis_nav_html(url), html
    except Exception as e:
        print("processing is failure. ", e)
        raise e


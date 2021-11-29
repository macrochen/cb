# import matplotlib.pyplot as plt
#
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

import utils.echarts_html_utils
import utils.table_html_utils
import views.nav_utils
from utils import db_utils
from utils.db_utils import get_cursor
from utils.html_utils import env


def draw_my_view(url):
    try:

        html = ''
        nav_html_list = {}

        # 用来画收益曲线图的数据

        cur = get_cursor("""
            SELECT
            date_string as 时间, 
            my_today_profit  as 我的实盘日收益,
            my_real_profit  as 我的实盘累积收益,
            my_real_yield || '%' as 我的实盘收益率,
            my_day_yield || '%' as 我的日收益率,
            cb_day_yield || '%' as 可转债指数日收益率,
            hs_day_yield || '%' as 沪深300日收益率,
            round(my_all_yield-1, 2) as 我的累积收益率,
            round(cb_all_yield-1, 2) as 可转债指数累积收益率,
            round(hs_all_yield-1, 2) as 沪深300累积收益率
            from invest_yield 
            order by date  desc   --limit 2   
        """)

        # table_html = table.get_html_string()
        table, table_html = utils.table_html_utils.generate_table_html_with_data(None, cur, html, need_title=False,
                                                                                 remark_fields=['我的日收益率', '可转债指数日收益率', '沪深300日收益率'],
                                                                                 ignore_fields=['我的累积收益率', '可转债指数累积收益率', '沪深300累积收益率'],
                                                                                 nav_html_list=nav_html_list, table_width='800px')

        rows = []
        dict_rows = []
        for row in table._rows:
            rows.append(row)
            dict_row = db_utils.get_dict_row(cur, row)
            dict_rows.append(dict_row)

        line_html = generate_line_html(dict_rows)

        html = """
                <center>
                    """ + line_html + "<br/>" + table_html + """
                </center>
        """

        return '我的可转债收益情况', views.nav_utils.build_personal_nav_html(url), html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


def generate_line_html(rows, select=None):
    # 用散点图展示
    line = Line(opts.InitOpts(height='700px', width='1424px', theme=ThemeType.LIGHT))

    x = []
    y1 = []
    y2 = []
    y3 = []

    for row in rows:
        x.append(row['时间'])
        y1.append(row['我的累积收益率'])
        y2.append(row['可转债指数累积收益率'])
        y3.append(row['沪深300累积收益率'])

    line.add_xaxis(x)

    line.add_yaxis("我的涨跌", y1)
    line.add_yaxis("可转债指数涨跌", y2)
    line.add_yaxis("沪深300涨跌", y3)

    line.set_global_opts(
        title_opts=opts.TitleOpts(title="收益率曲线", pos_left='center', pos_top=-5),
        tooltip_opts=opts.TooltipOpts(
            trigger='axis',
            formatter=JsCode(
                "function (params) {"
                "return '<table style=\"width:150px;\">'+"
                "'<tr ><td style=\"height:20px;background-color:white;border:0px\" colspan=2>'+ params[0].data[0] +'</td></tr>' +"
                "'<tr ><td style=\"height:15px;background-color:white;border:0px;text-align: right;color:'+params[0].color+'\">我的</td><td style=\"height:15px;background-color:white;border:0px\">' + params[0].value[1] + '%</td></tr>' +"
                "'<tr><td style=\"height:15px;background-color:white;border:0px;text-align: right;color:'+params[1].color+'\">可转债指数</td><td style=\"height:15px;background-color:white;border:0px\">' + params[1].value[1] + '%</td></tr>' +"
                "'<tr><td style=\"height:15px;background-color:white;border:0px;text-align: right;color:'+params[2].color+'\">沪深300</td><td style=\"height:15px;background-color:white;border:0px\">' + params[2].value[1] + '%</td></tr>' +"
                "'</table>';}"
            )
        ),
        legend_opts=opts.LegendOpts(
            pos_top=20,
            # selected_mode='single'
        ),
        datazoom_opts={'start': 0, 'end': 100},
        toolbox_opts=opts.ToolboxOpts(feature={
            'dataZoom': {},
        }
        ),
        # visualmap_opts=opts.VisualMapOpts(
        #     type_="color", max_=150, min_=20, dimension=1
        # ),
        xaxis_opts=opts.AxisOpts(
            # data=None,
            type_='time',
            name='时间',
            name_gap=30,
            is_scale=True,
            name_location='middle',
            splitline_opts=opts.SplitLineOpts(is_show=False),
            # axislabel_opts=opts.LabelOpts(formatter="{value}"), #echarts.format.formatTime('yy-MM-dd', value*1000)
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        ),
        yaxis_opts=opts.AxisOpts(
            type_='value',
            name='收益率(%)',
            name_rotate=90,
            name_gap=55,
            name_location='middle',
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        )
    )
    line.set_series_opts(
        symbol='none',
        smooth=False,
        label_opts=opts.LabelOpts(is_show=False),
    )
    line_html = line.render_embed('template.html', env)
    return line_html


# import matplotlib.pyplot as plt
#
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

from pyecharts import options as opts
from pyecharts.charts import Line
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

from utils import db_utils
from utils.db_utils import get_cursor
from utils.html_utils import env
from utils.table_html_utils import generate_table_html_with_data


def draw_view():
    try:

        html = ''
        nav_html_list = {}

        # 用来画收益曲线图的数据

        cur = get_cursor("""
            SELECT
            date_string as 时间, 
            strategy_double_low_day_yield || '%' as 双低策略日收益率,
            strategy_high_yield_day_yield || '%' as 高收益率策略日收益率,
            strategy_low_premium_day_yield || '%' as 低溢价率策略日收益率,
            cb_day_yield || '%' as 可转债指数日收益率,
            hs_day_yield || '%' as 沪深300日收益率,
            
            round(cb_all_yield-1.84, 2) as 可转债指数累积收益率,
            round(hs_all_yield-0.06, 2) as 沪深300累积收益率,
            strategy_double_low_all_yield as 双低策略累积收益率,
            strategy_high_yield_all_yield as 高收益率策略累积收益率,
            strategy_low_premium_all_yield as 低溢价率策略累积收益率
            from invest_yield where strategy_double_low_day_yield is not NULL
            order by date  desc   
        """)

        # 日收益率看表格, 累积收益率看折线图
        table, table_html = generate_table_html_with_data(None, cur, html, need_title=False,
             remark_fields=['可转债指数日收益率', '沪深300日收益率', '双低策略日收益率', '高收益率策略日收益率', '低溢价率策略日收益率'],
             ignore_fields=['可转债指数累积收益率', '沪深300累积收益率', '双低策略累积收益率', '高收益率策略累积收益率', '低溢价率策略累积收益率'],
             nav_html_list=nav_html_list, table_width='800px')

        rows = []
        dict_rows = []
        for row in table._rows:
            rows.append(row)
            dict_row = db_utils.get_dict_row(cur, row)
            dict_rows.append(dict_row)

        line_html = generate_line_html(dict_rows)

        html = """
            <br/>
            <br/>
            <br/>
            <br/>
                <center>
                    """ + line_html + "<br/><br/><br/>" + table_html + """
                </center>
        """

        return html

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
    y4 = []
    y5 = []

    for row in rows:
        x.append(row['时间'])
        y1.append(row['双低策略累积收益率'])
        y2.append(row['高收益率策略累积收益率'])
        y3.append(row['低溢价率策略累积收益率'])
        y4.append(row['可转债指数累积收益率'])
        y5.append(row['沪深300累积收益率'])

    line.add_xaxis(x)

    line.add_yaxis("双低策略", y1)
    line.add_yaxis("高收益率策略", y2)
    line.add_yaxis("低溢价率策略", y3)
    line.add_yaxis("可转债指数", y4)
    line.add_yaxis("沪深300", y5)

    line.set_global_opts(
        title_opts=opts.TitleOpts(title="策略组合收益率", subtitle='策略收益率采用加权计算', pos_left='center', pos_top=-5),
        tooltip_opts=opts.TooltipOpts(
            trigger='axis',
            formatter=JsCode(
                "function (params) {"
                "return '<table style=\"width:150px;\">'+"
                "'<tr ><td style=\"height:20px;background-color:white;border:0px\" colspan=2>'+ params[0].data[0] +'</td></tr>' +"
                "'<tr ><td style=\"height:15px;background-color:white;border:0px;text-align: left;color:'+params[0].color+'\">双低策略</td><td style=\"height:15px;background-color:white;border:0px\">' + params[0].value[1] + '%</td></tr>' +"
                "'<tr><td style=\"height:15px;background-color:white;border:0px;text-align: left;color:'+params[1].color+'\">高收益率策略</td><td style=\"height:15px;background-color:white;border:0px\">' + params[1].value[1] + '%</td></tr>' +"
                "'<tr><td style=\"height:15px;background-color:white;border:0px;text-align: left;color:'+params[2].color+'\">低溢价率策略</td><td style=\"height:15px;background-color:white;border:0px\">' + params[2].value[1] + '%</td></tr>' +"
                "'<tr><td style=\"height:15px;background-color:white;border:0px;text-align: left;color:'+params[3].color+'\">可转债指数</td><td style=\"height:15px;background-color:white;border:0px\">' + params[3].value[1] + '%</td></tr>' +"
                "'<tr><td style=\"height:15px;background-color:white;border:0px;text-align: left;color:'+params[4].color+'\">沪深300</td><td style=\"height:15px;background-color:white;border:0px\">' + params[4].value[1] + '%</td></tr>' +"
                "'</table>';}"
            )
        ),
        legend_opts=opts.LegendOpts(
            pos_top=50,
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

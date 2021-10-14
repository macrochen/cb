from random import choice

from pyecharts import options as opts
from pyecharts.charts import Pie, Line, Scatter
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

import utils.trade_utils
from utils import db_utils
from utils.db_utils import get_record
from utils.html_utils import env, default_get_label

colors = [
        "#c23531",
        "#61a0a8",
        "#ca8622",
        "#ef5b9c",
        "#f47920",
        "#2a5caa",
        "#b2d235",
        "#1d953f",
        "#6950a1",
    ]


def generate_pie_html(dict_rows, key, value):
    data = []
    for row in dict_rows:
        data.append([row[key], round(row[value], 2)])

    pie = Pie(init_opts=opts.InitOpts(theme=ThemeType.SHINE))
    pie.add("", data)
    # pie.set_global_opts(title_opts=opts.TitleOpts(title="我的摊大饼策略分布"))
    pie.set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
    pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
    pie_html = pie.render_embed('template.html', env)
    return pie_html


def generate_line_html(rows, select=None):
    # 用散点图展示
    line = Line(opts.InitOpts(height='700px', width='1424px', theme=ThemeType.LIGHT))

    x = []
    y1 = []
    y2 = []
    y3 = []

    for row in rows:
        x.append(row['时间'])
        # y.append([row['累积收益率'], row['日收益率']])
        y1.append(row['我的净值'])
        y2.append(row['可转债指数净值'])
        y3.append(row['沪深300净值'])

    line.add_xaxis(x)

    line.add_yaxis("我的净值", y1)
    line.add_yaxis("可转债指数净值", y2)
    line.add_yaxis("沪深300净值", y3)

    line.set_global_opts(
        title_opts=opts.TitleOpts(title="收益率曲线", pos_left='center', pos_top=-5),
        tooltip_opts=opts.TooltipOpts(
            formatter=JsCode(
                "function (params) {return '累积收益率<br/>' + params.value[1] + '%';}"
                # "function (params) {return '累积收益率:' + params.value[1] + '%' + '<br/>日收益率:' + params.value[2] + '%';}"
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
        # symbol='none',
        smooth=True,
        label_opts=opts.LabelOpts(is_show=False)
    )
    line_html = line.render_embed('template.html', env)
    return line_html


def generate_scatter_html_with_one_table(table, title=None, sub_title='',
                                         draw_figure=True,
                                         field_name='溢价率',
                                         get_label=default_get_label,
                                         label_y='转股溢价率(%)',
                                         use_personal_features=False):
    x = []
    y = []
    point_items = []
    for row in table._rows:
        record = db_utils.get_record(table, row)

        x1 = record['转债价格']
        x.append(x1)
        y1 = record[field_name].replace('%', '')
        amount = 0
        if use_personal_features:
            amount = record.get("持有数量", 0)
            y.append([y1, get_label(record), amount])
        else:
            y.append([y1, get_label(record)])

        if use_personal_features and record.get('hold_id') is not None:
            point_items.append(opts.MarkPointItem(
                coord=[x1, y1],
                symbol_size=amount,
                itemstyle_opts=opts.ItemStyleOpts(
                    opacity=0.2
                )
            ))
        else:
            point_items.append(opts.MarkPointItem(
                coord=[x1, y1],
                itemstyle_opts=opts.ItemStyleOpts(color='#fff', border_color='#000')
            ))

    if draw_figure is False:
        return ''

    return create_scatter(title, sub_title, field_name, label_y, point_items, x, y)


def get_hover_js_code(field_name='溢价率'):
    hover_text = "function (params) {" \
                    "return '价格:' + params.value[0] + '元<br/> " + \
                        field_name + ":' + params.value[1] + '%'+ " \
                        "( params.value[3] == null ? '' : " \
                                     "('<br/>持有数量:' + params.value[3] + '张'));" \
                 "}"
    return JsCode(hover_text)


def create_scatter(title, sub_title, field_name, label_y, point_items, x, y):
    scatter = Scatter(opts.InitOpts(height='700px', width='1424px'))
    scatter.add_xaxis(xaxis_data=x)
    scatter.add_yaxis(
        series_name="",
        y_axis=y,
        color=choice(colors),
        label_opts=opts.LabelOpts(
            position='bottom',
            # distance=20,
            formatter=JsCode(
                "function(params){return params.value[2];}"
            )
        ),
        # tooltip_opts=opts.TooltipOpts(
        #     formatter=JsCode(
        #         "function (params) {" \
        #         "return '价格:' + params.value[0] + '元<br/> " + \
        #         field_name + ":' + params.value[1] + '%'+ " \
        #                      "( params.value[3] == null ? '' : " \
        #                      "('<br/>持有数量:' + params.value[3] + '张'));" \
        #                      "}"
        #     )
        # ),
        markline_opts=opts.MarkLineOpts(
            linestyle_opts=opts.LineStyleOpts(type_='dashed'),
            is_silent=True,
            label_opts=opts.LabelOpts(
                position='end',
                formatter=JsCode(
                    "function(params){return params.data['name'];}"
                )
            ),
            data=[
                opts.MarkLineItem(x=utils.trade_utils.MID_X, name='中位数('+str(utils.trade_utils.MID_X)+'元)'),
                opts.MarkLineItem(y=utils.trade_utils.MID_Y, name='中位数('+str(utils.trade_utils.MID_Y)+'%)'),
            ]
        ),
        markpoint_opts=opts.MarkPointOpts(
            symbol='circle',
            symbol_size=12,
            data=point_items
        )
    )
    if title is not None and title.strip(' ') != '':
        title = "=========" + title + "========="

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title=title, subtitle=sub_title, pos_left='center'),
        tooltip_opts=opts.TooltipOpts(
            formatter=get_hover_js_code(field_name)
        ),
        toolbox_opts=opts.ToolboxOpts(feature={
            'dataZoom': {},
        }
        ),
        xaxis_opts=opts.AxisOpts(
            # data=None,
            type_='value',
            name='转债价格(元)',
            name_gap=30,
            is_scale=True,
            name_location='middle',
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axislabel_opts=opts.LabelOpts(formatter='{value}元'),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        ),
        yaxis_opts=opts.AxisOpts(
            type_='value',
            name=label_y,
            name_rotate=90,
            name_gap=35,
            name_location='middle',
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        ),
    )
    scatter_html = scatter.render_embed('template.html', env)
    return "<br/>" + scatter_html


def generate_scatter_html_with_multi_tables(tables, select=None):
    # 用散点图展示
    scatter = Scatter(opts.InitOpts(height='700px', width='1424px', theme=ThemeType.LIGHT))

    for label, table in tables.items():
        if select is not None and label not in select:
            continue

        x = []
        y = []

        point_items = []
        rows = table._rows
        for row in rows:
            record = get_record(table, row)
            x1 = record['转债价格']
            x.append(x1)
            y1 = record['溢价率'].replace('%', '')*1
            amount = record.get("持有数量", 0)
            y.append([y1, record['名称'].replace('转债', ''), amount])
            point_items.append(opts.MarkPointItem(
                coord=[x1, y1],
                symbol_size=amount,
                itemstyle_opts=opts.ItemStyleOpts(
                    opacity=0.2)
            ))

        scatter.add_xaxis(x)

        scatter.add_yaxis(
            label,
            y,
            label_opts=opts.LabelOpts(
                position='bottom',
                formatter=JsCode(  # 调用js代码设置方法提取参数第2个值和参数第3个值
                    "function(params){return params.value[2];}"
                )
            ),
            # markarea_opts=opts.MarkAreaOpts(
            #     is_silent=True,
            #     itemstyle_opts=opts.ItemStyleOpts(
            #         color='transparent',
            #         border_type='dashed',
            #         border_width=1,
            #     ),
            #     data=[
            #         [
            #             {
            #                 'name': label,
            #                 'xAxis': 'min',
            #                 'yAxis': 'min',
            #             },
            #             {
            #                 'xAxis': 'max',
            #                 'yAxis': 'max'
            #             }
            #         ]
            #
            #     ]
            # ),
            # markpoint_opts=opts.MarkPointOpts(
            #     data=[
            #         {'type': 'max', 'name': 'Max'},
            #         {'type': 'min', 'name': 'Min'}
            #     ]
            # ),
            markpoint_opts=opts.MarkPointOpts(
                symbol='circle',
                data=point_items
            ),
            markline_opts=opts.MarkLineOpts(
                linestyle_opts=opts.LineStyleOpts(type_='dashed'),
                is_silent=True,
                label_opts=opts.LabelOpts(
                    position='end',
                    formatter=JsCode(
                        "function(params){return params.data['name'];}"
                    )
                ),
                data=[
                    opts.MarkLineItem(x=utils.trade_utils.MID_X, name='中位数('+str(utils.trade_utils.MID_X)+'元)'),
                    opts.MarkLineItem(y=utils.trade_utils.MID_Y, name='中位数('+str(utils.trade_utils.MID_Y)+'%)'),
                ]
            )
        )

    # scatter.add_xaxis(x)

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="可转债分布情况", pos_left='center'),
        tooltip_opts=opts.TooltipOpts(
            formatter=get_hover_js_code()
        ),
        legend_opts=opts.LegendOpts(
            pos_bottom=-5,
            # selected_mode='single'
        ),
        toolbox_opts=opts.ToolboxOpts(feature={
            'dataZoom': {},
        }
        ),
        # visualmap_opts=opts.VisualMapOpts(
        #     type_="color", max_=150, min_=20, dimension=1
        # ),
        xaxis_opts=opts.AxisOpts(
            # data=None,
            type_='value',
            name='转债价格(元)',
            name_gap=30,
            is_scale=True,
            name_location='middle',
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axislabel_opts=opts.LabelOpts(formatter='{value}元'),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        ),
        yaxis_opts=opts.AxisOpts(
            type_='value',
            name='转股溢价率(%)',
            name_rotate=90,
            name_gap=35,
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
    # scatter.set_series_opts(emphasis={
    #     'focus': 'series'
    # })
    scatter_html = scatter.render_embed('template.html', env)
    return scatter_html
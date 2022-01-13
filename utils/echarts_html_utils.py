from random import choice

from pyecharts import options as opts
from pyecharts.charts import Pie, Line, Scatter
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

import utils.trade_utils
from utils import db_utils, trade_utils
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


def generate_line_html2(rows, select=None):
    line = Line(opts.InitOpts(height='500px', width='1424px', theme=ThemeType.LIGHT))

    x = []
    y1 = []
    y2 = []

    min_y = 10000
    max_y = 0
    for row in rows:
        x.append(row['date'])
        mid_price = row['mid_price']
        avg_premium = row['avg_premium']
        if mid_price > max_y:
            max_y = mid_price
        elif mid_price < min_y:
            min_y = mid_price

        y1.append(mid_price)
        y2.append(avg_premium)
    delta = max_y - min_y
    interval = round(delta / 5, 2)
    star_up1 = round(min_y + interval * 1, 2)
    star_up2 = round(min_y + interval * 2, 2)
    star_up3 = round(min_y + interval * 3, 2)
    star_up4 = round(min_y + interval * 4, 2)

    line.add_xaxis(x)
    line.extend_axis(yaxis=opts.AxisOpts(
        type_='value',
        name='溢价率平均值(%)',
        name_rotate=90,
        name_gap=55,
        name_location='middle',
        is_scale=True,
        axislabel_opts=opts.LabelOpts(formatter='{value}%'),
        splitline_opts=opts.SplitLineOpts(is_show=False),
        axisline_opts=opts.AxisLineOpts(
            is_on_zero=False,
            symbol=['none', 'arrow']
        )))

    line.add_yaxis("价格中位数", y1, yaxis_index=0)
    line.add_yaxis("溢价率平均值", y2, yaxis_index=1)

    line.set_global_opts(
        title_opts=opts.TitleOpts(title="用价格中位数估值", pos_left='center', pos_top=-5),
        tooltip_opts=opts.TooltipOpts(
            trigger='axis',
        ),
        legend_opts=opts.LegendOpts(
            is_show=True,
            pos_top=20,
            # pos_bottom=-50,
            selected_mode='multiple'
        ),
        datazoom_opts={'start': 0, 'end': 100},
        toolbox_opts=opts.ToolboxOpts(feature={
            'dataZoom': {},
        }
        ),
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
            name='价格中位数(元)',
            name_rotate=90,
            name_gap=55,
            name_location='middle',
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}元'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        ),
        visualmap_opts=opts.VisualMapOpts(is_show=True,
                                          type_='color',
                                          pos_top='50',
                                          pos_left='5',
                                          min_=min_y,
                                          max_=max_y,
                                          is_piecewise=True,
                                          split_number=5,
                                          series_index=0,
                                          pieces=[
                                              {'min': min_y, 'max': star_up1, 'color': '#93CE07', 'label': '★★★★★'},
                                              {'min': star_up1, 'max': star_up2, 'color': '#FBDB0F', 'label': '★★★★'},
                                              {'min': star_up2, 'max': star_up3, 'color': '#FC7D02', 'label': '★★★'},
                                              {'min': star_up3, 'max': star_up4, 'color': '#FD0100', 'label': '★★'},
                                              {'min': star_up4, 'max': max_y, 'color': '#AC3B2A', 'label': '★'},
                                          ]
                                          ),
    )
    line.set_colors(['lightcoral', 'lightskyblue'])
    line.set_series_opts(
        symbol='none',
        smooth=False,
        linestyle_opts=opts.LineStyleOpts(
            width=2,
        ),
        label_opts=opts.LabelOpts(is_show=False),
        markline_opts=opts.MarkLineOpts(
            is_silent=True,
            symbol='none',
            label_opts=opts.LabelOpts(
                position='end',
                is_show=False,
                formatter=JsCode("function (params){return params.name}")
            ),

            linestyle_opts=opts.LineStyleOpts(
                color='#333',
                type_='dashed',
            ),
            data=[
                opts.MarkLineItem(y=min_y, name='0%'),
                opts.MarkLineItem(y=star_up1, name='20%'),
                opts.MarkLineItem(y=star_up2, name='40%'),
                opts.MarkLineItem(y=star_up3, name='60%'),
                opts.MarkLineItem(y=star_up4, name='80%'),
                opts.MarkLineItem(y=max_y, name='100%'),
            ]
        ),

    )
    line_html = line.render_embed('template.html', env)
    return line_html


def generate_line_html3(rows, select=None):
    line = Line(opts.InitOpts(height='500px', width='1424px', theme=ThemeType.LIGHT))

    x = []
    y1 = []
    y2 = []

    min_y = 10000
    max_y = 0
    for row in rows:
        x.append(row['date'])
        mid_price = row['mid_price']
        avg_premium = row['avg_premium']
        double_low = round(mid_price + avg_premium, 2)
        if double_low > max_y:
            max_y = double_low
        elif double_low < min_y:
            min_y = double_low

        y1.append(double_low)
        y2.append(avg_premium)
    delta = max_y - min_y
    interval = round(delta / 5, 2)
    star_up1 = round(min_y + interval * 1, 2)
    star_up2 = round(min_y + interval * 2, 2)
    star_up3 = round(min_y + interval * 3, 2)
    star_up4 = round(min_y + interval * 4, 2)

    line.add_xaxis(x)
    line.extend_axis(yaxis=opts.AxisOpts(
        type_='value',
        name='溢价率平均值(%)',
        name_rotate=90,
        name_gap=55,
        name_location='middle',
        is_scale=True,
        axislabel_opts=opts.LabelOpts(formatter='{value}%'),
        splitline_opts=opts.SplitLineOpts(is_show=False),
        axisline_opts=opts.AxisLineOpts(
            is_on_zero=False,
            symbol=['none', 'arrow']
        )))

    line.add_yaxis("双低值", y1, yaxis_index=0)
    line.add_yaxis("溢价率平均值", y2, yaxis_index=1)

    line.set_global_opts(
        title_opts=opts.TitleOpts(title="用双低值估值", pos_left='center', pos_top=-5),
        tooltip_opts=opts.TooltipOpts(
            trigger='axis',
        ),
        legend_opts=opts.LegendOpts(
            is_show=True,
            pos_top=20,
            # pos_bottom=-50,
            selected_mode='multiple'
        ),
        datazoom_opts={'start': 0, 'end': 100},
        toolbox_opts=opts.ToolboxOpts(feature={
            'dataZoom': {},
        }
        ),
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
            name='双低值',
            name_rotate=90,
            name_gap=55,
            name_location='middle',
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        ),
        visualmap_opts=opts.VisualMapOpts(is_show=True,
                                          type_='color',
                                          pos_top='50',
                                          pos_left='5',
                                          min_=min_y,
                                          max_=max_y,
                                          is_piecewise=True,
                                          split_number=5,
                                          series_index=0,
                                          pieces=[
                                              {'min': min_y, 'max': star_up1, 'color': '#93CE07', 'label': '★★★★★'},
                                              {'min': star_up1, 'max': star_up2, 'color': '#FBDB0F', 'label': '★★★★'},
                                              {'min': star_up2, 'max': star_up3, 'color': '#FC7D02', 'label': '★★★'},
                                              {'min': star_up3, 'max': star_up4, 'color': '#FD0100', 'label': '★★'},
                                              {'min': star_up4, 'max': max_y, 'color': '#AC3B2A', 'label': '★'},
                                          ]
                                          ),
    )
    line.set_colors(['lightcoral', 'lightskyblue'])
    line.set_series_opts(
        symbol='none',
        smooth=False,
        linestyle_opts=opts.LineStyleOpts(
            width=2,
        ),
        label_opts=opts.LabelOpts(is_show=False),
        markline_opts=opts.MarkLineOpts(
            is_silent=True,
            symbol='none',
            label_opts=opts.LabelOpts(
                position='end',
                is_show=False,
                formatter=JsCode("function (params){return params.name}")
            ),

            linestyle_opts=opts.LineStyleOpts(
                color='#333',
                type_='dashed',
            ),
            data=[
                opts.MarkLineItem(y=min_y, name='0%'),
                opts.MarkLineItem(y=star_up1, name='20%'),
                opts.MarkLineItem(y=star_up2, name='40%'),
                opts.MarkLineItem(y=star_up3, name='60%'),
                opts.MarkLineItem(y=star_up4, name='80%'),
                opts.MarkLineItem(y=max_y, name='100%'),
            ]
        ),

    )
    line_html = line.render_embed('template.html', env)
    return line_html


def generate_scatter_html_with_one_table(table, title=None, sub_title='',
                                         draw_figure=True,
                                         field_name='溢价率',
                                         get_label=default_get_label,
                                         label_y='转股溢价率(%)',
                                         use_personal_features=False,
                                         hover_maker=None,
                                         click_maker=None,
                                         hover_content_field=None,
                                         ):
    x = []
    y = []
    point_items = []
    for row in table._rows:
        record = db_utils.get_record(table, row)

        x1 = record['转债价格']
        bond_code = record['bond_code']
        bond_code = trade_utils.rebuild_bond_code(bond_code)
        x.append(x1)
        field_value = record[field_name]
        y1 = float(field_value.replace('%', ''))
        y.append(y1)

        hover_content = None
        if hover_content_field is not None:
            hover_content = record[hover_content_field]

        if use_personal_features and record.get('hold_id') is not None:
            amount = record.get("持有数量", 0)
            point_items.append(opts.MarkPointItem(
                coord=[x1, y1],
                symbol_size=amount,
                itemstyle_opts=opts.ItemStyleOpts(
                    opacity=0.5,
                    border_color='#000',
                    border_width=1,
                ),
                value=[get_label(record), x1, y1, bond_code, amount, hover_content]
            ))
        else:
            point_items.append(opts.MarkPointItem(
                coord=[x1, y1],
                itemstyle_opts=opts.ItemStyleOpts(border_color='#000'),
                value=[get_label(record), x1, y1, bond_code, None, hover_content]
            ))

    if draw_figure is False:
        return ''

    return create_scatter(title, sub_title, field_name, label_y, point_items, x, y,
                          hover_maker=hover_maker, click_maker=click_maker)


def get_hover_js_code(field_name='溢价率'):
    hover_text = "function (params) {" \
                 "return " \
                 "'名称:' + params.data.value[0]+ '<br/>' + " \
                 "'价格:' + params.data.value[1] + '元<br/> " + \
                 field_name + ":' + params.value[2] + '%<br/>'+ " \
                              "( params.data.value[4] == null ? '' : " \
                              "('头寸:' + params.data.value[4] + '张'));" \
                              "}"
    return JsCode(hover_text)


def create_scatter(title, sub_title, field_name, label_y, point_items, x, y, hover_maker=None, click_maker=None):
    chart_id = str(abs(hash(title)))
    scatter = Scatter(opts.InitOpts(
        height='700px',
        width='1424px',
        chart_id=chart_id
    ))
    if click_maker is None:
        click_maker = get_click_js_code

    scatter.add_js_funcs(click_maker(chart_id))
    scatter.add_xaxis(xaxis_data=x)
    show_label = True
    if len(point_items) > 100:
        show_label = False

    scatter.add_yaxis(
        series_name="",
        y_axis=y,
        color=choice(colors),
        label_opts=opts.LabelOpts(
            is_show=False,
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
                opts.MarkLineItem(x=utils.trade_utils.MID_X, name='中位数(' + str(utils.trade_utils.MID_X) + '元)'),
                opts.MarkLineItem(y=utils.trade_utils.MID_Y, name='中位数(' + str(utils.trade_utils.MID_Y) + '%)'),
            ]
        ),
        markpoint_opts=opts.MarkPointOpts(
            symbol='circle',
            symbol_size=12,
            data=point_items,
            label_opts=opts.LabelOpts(
                is_show=show_label,
                position='bottom',
                formatter=JsCode('function(params){return params.value[0]}')
            )
        )
    )
    if title is not None and title.strip(' ') != '':
        title = "=========" + title + "========="
    if hover_maker is None:
        hover_maker = get_hover_js_code

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title=title, subtitle=sub_title, pos_left='center'),
        tooltip_opts=opts.TooltipOpts(
            formatter=hover_maker(field_name),
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


def get_click_js_code(chart_id):
    return 'chart_' + chart_id + """.on('click', function(params){
            // alert(params)
            popWin.showWin("1200","600", params['data']['value'][3]);
        })
    """


def generate_scatter_html_with_multi_tables(tables, title="可转债分布情况", subtitle=None, select=None,
                                            use_personal_features=True, price_field_name='转债价格'):
    chart_id = str(abs(hash(title)))
    scatter = Scatter(opts.InitOpts(
        height='700px',
        width='1424px',
        theme=ThemeType.LIGHT,
        chart_id=chart_id)
    )
    scatter.add_js_funcs(
        'chart_' + chart_id + """.on('click', function(params){
            // alert(params)
            popWin.showWin("1200","600", params['data']['value'][3]);
        })
    """)

    for label, table in tables.items():
        if select is not None and label not in select:
            continue

        x = []
        y = []

        point_items = []
        rows = table._rows
        for row in rows:
            record = get_record(table, row)
            if record['溢价率'] is None:
                continue

            x1 = record[price_field_name]
            x.append(x1)
            y1 = record['溢价率'].replace('%', '') * 1
            amount = record.get("持有数量", 0)
            bond_name = record['名称'].replace('转债', '')
            bond_code = record['bond_code']
            bond_code = trade_utils.rebuild_bond_code(bond_code)
            y.append([y1])

            # todo symbol 轮出:triangle 轮入:diamond
            if use_personal_features and record.get('hold_id') is not None and amount > 0:
                point_items.append(opts.MarkPointItem(
                    coord=[x1, y1],
                    symbol_size=amount,
                    itemstyle_opts=opts.ItemStyleOpts(
                        opacity=0.5,
                        border_color='#000',
                        border_width=1,
                    ),
                    value=[bond_name, x1, y1, bond_code, amount]
                ))
            else:
                point_items.append(opts.MarkPointItem(
                    coord=[x1, y1],
                    # symbol_size=symbol_size,
                    itemstyle_opts=opts.ItemStyleOpts(
                        # color='#fff',
                        # border_color='#000'
                    ),
                    value=[bond_name, x1, y1, bond_code]
                ))

        scatter.add_xaxis(x)

        scatter.add_yaxis(
            label,
            y,
            label_opts=opts.LabelOpts(
                is_show=False
            ),
            markpoint_opts=opts.MarkPointOpts(
                symbol='circle',
                symbol_size=10,
                data=point_items,
                label_opts=opts.LabelOpts(
                    position='bottom',
                    formatter=JsCode('function(params){return params.value[0]}')
                )
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
                    opts.MarkLineItem(x=utils.trade_utils.MID_X, name='中位数(' + str(utils.trade_utils.MID_X) + '元)'),
                    opts.MarkLineItem(y=utils.trade_utils.MID_Y, name='中位数(' + str(utils.trade_utils.MID_Y) + '%)'),
                ]
            )
        )

    # scatter.add_xaxis(x)

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title=title, subtitle=subtitle, pos_left='center'),
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
    scatter_html = scatter.render_embed('template.html', env)
    return scatter_html

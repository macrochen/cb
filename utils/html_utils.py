import os
from random import choice

from jinja2 import Environment, FileSystemLoader
from pyecharts import options as opts
from pyecharts.charts import Pie, Line, Scatter
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

import utils.trade_utils
from utils import db_utils
from utils.db_utils import from_db, get_record
from utils.trade_utils import MID_X, MID_Y

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


default_get_label = lambda row: row['名称'].replace('转债', '')


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


def generate_table_html_with_data(type, cur, html, need_title=True, ext_field_names=None, rows=None,
                                  remark_fields_color=[],
                                  nav_html_list=None,
                                  tables=None,
                                  subtitle='',
                                  ignore_fields=[],
                                  field_links={},
                                  is_login_user=False,
                                  table_width=None
                                  ):

    table = from_db(cur, ext_field_names, rows)

    if table.rowcount == 0:
        return table, html

    if tables is not None:
        tables[type] = table

    add_nav_html(nav_html_list, type)

    title = ''
    title_suffix = ''
    if need_title:
        # 首行加两个换行, 避免被但导航栏遮挡
        title = """
            <div id=\"""" + type + """\">""" + """
                <br><br><center><font size='4'><b> =========""" + type + """=========</b></font></center>""" \
               + ('' if len(subtitle) == 0 else """<center> """ + subtitle + """</center>""") + """<br>"""
        title_suffix = """</div>"""

    return table, html + title + build_table_html(table, remark_fields_color, ignore_fields, is_login_user, field_links, table_width=table_width) + title_suffix


def generate_table_html(type, cur, html, need_title=True, ext_field_names=None, rows=None,
                        remark_fields_color=[],
                        nav_html_list=None,
                        tables=None,
                        subtitle='',
                        ignore_fields=[],
                        field_links={},
                        is_login_user=False):
    table, html = generate_table_html_with_data(type, cur, html, need_title, ext_field_names, rows, remark_fields_color, nav_html_list, tables, subtitle, ignore_fields, field_links, is_login_user)
    return html


def generate_head_tail_html(field, is_login_user, record):
    # 标题增加链接
    # 可转债: http://quote.eastmoney.com/bond/sz128051.html
    # 正股: http://quote.eastmoney.com/sz002741.html
    prefix = ''
    prefix_append = ''
    suffix = ''
    if field == '名称':
        bond_code = record.get('bond_code')
        nid = record['nid']
        stock_code = record['stock_code']
        market = 'sz'
        if bond_code.startswith('11'):
            market = 'sh'
        prefix = "<a target = '_blank' href = 'http://quote.eastmoney.com/bond/" + market + bond_code + ".html'>"

        prefix_append += "</a>&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=detail&a=detail&id=" + str(
            nid) + "'><img src='../static/img/nw.png' alt='宁稳网' title='宁稳网查看转债信息' width='14' height='14' class='site-link'/></a>"

        prefix_append += "&nbsp;<a target='_blank' href='https://www.jisilu.cn/data/convert_bond_detail/" + bond_code + "'><img src='../static/img/jsl.png' alt='集思录' title='集思录查看转债信息' width='14' height='14' class='site-link'/></a>"

        # https://xueqiu.com/S/SH600998
        suffix = "<br/><a target = '_blank' href = 'https://xueqiu.com/S/" + market + bond_code + "'><img src='../static/img/xueqiu.png' alt='雪球' title='雪球查看转债讨论' width='14' height='14' class='next-site-link'/></a>"
        suffix += "&nbsp;<a target='_blank' href='http://quote.eastmoney.com/" + market + stock_code + ".html'><img src='../static/img/eastmoney.png' alt='东方财富' title='东方财富查看正股信息' width='14' height='14' class='next-site-link'/></a> "
        suffix += "<a target='_blank' href='http://doctor.10jqka.com.cn/" + stock_code + "/'><img src='../static/img/ths.png' alt='同花顺' title='同花顺正股诊断' width='14' height='14' class='next-site-link'/></a>"

        # http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=157
        suffix += "&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=" + str(
            nid) + "'><img src='../static/img/trend.png' alt='走势图' title='宁稳网查看转债&正股走势(非会员20次/天)' width='14' height='14' class='next-site-link'/></a>"

        if is_login_user:
            hold_id = record.get('hold_id', None)
            suffix += "&nbsp;<a href='" + default_edit_link_maker(hold_id,
                                                                  bond_code) + "'><img src='../static/img/trade.png' alt='交易' title='交易' width='14' height='14' class='next-site-link'/></a>"
    return prefix, prefix_append, suffix


def add_nav_html(nav_html_list, type):
    if type is not None and nav_html_list is not None:
        nav_html_list.append(get_nav_html(type))


def add_sub_nav_html(htmls, title, s):
    # 增加导航
    nav_html = htmls.get('nav', '')

    nav_html += """
        <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">""" + title + """</a>
            <ul class="dropdown-menu">
              """ + s + """
            </ul>
        </li>
    """
    htmls['nav'] = nav_html


def get_nav_html(type):
    return '<li><a href="#' + type + '">' + type + '</a></li>'


def build_table_html(table, remark_fields_color=[],
                     ignore_fields=[], is_login_user=False,
                     field_links={},
                     table_rows_size=10,
                     table_width=None
                     ):
    options = table._get_options({})
    rows = table._get_rows(options)
    table_height_style_content = ''
    if table_width is not None:
        table_height_style_content = 'width: ' + table_width

    if len(rows) > table_rows_size:
        table_height_style_content = ',height: ' + str(50*10) + 'px' #'style:' + str(50*15) + 'px'

    table_height_style = """style=" """ + table_height_style_content + """ " """

    ignore_fields.extend(['nid', 'id', 'hold_id', 'bond_code', 'stock_code', '持有', '持有成本', 'cb_mov2_id', '_sign'])
    lines = []
    linebreak = "<br>"

    lines.append("<div class='outer_table'>")
    lines.append("<div class='inner_table' " + table_height_style + ">")
    lines.append("<table>")

    # Headers
    lines.append("    <thead>")
    lines.append("        <tr>")

    for field in table._field_names:
        if ignore_fields.count(field) > 0:
            continue

        lines.append(
            "            <th>%s</th>" % field.replace("\n", linebreak)
        )
    lines.append("        </tr>")
    lines.append("    </thead>")

    # Data
    lines.append("    <tbody>")
    # formatted_rows = table._format_rows(rows, options)
    for row in rows:
        lines.append("        <tr>")
        record = get_record(table, row)
        for field, datum in record.items():
            if ignore_fields.count(field) > 0:
                continue

            if datum is not None:
                datum = str(datum)
            else:
                datum = ''

            remark_color = ''
            if remark_fields_color.count(field) > 0:
                if datum.startswith('-'):
                    remark_color = 'class="remarked-down"'
                else:
                    remark_color = 'class="remarked-up"'

            if len(field_links) > 0 and id is not None:
                for key, value in field_links.items():
                    if field == key:
                        datum = value(datum, record)

            prefix, prefix_append, suffix = generate_head_tail_html(field, is_login_user, record)

            lines.append(
                ("            <td " + remark_color + ">" + prefix + "%s" + prefix_append + "" + suffix + "</td>") % datum.replace("\n", linebreak)
                # fixme 重构成函数变量
                .replace('转债标的 ', '')
                .replace('标准普尔 ', '')
                .replace('富时罗素 ', '')
                .replace('上证380 ', '')
                .replace('央视50_ ', '')
                .replace('中证500 ', '')
                .replace('深成500 ', '')
                .replace('融资融券 ', '')
                .replace('上证180_ ', '')
                .replace('HS300_ ', '')
                .replace('MSCI中国 ', '')
                .replace('深股通 ', '')
                .replace('创业板综 ', '')
                .replace('沪股通 ', '')
                )
        lines.append("        </tr>")
    lines.append("    </tbody>")
    lines.append("</table>")
    lines.append("</div>")
    lines.append("</div>")

    return "\n".join(lines)


def default_edit_link_maker(hold_id, bond_code):
    if hold_id is not None:
        return '/sync_trade_data.html/' + str(hold_id) + '/'

    return '/new_sync_trade_data.html/' + bond_code + '/'


env = Environment(
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            loader=FileSystemLoader(
                (
                    os.path.join(os.path.dirname(__file__), "../templates")
                )
            )
        )
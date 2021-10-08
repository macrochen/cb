import os

from jinja2 import Environment, FileSystemLoader
from pyecharts import options as opts
from pyecharts.charts import Pie, Line, Scatter
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

from utils.trade_utils import MID_X, MID_Y
from utils.db_utils import from_db, get_record


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
    line = Line(opts.InitOpts(height='700px', width='1524px', theme=ThemeType.LIGHT))

    x = []
    y1 = []
    y2 = []
    y3 = []

    for row in rows:
        x.append(row['时间'])
        # y.append([row['累积收益率'], row['日收益率']])
        y1.append(row['我的净值'])
        y2.append(row['等权指数净值'])
        y3.append(row['沪深300净值'])

    line.add_xaxis(x)

    line.add_yaxis("我的净值", y1)
    line.add_yaxis("等权指数净值", y2)
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


def generate_scatter_html(tables, select=None):
    # 用散点图展示
    scatter = Scatter(opts.InitOpts(height='700px', width='1624px', theme=ThemeType.LIGHT))

    # x = []
    # y = []

    for label, table in tables.items():
        if select is not None and label not in select:
            continue

        x = []
        y = []

        rows = table._rows
        for row in rows:
            record = get_record(table, row)
            x.append(record['转债价格'])
            y.append([record['溢价率'].replace('%', '')*1, record['名称'].replace('转债', '')])

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
            markline_opts=opts.MarkLineOpts(
                linestyle_opts=opts.LineStyleOpts(type_='dashed'),
                is_silent=True,
                data=[
                    opts.MarkLineItem(x=MID_X, name='转债价格中位数'),
                    opts.MarkLineItem(y=MID_Y, name='转债溢价率中位数'),
                ]
            )
        )

    # scatter.add_xaxis(x)

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="可转债分布情况", pos_left='center'),
        tooltip_opts=opts.TooltipOpts(
            formatter=JsCode(
                "function (params) {return '价格:' + params.value[0] + '元<br/> 溢价率:' + params.value[1] + '%';}"
            )
        ),
        legend_opts=opts.LegendOpts(
            pos_bottom=-8,
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


def generate_table(type, cur, html, need_title=True, field_names=None, rows=None,
                   remark_fields_color=[],
                   htmls={},
                   tables=None,
                   subtitle='',
                   ignore_fields=[],
                   field_links={},
                   is_login_user=False,
                   table_width=None
                   ):

    table = from_db(cur, field_names, rows)

    if len(table._rows) == 0:
        return table, html

    if tables is not None:
        tables[type] = table

    add_nav_html(htmls, type)

    title = ''
    title_suffix = ''
    if need_title:
        # 首行加两个换行, 避免被但导航栏遮挡
        title = """
            <div id=\"""" + type + """\">""" + ('' if len(html) > 0 else '<br/><br/>') + """
                <br><br><center><font size='4'><b> =========我的""" + type + """账户=========</b></font></center>""" \
               + ('' if len(subtitle) == 0 else """<center> """ + subtitle + """</center>""") + """<br>"""
        title_suffix = """</div>"""

    return table, html + title + get_html_string(table, remark_fields_color, ignore_fields, is_login_user, field_links, table_width=table_width) + title_suffix


def generate_table_html(type, cur, html, need_title=True, field_names=None, rows=None,
                        remark_fields_color=[],
                        htmls={},
                        tables=None,
                        subtitle='',
                        ignore_fields=[],
                        field_links={},
                        is_login_user=False):
    table, html = generate_table(type, cur, html, need_title, field_names, rows, remark_fields_color, htmls, tables, subtitle, ignore_fields, field_links, is_login_user)
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


def add_nav_html(htmls, type):
    if type is not None:
        # 增加导航
        nav_html = htmls.get('nav', '')
        nav_html += get_sub_nav_html(type)
        htmls['nav'] = nav_html


def add_nav_html_to_head(htmls, type, prefix_nav = ''):
    # 'nav': '<li><a href="/">Home</a></li>'
    # 增加导航
    nav_html = htmls.get('nav', '')
    nav_html = '<li><a href="/">Home</a></li>' + prefix_nav + get_sub_nav_html(type) + nav_html
    htmls['nav'] = nav_html


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


def get_sub_nav_html(type):
    return '<li><a href="#' + type + '">' + type + '</a></li>'


def get_html_string(table, remark_fields_color=[],
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

    ignore_fields.extend(['nid', 'id', 'hold_id', 'bond_code', 'stock_code', '持有', '持有成本', '持有数量', 'cb_mov2_id'])
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
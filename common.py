#一些公共方法
import os
import sqlite3

from jinja2 import Environment, FileSystemLoader
from prettytable import PrettyTable
from pyecharts.charts import Pie, Bar
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from pyecharts.charts import Scatter, Line
from pyecharts.commons.utils import JsCode

from selenium import webdriver

import re

env = Environment(
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            loader=FileSystemLoader(
                (
                    os.path.join(os.path.dirname(__file__), "templates")
                )
            )
        )
#https://www.jisilu.cn/data/cbnew/cb_index/
#转股价格中位数
MID_X = 124.08
#转股溢价率中位数
MID_Y = 33.4
#到期收益率中位数
MID_YIELD = -3.92

# MID_Y, MID_X, MID_YIELD = get_cb_sum_data()


def calc_yield():
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    cur = con_file.cursor()
    cur.execute("""
SELECT    
	round(sum(round((c.cb_price2_id/(1+c.cb_mov2_id) * c.cb_mov2_id)*h.hold_amount, 2)) /    sum(h.sum_buy-h.sum_sell)*100,2)  as '日收益率',
	round(sum(round(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy, 3)) /sum(h.sum_buy - h.sum_sell) * 100, 2)  as 累积收益率
from hold_bond h , changed_bond c 
where h.bond_code = c.bond_code and hold_owner='me'
        """)

    row = cur.fetchone()
    day_yield = row[0]
    all_yield = row[1]
    return day_yield, all_yield


# 计算可转债中位数
def calc_middle_info():

    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    cur = con_file.cursor()
    cur.execute("""
SELECT mid_price, mid_premium from (
    SELECT  AVG(cb_price2_id) as mid_price, row_number() OVER () as rn
    FROM (SELECT cb_price2_id
          FROM changed_bond
          ORDER BY cb_price2_id
          LIMIT 2 - (SELECT COUNT(*) FROM changed_bond) % 2    -- odd 1, even 2
          OFFSET (SELECT (COUNT(*) - 1) / 2
                  FROM changed_bond))) a
left join(
    SELECT AVG(cb_premium_id) as mid_premium, row_number() OVER () as rn
    FROM (SELECT cb_premium_id
          FROM changed_bond
          ORDER BY cb_premium_id
          LIMIT 2 - (SELECT COUNT(*) FROM changed_bond) % 2    -- odd 1, even 2
          OFFSET (SELECT (COUNT(*) - 1) / 2
                  FROM changed_bond)) ) b			 
on a.rn = b.rn
    
    """)

    row = cur.fetchone()
    MID_X = row[0]
    MID_Y = row[1]
    print('init mid data is successful.MID_X:' + str(MID_X) + ', MID_Y:' + str(MID_Y))

    # for row in rows:

        # if key == 'mid_premium':
        #     MID_Y = value
        # elif key == 'mid_price':
        #     MID_X = value
        # elif key == 'mid_yield':
        #     mid_yield = value
        # else:
        #     raise Exception('unknow key:' + key)

    # return mid_y, mid_x #, mid_yield


def update_cb_sum_data():

    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    driver = webdriver.Chrome()

    driver.implicitly_wait(10)

    url = "https://www.jisilu.cn/data/cbnew/cb_index/"

    # fixme 需要把chromedriver放到/usr/local/bin目录下
    driver.get(url)

    div = driver.find_element_by_id("cb_index")

    s = div.text
    ss = re.findall(r"转股溢价率 (\d+\.?\d*)%", s)
    if len(ss) != 1:
        raise Exception("没有找到转股溢价率中位数:" + s)
    # MID_Y = ss[0]
    result = con_file.execute("""insert into config(key,value,field_name)values
                                    ('mid_premium_rate', ?, 'cb_sum_data')""",
                              (ss[0])
                              )
    if result.rowcount == 0:
        print("not insert mid_premium_rate config:" + ss[0])
    else:
        print("insert mid_premium_rate is successful. count:" + str(result.rowcount))

    ss = re.findall(r"中位数价格 (\d+\.?\d*)", s)
    if len(ss) != 1:
        raise Exception("没有找到转股价格中位数:" + s)
    # MID_X = ss[0]
    result = con_file.execute("""insert into config(key,value,field_name)values
                                    ('mid_price', ?, 'cb_sum_data')""",
                              (ss[0])
                              )
    if result.rowcount == 0:
        print("not insert mid_price config:" + ss[0])
    else:
        print("insert mid_price is successful. count:" + str(result.rowcount))

    ss = re.findall(r"到期收益率 (-?\d+\.?\d*)%", s)
    if len(ss) != 1:
        raise Exception("没有找到到期收益率中位数:" + s)
    # MID_YIELD = ss[0]
    result = con_file.execute("""insert into config(key,value,field_name)values
                                    ('mid_yield_rate', ?, 'cb_sum_data')""",
                              (ss[0])
                              )
    if result.rowcount == 0:
        print("not insert mid_yield_rate config:" + ss[0])
    else:
        print("insert mid_yield_rate is successful. count:" + str(result.rowcount))

    # print("MID_Y = " + MID_Y + ' \nMID_X = ' + MID_X + '\nMID_YIELD = ' + MID_YIELD)

    driver.close()


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
            pos_bottom=5,
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
        return html

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

def from_db(cursor, field_names, rows, **kwargs):
    if cursor.description:
        table = PrettyTable(**kwargs)
        table.field_names = [col[0] for col in cursor.description]
        if field_names is not None:
            table.field_names.extend(field_names)
        if rows is None:
            rows = cursor.fetchall()
        for row in rows:
            table.add_row(row)
        return table


def default_edit_link_maker(hold_id, bond_code):
    if hold_id is not None:
        return '/sync_trade_data.html/' + str(hold_id) + '/'

    return '/new_sync_trade_data.html/' + bond_code + '/'


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


def get_record(table, row):
    return dict(zip(table._field_names, row))


def get_dict_row(cursor, row):
    if cursor.description:
        field_names = [col[0] for col in cursor.description]
        return dict(zip(field_names, row))

    raise Exception('not convert to dict row')


def rebuild_stock_code(stock_code):
    # 沪市A股票买卖的代码是以600、601或603打头, 688创业板
    # 深市A股票买卖的代码是以000打头, 中小板股票代码以002打头, 创业板股票代码以300打头
    if stock_code.startswith('600') or stock_code.startswith('601') or \
            stock_code.startswith('605') or stock_code.startswith('603') or stock_code.startswith('688'):
        stock_code = 'SH' + stock_code
    elif stock_code.startswith('000') or stock_code.startswith('001') or stock_code.startswith(
            '002') or stock_code.startswith('300'):
        stock_code = 'SZ' + stock_code
    else:
        raise Exception("未知股票类型。" + stock_code)
    return stock_code

def rebuild_bond_code(bond_code):
    market = 'sz'
    if bond_code.startswith('11'):
        market = 'sh'
    return market + bond_code

if __name__ == "__main__":
    update_cb_sum_data()
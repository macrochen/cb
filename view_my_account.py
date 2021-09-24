# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

import sqlite3

from pyecharts.globals import ThemeType

import common

import matplotlib.pyplot as plt
from prettytable import PrettyTable

import webbrowser
import os

from pyecharts import options as opts
from pyecharts.charts import Pie

from pyecharts.charts import Scatter
from pyecharts.commons.utils import JsCode

from jinja2 import Environment, FileSystemLoader

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# 单选
select = [
    "银河",
    "财通",
    "华泰",
    "华宝",
    "其他",
]

myCb = {}

def generate_table_html(type, cur, html, need_title = True, ignore_table = False, field_names = None, rows = None,
                        remark_fields_color=[], htmls={}, subtitle=''):
    table = from_db(cur, field_names, rows)

    if len(table._rows) == 0:
        return html

    if ignore_table is False:
        myCb[type] = table

    common.add_nav_html(htmls, type)

    title = ''
    if need_title:
        # 首行加两个换行, 避免被但导航栏遮挡
        return html + """
            <div id=\"""" + type + """\">""" + ('' if len(html) > 0 else '<br/><br/>') + """
                <br><br><center><font size='4'><b> =========我的""" + type + """账户=========</b></font></center>""" \
               + ('' if len(subtitle) == 0 else """<center> """ + subtitle + """</center>""") + """<br>
                
                """ + common.get_html_string(table, remark_fields_color, link_fields={'数量': common.make_link}) + """
            </div>
            """
    else:
        return html + common.get_html_string(table, remark_fields_color, link_fields={'数量': common.make_link})



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


def draw_my_view(need_open_page):
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    cur = con_file.cursor()
    try:

        html = ''
        htmls = {'nav': '<li><a href="/">Home</a></li>'}

        # =========银河=========
        account = '银河'
        html = generate_account_block(account, cur, html, htmls)

        # =========华宝=========
        #fixme 华宝证券的手和张要分开处理(如果是手, 要除以10)
        account = '华宝'
        html = generate_account_block(account, cur, html, htmls, 'case when h.hold_unit = 10 then  h.hold_amount/10 else  h.hold_amount END')

        # =========其他=========
        account = '其他'
        html = generate_account_block(account, cur, html, htmls)

        # 数据汇总

        # 用来画统计图的数据

        cur.execute("""
SELECT account as 账户, 
     
    count(h.bond_code) as 个数, 
    sum(h.hold_amount) as 数量,
    
    round(sum(h.hold_amount * h.hold_price),2) as 投入金额, 
    
    round(sum(round((c.cb_price2_id/(1+c.cb_mov2_id) * c.cb_mov2_id)*h.hold_amount, 2)), 2) as '当日(浮)盈亏金额', 
    round((round(sum(c.cb_price2_id*h.hold_amount)/sum(c.cb_price2_id/(1+c.cb_mov2_id)*h.hold_amount),4)-1)*100,2) || '%' as '当日收益率',
    
    round(sum(round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2)), 2) as '累积(浮)盈亏金额',   
    round(sum(round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2)) /sum(h.hold_amount * c.cb_price2_id) * 100, 2) || '%' as 累积收益率
from hold_bond h , changed_bond c 
where h.bond_code = c.bond_code and h.hold_amount >0 and hold_owner='me' GROUP by account order by 投入金额 DESC        
        """)

        rows = []
        dict_rows = []
        # 增加合计行
        total_money = 0
        total_profit = 0
        total_now_profit = 0
        total_now_profit_rate = 0
        total_amount = 0
        total_num = 0

        money_rows = []
        for row in cur.fetchall():
            rows.append(row)
            dict_row = common.get_dict_row(cur, row)
            dict_rows.append(dict_row)
            money_row = dict_row['投入金额']
            money_rows.append(money_row)
            total_money += money_row
            total_profit += dict_row['累积(浮)盈亏金额']
            total_now_profit += dict_row['当日(浮)盈亏金额']
            total_num += dict_row['个数']
            total_amount += dict_row['个数'] * dict_row['数量']

        money_rows.reverse()
        new_rows = []
        for row in rows:
            money_row = money_rows.pop()
            new_row = row + (str(round(money_row/total_money*100, 2)) + '%',)
            new_rows.append(new_row)

        total_yield = round(total_profit / total_money * 100, 2)
        total_now_yield = round(total_now_profit / total_money * 100, 2)
        new_rows.append(['合计', total_num, total_amount, round(total_money, 2), round(total_now_profit, 2), str(round(total_now_yield, 2))+'%', round(total_profit, 2), str(total_yield) + '%', '100%'])

        data = []
        for row in dict_rows:
            data.append([row['账户'], round(row['投入金额'], 2)])

        pie = Pie(init_opts=opts.InitOpts(theme=ThemeType.SHINE))
        pie.add("", data)
        # pie.set_global_opts(title_opts=opts.TitleOpts(title="我的摊大饼策略分布"))
        pie.set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
        pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
        pie_html = pie.render_embed('template.html', common.env)

        type = "统计"
        sum_html = generate_table_html(type, cur, '', need_title=False, ignore_table=True, field_names=['投入占比'],
                                       remark_fields_color=['当日(浮)盈亏金额', '当日收益率', '累积收益率', '累积(浮)盈亏金额'],
                                       rows=new_rows, htmls={})

        common.add_nav_html(htmls, type)

        # 用柱状图从大到小展示持有可转债涨跌幅情况
        scatter_html = generate_scatter_html()

        html += """
            <br/>
            <div id=\"""" + type + """\">
                <center>
                    """ + scatter_html + pie_html + "<br/>" + sum_html + '<br/>' + """
                </center>
            </div>
        """

        con_file.close()

        return '我的账户', htmls['nav'], html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


def generate_account_block(account, cur, html, htmls, amount_field='h.hold_amount'):
    cur.execute("""
   SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
		--c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
		--h.account as 账户,  
		""" + amount_field + """
		--case when h.hold_unit = 10 then  h.hold_amount/10 else  h.hold_amount END as 数量,
		--h.hold_amount
		 as 数量, 
		h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
		--remain_amount as '余额(亿元)', 
        --round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',
		round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
		--round(bt_yield*100,2) || '%' as 到期收益率, round(cb_price2_id + cb_premium_id * 100,2) as 双低值, 
        --round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
        
        --rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, 
        h.strategy_type as 策略,
		h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    WHERE c.stock_code = s.stock_code and  c.bond_code = h.bond_code 
    and h.hold_owner = 'me' 
    and h.hold_amount != -1
    and h.account = '""" + account + """'
    order by 数量, h.bond_code
        """)
    html = generate_table_html(account, cur, html, htmls=htmls,
                               remark_fields_color=['盈亏', '正股涨跌', '溢价率', '可转债涨跌'])
    return html


def generate_scatter_html():
    # 用散点图展示
    scatter = Scatter(opts.InitOpts(height='700px', width='1624px', theme=ThemeType.LIGHT))

    # x = []
    # y = []

    for label, table in myCb.items():
        if label not in select:
            continue

        x = []
        y = []

        rows = table._rows
        for row in rows:
            record = common.get_record(table, row)
            x.append(record['转债价格'])
            y.append([record['溢价率'].replace('%', '')*1, record['名称'].replace('转债', ''), record['数量']])

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
                    opts.MarkLineItem(x=common.MID_X, name='转债价格中位数'),
                    opts.MarkLineItem(y=common.MID_Y, name='转债溢价率中位数'),
                ]
            )
        )

    # scatter.add_xaxis(x)

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="不同账户可转债分布情况", pos_left='center'),
        tooltip_opts=opts.TooltipOpts(
            formatter=JsCode(
                "function (params) {return '价格:' + params.value[0] + '元<br/> 溢价率:' + params.value[1] + '%<br/> 数量:' + params.value[3];}"
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
    scatter_html = scatter.render_embed('template.html', common.env)
    return scatter_html


if __name__ == "__main__":
    # draw_my_view(True, True)

    common.init_cb_sum_data()

    draw_my_view(True)
    print("processing is successful")
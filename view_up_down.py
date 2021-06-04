# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
import sqlite3

from pyecharts.globals import ThemeType

import cb_jsl
import common

import matplotlib.pyplot as plt
from prettytable import PrettyTable
from prettytable import from_db_cursor

import webbrowser
import os

from pyecharts import options as opts
from pyecharts.charts import Pie, Bar

from pyecharts.charts import Scatter
from pyecharts.commons.utils import JsCode

from jinja2 import Environment, FileSystemLoader

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']


def generate_table_html(type, cur, html, need_title=True, field_names=None, rows=None,
                        color=None, remark_fields_color=[]):
    table = from_db(cur, field_names, rows)

    if len(table._rows) == 0:
        return html

    return html + common.get_html_string(table, remark_fields_color)

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



def draw_view(need_show_figure, need_open_page):
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    cur = con_file.cursor()
    try:

        html = ''

        # =========我的转债涨跌TOP20柱状图=========
        cur.execute("""
select cb_name_id as 名称, round(cb_mov2_id * 100, 2) as 涨跌, cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率
 from (SELECT DISTINCT c. * from changed_bond c, hold_bond h 
 where  c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount > 0 order by cb_mov2_id DESC limit 20)     
UNION  
select cb_name_id as 名称, round(cb_mov2_id * 100, 2) as 涨跌, cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率
 from (SELECT DISTINCT c. * from changed_bond c, hold_bond h 
 where  c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount > 0  order by cb_mov2_id ASC limit 20) 
order by 涨跌 desc
                    """)
        rows = cur.fetchall()
        html += '<br/>' + generate_bar_html(rows, '我持有的可转债涨跌TOP20')

        # =========我的转债涨跌TOP20表格=========

        cur.execute("""
    SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, h.strategy_type as 策略, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', remain_amount as '余额(亿元)', 
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率, round(cb_price2_id + cb_premium_id * 100,2) as 双低值, 
        round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值', rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名, 
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名,
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', rank_roe ||'【' || level_roe || '】' as ROE排名,
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, 
        s.pe||'|' || avg_pe as 'PE(动)|均值', rank_pe ||'【' || level_pe || '】' as PE排名, 
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', rank_pb ||'【' || level_pb || '】' as PB排名,
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        stock_total as 综合评分, trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
    from (select * from (SELECT DISTINCT c. * from changed_bond c, (select * 
            from hold_bond where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
             ) h where  c.bond_code = h.bond_code  order by cb_mov2_id DESC limit 10)     
UNION  
select * from (SELECT DISTINCT c. * from changed_bond c, hold_bond h where  c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount > 0  order by cb_mov2_id ASC limit 10)) c, 
stock_report s, (select * 
            from hold_bond where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
             ) h
    WHERE c.stock_code = s.stock_code and  c.bond_code = h.bond_code 
    order  by cb_mov2_id desc
            """)

        html = generate_table_html("涨跌TOP10", cur, html, need_title=False, remark_fields_color=['策略', '转债价格', '到期收益率', '溢价率', '可转债涨跌'])

        # =========全网可转债涨跌TOP20柱状图=========

        cur.execute("""
        select cb_name_id as 名称, round(cb_mov2_id * 100, 2) as 涨跌, cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率
         from (SELECT DISTINCT c. * from changed_bond c 
          order by cb_mov2_id DESC limit 20)     
        UNION  
        select cb_name_id as 名称, round(cb_mov2_id * 100, 2) as 涨跌, cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率
         from (SELECT DISTINCT c. * from changed_bond c 
           order by cb_mov2_id ASC limit 20) 
        order by 涨跌 desc
                            """)
        rows = cur.fetchall()
        html += '<br/>' + generate_bar_html(rows, '全网可转债涨跌TOP20')

        cur.execute("""
SELECT DISTINCT d.* , e.strategy_type as 策略, case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称,cb_mov2_id, round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, 
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', remain_amount as '余额(亿元)', cb_trade_amount_id as '成交额(百万)', round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值', rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名, 
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名,
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', rank_roe ||'【' || level_roe || '】' as ROE排名,
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比',  
        s.pe||'|' || avg_pe as 'PE(动)|均值', rank_pe ||'【' || level_pe || '】' as PE排名, 
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', rank_pb ||'【' || level_pb || '】' as PB排名,
        net_asset||'|' || avg_net_asset as '净资产|行业均值', rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名,
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        stock_total as 综合评分, trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度

    from (select *
         from (SELECT DISTINCT c. * from changed_bond c 
          order by cb_mov2_id DESC limit 10)     
        UNION  
        select *
         from (SELECT DISTINCT c. * from changed_bond c 
           order by cb_mov2_id ASC limit 10) ) c LEFT join stock_report s on c.stock_code = s.stock_code 
    where c.enforce_get not in ('强赎中') or c.enforce_get is null ) d left join 
        (select id as hold_id, bond_code, hold_price, hold_amount, strategy_type 
            from hold_bond where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
             ) e 
        on d.id = e.bond_code	
        ORDER by cb_mov2_id DESC
                    """)

        html = generate_table_html("全网涨跌TOP10", cur, html, need_title=False, remark_fields_color=['转债价格', '到期收益率', '溢价率', '可转债涨跌'])


        f = open('view/view_up_down.html', 'w')
        s = ("""
    <html>
        <head>
        <meta charset="UTF-8">
        <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/echarts-nightly@5.1.2-dev.20210512/dist/echarts.min.js"></script>
        <title>可转债涨跌数据</title>
            """ +
             common.css_html
             + """
      </head>
      <body>
        """
             + html
             + """
    </body>
    </html>
        """)
        f.write(s)
        f.close()
        filename = 'file:///' + os.getcwd() + '/view/' + 'view_up_down.html'

        if need_open_page:
            webbrowser.open_new_tab(filename)

        con_file.close()


    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


def generate_bar_html(rows, title):
    xx1 = []
    xx2 = []
    yy1 = []
    yy2 = []

    for row in rows:
        if row[1] > 0:
            xx1.append(row[0].replace('转债', ''))
            yy1.append(row[1])
        else:
            xx2.append(row[0].replace('转债', ''))
            yy2.append(row[1])

    max_value = 0
    size = len(yy1)
    for i in range(size):
        if yy1[i] + abs(yy2[i]) > max_value:
            max_value = yy1[i] + abs(yy2[i])

    max_value = round(max_value * 1.1, 2) + 1

    bar = Bar(init_opts=opts.InitOpts(height='700px', width='1424px', theme=ThemeType.SHINE))
    # 底部x轴
    bar.add_xaxis(xx1)
    # 顶部x轴
    bar.extend_axis(
        xaxis_data=xx2,
        xaxis=opts.AxisOpts(
            type_="category",
            position='top',
            axislabel_opts=opts.LabelOpts(
                rotate=-60,
            )
        ),
    )
    # 右侧y轴
    bar.extend_axis(
        yaxis=opts.AxisOpts(
            type_="value",
            position="right",
            name='跌幅(%)',
            name_gap=45,
            name_location='middle',
            min_=-max_value,
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(
                    is_show=True,

                )
            ),
            axislabel_opts=opts.LabelOpts(formatter="{value}%"),
        )
    )
    # 添加涨的柱状图
    bar.add_yaxis("涨", yy1,
                  bar_width=25,
                  category_gap='1%',
                  gap='1%',
                  label_opts=opts.LabelOpts(
                      position="top",
                      formatter=JsCode(
                          "function(x){return x.data +'%';}"
                      )
                  ),
                  )
    # 添加跌的柱状图
    bar.add_yaxis("跌",
                  yy2,
                  bar_width=25,
                  yaxis_index=1,
                  label_opts=opts.LabelOpts(
                      position="bottom",
                      formatter=JsCode(
                          "function(x){return x.data +'%';}"
                      )
                  ),
                  )
    # bar.reversal_axis()
    bar.set_series_opts(
        itemstyle_opts=opts.ItemStyleOpts(
            color=JsCode(
                "function(x){return x.data>0?'#c23531':'#1d953f'}"
            )
        )
    )
    bar.set_global_opts(
        title_opts=opts.TitleOpts(
            title="=========" + title + "=========",
            pos_left='center',
            pos_top='-1px',
        ),
        tooltip_opts=opts.TooltipOpts(
            is_show=False
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(
            # data=None,
            # type_='category',
            # name_gap=0,
            # name_rotate=90,
            axislabel_opts=opts.LabelOpts(
                rotate=-60,
            ),
            is_scale=True,
            name_location='middle',
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=True,
                # symbol=['none', 'arrow']
            )
        ),
        yaxis_opts=opts.AxisOpts(
            type_='value',
            name='涨幅(%)',
            # name_rotate=90,
            name_gap=35,
            name_location='middle',
            # min_=0,
            max_=max_value,
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                # symbol=['none', 'arrow']
            )
        ),
    )

    bar_html = bar.render_embed('template.html', common.env)
    return bar_html


if __name__ == "__main__":
    # 展示之前先更新一下数据
    cb_jsl.fetch_data()
    # draw_my_view(True, True)
    draw_view(False, True)
    print("processing is successful")
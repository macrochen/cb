# 目前市面上各种策略(高收益, 双低, 活性债, 回售)的数据视图展示


# 需导入要用到的库文件
import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
import sqlite3

from pyecharts.charts import Scatter
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

import common

import random
from random import choice

import numpy as np
from prettytable import PrettyTable
from prettytable import from_db_cursor

import webbrowser
import os

# 求各种字段的中位数
# select c.market_cap from (select row_number() over (order by market_cap asc) as num , * from changed_bond) c, (SELECT count(*)/2 as mid from changed_bond) m where c.num = m.mid

config = {'type': [
    '双低策略',
    '高收益策略',
    '回售策略',
    '活性债策略',
    '低余额策略',
    '溢价率折价策略',
    '高收益率策略',
    '广撒网筛选策略',
    # '快到期保本策略',
    '正股优秀策略',
    '自选集',
],
}

use_personal_features = True

default_get_label = lambda row: row['名称'].replace('转债', '')

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

def generate_strategy_html(con_file,
                           sql,
                           type,
                           sub_title,
                           html,
                           midY=common.MID_Y,  # 溢价率(或各种收益率)中位数
                           midX=common.MID_X,  # 转债价格中位数
                           labelY='转债溢价率(%)',
                           field_name='溢价率',
                           get_label=default_get_label,
                           checked='',
                            htmls=None,
                           remark_fields_color = []
                           ):

    cur = con_file.cursor()
    cur.execute(sql)

    table = from_db_cursor(cur)

    x = []
    y = []
    unselects = []
    for row in table._rows:
        record = common.getRecord(table, row)

        x1 = record['转债价格']
        x.append(x1)
        y1 = record[field_name].replace('%', '')
        y.append([y1, get_label(record), record.get("持有成本", 0), record.get("持有数量", 0)])

        if use_personal_features and record.get('持有') is not None and record.get('持有') == '':
            unselects.append(opts.MarkPointItem(
                    coord=[x1, y1],
                    itemstyle_opts=opts.ItemStyleOpts(color='#fff', border_color='#000')
                ))

    if len(x) == 0:
        return html

    scatter_html = genrate_pei_html(field_name, labelY, midX, midY, sub_title, type, unselects, x, y)

    common.add_nav_html(htmls, type)

    html += """
    <div id=\"""" + type + """\">
        """ + scatter_html + common.get_html_string(table, remark_fields_color) + """
    </div>
    """

    return html


def genrate_pei_html(field_name, labelY, midX, midY, sub_title, type, unselects, x, y):
    scatter = Scatter(opts.InitOpts(height='700px', width='1424px'))
    scatter.add_xaxis(xaxis_data=x)
    scatter.add_yaxis(
        series_name="",
        y_axis=y,
        color=choice(colors),
        label_opts=opts.LabelOpts(
            position='bottom',
            formatter=JsCode(
                "function(params){return params.value[2];}"
            )
        ),
        markline_opts=opts.MarkLineOpts(
            linestyle_opts=opts.LineStyleOpts(type_='dashed'),
            is_silent=True,
            data=[
                opts.MarkLineItem(x=midX, name='转债价格中位数'),
                opts.MarkLineItem(y=midY, name='转债溢价率中位数'),
            ]
        ),
        markpoint_opts=opts.MarkPointOpts(
            symbol='circle',
            symbol_size=12,
            data=unselects
        )
    )
    hover_text = ''
    if len(unselects) > 0:
        hover_text = "function (params) {return '价格:' + params.value[0] + '元<br/> " + field_name + ":' + params.value[1] + '%<br/>持有成本:' + params.value[3] + '元<br/>持有数量:' + params.value[4] + '张';}"
    else:
        hover_text = "function (params) {return '价格:' + params.value[0] + '元<br/> " + field_name + ":' + params.value[1] + '%';}"
    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="=========" + type + "=========", subtitle=sub_title, pos_left='center'),
        tooltip_opts=opts.TooltipOpts(
            formatter=JsCode(
                hover_text
            )
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
            name=labelY,
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
    scatter_html = scatter.render_embed('template.html', common.env)
    return "<br/>" + scatter_html


def draw_market_view(need_show_figure, need_open_page):
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    html = ''
    htmls = {}
    try:

        # =========强赎=========
        sql = """
    SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, enforce_get as 强赎状态, 
    cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率
    from (select * from changed_bond where enforce_get in ('强赎中')) c
    order by 转债价格 desc 
            """
        # 加几个换行避免顶部的菜单遮住title
        html = "<br/><br/>" + generate_strategy_html(con_file, sql, "强赎转债", "", html, htmls=htmls)

        # =========回售策略=========
        if "回售策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        cb_price2_id as 转债价格, round(bt_red * 100,2) || '%' as 回售收益率, red_t as '回售年限(年)', round((bt_red * 100) + (2-bond_t1),2) as 性价比,round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)', cb_trade_amount_id as '成交额(百万)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
        where c.stock_code = s.stock_code
         and red_t not in('无权', '回售内')
         and red_t < 1
         and round(bt_red * 100,2) > 1
        --ORDER by 回售年限 ASC, 回售收益率 DESC;
        ORDER by 性价比 DESC) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
             ) e 
        on d.id = e.bond_code
            """
            html = generate_strategy_html(con_file, sql, "回售策略", "回售年限<1年, 回收收益率>1%", html, htmls=htmls,
                                          labelY="回售收益率(%)", field_name='回售收益率', midY=0, checked='checked',
                                          remark_fields_color=['回售年限(年)', '回售收益率', '转债价格', '可转债涨跌'])

        # =========低余额策略=========
        if "低余额策略" in config['type']:
            sql = """
    SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, remain_amount as '余额(亿元)', 
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(bt_yield*100,2) || '%' as 到期收益率, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)', cb_trade_amount_id as '成交额(百万)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度

    from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
    where c.stock_code = s.stock_code
        --and cb_premium_id * 100 < 30 
        and remain_amount < 3 
        and cb_price2_id < 110
        ORDER by remain_amount ASC
        -- limit 50
        ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
             ) e 
        on d.id = e.bond_code            
            """

            get_label = lambda row: row['名称'].replace('转债', '') + '(' + str(row['余额(亿元)']) + ')'

            html = generate_strategy_html(con_file, sql, "低余额策略", "价格<110, 余额<3亿", html, htmls=htmls,
                                          get_label=get_label,
                                          remark_fields_color=['余额(亿元)', '溢价率', '转债价格', '可转债涨跌'])

        # =========双低债=========
        if "双低策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
         
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'

    from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
    where c.stock_code = s.stock_code
        ORDER by 双低值
        limit 20) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
            ) e 
        on d.id = e.bond_code
        
            """
            html = generate_strategy_html(con_file, sql, "双低策略", "双低值前20", html, htmls=htmls,
                                          remark_fields_color=['溢价率', '转债价格', '可转债涨跌', '到期收益率', '双低值'])

        # =========高收益策略=========
        if "高收益策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        cb_price2_id as '转债价格', round(bt_yield*100,2) || '%' as 到期收益率, round(100- cb_price2_id + BT_yield * 100, 2) as 性价比,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
         
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'

        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
    where c.stock_code = s.stock_code
        and c.rating in ('AA+', 'AA-', 'AA', 'AAA', 'A', 'A+')
        --and c.cb_name_id not in( '亚药转债' , '本钢转债','搜特转债','广汇转债')
        AND bt_yield > 0
        and cb_price2_id < 110
        order by 性价比 DESC
        limit  20) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
            ) e 
        on d.id = e.bond_code;
            """

            html = generate_strategy_html(con_file, sql, "高收益策略", "价格<110, 到期收益率前20, 信用A以上", html, htmls=htmls,
                                          labelY="到期收益率(%)", field_name='到期收益率', midY=common.MID_YIELD,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'])

        # =========活性债策略=========
        if "活性债策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'
      
      from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
      where c.stock_code = s.stock_code
      and duration < 3 
      and cb_price2_id > 99 
      and cb_price2_id < 115 
      and roe > 1 
      and s.net > 0
      -- and s.margin > 10
      and cb_t_id = '转股中' 
      -- and 溢价率 < 20 
      and 双低值 < 120
      order by 双低值 ASC) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
            ) e 
          on d.id = e.bond_code
          """
            html = generate_strategy_html(con_file, sql, "活性债策略", "价格在99~115, 净利润为正, ROE>1, 双低值<120, 存续期<3年",
                                          html, htmls=htmls,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '双低值'])

        # =========低溢价率策略=========
        if "溢价率折价策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        round(cb_premium_id*100,2) || '%' as 溢价率, cb_price2_id as '转债价格', cb_t_id as 距离转股日,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'
      
      from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
      where c.stock_code = s.stock_code
      and cb_premium_id < 0 
      -- and cb_price2_id > 99 
      -- and cb_price2_id < 115 
      -- and roe > 1 
      -- and s.net > 0
      -- and s.margin > 10
      -- and cb_t_id = '转股中' 
      -- and 溢价率 < 20 
      -- and 双低值 < 120
      order by cb_premium_id) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
            ) e 
          on d.id = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "溢价率折价策略", "溢价率为负", html, htmls=htmls,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'])

        # =========高收益率策略=========
        if "高收益率策略" in config['type']:
            sql = """
    SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
    FROM (
    SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, round(bt_yield*100,2) || '%' as 到期收益率, cb_price2_id as '转债价格', 
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', round(cb_premium_id*100,2) || '%' as 溢价率, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'
    
    from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
    where c.stock_code = s.stock_code
    -- and duration < 3 
    -- and cb_price2_id > 99 
    -- and cb_price2_id < 115 
    -- and roe > 1 
    -- and s.net > 0
    -- and s.margin > 10
    -- and cb_t_id = '转股中' 
    -- and 溢价率 < 20 
    -- and 双低值 < 120
    order by bt_yield desc limit 10) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
            ) e 
      on d.id = e.bond_code
          """
            html = generate_strategy_html(con_file, sql, "高收益率策略", "高收益率top5", html, htmls=htmls,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'])

        # =========快到期保本策略=========
        if "快到期保本策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        round(bt_yield*100,2) || '%' as 到期收益率, bond_t1 as 剩余年限,
        
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, c.stock_pb as 市净率, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'
  
      from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
      where c.stock_code = s.stock_code
      and bt_yield > 0
      and bond_t1 < 2.5
      -- and duration < 3 
      -- and cb_price2_id > 99 
      --and cb_price2_id < 105 
      --and stock_pb > 1 
      -- and s.net > 0
      -- and s.margin > 10
      -- and cb_t_id = '转股中' 
      --and cb_premium_id*100 < 20 
      -- and 双低值 < 120
      order by (2.5-bond_t1) + bt_yield * 100 desc limit 5) d left join
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
            ) e 
          on d.id = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "快到期保本策略", "收益率>0, 剩余年限<3", html, htmls=htmls,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '剩余年限'])

        # =========广撒网筛选策略=========
        if "广撒网筛选策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'
    
      from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
      where c.stock_code = s.stock_code
      -- and duration < 3 
      -- and cb_price2_id > 99 
      and cb_price2_id < 105 
      and stock_pb > 1 
      -- and s.net > 0
      -- and s.margin > 10
      -- and cb_t_id = '转股中' 
      and cb_premium_id*100 < 20 
      -- and 双低值 < 120
      order by bt_yield desc) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
             ) e 
        on d.id = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "广撒网筛选策略", "价格<105, 溢价率<20%, pb>1", html, htmls=htmls,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'])

        # =========正股优秀策略=========
        if "正股优秀策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有, e.hold_price as 持有成本, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'
    
      from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s
      where c.stock_code = s.stock_code
      -- and duration < 3 
      -- and cb_price2_id > 99 
      -- and cb_price2_id < 105 
      -- and stock_pb > 1 
      -- and s.net > 0
      -- and s.margin > 10
      -- and cb_t_id = '转股中' 
      -- and cb_premium_id*100 < 20 
      and 双低值 < 130
      and stock_total >= 6
      -- and cb_price2_id < 115
      -- order by stock_total desc
      -- and fact_base > 6
      and cb_price2_id < 115
      order by fact_base desc
      ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount != -1 group by bond_code) ) 
             ) e 
        on d.id = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "正股优秀策略", "正股综合评分>6, 转债价格<115, 双低值<130", html, htmls=htmls,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'])

        # =========自选集=========
        if "自选集" in config['type']:
            sql = """
      SELECT c.data_id as nid, c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        rank_gross_rate ||'【' || level_gross_rate || '】' as 毛利率排名,rank_net_margin ||'【' || level_net_margin || '】' as 净利润排名,
        rank_net_profit_ratio ||'【' || level_net_profit_ratio || '】'  as 利润率排名, rank_roe ||'【' || level_roe || '】' as ROE排名,
        rank_pe ||'【' || level_pe || '】' as PE排名, rank_pb ||'【' || level_pb || '】' as PB排名,
        rank_net_asset ||'【' || level_net_asset || '】' as 净资产排名, rank_market_cap ||'【' || level_market_cap || '】' as 市值排名,
        stock_total as 综合评分, 
        
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比',
        gross_rate||'|' || avg_gross_rate as '毛利率|行业均值',  
        round(s.net,2)||'|' || avg_net_margin as '净利润|均值(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin ||'|' || avg_net_profit_ratio as '利润率|行业均值', s.yoy_margin_rate || '%' as '利润率同比', 
        s.roe ||'|' || avg_roe as 'ROE|行业均值', s.yoy_roe_rate || '%' as 'ROE同比', 
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', 
        s.pe||'|' || avg_pe as 'PE(动)|均值',  
        c.stock_pb||'|' || avg_pb as 'PB|行业均值', 
        net_asset||'|' || avg_net_asset as '净资产|行业均值', 
        market_cap||'|' || avg_market_cap as '市值|均值(亿元)', 
        remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)'
    
      from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, hold_bond h
      where c.stock_code = s.stock_code and c.bond_code = h.bond_code
      and hold_owner = 'me' and hold_amount != -1
      and h.strategy_type = '自选'"""
            html = generate_strategy_html(con_file, sql, "自选集", "收集近期大V们推荐", html, htmls=htmls,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'])

        con_file.close()

        f = open('view/view_market.html', 'w')
        s = ("""
        <html>
        <head>
        <meta charset="UTF-8">
        
        <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/echarts-nightly@5.1.2-dev.20210512/dist/echarts.min.js"></script>
        
        <link rel="stylesheet" href="https://www.jq22.com/jquery/bootstrap-3.3.4.css">
        <script src="https://www.jq22.com/jquery/1.11.1/jquery.min.js"></script>
        
        <script src="https://www.jq22.com/jquery/bootstrap-3.3.4.js"></script>
        <script src="https://www.jq22.com/demo/bootstrap-autohidingnavbar-master/src/jquery.bootstrap-autohidingnavbar.js"></script>
        <title>市场策略</title>
            """ +
             common.css_html
             + """
          
        </head>
        <body>
            <div class="navbar navbar-default navbar-fixed-top" role="navigation">
                <div class="container">
                    <ul class="nav navbar-nav">
                        """ + htmls['nav'] + """
                    </ul>
                </div>
            </div>
            <div class="container">
            """
             + html
             + """
             </div>
             <script>
                let lis = document.querySelectorAll('.nav>li')
                console.log(lis)
                for (var i = 0; i < lis.length; i++) {
                    lis[i].onclick = function(event) {
                        let li = document.getElementsByClassName('active')[0]
                        li.classList.remove('active')
                        this.classList.add('active')
                    }
                }
                $("div.navbar-fixed-top").autoHidingNavbar();
            </script>
        </body>
        </html>
            """)
        f.write(s)
        f.close()
        filename = 'file:///' + os.getcwd() + '/view/' + 'view_market.html'

        if need_open_page:
            webbrowser.open_new_tab(filename)

    except Exception as e:
        con_file.close()
        print("processing is failure. " + str(e), e)
        raise e

if __name__ == "__main__":
    draw_market_view(False, True)
    print("processing is successful")

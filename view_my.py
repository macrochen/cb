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
    "高收益",
    "回售",
    "双低",
    "双低轮动",
    "多因子",
    "低余额",
    # "每周精选",
    "网格",
    '打新',
    "活性债",
    "基本面",
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
                <br><center><font size='4'><b> =========我的""" + type + """策略=========</b></font></center>""" \
               + ('' if len(subtitle) == 0 else """<center> """ + subtitle + """</center>""") + """<br>
                
                """ + common.get_html_string(table, remark_fields_color, link_fields={'成本(量)': common.make_link}) + """
            </div>
            """
    else:
        return html + common.get_html_string(table, remark_fields_color, link_fields={'成本(量)': common.make_link})



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

        # =========我的强赎=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, enforce_get as 强赎状态, round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
    h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, h.account as 账户, h.memo as 备注
    from (select * from changed_bond where enforce_get in ('强赎中')) c, hold_bond h
    WHERE c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount != -1
    order by 转债价格 desc 
            """)

        html = generate_table_html("强赎", cur, html, htmls=htmls)

        # =========我的回售=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', 
        cb_price2_id as 转债价格, round(bt_red * 100,2) as 回售收益率, red_t as 回售年限,  
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        round(cb_premium_id*100,2) || '%' as 溢价率, 
        
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    WHERE c.stock_code = s.stock_code and  c.bond_code = h.bond_code AND h.strategy_type = '回售' and h.hold_owner = 'me' and h.hold_amount != -1
    order by 回售收益率
            """)

        html = generate_table_html("回售", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '回售年限', '回售收益率'], htmls=htmls)

        # =========我的低余额策略=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', remain_amount as '余额(亿元)', 
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率, round(cb_price2_id + cb_premium_id * 100,2) as 双低值, 
        round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
        
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
        cb_trade_amount_id as '成交额(百万)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    WHERE c.stock_code = s.stock_code and  c.bond_code = h.bond_code 
    AND h.strategy_type = '低余额' 
    and h.hold_owner = 'me' 
    and h.hold_amount != -1
    order by 转债价格
            """)

        html = generate_table_html("低余额", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '正股涨跌'], htmls=htmls)

        # =========我的低价高收益策略=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', 
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率, round(100- cb_price2_id + BT_yield * 100, 2) as 性价比,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
        
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    WHERE c.stock_code = s.stock_code and  c.bond_code = h.bond_code AND h.strategy_type = '高收益' and h.hold_owner = 'me' and h.hold_amount != -1
    ORDER by 性价比 desc
            """)

        html = generate_table_html("高收益", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率'], htmls=htmls)

        # =========我的双低策略=========
        cur.execute("""
        SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
            round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
            round(cb_price2_id + cb_premium_id * 100,2) as 双低值, round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
            round(bt_yield*100,2) || '%' as 到期收益率,round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', 

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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
        from changed_bond c, stock_report s, hold_bond h
        WHERE c.stock_code = s.stock_code and c.bond_code = h.bond_code AND h.strategy_type = '双低' and h.hold_owner = 'me' and h.hold_amount != -1
        order by 双低值
                """)

        html = generate_table_html("双低", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)

        # =========我的双低轮动策略=========
        cur.execute("""
        SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
            round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
            round(cb_price2_id + cb_premium_id * 100,2) as 双低值,round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
            round(bt_yield*100,2) || '%' as 到期收益率, round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', 

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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
        from changed_bond c, stock_report s, hold_bond h
        WHERE c.stock_code = s.stock_code and c.bond_code = h.bond_code AND h.strategy_type = '双低轮动' and h.hold_owner = 'me' and h.hold_amount != -1
        order by 双低值
                """)

        html = generate_table_html("双低轮动", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)

        # =========我的多因子策略=========
        cur.execute("""
        SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
            round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率,
            round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
            round(cb_price2_id + cb_premium_id * 100,2) as 双低值, 
            round(bt_yield*100,2) || '%' as 到期收益率,round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', 

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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
        from changed_bond c, stock_report s, hold_bond h
        WHERE c.stock_code = s.stock_code and c.bond_code = h.bond_code AND h.strategy_type = '多因子' and h.hold_owner = 'me' and h.hold_amount != -1
        order by 双低值
                """)

        html = generate_table_html("多因子", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率'], htmls=htmls)

        # =========我的打新策略=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
        h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
        round(cb_price2_id + cb_premium_id * 100,2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
        
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    WHERE c.stock_code = s.stock_code and c.bond_code = h.bond_code AND h.strategy_type = '打新' and h.hold_owner = 'me' and h.hold_amount != -1
    order by 转债价格
            """)

        html = generate_table_html("打新", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)

        # =========我的网格策略=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
        h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率, 
        round(cb_price2_id + cb_premium_id * 100,2) as 双低值, 
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    WHERE c.stock_code = s.stock_code and c.bond_code = h.bond_code AND h.strategy_type = '网格' and h.hold_owner = 'me' and h.hold_amount != -1
    order by 转债价格
            """)

        html = generate_table_html("网格", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)

        # =========我的基本面策略=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', 
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度,
        h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    where c.stock_code = s.stock_code and c.bond_code = h.bond_code
     AND h.strategy_type = '基本面' and h.hold_owner = 'me' and h.hold_amount != -1
    order by 转债价格
        """)

        html = generate_table_html("基本面", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)

        # =========我的每周精选策略=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, 
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        rating as '信用', duration as 续存期, round(bt_yield*100,2) || '%' as 到期收益率,
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as '市盈率(动)', c.stock_pb as 市净率,
        market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
        cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
        from changed_bond c, stock_report s, hold_bond h
    	where c.stock_code = s.stock_code and c.bond_code = h.bond_code 
    	AND h.strategy_type = '每周精选' and h.hold_owner = 'me' and h.hold_amount != -1
    order by 转债价格
            """)

        html = generate_table_html("每周精选", cur, html, htmls=htmls)

        # =========我的活性债策略=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度,
        h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    where c.stock_code = s.stock_code and c.bond_code = h.bond_code
    AND h.strategy_type = '活性债' and h.hold_owner = 'me' and h.hold_amount != -1 
    --and h.hold_owner = '水晶杯'
    order by 转债价格
            """)

        html = generate_table_html("活性债", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)

        # =========其他=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度,
        h.account as 账户, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    where c.stock_code = s.stock_code and c.bond_code = h.bond_code 
    AND h.strategy_type = '其他' and h.hold_owner = 'me' and h.hold_amount != -1
order by 双低值
        """)

        html = generate_table_html("其他", cur, html,
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)
        # =========清仓建议=========
        cur.execute("""
    SELECT h.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        round(bt_yield*100,2) || '%' as 到期收益率, round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',
        
        h.account as 账户, h.strategy_type as 策略, h.memo as 备注
    from changed_bond c, stock_report s, hold_bond h
    where c.stock_code = s.stock_code and c.bond_code = h.bond_code 
        AND (
        cb_price2_id < 100 and cb_premium_id > 0.9 	
        or cb_price2_id > 130 
        or cb_price2_id > 100 and cb_price2_id < 110 and cb_premium_id > 0.6
        )
        and h.hold_owner = 'me' and h.hold_amount != -1
    order by cb_price2_id
        """)

        html = generate_table_html("清仓建议", cur, html,
                                   subtitle='(价格<100且溢价率>90%或100<价格<110且溢价率>60%或价格>130)',
                                   remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'], htmls=htmls)

        # 数据汇总

        # 用来画统计图的数据

        cur.execute("""
SELECT strategy_type as 策略, 
     
    count(h.bond_code) as 个数, 
    sum(h.hold_amount) as 数量,
    
    round(sum(h.hold_amount * h.hold_price),2) as 投入金额, 
    
    round(sum(round((c.cb_price2_id/(1+c.cb_mov2_id) * c.cb_mov2_id)*h.hold_amount, 2)), 2) as '当日(浮)盈亏金额', 
    round((round(sum(c.cb_price2_id*h.hold_amount)/sum(c.cb_price2_id/(1+c.cb_mov2_id)*h.hold_amount),4)-1)*100,2) || '%' as '当日收益率',
    
    round(sum(round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2)), 2) as '累积(浮)盈亏金额',   
    round(sum(round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2)) /sum(h.hold_amount * c.cb_price2_id) * 100, 2) || '%' as 累积收益率
from hold_bond h , changed_bond c 
where h.bond_code = c.bond_code and h.hold_amount >0 and hold_owner='me' GROUP by strategy_type order by 投入金额 DESC        
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
            data.append([row['策略'], round(row['投入金额'], 2)])

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

        return '我的策略', htmls['nav'], html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


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
                    opts.MarkLineItem(x=common.MID_X, name='转债价格中位数'),
                    opts.MarkLineItem(y=common.MID_Y, name='转债溢价率中位数'),
                ]
            )
        )

    # scatter.add_xaxis(x)

    scatter.set_global_opts(
        title_opts=opts.TitleOpts(title="不同策略可转债分布情况", pos_left='center'),
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
    scatter_html = scatter.render_embed('template.html', common.env)
    return scatter_html


if __name__ == "__main__":
    # draw_my_view(True, True)

    common.init_cb_sum_data()

    draw_my_view(True)
    print("processing is successful")
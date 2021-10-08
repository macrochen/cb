# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

import sqlite3

# import matplotlib.pyplot as plt

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# 单选
from utils import db_utils, html_utils
from utils.db_utils import get_connect

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

tables = {}


def draw_my_view(is_login_user):
    # 打开文件数据库
    con_file = get_connect()
    cur = con_file.cursor()
    try:

        html = ''
        htmls = {}

        # =========我的强赎=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, enforce_get as 强赎状态, 
    round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, h.account as 账户, h.memo as 备注
    from (select * from changed_bond where enforce_get in ('强赎中')) c, hold_bond h
    WHERE c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount != -1
    order by 转债价格 desc 
            """)

        html = html_utils.generate_table_html("强赎", cur, html, htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的回售=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', 
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

        html = html_utils.generate_table_html("回售", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '回售年限', '回售收益率'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的低余额策略=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', remain_amount as '余额(亿元)', 
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

        html = html_utils.generate_table_html("低余额", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '正股涨跌'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的低价高收益策略=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', 
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

        html = html_utils.generate_table_html("高收益", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的双低策略=========
        cur.execute("""
        SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
            round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
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

        html = html_utils.generate_table_html("双低", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的双低轮动策略=========
        cur.execute("""
        SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
            round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
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

        html = html_utils.generate_table_html("双低轮动", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的多因子策略=========
        cur.execute("""
        SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
            round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率,
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

        html = html_utils.generate_table_html("多因子", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的打新策略=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
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

        html = html_utils.generate_table_html("打新", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的网格策略=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
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

        html = html_utils.generate_table_html("网格", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的基本面策略=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', 
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

        html = html_utils.generate_table_html("基本面", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========我的每周精选策略=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, 
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

        html = html_utils.generate_table_html("每周精选", cur, html, htmls=htmls, tables=tables)

        # =========我的活性债策略=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
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

        html = html_utils.generate_table_html("活性债", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)

        # =========其他=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,
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

        html = html_utils.generate_table_html("其他", cur, html,
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, tables=tables,
                                              is_login_user=is_login_user)
        # =========清仓建议=========
        cur.execute("""
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
    
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        round(bt_yield*100,2) || '%' as 到期收益率, round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',
        h.account as 账户, h.strategy_type as 策略,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', 
        h.memo as 备注
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

        html = html_utils.generate_table_html("清仓建议", cur, html,
                                              subtitle='(价格<100且溢价率>90%或100<价格<110且溢价率>60%或价格>130)',
                                              remark_fields_color=['盈亏', '转债价格', '溢价率', '可转债涨跌', '到期收益率', '双低值'],
                                              htmls=htmls, is_login_user=is_login_user)

        # 数据汇总

        # 用来画统计图的数据

        cur.execute("""
SELECT strategy_type as 策略, 
     
    count(h.bond_code) as 个数, 
    sum(h.hold_amount) as 数量,
    
    round(sum(h.sum_buy-h.sum_sell),2) as 投入金额, 
    round(sum(h.hold_amount * c.cb_price2_id),2) as 市值, 
    
    round(sum(round((c.cb_price2_id/(1+c.cb_mov2_id) * c.cb_mov2_id)*h.hold_amount, 2)), 2) as '日收益', 
    round((round(sum(c.cb_price2_id*h.hold_amount)/sum(c.cb_price2_id/(1+c.cb_mov2_id)*h.hold_amount),4)-1)*100,2) || '%' as '日收益率',
    
    round(sum(round(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy, 3)), 2) as '累积收益',   
    round(sum(round(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy, 3)) /sum(h.sum_buy-h.sum_sell) * 100, 2) || '%' as 累积收益率
from hold_bond h , changed_bond c 
where h.bond_code = c.bond_code and hold_owner='me' GROUP by strategy_type order by 投入金额 DESC        
        """)

        rows = []
        dict_rows = []
        # 增加合计行
        total_money = 0
        assets_money = 0
        total_profit = 0
        total_now_profit = 0
        total_now_profit_rate = 0
        total_amount = 0
        total_num = 0

        money_rows = []
        for row in cur.fetchall():
            rows.append(row)
            dict_row = db_utils.get_dict_row(cur, row)
            dict_rows.append(dict_row)
            asset_row = dict_row['市值']
            money_row = dict_row['投入金额']
            money_rows.append(money_row)
            total_money += money_row
            assets_money += asset_row
            total_profit += dict_row['累积收益']
            total_now_profit += dict_row['日收益']
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
        new_rows.append(['合计', total_num, total_amount, round(total_money, 2), round(assets_money, 2), round(total_now_profit, 2), str(round(total_now_yield, 2))+'%', round(total_profit, 2), str(total_yield) + '%', '100%'])

        pie_html = html_utils.generate_pie_html(dict_rows, '策略', '投入金额')

        type = "汇总"
        sum_html = html_utils.generate_table_html(type, cur, '', need_title=False, field_names=['投入占比'],
                                                  remark_fields_color=['日收益', '日收益率', '累积收益率', '累积收益'],
                                                  ignore_fields=['投入金额'],
                                                  rows=new_rows, htmls={})

        html_utils.add_nav_html_to_head(htmls, type, '<li><a href="/view_my_account.html">切换到按账户</a></li>')

        # 用柱状图从大到小展示持有可转债涨跌幅情况
        scatter_html = html_utils.generate_scatter_html(tables, select)

        html = """
            <br/>
            <br/>
            <br/>
            <br/>
            <div id=\"""" + type + """\">
                <center>
                    """ + sum_html + '<br/>' + pie_html + scatter_html + "<br/>" + """
                </center>
            </div>
        """ + html

        con_file.close()

        return '我的策略', htmls['nav'], html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


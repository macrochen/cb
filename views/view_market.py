# 目前市面上各种策略(高收益, 双低, 活性债, 回售)的数据视图展示


# 需导入要用到的库文件

from prettytable import from_db_cursor

import utils.trade_utils
from utils import html_utils
from utils.db_utils import get_connect
from utils.html_utils import default_get_label, generate_scatter_html_with_one_table

config = {'type': [
    '双低策略',
    '高收益策略',
    '回售策略',
    # '活性债策略',
    '低余额策略',
    '低溢价率策略',
    # '溢价率折价策略',
    # '高收益率策略',
    # '下修博弈策略',
    # '广撒网策略',
    '快到期保本策略',
    '正股优选策略',
    '高成长策略',
    '股性策略',
    # '换手率排行榜',
    # '正股涨幅榜',
    # '妖债策略',
    # '抄作业',
    # '非200不卖',
    # '自选集',
    '凌波双低轮动',
],
}


def generate_strategy_html(con_file,
                           sql,
                           type,
                           sub_title,
                           html,
                           label_y='转股溢价率(%)',
                           field_name='溢价率',
                           get_label=default_get_label,
                           nav_html_list=None,
                           remark_fields_color=[],
                           draw_figure=True,
                           use_personal_features=False,
                           ):

    cur = con_file.cursor()
    cur.execute(sql)

    table = from_db_cursor(cur)
    if table.rowcount == 0:
        return ''

    scatter_html = generate_scatter_html_with_one_table(table, type, sub_title, draw_figure, field_name, get_label, label_y,
                                                        use_personal_features)

    html_utils.add_nav_html(nav_html_list, type)

    html += """
    <div id=\"""" + type + """\">
        """ + scatter_html + html_utils.build_table_html(table, remark_fields_color, ignore_fields=['持有数量'], is_login_user=use_personal_features, table_rows_size=6) + """
    </div>
    """

    return html


def draw_market_view(use_my_features):
    use_personal_features = use_my_features


    # 打开文件数据库
    con_file = get_connect()

    html = """<br/><br/><br/><br/>"""

    nav_html_list = ['<li><a href="/">Home</a></li>']
    try:

        # =========强赎=========
        sql = """
    SELECT  c.data_id as nid, e.hold_id, c.bond_code, c.stock_code, c.cb_name_id as 名称, enforce_get as 强赎状态, 
    cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率
    from (select * from changed_bond where enforce_get in ('强赎中')) c left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on c.bond_code = e.bond_code
    order by 转债价格 desc 
            """
        # 加几个换行避免顶部的菜单遮住title
        html += "<center>=========<font size=4><b>强赎可转债</b></font>=========</br></br></center>"
        html = generate_strategy_html(con_file, sql, "强赎转债", "", html, nav_html_list=nav_html_list, draw_figure=False,
                                      use_personal_features=use_personal_features)

        # =========回售策略=========
        if "回售策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        cb_price2_id as 转债价格, round(bt_red * 100,2) || '%' as 回售收益率, red_t as '回售年限(年)', round((bt_red * 100) + (2-bond_t1),2) as 性价比,round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',e.theme as 题材概念,
        
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
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
         and red_t not in('无权', '回售内')
         and red_t < 1
         and round(bt_red * 100,2) > 1
        --ORDER by 回售年限 ASC, 回售收益率 DESC;
        ORDER by 性价比 DESC) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code
            """
            html = generate_strategy_html(con_file, sql, "回售策略", "回售年限<1年, 回收收益率>1%", html, nav_html_list=nav_html_list,
                                          label_y="回售收益率(%)", field_name='回售收益率',
                                          remark_fields_color=['回售年限(年)', '回售收益率', '转债价格', '可转债涨跌'],
                                          use_personal_features=use_personal_features)

        # =========回售策略=========
        if "下修博弈策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', 
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',e.theme as 题材概念,
        
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
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
         and e.optional = 300
        --ORDER by 回售年限 ASC, 回售收益率 DESC;
        ORDER by 转债价格 ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code
            """
            html = generate_strategy_html(con_file, sql, "下修博弈策略", "100面值以下为主", html, nav_html_list=nav_html_list,
                                          label_y="到期收益率(%)", field_name='到期收益率', mid_y=0,
                                          remark_fields_color=['溢价率', '到期收益率', '转债价格', '可转债涨跌'],
                                          use_personal_features=use_personal_features)

        # =========低余额策略=========
        if "低余额策略" in config['type']:
            # 低价格
            html = build_low_remain_block(con_file, html, nav_html_list, 'cb_price2_id', '低价格', use_personal_features)
            # 低溢价
            html = build_low_remain_block(con_file, html, nav_html_list, 'cb_premium_id', '低溢价', use_personal_features)
            # 双低
            html = build_low_remain_block(con_file, html, nav_html_list, 'cb_price2_id+cb_premium_id*100', '双低', use_personal_features)

            # s = ''
            # s += common.get_sub_nav_html("低余额策略(低价格)")
            # s += common.get_sub_nav_html("低余额策略(低溢价)")
            # s += common.get_sub_nav_html("低余额策略(双低)")
            #
            # title = "低余额策略"
            # common.add_sub_nav_html(nav_html_list, title, s)

        # =========双低债=========
        if "双低策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', 
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念,
         
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
        ORDER by 双低值
        limit 10) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
            ) e 
        on d.bond_code = e.bond_code
        
            """
            get_label = lambda row: row['名称'].replace('转债', '') + '(' + str(row['双低值']) + ')'
            html = generate_strategy_html(con_file, sql, "双低策略", "双低值前10", html, nav_html_list=nav_html_list,
                                          get_label=get_label,
                                          remark_fields_color=['溢价率', '转债价格', '可转债涨跌', '到期收益率', '双低值', '正股涨跌'],
                                          use_personal_features=use_personal_features)

        # =========高收益策略=========
        if "高收益策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        cb_price2_id as '转债价格', round(bt_yield*100,2) || '%' as 到期收益率, round(100- cb_price2_id + BT_yield * 100, 2) as 性价比,
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念,
         
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
        --and c.rating in ('AA+', 'AA-', 'AA', 'AAA', 'A', 'A+')
        --and c.cb_name_id not in( '亚药转债' , '本钢转债','搜特转债','广汇转债')
        --AND bt_yield > 0
        --and cb_price2_id < 110
        order by bt_yield desc
        limit  10) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
            ) e 
        on d.bond_code = e.bond_code;
            """

            html = generate_strategy_html(con_file, sql, "高收益策略", "到期收益率前10", html, nav_html_list=nav_html_list,
                                          label_y="到期收益率(%)", field_name='到期收益率',
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'],
                                          use_personal_features=use_personal_features)

        # =========活性债策略=========
        if "活性债策略" in config['type']:
            # 当日概念题材
            gn_c, gn_s = generate_gn_slice(con_file, 'gn_custom')
            html = generate_active_strategy_html(con_file, gn_c, gn_s, '自定义概念题材', html, nav_html_list, use_personal_features)

            # 当日概念题材
            gn_c, gn_s = generate_gn_slice(con_file, 'gn_1')
            html = generate_active_strategy_html(con_file, gn_c, gn_s, '当日概念题材', html, nav_html_list, use_personal_features)

            # 5日概念题材
            gn_c, gn_s = generate_gn_slice(con_file, 'gn_5')
            html = generate_active_strategy_html(con_file, gn_c, gn_s, '最近5日概念题材', html, nav_html_list, use_personal_features)

            # 10日概念题材
            gn_c, gn_s = generate_gn_slice(con_file, 'gn_10')
            html = generate_active_strategy_html(con_file, gn_c, gn_s, '最近10日概念题材', html, nav_html_list, use_personal_features)



            # =========快到期保本策略=========
            if "快到期保本策略" in config['type']:
                sql = """
          SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
        FROM (
            SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
            round(at_yield*100,2) || '%' as 税后到期收益率, bond_t1 as 剩余年限,

            c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, 
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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
            e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
            case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
            case when e.memo is not null then  e.memo else  '' END as 备注

            from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
            where c.stock_code = s.stock_code and c.bond_code = e.bond_code
          and at_yield > 0
          and bond_t1 < 3
          -- and duration < 3 
          -- and cb_price2_id > 99 
          --and cb_price2_id < 105 
          --and stock_pb > 1 
          -- and s.net > 0
          -- and s.margin > 10
          -- and cb_t_id = '转股中' 
          --and cb_premium_id*100 < 20 
          -- and 双低值 < 120
          order by (2.5-bond_t1) + at_yield * 100 desc limit 5) d left join
                (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                    from hold_bond 
                    where id in (select id from hold_bond where id 
                        in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
                ) e 
              on d.bond_code = e.bond_code
                  """
                html = generate_strategy_html(con_file, sql, "快到期保本策略", "税后到期收益率>0, 剩余年限<3", html, nav_html_list=nav_html_list,
                                              remark_fields_color=['税后到期收益率', '溢价率', '转债价格', '可转债涨跌', '剩余年限'],
                                              use_personal_features = use_personal_features)

            # =========低溢价率策略=========
            if "低溢价率策略" in config['type']:
                sql = """
          SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
        FROM (
            SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
            cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,
            round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 

            c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, 
            round(bt_yield*100,2) || '%' as 到期收益率, bond_t1 as 剩余年限,
            c.stock_pb as 市净率, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,

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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
            e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
            case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
            case when e.memo is not null then  e.memo else  '' END as 备注

            from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
            where c.stock_code = s.stock_code and c.bond_code = e.bond_code
          and cb_premium_id < 0.05
		  and cb_price2_id < 140 
          order by (2.5-bond_t1) + bt_yield * 100 desc limit 5) d left join
                (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                    from hold_bond 
                    where id in (select id from hold_bond where id 
                        in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
                ) e 
              on d.bond_code = e.bond_code
                  """
                html = generate_strategy_html(con_file, sql, "低溢价率策略", "溢价率<4%, 转债价格<140, 如果持有, 坚持不卖", html, nav_html_list=nav_html_list,
                                              remark_fields_color=['溢价率', '转债价格', '可转债涨跌', '正股涨跌'],
                                              use_personal_features = use_personal_features)

        # =========广撒网策略=========
        if "广撒网策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
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
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "广撒网策略", "价格<105, 溢价率<20%, pb>1", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'],
                                          use_personal_features=use_personal_features)

        # =========正股优选策略=========
        if "正股优选策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
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
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "正股优选策略", "正股综合评分>6, 转债价格<115, 双低值<130", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'],
                                          use_personal_features=use_personal_features)

        # =========高成长策略=========
        if "高成长策略" in config['type']:
            sql = """
      SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
      and yoy_margin_rate > 0 
      and margin > 0 
      and cb_price2_id < 115
      ORDER by  yoy_margin_rate DESC limit 20
      ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "高成长策略", "利润率增长top20, 转债价格<115, 利润率>0", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '利润率|行业均值', '利润率同比'],
                                          use_personal_features=use_personal_features)

        # =========股性策略=========
        if "股性策略" in config['type']:
            sql = """
     SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        remain_amount as '余额(亿元)', round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
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
        round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
     -- and yoy_margin_rate > 0 
      --and margin > 0 
      and cb_price2_id < 115
	  and cb_premium_id < 0.1
      ORDER by  cb_premium_id asc
      ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "股性策略", "转债价格<115, 溢价率<10%, 用来筛选网格对象", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '余额(亿元)', '换手率(%)'],
                                          use_personal_features=use_personal_features)

        # =========妖债策略=========
        if "妖债策略" in config['type']:
            sql = """
     SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, 
         
        remain_amount as '余额(亿元)', round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念,
        
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
        round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
     -- and yoy_margin_rate > 0 
      and remain_amount < 3 
      and cb_trade_amount2_id > 0.5
      ORDER by  remain_amount asc
      ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code
              """
            html = generate_strategy_html(con_file, sql, "妖债策略", "余额<3亿, 换手率>50%, 找底部长时间横盘, 刚刚放量上涨, 当大盘跌, 柚子没有攒钱的地方, 就会来短炒妖债", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '余额(亿元)', '换手率(%)'],
                                          use_personal_features=use_personal_features)


        # =========抄作业=========
        if "抄作业" in config['type']:
            sql = """
     SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
    FROM (
      SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,
         
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
      and e.optional = 1
      ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code"""
            html = generate_strategy_html(con_file, sql, "抄作业", "收集近期大V们推荐", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'],
                                          use_personal_features=use_personal_features)

        # =========自选集=========
        if "自选集" in config['type']:
            sql = """
         SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
        FROM (
          SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 

            cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, round(bt_yield*100,2) || '%' as 到期收益率,

            c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
            e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
            case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
            case when e.memo is not null then  e.memo else  '' END as 备注

            from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
            where c.stock_code = s.stock_code and c.bond_code = e.bond_code
          and e.optional = 2
          ) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
                 ) e 
            on d.bond_code = e.bond_code"""

            html = generate_strategy_html(con_file, sql, "自选集", "根据各种策略选出来准备买入的", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'],
                                          use_personal_features=use_personal_features)

        # =========非200不卖=========
        if "非200不卖" in config['type']:
            sql = """
         SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
        FROM (
          SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 

            cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率, 
            round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
            round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
            round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',
            round(bt_yield*100,2) || '%' as 到期收益率, 

            c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, 

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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
            e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
            case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
            case when e.memo is not null then  e.memo else  '' END as 备注

            from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
            where c.stock_code = s.stock_code and c.bond_code = e.bond_code
          and e.optional = 200 and cb_price2_id < 200
          ) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
                 ) e 
            on d.bond_code = e.bond_code"""

            html = generate_strategy_html(con_file, sql, "非200不卖", "不到200元不卖", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '正股涨跌'],
                                          use_personal_features=use_personal_features)

        # =========凌波双低轮动=========
        if "凌波双低轮动" in config['type']:
            sql = """
         SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
        FROM (
          SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 

            cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,
            round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, 
            round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
            round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',
            round(bt_yield*100,2) || '%' as 到期收益率, 

            c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念, 

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

            rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
            e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
            case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
            case when e.memo is not null then  e.memo else  '' END as 备注

            from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
            where c.stock_code = s.stock_code and c.bond_code = e.bond_code
          and e.optional = 'yyb' order by 转债价格 
          ) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
                 ) e 
            on d.bond_code = e.bond_code"""

            html = generate_strategy_html(con_file, sql, "凌波双低轮动", "脉冲卖出标准:110元以下(价格120双低值125)，110-115元(价格125双低值130)，115-120元(价格130双低值135)，120-125元(价格135双低值140)", html, nav_html_list=nav_html_list,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '正股涨跌'],
                                          use_personal_features=use_personal_features)

        con_file.close()

        return '市场策略', ''.join(nav_html_list), html

    except Exception as e:
        con_file.close()
        print("processing is failure. " + str(e), e)
        raise e


def build_low_remain_block(con_file, html, nav_html_list, sort_field, sub_strategy, use_personal_features=False):
    sql = """
    SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
  FROM (
      SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, remain_amount as '余额(亿元)', 
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业', e.theme as 题材概念,
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
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        case when e.memo is not null then  e.memo else  '' END as 备注
  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
        --and cb_premium_id * 100 < 30 
        and remain_amount < 3 
        --and cb_price2_id < 110
        ORDER by """ + sort_field + """ ASC
        limit 10
        ) d left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (select id from hold_bond where id 
                in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
             ) e 
        on d.bond_code = e.bond_code            
            """
    get_label = lambda row: row['名称'].replace('转债', '') + '(' + str(round(row['余额(亿元)'], 1)) + '亿)'
    html = generate_strategy_html(con_file, sql, "低余额策略(" + sub_strategy + ")", "余额<3亿, " + sub_strategy + "top10",
                                  html,
                                  nav_html_list=nav_html_list,
                                  get_label=get_label,
                                  remark_fields_color=['余额(亿元)', '溢价率', '转债价格', '可转债涨跌'],
                                  use_personal_features=use_personal_features)
    return html


def generate_gn_slice(con_file, key):
    gn_sql = """
            select value from config where field_name='theme' and key='""" + key + """' order by order_index
            """
    cur = con_file.cursor()
    cur.execute(gn_sql)
    gn_s = ''
    gn_c = 'and ('
    i = 0
    for row in cur.fetchall():
        if i == 0:
            i += 1
        else:
            gn_s += ','
            gn_c += ' or '

        gn_s += row[0]
        gn_c += "theme like '%" + row[0] + "%'"
    gn_c += ")"
    return gn_c, gn_s


def generate_active_strategy_html(con_file, gn_c, gn_s, suffix, html, htmls, use_personal_features):
    sql = """
      SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
    FROM (
        SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        e.theme as 题材概念,
        
        cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,
        
        round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌, round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
        round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', remain_amount as '余额(亿元)', 
        
        round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
        
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
        round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, cb_trade_amount_id as '成交额(百万)', 
        e.interest as 各期利息, case when e.ensure is not null then  '有' else  '无' END as 担保, case when e.buy_back_term is not null then  e.buy_back_term else  '无' END as 回售条款, 
        case when e.down_revise_term is not null then  e.down_revise_term else  '无' END as 下修条款, case when e.enforce_get_term is not null then  e.enforce_get_term else  '无' END as 强赎条款, 
        
        case when e.memo is not null then  e.memo else  '' END as 备注

  
        from (select * from changed_bond where enforce_get not in ('强赎中') or enforce_get is null) c, stock_report s, changed_bond_extend e
        where c.stock_code = s.stock_code and c.bond_code = e.bond_code
      --and duration < 3 
      --and remain_amount < 5 -- 余额
      --and cb_price2_id > 110
      and cb_price2_id < 130 -- 转债价格
      -- and cb_trade_amount2_id > 0.5 -- 换手率
	  and cb_premium_id < 0.3 -- 溢价率
""" + gn_c + """
      order by cb_price2_id ASC) d left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (select id from hold_bond where id 
                    in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
            ) e 
          on d.bond_code = e.bond_code
          """
    html = generate_strategy_html(con_file, sql, "活性债策略(" + suffix + ')',
                                  "按照主题>风格>行业方向, " + suffix + "(" + gn_s + ")\n\n结合价格<130, 溢价率<30%, 余额<3亿, 换手率>50%选出最具性价比和爆发力标的",
                                  html, nav_html_list=htmls,
                                  remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌', '正股涨跌'],
                                  use_personal_features=use_personal_features)
    return html


if __name__ == "__main__":
<<<<<<< HEAD:view_market.py
    draw_market_view(False, False)
    #common.init_cb_sum_data()
    #draw_market_view(False, True)
=======
    utils.trade_utils.calc_mid_data()

    draw_market_view(True)
>>>>>>> macro/master:views/view_market.py
    print("processing is successful")

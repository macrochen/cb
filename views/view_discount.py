# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
from utils.db_utils import get_connect
from views.view_market import generate_strategy_html


# import matplotlib.pyplot as plt


def draw_view(is_login_user):
    # 打开文件数据库
    con_file = get_connect()
    cur = con_file.cursor()
    try:

        html = ''

        sql = """
          SELECT DISTINCT d.* , e.hold_id, e.hold_amount as 持有数量
        FROM (
            SELECT c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
            round(cb_premium_id*100,2) || '%' as 溢价率, cb_price2_id as '转债价格', cb_t_id as 距离转股日,

            round(cb_price2_id + cb_premium_id * 100, 2) as 双低值, round(bt_yield*100,2) || '%' as 到期收益率,
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
          and cb_premium_id < 0 
          -- and cb_price2_id > 99 
          -- and cb_price2_id < 115 
          -- and roe > 1 
          -- and s.net > 0
          -- and s.margin > 10
          -- and cb_t_id = '转股中' 
          -- and 溢价率 < 20 
          -- and 双低值 < 120
          order by cb_premium_id limit 10) d left join 
                (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                    from hold_bond 
                    where id in (select id from hold_bond where id 
                        in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code) ) 
                ) e 
              on d.bond_code = e.bond_code
                  """
        html = '<br><br><br>' + generate_strategy_html(con_file, sql, "溢价率折价排行", "低溢价率top5", html,
                                          remark_fields_color=['到期收益率', '溢价率', '转债价格', '可转债涨跌'],
                                          use_personal_features=is_login_user
                                                              )

        con_file.close()

        return '溢价率折价排行', '<li><a href="/">Home</a></li>', html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e



# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040
from prettytable import from_db_cursor
from pyecharts.charts import Sunburst, Tree

import views.nav_utils
from utils.db_utils import get_cursor, get_record
from utils.echarts_html_utils import generate_scatter_html_with_one_table
from utils.html_utils import env
from utils.table_html_utils import generate_table_html_with_data
from utils.treemap_utils import generate_treemap_html
from pyecharts import options as opts

from views.chart_tree_industry_utils import get_data, generate_chart_html


def draw_view(url):
    try:

        html = ''

        cur = get_cursor("""
SELECT industry, sub_industry
,round(sum(cb_price2_id + cb_premium_id*100)/count(sub_industry),2) as value
, sum(cb_price2_id + cb_premium_id*100) as sum
, count(*) as count
from changed_bond group by sub_industry 
order by industry, value,sub_industry
        """)

        table = from_db_cursor(cur)
        html += generate_chart_html(table, '可转债行业双低值分布', '/view_industry_double_low_detail.html')

        return '可转债行业双低值分布', \
               views.nav_utils.build_analysis_nav_html(url), \
               html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


def generate_detail(key, is_login_user):
    cur = get_cursor("""
                SELECT DISTINCT d.*,
                    e.strategy_type                                        as 策略,
                    e.hold_id,
                    e.hold_price                                           as 持有成本,
                    e.hold_amount                                          as 持有数量
    FROM (
             SELECT c.data_id                                                                                       as nid,
                    case when cb_mov2_id > 0 then 1 when cb_mov2_id = 0 then 0 ELSE -1 end                          as _sign,
                    c.bond_code,
                    c.stock_code,
                    c.cb_name_id                                                                                    as 名称,
                    round(cb_price2_id + cb_premium_id * 100, 2)                                                    as 双低值,
                    round(cb_premium_id * 100, 2) || '%'                                                            as 溢价率,
                    cb_price2_id                                                                                    as '转债价格',
                    round(cb_mov2_id * 100, 2) || '%'                                                               as 可转债涨跌,
                    round(cb_mov_id * 100, 2) || '%'                                                                as 正股涨跌,
                    remain_amount                                                                                   as '余额(亿元)',
                    round(cb_trade_amount2_id * 100, 2) || '%'                                                      as '换手率(%)',
                    cb_trade_amount_id                                                                              as '成交额(百万)',
                    round(cb_price2_id + cb_premium_id * 100, 2)                                                    as 双低值,
                    round(bt_yield * 100, 2) || '%'                                                                 as 到期收益率,
                    c.stock_name                                                                                    as 正股名称,
                    c.industry                                                                                      as '行业',
                    c.sub_industry                                                                                  as '子行业',

                    rank_gross_rate || '【' || level_gross_rate || '】'                                               as 毛利率排名,
                    rank_net_margin || '【' || level_net_margin || '】'                                               as 净利润排名,
                    rank_net_profit_ratio || '【' || level_net_profit_ratio || '】'                                   as 利润率排名,
                    rank_roe || '【' || level_roe || '】'                                                             as ROE排名,
                    rank_pe || '【' || level_pe || '】'                                                               as PE排名,
                    rank_pb || '【' || level_pb || '】'                                                               as PB排名,
                    rank_net_asset || '【' || level_net_asset || '】'                                                 as 净资产排名,
                    rank_market_cap || '【' || level_market_cap || '】'                                               as 市值排名,
                    stock_total                                                                                     as 综合评分,

                    round(s.revenue, 2)                                                                             as '营收(亿元)',
                    s.yoy_revenue_rate || '%'                                                                       as '营收同比',
                    gross_rate || '|' || avg_gross_rate                                                             as '毛利率|行业均值',
                    round(s.net, 2) || '|' || avg_net_margin                                                        as '净利润|均值(亿元)',
                    s.yoy_net_rate || '%'                                                                           as '净利润同比',
                    s.margin || '|' || avg_net_profit_ratio                                                         as '利润率|行业均值',
                    s.yoy_margin_rate || '%'                                                                        as '利润率同比',
                    s.roe || '|' || avg_roe                                                                         as 'ROE|行业均值',
                    s.yoy_roe_rate || '%'                                                                           as 'ROE同比',
                    round(s.al_ratio, 2) || '%'                                                                     as 负债率,
                    s.yoy_al_ratio_rate || '%'                                                                      as '负债率同比',
                    s.pe || '|' || avg_pe                                                                           as 'PE(动)|均值',
                    c.stock_pb || '|' || avg_pb                                                                     as 'PB|行业均值',
                    net_asset || '|' || avg_net_asset                                                               as '净资产|行业均值',
                    market_cap || '|' || avg_market_cap                                                             as '市值|均值(亿元)',

                    fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' ||
                    fact_base                                                                                       as '技术|资金|消息|行业|基本面',
                    trade_suggest                                                                                   as 操作建议,

                    rating                                                                                          as '信用',
                    duration                                                                                        as 续存期,
                    cb_ma20_deviate                                                                                 as 'ma20乖离',
                    cb_hot                                                                                          as 热门度

             from (select *
                   from (SELECT DISTINCT c.*
                         from changed_bond c WHERE sub_industry = :sub_industry) 
                   ) c
                      LEFT join stock_report s on c.stock_code = s.stock_code) d
             left join
         (select id as hold_id, bond_code, hold_price, hold_amount, strategy_type
          from hold_bond
          where id in (select id
                       from hold_bond
                       where id
                                 in (SELECT min(id)
                                     from hold_bond
                                     where hold_owner = 'me' and hold_amount != -1
                                     group by bond_code))
         ) e
         on d.bond_code = e.bond_code
    order by 双低值
                                    """, {'sub_industry': key})

    table, table_html = generate_table_html_with_data('', cur, '', need_title=False,
                                                      remark_fields=['盈亏', '到期收益率', '溢价率', '可转债涨跌', '正股涨跌'],
                                                      ignore_fields=['持有数量'],
                                                      is_login_user=is_login_user)
    html = generate_scatter_html_with_one_table(table,
                                                 title=key + '行业可转债',
                                                 use_personal_features=is_login_user)
    html += table_html
    return html
# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040
import views.nav_utils
from utils.db_utils import get_cursor
from utils.echarts_html_utils import generate_scatter_html_with_one_table
from utils.table_html_utils import generate_table_html_with_data
from utils.treemap_utils import generate_treemap_html


def draw_view(is_login_user, key, start, end, rise, url):
    try:

        html = ''

        cur = get_cursor("""
        select i as 价格区间, round(s_m / c_i*100, 2) as 涨跌,  c_i as 数量
from (select DISTINCT(_interval) as i, count(_interval) as c_i, sum(cb_mov2_id) as s_m
      from (SELECT cb_price2_id,
                   cb_mov2_id,
                   case
                       when cb_price2_id <= 80 then '<=80元'
                       when cb_price2_id > 80 and cb_price2_id <= 90 then '80~90元'
                       when cb_price2_id > 90 and cb_price2_id <= 100 then '90~100元'
                       when cb_price2_id > 100 and cb_price2_id <= 110 then '100~110元'
                       when cb_price2_id > 110 and cb_price2_id <= 120 then '110~120元'
                       when cb_price2_id > 120 and cb_price2_id <= 130 then '120~130元'
                       when cb_price2_id > 130 and cb_price2_id <= 150 then '130~150元'
                       when cb_price2_id > 150 and cb_price2_id <= 200 then '150~200元'
                       when cb_price2_id > 200 then '>200元' end
                       as _interval,
                   case
                       when cb_price2_id <= 80 then 1
                       when cb_price2_id > 80 and cb_price2_id <= 90 then 2
                       when cb_price2_id > 90 and cb_price2_id <= 100 then 3
                       when cb_price2_id > 100 and cb_price2_id <= 110 then 4
                       when cb_price2_id > 110 and cb_price2_id <= 120 then 5
                       when cb_price2_id > 120 and cb_price2_id <= 130 then 6
                       when cb_price2_id > 130 and cb_price2_id <= 150 then 7
                       when cb_price2_id > 150 and cb_price2_id <= 200 then 8
                       when cb_price2_id > 200 then 9 end
                       as _interval_idx
            from changed_bond)
      GROUP by _interval
      order by _interval_idx)
        """)

        html += generate_treemap_html(cur,
                                      '=========可转债涨跌价格分布=========',
                                      '价格区间',
                                      '数量',
                                      '/view_tree_map_price.html')

        if start is not None or end is not None and rise is not None:
            rise = float(rise)
            up = 0
            down = 0
            if rise >= 0:
                up = 10
            else:
                down = 10

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
                cb_mov2_id,
                round(cb_mov2_id * 100, 2) || '%'                                                               as 可转债涨跌,
                cb_price2_id                                                                                    as '转债价格',
                round(cb_premium_id * 100, 2) || '%'                                                            as 溢价率,
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
                     from changed_bond c WHERE cb_price2_id > :start and cb_price2_id <= :end
                     order by cb_mov2_id DESC
                     limit :up_size) 
               UNION
               select *
               from (SELECT DISTINCT c.*
                     from changed_bond_view c WHERE cb_price2_id > :start and cb_price2_id <= :end
                     order by cb_mov2_id ASC
                     limit :down_size)) c
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
order by _sign desc, abs(cb_mov2_id) DESC
                                """, {'start':start, 'end':end, 'up_size':up, 'down_size':down})

            table, table_html = generate_table_html_with_data('', cur, '', need_title=False,
                                       remark_fields=['盈亏', '到期收益率', '溢价率', '可转债涨跌', '正股涨跌'],
                                       is_login_user=is_login_user)
            html += "<div id='cb_detail_list'>"
            html += generate_scatter_html_with_one_table(table,
                                                         title='价格' + key + '的可转债涨跌分布',
                                                         sub_title='仅展示涨/跌幅top10的可转债',
                                                         use_personal_features=is_login_user)
            html += table_html
            html += '</div>'

        return '可转债涨跌分布', \
               views.nav_utils.build_analysis_nav_html(url), \
               html

    except Exception as e:
        print("processing is failure. ", e)
        raise e



# def on_click():
#     alert('haha')

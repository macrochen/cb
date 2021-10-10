# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

import sqlite3

from pyecharts import options as opts
from pyecharts.charts import Bar, TreeMap
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

# import matplotlib.pyplot as plt

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
from utils import db_utils, html_utils
from utils.db_utils import get_connect, get_dict_row
from utils.html_utils import env, generate_table_html


def draw_view(is_login_user, industry, rise):
    # 打开文件数据库
    con_file = get_connect()
    cur = con_file.cursor()
    try:

        html = ''

        cur.execute("""
        select a.industry, round(b.涨跌幅 / a.个数*100, 4) as 涨跌, 余额
from (SELECT industry, count(industry) as 个数 from changed_bond group by industry) a,
     (SELECT industry, sum(cb_mov2_id) as 涨跌幅 from changed_bond group by industry) b,
     (SELECT industry, round(sum(remain_amount),2) as 余额 from changed_bond group by industry) c
where a.industry = b.industry
  and a.industry = c.industry
order by 涨跌 desc
        """)

        html += '<br/><br/><br/><br/>' + generate_treemap_html(cur, '=========可转债涨跌行业分布=========')

        if industry is not None and industry.strip(' ') != '' and rise is not None:
            rise = float(rise)
            up = 0
            down = 0
            if rise >= 0:
                up = 10
            else:
                down = 10

            cur.execute("""
            SELECT DISTINCT d.*,
                e.strategy_type                                        as 策略,
                case when e.hold_id is not null then '✔️️' else '' END as 持有,
                e.hold_price                                           as 持有成本,
                e.hold_amount                                          as 持有数量
FROM (
         SELECT c.data_id                                                                                       as nid,
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
                     from changed_bond c WHERE industry like ?
                     order by cb_mov2_id DESC
                     limit ?) 
               UNION
               select *
               from (SELECT DISTINCT c.*
                     from changed_bond c WHERE industry like ?
                     order by cb_mov2_id ASC
                     limit ?)) c
                  LEFT join stock_report s on c.stock_code = s.stock_code
         where c.enforce_get not in ('强赎中')
            or c.enforce_get is null) d
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
order by abs(cb_mov2_id) DESC
                                """, (industry, up, industry, down))

            html += generate_table_html(industry + '行业', cur, '', need_title=True,
                                       remark_fields_color=['盈亏', '到期收益率', '溢价率', '可转债涨跌', '正股涨跌'],
                                       is_login_user=is_login_user)

        con_file.close()

        return '可转债涨跌分布', '<li><a href="/">Home</a></li>', html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


def generate_treemap_html(cur, title):
    data, item_opts = [], []
    min_rise = 100
    max_rise = -100
    for row in cur.fetchall():
        item = get_dict_row(cur, row)
        rise_value = item['涨跌']

        if rise_value > max_rise:
            max_rise = rise_value

        if rise_value < min_rise:
            min_rise = rise_value

        if rise_value > 0:
            rise = '\n+{}%'.format(rise_value)
            rich = {'name': {'fontSize': 14, 'color': '#000'},
                    '涨跌': {'fontSize': 14, 'fontWeight': 'bolder', "align": "center", 'color': '#FF0000'}}
            tree_item = opts.TreeMapItemStyleOpts(color_alpha=1, color='rgb(255,0,0)', border_color='#fff')
        else:
            rise = '\n{}%'.format(rise_value)
            rich = {'name': {'fontSize': 14, 'color': '#000'},
                    '涨跌': {'fontSize': 14, 'fontWeight': 'bolder', "align": "center", 'color': '#2E8B57'}}
            tree_item = opts.TreeMapItemStyleOpts(color_alpha=1, color='rgb(60,179,113)', border_color='#fff')
        data.append(opts.TreeItem(name=item['industry'],
                                  # value 包含持仓占比和涨跌幅两项数据
                                  value=[item['余额'], rise_value],
                                  label_opts=opts.LabelOpts(position='insideBottomLeft',
                                                            formatter='{name|{b}}{rise|%s}' % rise, rich=rich)))
        item_opts.append(tree_item)

    tool_js = """function (param) 
    {   const color = param.value[1] > 0 ? '#FF0000' : '#2E8B57';
        const detail_style = `color:${color};`;
        const msgContent = `<div style='width:fit-content;height:fit-content;'>
            ${param.name}<br/>
            余额：&nbsp<span style='color:'#fff';'>&nbsp${param.value[0]}&nbsp亿元&nbsp&nbsp</span><br/>
            涨跌：&nbsp<span style='${detail_style};'>&nbsp${param.value[1]}&nbsp%&nbsp&nbsp</span><br/>
        <div>`;
    return msgContent}
    """

    tp = TreeMap(init_opts=opts.InitOpts(theme='white',
                                         width='1424px',
                                         height='700px',
                                         chart_id='cb_tree_map'
                                         ))
    tp.add_js_funcs("""
        chart_cb_tree_map.on('click', function(params){
            // alert(params)
            window.location.replace('/view_tree_map.html?industry=' + encodeURIComponent(params['data']['name']) + '&rise=' + params['data']['value'][1] + '#'+encodeURIComponent(params['data']['name']+'行业'))
        })
    """)
    tp.add('ALL',
           data,
           roam=False,
           node_click='link',
           width='90%',
           breadcrumb_opts=opts.TreeMapBreadcrumbOpts(is_show=False),
           levels=[
               opts.TreeMapLevelsOpts(
                   treemap_itemstyle_opts=opts.TreeMapItemStyleOpts(gap_width=1, stroke_width=1, stroke_color='#fff'),
                   color_mapping_by='value',

               )
           ],
           tooltip_opts=opts.TooltipOpts(is_show=True, formatter=JsCode(tool_js),
                                         textstyle_opts=opts.TextStyleOpts(font_size=14)),
           color_mapping_by='value',
           )
    tp.set_global_opts(title_opts=opts.TitleOpts(title=title, pos_left='center'),
                       legend_opts=opts.LegendOpts(is_show=False),
                       visualmap_opts=opts.VisualMapOpts(is_show=False,
                                                         type_='color',
                                                         min_=min_rise,
                                                         max_=max_rise,
                                                         range_color=[
                                                                      'green',
                                                                      'rgb(50, 220, 50)',
                                                                      'rgb(90, 220, 90)',
                                                                      'rgb(120, 220, 120)',
                                                                      'rgb(150, 220, 150)',

                                                                      'rgb(255, 200, 200)',
                                                                      'rgb(255, 150, 150)',
                                                                      'rgb(255, 100, 100)',
                                                                      'rgb(255, 50, 50)',
                                                                      'rgb(255, 0, 0)',
                                                                      ],
                                                         # 指定使用的数据维度
                                                         dimension=1,
                                                         is_piecewise=True,
                                                         pieces=[
                                                             {'min': min_rise, 'max': min_rise/5*4},
                                                             {'min': min_rise/5*4, 'max': min_rise/5*3},
                                                             {'min': min_rise/5*3, 'max': min_rise/5*2},
                                                             {'min': min_rise/5*2, 'max': min_rise/5},
                                                             {'min': min_rise/5, 'max': 0},

                                                             {'min': 0, 'max': max_rise/5},
                                                             {'min': max_rise/5, 'max': max_rise/5*2},
                                                             {'min': max_rise/5*2, 'max': max_rise/5*3},
                                                             {'min': max_rise/5*3, 'max': max_rise/5*4},
                                                             {'min': max_rise/5*4, 'max': max_rise},
                                                         ]
                                                         ),
                       )

    return tp.render_embed('template.html', env)

# def on_click():
#     alert('haha')

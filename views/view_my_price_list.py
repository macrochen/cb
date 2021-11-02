# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
import views.nav_utils
from utils import html_utils, trade_utils, table_html_utils
from utils.db_utils import get_cursor
# import matplotlib.pyplot as plt
from views.view_utils import add_popwin_js_code


def draw_view(is_login_user):
    try:

        html = '<br/><br/><br/><br/><br/>'

        # =========我的转债价格TOP20柱状图=========
        cur = get_cursor("""
select bond_code, cb_name_id as 名称, cb_price2_id as 转债价格, round(cb_mov2_id * 100, 2) as 涨跌, round(cb_premium_id*100,2) || '%' as 溢价率
 from (SELECT DISTINCT c. * from changed_bond c, hold_bond h 
 where  c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount > 0 order by cb_price2_id DESC limit 20)     
UNION  
select bond_code, cb_name_id as 名称, cb_price2_id as 转债价格, round(cb_mov2_id * 100, 2) as 涨跌, round(cb_premium_id*100,2) || '%' as 溢价率
 from (SELECT DISTINCT c. * from changed_bond c, hold_bond h 
 where  c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount > 0  order by cb_price2_id ASC limit 20) 
order by 转债价格 desc
                    """)

        rows = cur.fetchall()
        html += '<br/>' + generate_price_bar_html(rows, '我的可转债价格高低TOP20')

        cur = get_cursor("""
        
    SELECT h.id as hold_id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称,    
        cb_price2_id as 转债价格, round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌,
        h.hold_price || ' (' || h.hold_amount || ')' as '成本(量)',
        round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) || '(' || round((c.cb_price2_id - h.hold_price) / c.cb_price2_id * 100, 2) || '%)' as 盈亏, 
   
        round(cb_premium_id*100,2) || '%' as 溢价率, round(cb_mov_id * 100, 2) || '%' as 正股涨跌,
        remain_amount as '余额(亿元)',round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)', 
        h.strategy_type as 策略, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(cb_price2_id + cb_premium_id * 100,2) as 双低值, 
        round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
        round(bt_yield*100,2) || '%' as 到期收益率,
        
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
                
        fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' || fact_base as '技术|资金|消息|行业|基本面',  
        trade_suggest as 操作建议,
        
        rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, h.memo as 备注
        from changed_bond c left join stock_report s on c.stock_code = s.stock_code , (select * from (SELECT DISTINCT h. * from changed_bond c, hold_bond h 
 where  c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount > 0 order by cb_price2_id DESC limit 10)  
UNION  
select * from (SELECT DISTINCT h. * from changed_bond c, hold_bond h 
 where  c.bond_code = h.bond_code and h.hold_owner = 'me' and h.hold_amount > 0  order by cb_price2_id ASC limit 10)) h 
 where  c.bond_code = h.bond_code order by cb_price2_id desc
        """)

        html = table_html_utils.generate_simple_table_html(cur, html, is_login_user=is_login_user)

        return '我的可转债价格top列表', ''.join(views.nav_utils.build_personal_nav_html_list('/view_my_price_list.html')), html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


# 高低top20
def generate_price_bar_html(rows, title):
    xx1 = []
    xx2 = []
    yy1 = []
    yy2 = []

    count = 0
    for row in rows:
        bond_code = row[0]
        bond_code = trade_utils.rebuild_bond_code(bond_code)
        count += 1
        if count <= 20:
            xx1.append(row[1].replace('转债', ''))
            yy1.append({'value': row[2], 'bond_code': bond_code, 'rise': row[3], 'premium': row[4]})
        else:
            xx2.insert(0, row[1].replace('转债', ''))
            yy2.insert(0, {'value': round(-float(row[2])+0, 2), 'bond_code': bond_code, 'rise': row[3], 'premium': row[4]})

    max_value = 0
    size = len(yy1)

    for i in range(size):
        if yy1[i]['value'] + abs(yy2[i]['value']) > max_value:
            max_value = yy1[i]['value'] + abs(yy2[i]['value'])

    max_value = round(max_value * 0.7, 2) + 1

    chart_id = str(abs(hash(title)))
    bar = Bar(init_opts=opts.InitOpts(height='700px', width='1424px', theme=ThemeType.SHINE, chart_id=chart_id))

    add_popwin_js_code(bar, chart_id)

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
            name='可转债价格(元)',
            name_gap=45,
            name_location='middle',
            min_=-max_value,
            is_scale=True,
            axisline_opts=opts.AxisLineOpts(
                linestyle_opts=opts.LineStyleOpts(
                    is_show=True,

                )
            ),
            # axislabel_opts=opts.LabelOpts(formatter="{value}"),
            axislabel_opts=opts.LabelOpts(formatter=JsCode(
                          "function(x){return (x + '元').substring(1);}"
                      )),
        )
    )
    # 添加高价格的柱状图
    bar.add_yaxis("高价格", yy1,
                  bar_width=25,
                  category_gap='1%',
                  gap='1%',
                  label_opts=opts.LabelOpts(
                      is_show=True,
                      position="top",
                      formatter=JsCode(
                          "function(x){return x.data['value']+'元';}"
                      )
                  ),
                  )
    # 添加低价格的柱状图
    bar.add_yaxis("低价格",
                  yy2,
                  bar_width=25,
                  yaxis_index=1,
                  label_opts=opts.LabelOpts(
                      is_show=True,
                      position="bottom",
                      formatter=JsCode(
                          "function(x){return (x.data['value'] + '元').substring(1);}"
                      )
                  ),
                  )
    # bar.reversal_axis()
    bar.set_series_opts(
        # itemstyle_opts=opts.ItemStyleOpts(
        #     color=JsCode(
        #         "function(x){return x.data['value']>0?'#c23531':'#1d953f'}"
        #     )
        # )
    )
    bar.set_global_opts(
        title_opts=opts.TitleOpts(
            title="=========" + title + "=========",
            pos_left='center',
            pos_top='-1px',
        ),
        tooltip_opts=opts.TooltipOpts(
            is_show=True,
            formatter=JsCode("function (params){return '名&nbsp;&nbsp;&nbsp;称: ' + params.name + '<br/>' + '涨&nbsp;&nbsp;&nbsp;跌: ' + params.data['rise'] + '%<br/>' + '溢价率: ' + params.data['premium']}")
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
            name='可转债价格(元)',
            # name_rotate=90,
            name_gap=35,
            name_location='middle',
            # min_=0,
            max_=max_value,
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}元'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                # symbol=['none', 'arrow']
            )
        ),
    )

    bar_html = bar.render_embed('template.html', html_utils.env)
    return bar_html



# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
from pyecharts.charts import WordCloud
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

import views.nav_utils
from utils.db_utils import get_cursor
from utils.echarts_html_utils import generate_scatter_html_with_one_table
from utils.html_utils import env
from utils.table_html_utils import generate_table_html_with_data
from views.view_market import generate_strategy_html


# import matplotlib.pyplot as plt


def draw_view(url):
    try:

        html = ''
        ignore_words = (
            '转债标的',
            '上证180_',
            '证金持股',
            '预盈预增',
            'HS300_',
            '上证380',
            '中证500',
            '深成500',
            'MSCI中国',
            '沪股通',
            '创业板综',
            '深股通',
            '标准普尔',
            '融资融券',
            '富时罗素',
            '转债标的',
            '广东板块',
            '机构重仓',
            '浙江板块',
            '江苏板块',
            '基金重仓',
            '上海板块',
            '北京板块',
            '股权激励',
            '创投',
            '参股银行',
            'QFII重仓',
            '高送转',
            '山东板块',
            '深证100R',
            '参股券商',
            '股权转让',
            '茅指数',
            '养老金',
            '军民融合',
            '上证50_',
            '京津冀',
            '湖北自贸',
            'IPO受益',
            'AH股',
            '央视50',
            '央视50_',
            '地塞米松',
            '长江三角',
            '参股保险',
            '深圳特区',
            '雄安新区',
            'ST股',
            '',
        )

        sql = """SELECT theme from changed_bond_extend"""
        cur = get_cursor(sql)
        rows = cur.fetchall()
        word_count = {}
        for row in rows:
            if row[0] is None:
                continue
            words = row[0].split(' ')
            for word in words:
                if word in ignore_words or word.endswith('板块'):
                    continue

                count = word_count.get(word, 0)
                word_count[word] = count + 1

        new_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        words = []
        for key, value in new_words:
            # if value < 3:
            #     continue

            words.append((key, value))
        print(words)
        chart = WordCloud(opts.InitOpts(height='1000px', width='1424px', theme=ThemeType.MACARONS,
                                      chart_id='cb_wordcloud'))
        chart.add_js_funcs("""
            chart_cb_wordcloud.on('click', function(x){
                if(x.name == undefined) {return true;}
                if ($('#cb_detail_list').length==0){
                    $(document.body).append('<div id=\\'cb_detail_list\\'></div>')
                }
                $.get('/view_cb_wordcloud_detail.html?key=' + encodeURIComponent(x.name), function(result){
                    $('#cb_detail_list').html(result)
                    $('body,html').animate({scrollTop: $('#cb_detail_list').offset().top}, 500);
                })
            })
        """)
        chart.add(series_name="",
                # 添加数据
                data_pair=words,
                # 字间隙
                word_gap=5,
                # 调整字大小范围
                word_size_range=[5, 100],
                # shape="cardioid",
                is_draw_out_of_bound=True,
               rotate_step=90,
                #  选择背景图，也可以不加该参数，使用默认背景
                #  mask_image='购物车.jpg'
             )
        chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title="", title_textstyle_opts=opts.TextStyleOpts(font_size=23)
            ),
            tooltip_opts=opts.TooltipOpts(is_show=True),
        )
        html = """<br/><br/><br/><br/><br/><br/><br/>
        <center>
            <input type='text' id='theme_key_word'>&nbsp;<input type='button' value='查 询' id='btn_query' onclick="find_by_key_word()">
            <script>
                //回车执行查询事件(执行class='btn-query'的单击事件)
                $(document).keydown(function (event) {
                    if (event.keyCode == "13") {
                        //回车执行的事件
                        $("#btn_query").click();
                        return;
                    }
                });
                function find_by_key_word(){
                    if ($('#cb_detail_list').length==0){
                        $(document.body).append('<div id=\\'cb_detail_list\\'></div>');
                    }
                    $.get('/view_cb_wordcloud_detail.html?key=' + encodeURIComponent($('#theme_key_word').val()), 
                        function(result){
                            $('#cb_detail_list').html(result);
                            $('body,html').animate({scrollTop: $('#cb_detail_list').offset().top}, 500);
                        }
                    )
                }
            </script>
        </center>""" + chart.render_embed('template.html', env)

        return '可转债概念分析', views.nav_utils.build_analysis_nav_html(url), html
    except Exception as e:
        print("processing is failure. ", e)
        raise e


def generate_detail(key, is_login_user):
    cur = get_cursor("""
                SELECT DISTINCT d.*, e.hold_id, e.hold_amount as 持有数量
FROM (
         SELECT c.data_id                                                                                       as nid,
                c.bond_code,
                c.stock_code,
                c.cb_name_id                                                                                    as 名称,
                round(cb_premium_id * 100, 2) || '%'                                                            as 溢价率,
                cb_price2_id                                                                                    as '转债价格',
                cb_t_id                                                                                         as 距离转股日,

                round(cb_price2_id + cb_premium_id * 100, 2)                                                    as 双低值,
                round(bt_yield * 100, 2) || '%'                                                                 as 到期收益率,
                round(cb_trade_amount2_id * 100, 2) || '%'                                                      as '换手率(%)',
                round(cb_mov2_id * 100, 2) || '%'                                                               as 可转债涨跌,
                round(cb_mov_id * 100, 2) || '%'                                                                as 正股涨跌,

                c.stock_name                                                                                    as 正股名称,
                c.industry                                                                                      as '行业',
                c.sub_industry                                                                                  as '子行业',
                e.theme                                                                                         as 题材概念,

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
                remain_amount                                                                                   as '余额(亿元)',
                round(cb_to_share_shares * 100, 2) || '%'                                                       as '余额/股本(%)',

                fact_trend || '|' || fact_money || '|' || fact_news || '|' || fact_industry || '|' ||
                fact_base                                                                                       as '技术|资金|消息|行业|基本面',
                trade_suggest                                                                                   as 操作建议,

                rating                                                                                          as '信用',
                duration                                                                                        as 续存期,
                cb_ma20_deviate                                                                                 as 'ma20乖离',
                cb_hot                                                                                          as 热门度,
                cb_trade_amount_id                                                                              as '成交额(百万)',
                e.interest                                                                                      as 各期利息,
                case when e.ensure is not null then '有' else '无' END                                            as 担保,
                case when e.buy_back_term is not null then e.buy_back_term else '无' END                         as 回售条款,
                case when e.down_revise_term is not null then e.down_revise_term else '无' END                   as 下修条款,
                case when e.enforce_get_term is not null then e.enforce_get_term else '无' END                   as 强赎条款

         from (changed_bond c left join stock_report s on c.stock_code = s.stock_code)
                  left join changed_bond_extend e on c.bond_code = e.bond_code where theme like :theme
     ) d
         left join
     (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount
      from hold_bond
      where id in (select id
                   from hold_bond
                   where id
                             in
                         (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code))
     ) e
     on d.bond_code = e.bond_code
                                    """, {'theme': '%' + key + '%'})

    table, table_html = generate_table_html_with_data('', cur, '', need_title=False,
                                                      remark_fields=['盈亏', '到期收益率', '溢价率', '可转债涨跌', '正股涨跌'],
                                                      ignore_fields=['持有数量'],
                                                      is_login_user=is_login_user)
    html = generate_scatter_html_with_one_table(table,
                                                 title=key + '概念相关可转债',
                                                 use_personal_features=is_login_user)
    html += table_html
    return html
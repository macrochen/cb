# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
import views.nav_utils
from utils import html_utils
from utils.db_utils import get_cursor


# import matplotlib.pyplot as plt
from utils.trade_utils import calc_mid_data


def draw_view(url):
    try:

        html = ''

        # =========全网可转债涨跌幅柱状图=========
        cur = get_cursor("""select case
           when cb_price2_id < 90 then '低于90元'
           when cb_price2_id > 90 and cb_price2_id <= 100 then '[90元~100元]'
           when cb_price2_id > 100 and cb_price2_id <= 110 then '[100元~110元]'
           when cb_price2_id > 110 and cb_price2_id <= 120 then '[110元~120元]'
           when cb_price2_id > 120 and cb_price2_id < 130 then '[120元~130元]'
           when cb_price2_id > 130 and cb_price2_id <= 150 then '[130~150元]'
           when cb_price2_id > 150 and cb_price2_id <= 180 then '[150元~180元]'
           when cb_price2_id > 180 and cb_price2_id <= 200 then '[180元~200元]'
           when cb_price2_id > 200 and cb_price2_id <= 300 then '[200元~300元]'
           when cb_price2_id > 300 then '超过300元'
    end as 范围
     , count(id) as 个数, round(min(cb_price2_id), 2) as min_value, round(max(cb_price2_id), 2) as max_value
from (SELECT id, cb_price2_id, cb_name_id from changed_bond) c

group by case
           when cb_price2_id < 90 then '低于90元'
           when cb_price2_id > 90 and cb_price2_id <= 100 then '[90元~100元]'
           when cb_price2_id > 100 and cb_price2_id <= 110 then '[100元~110元]'
           when cb_price2_id > 110 and cb_price2_id <= 120 then '[110元~120元]'
           when cb_price2_id > 120 and cb_price2_id < 130 then '[120元~130元]'
           when cb_price2_id > 130 and cb_price2_id <= 150 then '[130~150元]'
           when cb_price2_id > 150 and cb_price2_id <= 180 then '[150元~180元]'
           when cb_price2_id > 180 and cb_price2_id <= 200 then '[180元~200元]'
           when cb_price2_id > 200 and cb_price2_id <= 300 then '[200元~300元]'
           when cb_price2_id > 300 then '超过300元'
             end
order by cb_price2_id""")
        rows = cur.fetchall()
        html += '<br/><br/><br/><br/><br/><br/>' + generate_bar_html(rows, '全网可转债价格范围分布情况')

        return '可转债价格范围分布', \
               views.nav_utils.build_analysis_nav_html(url), \
               html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


def generate_bar_html(rows, title):
    x = []
    y = []
    for row in rows:
        x.append(row[0])
        y.append({'value': row[1], 'range': [row[2], row[3]]})


    bar = Bar(init_opts=opts.InitOpts(height='700px', width='1424px', theme=ThemeType.SHINE, chart_id="cb_tree_map"))
    bar.add_xaxis(x)
    bar.add_yaxis("个数", y,
                  yaxis_index=0,
                  bar_width=50,
                  category_gap='1%',
                  gap='1%',
                  label_opts=opts.LabelOpts(
                      position="top",
                      formatter=JsCode(
                          "function(x){return x.data[0];}"
                      )
                  ),
                  )
    bar.set_series_opts(
        itemstyle_opts=opts.ItemStyleOpts(
            color=JsCode(
                "function(x){return x.data['range'][0]=='0'?'lightgray':(x.data['range'][0] < 0 ? 'lightgreen':'lightcoral')}"
            )
        )
    )
    bar.set_global_opts(
        title_opts=opts.TitleOpts(
            title="=========" + title + "=========",
            subtitle_textstyle_opts=opts.TextStyleOpts(font_weight='bold', font_size='15px'),
            pos_left='center',
            pos_top='-1px',
        ),
        tooltip_opts=opts.TooltipOpts(
            is_show=False
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(
            # data=None,
            # type_='category',
            # name_gap=0,
            # name_rotate=90,
            # axislabel_opts=opts.LabelOpts(
            #     rotate=-60,
            # ),
            name='价格涨跌区间',
            name_gap=35,
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
            name='个数',
            # name_rotate=90,
            name_gap=35,
            name_location='middle',
            # min_=0,
            # max_=max_value,
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                # symbol=['none', 'arrow']
            )
        ),
    )

    bar_html = bar.render_embed('template.html', html_utils.env)
    return bar_html

def generate_top_bar_html(rows, title):
    xx1 = []
    yy1 = []

    for row in rows:
        xx1.append(row[0].replace('转债', ''))
        yy1.append(row[1])

    bar = Bar(init_opts=opts.InitOpts(height='700px', width='1424px', theme=ThemeType.SHINE))
    # 底部x轴
    bar.add_xaxis(xx1)
    bar.add_yaxis('价格(元)', yy1,
                  bar_width=25,
                  category_gap='1%',
                  gap='1%',
                  label_opts=opts.LabelOpts(
                      position="top",
                  ),
                  )
    bar.set_series_opts(
        itemstyle_opts=opts.ItemStyleOpts(
            color=JsCode(
                "function(x){return x.data>0?'#c23531':'#1d953f'}"
            )
        )
    )
    bar.set_global_opts(
        title_opts=opts.TitleOpts(
            title="=========" + title + "=========",
            pos_left='center',
            pos_top='-1px',
        ),
        tooltip_opts=opts.TooltipOpts(
            is_show=False
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
            name='价格(元)',
            # name_rotate=90,
            name_gap=40,
            name_location='middle',
            # min_=0,
            is_scale=True,
            # axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                # symbol=['none', 'arrow']
            )
        ),
    )

    bar_html = bar.render_embed('template.html', html_utils.env)
    return bar_html
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


def draw_view(url):
    try:

        html = ''

        # =========全网可转债涨跌幅柱状图=========
        cur = get_cursor("""select case
           when cb_mov2_id < -20 then '低于-20%'
           when cb_mov2_id > -20 and cb_mov2_id <= -10 then '[-20%~-10%]'
           when cb_mov2_id > -10 and cb_mov2_id <= -5 then '[-10%~-5%]'
           when cb_mov2_id > -5 and cb_mov2_id <= -1 then '[-5%~-1%]'
           when cb_mov2_id > -1 and cb_mov2_id < 0 then '[-1%~0]'
           when cb_mov2_id = 0 then '[0]'
           when cb_mov2_id > 0 and cb_mov2_id <= 1 then '[0~1%]'
           when cb_mov2_id > 1 and cb_mov2_id <= 5 then '[1%,5%]'
           when cb_mov2_id > 5 and cb_mov2_id <= 10 then '[5%,10%]'
           when cb_mov2_id > 10 and cb_mov2_id <= 20 then '[10~20%]'
           when cb_mov2_id > 20 then '超过20%'
    end as 范围
     , count(id) as 个数, round(min(cb_mov2_id), 2) as min_value, round(max(cb_mov2_id), 2) as max_value
from (SELECT id, cb_mov2_id * 100 as cb_mov2_id, cb_name_id from changed_bond) c

group by case
             when cb_mov2_id < -20 then '低于-20%'
             when cb_mov2_id > -20 and cb_mov2_id <= -10 then '[-20%~-10%]'
             when cb_mov2_id > -10 and cb_mov2_id <= -5 then '[-10%~-5%]'
             when cb_mov2_id > -5 and cb_mov2_id <= -1 then '[-5%~-1%]'
             when cb_mov2_id > -1 and cb_mov2_id < 0 then '[-1%~0]'
             when cb_mov2_id = 0 then '[0]'
             when cb_mov2_id > 0 and cb_mov2_id <= 1 then '[0~1%]'
             when cb_mov2_id > 1 and cb_mov2_id <= 5 then '[1%,5%]'
             when cb_mov2_id > 5 and cb_mov2_id <= 10 then '[5%~10%]'
             when cb_mov2_id > 10 and cb_mov2_id <= 20 then '[10~20%]'
             when cb_mov2_id > 20 then '超过20%'
             end
order by cb_mov2_id""")
        rows = cur.fetchall()
        html += generate_bar_html(rows, '全网可转债涨跌幅情况')

        return '可转债涨跌幅分布', \
               views.nav_utils.build_analysis_nav_html(url), \
               html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


def generate_bar_html(rows, title):
    x = []
    y = []
    up_count = 0
    down_count = 0
    for row in rows:
        x.append(row[0])
        y.append({'value': row[1], 'range': [row[2], row[3]]})

        if row[3] < 0:
            down_count += row[1]
        elif row[2] > 0:
            up_count += row[1]

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
            subtitle="(跌:" + str(down_count) + " 涨:" + str(up_count) + ")",
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
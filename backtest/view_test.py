import datetime
import json

from pyecharts import options as opts
from pyecharts.charts import Line, Timeline, Bar
from pyecharts.globals import ThemeType

from backtest.test_utils import get_max_drawdown
from utils.db_utils import get_cursor
from utils.html_utils import env
import numpy as np

# from empyrical import max_drawdown, alpha_beta


def generate_timeline_html(time_data):
    tl = Timeline()
    tl.add_schema(is_auto_play=False,
                  play_interval=500,
                  is_loop_play=False)
    for date, bonds in time_data.items():
        _date = datetime.datetime.strftime(date, '%Y-%m-%d')
        x = []
        y = []
        bonds = sorted(bonds.items(), key=lambda i: i[1], reverse=False)
        for name, money, in bonds:
            x.append(name)
            y.append(money)

        bar = (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.ROMANTIC))
                .add_xaxis(x)
                .add_yaxis("价格", y)
                # .add_yaxis("投入资金", y)
                .reversal_axis()
                .set_series_opts(label_opts=opts.LabelOpts(is_show=True, position='right'),
                                 )
                .set_global_opts(
                legend_opts=opts.LegendOpts(is_show=True),
                title_opts=opts.TitleOpts("{}可转债组合".format(_date)),
            )
        )
        tl.add(bar, "{}".format(_date))
    return "<center>" + tl.render_embed('template.html', env) + "</center>"


def generate_line_html(rows, period, start, end, bond_num, line_names=[], title=None, max_price=None,
                       max_double_low=None):
    # 用散点图展示
    line = Line(opts.InitOpts(height='700px', width='1424px', theme=ThemeType.LIGHT))

    x, data = get_line_data(rows, line_names)
    # i = 0
    # y1_max = None
    # y1_min = None
    # y2_max = None
    # y2_min = None
    # for e in x:
    #     if i == y1_start:
    #         y1_max = e
    #     elif i == y1_end:
    #         y1_min = e
    #
    #     if i == y2_start:
    #         y2_max = e
    #     elif i == y2_end:
    #         y2_min = e
    #     i += 1
    line.add_xaxis(x)
    for d in data:
        line.add_yaxis(d[0], d[1])

    line.set_global_opts(
        title_opts=opts.TitleOpts(title=title if title is not None else "各种轮动策略回测结果",
                                  subtitle=get_subtitle(bond_num, end, period, start, max_price, max_double_low),
                                  pos_left='center'),
        tooltip_opts=opts.TooltipOpts(
            trigger='axis',
        ),
        legend_opts=opts.LegendOpts(
            pos_top=50,
            pos_left=160,
            orient='vertical'
            # selected_mode='single'
        ),
        datazoom_opts={'start': 0, 'end': 100},
        toolbox_opts=opts.ToolboxOpts(feature={
            'dataZoom': {},
        }
        ),
        # visualmap_opts=opts.VisualMapOpts(
        #     type_="color", max_=150, min_=20, dimension=1
        # ),
        xaxis_opts=opts.AxisOpts(
            # data=None,
            type_='time',
            name='时间',
            name_gap=30,
            is_scale=True,
            name_location='middle',
            splitline_opts=opts.SplitLineOpts(is_show=False),
            # axislabel_opts=opts.LabelOpts(formatter="{value}"), #echarts.format.formatTime('yy-MM-dd', value*1000)
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        ),
        yaxis_opts=opts.AxisOpts(
            type_='value',
            name='收益率(%)',
            name_rotate=90,
            name_gap=55,
            name_location='middle',
            is_scale=True,
            axislabel_opts=opts.LabelOpts(formatter='{value}%'),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(
                is_on_zero=False,
                symbol=['none', 'arrow']
            )
        )
    )
    line.set_series_opts(
        symbol='none',
        smooth=False,
        label_opts=opts.LabelOpts(is_show=False),
        # markarea_opts=opts.MarkAreaOpts(
        #     is_silent=False,
        #     data=[
        #         opts.MarkAreaItem(
        #             name="" + str(y1_mdd) + "%",
        #             x=(y1_max, y1_min),
        #             label_opts=opts.LabelOpts(is_show=True, color="#DCA3A2"),
        #             itemstyle_opts=opts.ItemStyleOpts(color="#DCA3A2", opacity=0.5),
        #         ),
        #         opts.MarkAreaItem(
        #             name="" + str(y2_mdd) + "%",
        #             x=(y2_max, y2_min),
        #             label_opts=opts.LabelOpts(is_show=True, color="#b0fca2"),
        #             itemstyle_opts=opts.ItemStyleOpts(color="#b0fca2", opacity=0.5),
        #         )
        #     ]
        # )
    )
    line_html = line.render_embed('template.html', env)
    return "<br/>" + line_html


def get_subtitle(bond_num, end, period, start, max_price, max_double_low):
    s = "回测时间:" + datetime.datetime.strftime(start, '%Y-%m-%d') + "~" + datetime.datetime.strftime(end, '%Y-%m-%d')
    if period is not None and bond_num is not None:
        s += ", " + str(bond_num) + "只可转债, " + str(period) + "个交易日轮动"
    if max_price is not None:
        s += ", 价格上限:" + str(max_price) + "元"
    if max_double_low is not None:
        s += ", 估值上限:" + str(max_double_low)
    return s


def get_line_data(rows, line_names=[]):
    data = []
    x = []

    lines_data = {}
    for line_name in line_names:
        lines_data.setdefault(line_name, {"rate": [], "money": [], "day_rate": []})

    add_base_data(lines_data, rows, x)

    for line_data in lines_data.values():
        mdd, start, end, max_profit = get_max_drawdown(x, line_data['rate'], line_data['money'])
        line_data.setdefault('mdd', mdd)
        line_data.setdefault('max_profit', max_profit)
        line_data.setdefault('sharp_ratio', get_sharpe_ratio(line_data['day_rate']))

    for line, line_data in lines_data.items():
        current_rate = line_data['rate'][len(line_data['rate']) - 1]
        data.append(
            [line
             + "(最大回撤:" + str(line_data['mdd']) + "%, "
             + "夏普比率:" + str(line_data['sharp_ratio']) + "%, "
             + "最高收益:" + str(line_data['max_profit']) + "%, "
             + "当前收益:" + str(current_rate) + "%)",
             line_data['rate'], current_rate])

    data = sorted(data, key=lambda d: d[2], reverse=True)
    return x, data


def get_sharpe_ratio(return_list):
    '''夏普比率'''
    average_return = np.mean(return_list)
    return_stdev = np.std(return_list)
    # 10年国债无风险收益率: https://www.chinabond.com.cn/d2s/cbData.html
    sharpe_ratio = (average_return - 0.027957) * np.sqrt(252) / return_stdev  # 默认252个工作日
    return round(sharpe_ratio, 2)


def add_base_data(lines_data, rows, x):
    base = None
    original_price = 1000
    pre_price = None
    base_rate = 0
    day_rate = 0
    index_line_data = {"rate": [], "money": [], "day_rate": []}
    idx_data = get_idx_data()
    for date, value in rows.items():
        price = idx_data.get(date)
        if pre_price is None:
            pre_price = price

        if base is None:
            if price is not None:
                base = price

        x.append(datetime.datetime.strftime(date, '%Y-%m-%d'))

        i = 0
        for v in lines_data.values():
            v['rate'].append(value[i][0])
            v['money'].append(value[i][1])
            v['day_rate'].append(value[i][2])
            i += 1

        if price is not None:
            base_rate = round((price - base) / base * 100, 2)
            day_rate = round((price - pre_price) / pre_price * 100, 2)
            original_price = price
        index_line_data['rate'].append(base_rate)
        index_line_data['money'].append(original_price)
        index_line_data['day_rate'].append(day_rate)

        pre_price = original_price
    lines_data.setdefault('可转债等权指数', index_line_data)


def get_idx_data():
    cur = get_cursor("select date, idx_data from cb_index_history")
    idx_rows = cur.fetchall()
    idx_data = {}
    for idx_row in idx_rows:
        ss = idx_row[0].split()
        idx_data[datetime.datetime.strptime(ss[0], '%Y-%m-%d')] = idx_row[1]
    return idx_data


if __name__ == "__main__":
    # get_data()
    print(round(10 * 2 / 3, 0))

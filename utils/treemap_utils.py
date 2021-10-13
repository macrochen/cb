import math

from pyecharts import options as opts
from pyecharts.charts import TreeMap
from pyecharts.commons.utils import JsCode

from utils.db_utils import get_dict_row
from utils.html_utils import env


def hsv2rgb(h, s, v):
    h = float(h)
    s = float(s)
    v = float(v)
    h60 = h / 60.0
    h60f = math.floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0: r, g, b = v, t, p
    elif hi == 1: r, g, b = q, v, p
    elif hi == 2: r, g, b = p, v, t
    elif hi == 3: r, g, b = p, q, v
    elif hi == 4: r, g, b = t, p, v
    elif hi == 5: r, g, b = v, p, q
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return str(r), str(g), str(b)


def red_hsv2rgb(v):
    r, g, b = hsv2rgb(700, 0.8, 1 - v)
    return "rgb(" + r + ',' + g + ',' + b + ')'


def green_hsv2rgb(v):
    r, g, b = hsv2rgb(500, 0.5, 0.4 + v)
    return "rgb(" + r + ',' + g + ',' + b + ')'


def calc_range(max_rise, min_rise):
    rise_range = []
    color_range = []
    v = 0.5
    if min_rise >= 0:  # 都是正数, 只用红色部分
        # 将范围值分成一个五部分的数组
        piece = (max_rise - min_rise) / 5
        set_range(piece, min_rise, rise_range, color_range, red_hsv2rgb)
    elif max_rise < 0:  # 都是负数, 只用绿色部分
        # 将范围值分成一个五部分的数组
        piece = (max_rise - min_rise) / 5
        set_range(piece, min_rise, rise_range, color_range, green_hsv2rgb)
    else:  # 有负有正, 拆成正负两部分组装数组
        # 将范围值分成一个五部分的数组
        piece = (0 - min_rise) / 5
        set_range(piece, min_rise, rise_range, color_range, green_hsv2rgb, ignore_end=False)

        piece = max_rise / 5
        set_range(piece, 0, rise_range, color_range, red_hsv2rgb, ignore_start=False)
    return color_range, rise_range


def set_range(piece, min, rise_range, color_range, transfer, ignore_start=True, ignore_end=True):
    for i in range(1, 6):
        max = min + piece
        if i == 1 and ignore_start:
            rise_range.append({'max': max})
        elif i == 5 and ignore_end:
            rise_range.append({'min': min})
        else:
            rise_range.append({'min': min, 'max': max})

        color_range.append(transfer(0.1 * i))
        min = max


def generate_treemap_html(cur, title, key_field_name, area_field_name, click_link, area_data_name='数量', area_data_unit='个'):
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
        data.append(opts.TreeItem(name=item[key_field_name],
                                  # value 包含持仓占比和涨跌幅两项数据
                                  value=[item[area_field_name], rise_value],
                                  label_opts=opts.LabelOpts(position='insideBottomLeft',
                                                            formatter='{name|{b}}{rise|%s}' % rise, rich=rich)))
        item_opts.append(tree_item)

    color_range, rise_range = calc_range(max_rise, min_rise)

    tooltip_js = """function (param) 
    {   const color = param.value[1] > 0 ? '#FF0000' : '#2E8B57';
        const detail_style = `color:${color};`;
        const msgContent = `<div style='width:fit-content;height:fit-content;'>
            ${param.name}<br/>
            """ + area_data_name + """：&nbsp<span style='color:'#fff';'>&nbsp${param.value[0]}&nbsp""" + area_data_unit + """&nbsp&nbsp</span><br/>
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
            window.location.replace('""" + click_link + """?key=' + encodeURIComponent(params['data']['name']) + '&rise=' + params['data']['value'][1] + '#cb_detail_list')
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
           tooltip_opts=opts.TooltipOpts(is_show=True, formatter=JsCode(tooltip_js),
                                         textstyle_opts=opts.TextStyleOpts(font_size=14)),
           color_mapping_by='value',
           )
    tp.set_global_opts(title_opts=opts.TitleOpts(title=title, pos_left='center', pos_top='30px'),
                       legend_opts=opts.LegendOpts(is_show=False),
                       visualmap_opts=opts.VisualMapOpts(is_show=False,
                                                         type_='color',
                                                         min_=min_rise,
                                                         max_=max_rise,
                                                         range_color=color_range,
                                                         # 指定使用的数据维度
                                                         dimension=1,
                                                         is_piecewise=True,
                                                         pieces=rise_range
                                                         ),
                       )

    return tp.render_embed('template.html', env)
from prettytable import from_db_cursor
from pyecharts import options as opts
from pyecharts.charts import Tree
from pyecharts.commons.utils import JsCode

from utils.db_utils import get_record
from utils.html_utils import env


def generate_chart_html(table, title, click_link):
    chart = Tree(init_opts=opts.InitOpts(theme='white',
                                      width='1024px',
                                      height='1000px',
                                      chart_id='cb_tree'
                                     ))
    chart.add_js_funcs("""
        chart_cb_tree.on('click', function(x){
            if(x.data['is_child'] == undefined) {return true;}
            if ($('#cb_detail_list').length==0){
                $(document.body).append('<div id=\\'cb_detail_list\\'></div>')
            }
            $.get('""" + click_link + """?key=' + encodeURIComponent(x['data']['name']), function(result){
                $('#cb_detail_list').html(result)
                $('body,html').animate({scrollTop: $('#cb_detail_list').offset().top}, 500);
            })
        })
    """)

    data = get_data(table)
    chart.add(
        series_name='',
        data=data,
        initial_tree_depth=1,
        label_opts=opts.LabelOpts(
            is_show=False
        ),
    )
    chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title="=========" + title + "=========",
            subtitle_textstyle_opts=opts.TextStyleOpts(font_weight='bold', font_size='15px'),
            pos_left='center',
            pos_top='-1px',
        ),
        tooltip_opts=opts.TooltipOpts(
            is_show=False
        )
    )
    chart.set_series_opts(
        label_opts=opts.LabelOpts(
            formatter=JsCode("""function (x){return x.data['name'] + '(均值:' + x.data['value'] + ', ' + x.data['count'] + x.data['suffix'] + ')';}""")
        )
    )
    return chart.render_embed('template.html', env)


def get_data(table):
    options = table._get_options({})
    rows = table._get_rows(options)
    # 构造父子关系图
    parent = []
    industries = get_industry_rows(rows, table)
    p_count = 0
    p_sum = 0
    j = 0
    for industry, rows in industries.items():
        children = []
        count = 0
        sum = 0
        i = 0
        for row in rows:
            i += 1
            record = get_record(table, row)
            sub_industry = record['sub_industry']
            value = record['value']
            sum += record['sum']
            count += record['count']
            children.append({'name': sub_industry, 'value': value, 'count': record['count'], 'is_child': True, 'suffix': '只可转债'})
        parent.append({'name': industry, 'children': children, 'value': round(sum / count, 2), 'count': i, 'suffix': '个子行业'})
        p_count += count
        p_sum += sum
        j += 1
    parent.sort(key=lambda x: x['value'])
    return [{'name': '所有行业', 'children': parent, 'value': round(p_sum/p_count, 2), 'count': j, 'suffix': '个行业'}]


def get_industry_rows(rows, table):
    industries = {}
    for row in rows:
        record = get_record(table, row)
        industry = record['industry']
        if industry in industries.keys():
            continue
        s_rows = get_sub_rows(industry, rows, table)
        industries[industry] = s_rows

    return industries


def get_sub_rows(industry, rows, table):
    children = []

    for row in rows:
        record = get_record(table, row)
        s = record['industry']
        if industry == s:
            children.append(row)
    return children
# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
import utils.table_html_utils
import views.nav_utils
from utils import db_utils, html_utils, trade_utils, table_html_utils
from utils.db_utils import get_cursor
from views import view_utils


# import matplotlib.pyplot as plt


def draw_my_view(user_id):
    is_login_user = user_id is not None
    try:

        html = '<br/><br/><br/><br/><br/>'

        cur = get_cursor("""select h.id,
       c.data_id   as nid,
       c.stock_code,
       hold_id,
       h.bond_code,
       h.cb_name_id  as 名称,
       price       as 成交价,
       amount      as 成交量,
       fee         as 费用,
       create_date as 成交时间,
       account     as 交易账号,
       strategy_type     as 策略类型
from trade_history h,
     changed_bond c
where h.bond_code = c.bond_code
  and owner_id = :user_id and h.is_delete = 0
order by create_date desc
limit 20""", {'user_id':user_id})
        table_html_utils.operation_html_content.maker = operation_html_content_makter

        html = table_html_utils.generate_simple_table_html(cur, html, is_login_user=is_login_user)

        html += """
        <script>
            function undo_trade(cur, id){
                var r=confirm("确认要撤回?");
                if (r == true){
                    tr = cur.parentElement.parentElement
                    $.get("/un_save_trade_data.html/" + id, function (data, status) {
                        // alert(data)
                        if (status == 'success') {
                            alert('undo save is successful')
                            tr.remove()
                        } else {
                            alert("undo trade is failure. id:" + id)
                        }
                    }).error(function (XMLHttpRequest, status, error){
                        // alert("occur exception. not find bond by code:" + $("#bond_code").val())
                    })
                }
            }
        </script>
        """

        return '我的可转债交易记录', ''.join(views.nav_utils.build_personal_nav_html_list('/view_my_trade_history.html')), html

    except Exception as e:
        print("processing is failure. ", e)
        raise e

def operation_html_content_makter(id, hold_id, bond_code):
    return "&nbsp;<a href='javascript:void()' onclick='undo_trade(this, " + str(id) + ")'><img src='../static/img/undo.png' alt='撤销' title='撤销' width='14' height='14' class='next-site-link'/></a>"

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
            yy1.append({'value': row[2], 'bond_code': bond_code})
        else:
            xx2.insert(0, row[1].replace('转债', ''))
            yy2.insert(0, {'value': round(-float(row[2])+0, 2), 'bond_code': bond_code})

    max_value = 0
    size = len(yy1)

    for i in range(size):
        if yy1[i]['value'] + abs(yy2[i]['value']) > max_value:
            max_value = yy1[i]['value'] + abs(yy2[i]['value'])

    max_value = round(max_value * 0.7, 2) + 1

    chart_id = str(abs(hash(title)))
    bar = Bar(init_opts=opts.InitOpts(height='700px', width='1424px', theme=ThemeType.SHINE, chart_id=chart_id))

    bar.add_js_funcs(
        'chart_' + chart_id + """.on('click', function(params){
            // alert(params)
            popWin.showWin("1200","600", params['data']['bond_code']);
        })
    """)
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

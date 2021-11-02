# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

# import matplotlib.pyplot as plt
#
#
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
from pyecharts.commons.utils import JsCode

from utils.echarts_html_utils import generate_scatter_html_with_one_table
import utils.table_html_utils
from utils import db_utils
from utils.db_utils import get_cursor
from views.nav_utils import build_select_nav_html


def generate_table_html(table, html,
                        remark_fields=[], is_login_user=False, field_links={},
                        support_selected_operation=None):

    if table.rowcount == 0:
        return table, html

    return table, html + utils.table_html_utils.build_table_html(table, remark_fields, ignore_fields=['持有数量', ],
                                                                 is_login_user=is_login_user, field_links=field_links,
                                                                 support_selected_operation=support_selected_operation
                                                                 )


def draw_view(is_login_user):
    # 打开文件数据库
    try:

        html = ''

        # =========我的转债自选集=========
        cur = get_cursor("""
            SELECT b.id,
                   h.id                                                                     as hold_id,
                   h.hold_amount                                                            as 持有数量,
                   c.data_id                                                                as nid,
                   c.bond_code,
                   c.stock_code,
                   c.cb_name_id                                                             as 名称,
                   round(cb_mov2_id * 100, 2) || '%'                                        as 可转债涨跌,
                   cb_price2_id                                                             as 转债价格,
                   round(cb_premium_id * 100, 2) || '%'                                     as 溢价率,
                   b.memo                                                                   as 备注,
                   h.hold_price || ' (' || h.hold_amount || ')'                             as '成本(量)',
                   round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) || '(' ||
                   round((c.cb_price2_id - h.hold_price) / c.cb_price2_id * 100, 2) || '%)' as 盈亏,
                   remain_amount                                                            as '余额(亿元)',
                   c.stock_name                                                             as 正股名称,
                   c.industry                                                               as '行业',
                   round(cb_mov_id * 100, 2) || '%'                                         as 正股涨跌,
                   round(bt_yield * 100, 2) || '%'                                          as 到期收益率,
                   b.strategy_type                                                          as 策略,
                   --strftime('%Y-%m-%d %H:%M', b.create_date)                                as 创建时间,
                   strftime('%Y-%m-%d %H:%M', b.modify_date)                                as 最近修改
            from changed_bond_select b
                     left join (select *
                                from hold_bond
                                where id in (select min(id)
                                             from hold_bond
                                             where hold_owner = 'me'
                                               and hold_amount > 0
                                             group by bond_code)) h on b.bond_code = h.bond_code,
                 changed_bond c
            WHERE c.bond_code = b.bond_code
              and b.is_deleted != 1
            order by b.modify_date desc

            """)

        table = db_utils.from_db(cur)

        scatter_html = generate_scatter_html_with_one_table(table, use_personal_features=is_login_user,
                                                            hover_maker=hover_maker,
                                                            hover_content_field='备注',
                                                            )

        table, html = generate_table_html(table, html,
                                          remark_fields=['策略',  '到期收益率', '溢价率', '可转债涨跌', '正股涨跌'],
                                          is_login_user=is_login_user, field_links={'备注': select_link_maker},
                                          support_selected_operation={'name': '删除', 'url': '/delete_selected_bond.html'}
                                          )

        return '我的可转债自选', build_select_nav_html('/view_my_select.html'), '<br/><br/>' + scatter_html + "<br/>" + html + '<br/><br/>'

    except Exception as e:
        print("processing is failure. ", e)
        raise e


def hover_maker(s):
    hover_text = """function (params) {
                    return '<p style="width:300px;display:block;word-break: break-all;word-wrap: break-word;white-space:pre-wrap">' + params.data.value[5] + '<br/>' +
                          '<font style="color:red">转股价:' + params.data.value[1] + '元<br/>' +
                          '溢价率:' + params.value[2] + '%<br/></font>' +
                          '</p>'  
                 }"""
    return JsCode(hover_text)


def select_link_maker(data, record):
    if data is None or data.strip(' ') == '':
        data = '编辑'

    org_data = data
    if len(data) > 6:
        data = data[0:6] + "..."

    return "<a href='/edit_changed_bond_select.html/" + record['bond_code'] + "/' title='" + org_data + "'>" + data + "</a>"

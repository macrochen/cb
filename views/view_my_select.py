# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

# import matplotlib.pyplot as plt
#
#
# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
import utils.echarts_html_utils
import utils.table_html_utils
from utils import db_utils
from utils.db_utils import get_cursor


def generate_table_html(cur, html, ext_field_names=None, rows=None,
                        remark_fields=[], is_login_user=False, field_links={}):
    table = db_utils.from_db(cur, ext_field_names, rows)

    if table.rowcount == 0:
        return html

    return table, html + utils.table_html_utils.build_table_html(table, remark_fields, ignore_fields=['持有数量', ],
                                                                 is_login_user=is_login_user, field_links=field_links)


def draw_view(is_login_user):
    # 打开文件数据库
    try:

        html = '<br/><br/><br/><br/><br/><br/><br/>'

        # =========我的转债自选集=========
        cur = get_cursor("""
    SELECT b.id, h.id as hold_id, h.hold_amount as 持有数量,
        c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌,   
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
         
        c.stock_name as 正股名称, c.industry as '行业',round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
        round(bt_yield*100,2) || '%' as 到期收益率,
        --remain_amount as '余额(亿元)',
        
        b.strategy_type as 策略, b.memo as 备注
    from changed_bond_select b left join hold_bond h on b.bond_code = h.bond_code,  
        changed_bond c
    WHERE  c.bond_code = b.bond_code
    --order  by cb_mov2_id desc
            """)

        table, html = generate_table_html(cur, html,
                                   remark_fields=['策略',  '到期收益率', '溢价率', '可转债涨跌', '正股涨跌'],
                                   is_login_user=is_login_user, field_links={'备注': select_link_maker})

        scatter_html = utils.echarts_html_utils.generate_scatter_html_with_one_table(table, use_personal_features=is_login_user)

        return '我的可转债自选', '<li><a href="/">Home</a></li>', html + "<br/>" + scatter_html + '<br/><br/>'

    except Exception as e:
        print("processing is failure. ", e)
        raise e

def select_link_maker(data, record):
    if data is None or data.strip(' ') == '':
        data = '编辑'

    return "<a href='/edit_changed_bond_select.html/" + record['bond_code'] + "/'>" + data + "</a>"

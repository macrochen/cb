# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

import sqlite3

import common

import matplotlib.pyplot as plt


plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']


def generate_table_html(cur, html, field_names=None, rows=None,
                        remark_fields_color=[], is_login_user=False):
    table = common.from_db(cur, field_names, rows)

    if len(table._rows) == 0:
        return html

    return table, html + common.get_html_string(table, remark_fields_color,
                                         edit_link="/edit_changed_bond_select.html", is_login_user=is_login_user)


def draw_view(is_login_user):
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    cur = con_file.cursor()
    try:

        html = '<br/><br/><br/><br/><br/><br/><br/>'

        # =========我的转债自选集=========
        cur.execute("""
    SELECT b.id, c.data_id as nid, c.bond_code, c.stock_code, c.cb_name_id as 名称, 
        round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌,   
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, 
         
        c.stock_name as 正股名称, c.industry as '行业',round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
        round(bt_yield*100,2) || '%' as 到期收益率,
        --remain_amount as '余额(亿元)',
        
        b.strategy_type as 策略, b.memo as 备注
    from changed_bond c, 
        stock_report s, 
        hold_bond h,
        changed_bond_select b
    WHERE c.stock_code = s.stock_code and  c.bond_code = h.bond_code and c.bond_code = b.bond_code
        and h.hold_owner = 'me' and hold_amount > 0
    order  by cb_mov2_id desc
            """)

        table, html = generate_table_html(cur, html,
                                   remark_fields_color=['策略',  '到期收益率', '溢价率', '可转债涨跌', '正股涨跌'],
                                   is_login_user=is_login_user)

        scatter_html = common.generate_scatter_html({'所有': table})

        con_file.close()

        return '我的可转债自选', '<li><a href="/">Home</a></li>', html + "<br/>" + scatter_html

    except Exception as e:
        con_file.close()
        print("processing is failure. ", e)
        raise e


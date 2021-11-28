# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# https://blog.csdn.net/idomyway/article/details/82390040

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
import views.nav_utils
from utils import table_html_utils
from utils.db_utils import get_cursor


# import matplotlib.pyplot as plt


def draw_my_view(user_id, bond_code, url):
    is_login_user = user_id is not None
    try:

        html = ''

        cur = None
        if bond_code != '':
            cur = get_cursor("""select h.id,
                   c.data_id   as nid,
                   c.stock_code,
                   hold_id,
                   h.bond_code,
                   h.cb_name_id  as 名称,
                   price|| (case when amount > 0 then  '(<font style=color:green>买入</font>)' else '(<font style=color:red>卖出</font>)' end)       as 成交价,
                   abs(amount)       as 成交量,
                   fee         as 费用,
                   create_date as 成交时间,
                   account     as 交易账号,
                   strategy_type     as 策略类型
            from trade_history h,
                 changed_bond c
            where h.bond_code = c.bond_code
              and owner_id = :user_id and h.is_delete = 0
              and h.bond_code = :bond_code
            order by create_date desc
            limit 20""", {'user_id': user_id, 'bond_code': bond_code})
        else:
            cur = get_cursor("""select h.id,
                   c.data_id   as nid,
                   c.stock_code,
                   hold_id,
                   h.bond_code,
                   h.cb_name_id  as 名称,
                   price|| (case when amount > 0 then  '(<font style=color:green>买入</font>)' else '(<font style=color:red>卖出</font>)' end)       as 成交价,
                   abs(amount)       as 成交量,
                   fee         as 费用,
                   create_date as 成交时间,
                   account     as 交易账号,
                   strategy_type     as 策略类型
            from trade_history h,
                 changed_bond c
            where h.bond_code = c.bond_code
              and owner_id = :user_id and h.is_delete = 0
            order by create_date desc
            limit 20""", {'user_id': user_id})

        html = table_html_utils.generate_simple_table_html(cur, html, is_login_user=is_login_user,
                                                           edit_link_maker=operation_html_content_maker)

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

        return '我的可转债交易记录', views.nav_utils.build_personal_nav_html(url), html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


def operation_html_content_maker(id, hold_id, bond_code):
    return "&nbsp;<a href='javascript:void(0)' onclick='undo_trade(this, " + str(id) + ")'><img src='/static/img/undo.png' alt='撤销' title='撤销' width='14' height='14' class='next-site-link'/></a>" + get_trade_link(id)


def get_trade_link(id):
    s = "&nbsp;<a href='"
    s += '/new_grid_trade_data.html/' + str(id) + '/'
    s += "'><img src='/static/img/trade.png' alt='交易' title='交易' width='14' height='14' class='next-site-link'/></a>"
    return s

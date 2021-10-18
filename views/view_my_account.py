# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# https://gallery.pyecharts.org/#/README

# import matplotlib.pyplot as plt

# plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# 单选
import utils.echarts_html_utils
import utils.table_html_utils
import views.nav_utils
from utils import db_utils
from utils.db_utils import get_cursor
from views import view_utils

select = [
    "银河",
    "财通",
    "华泰",
    "华宝",
    "其他",
]



def draw_my_view(is_login_user):
    # 打开文件数据库
    try:

        html = ''
        tables = {}
        nav_html_list = views.nav_utils.build_personal_nav_html_list('/view_my_account.html')

        # =========银河=========
        account = '银河'
        html = generate_account_block(account, html, nav_html_list, tables, is_login_user=is_login_user)

        # =========华宝=========
        #fixme 华宝证券的手和张要分开处理(如果是手, 要除以10)
        account = '华宝'
        html = generate_account_block(account, html, nav_html_list, tables, 10, is_login_user=is_login_user)

        # =========其他=========
        account = '其他'
        html = generate_account_block(account, html, nav_html_list, tables, is_login_user=is_login_user)

        # 数据汇总

        # 用来画统计图的数据

        cur = get_cursor("""
SELECT account as 账户, 
     
    count(h.bond_code) as 个数, 
    sum(h.hold_amount) as 数量,
    
    round(sum(h.sum_buy-h.sum_sell),2) as 投入金额, 
    round(sum(h.hold_amount * c.cb_price2_id),2) as 市值, 
    
    round(sum(round((c.cb_price2_id/(1+c.cb_mov2_id) * c.cb_mov2_id)*h.hold_amount, 2)), 2) as '日收益', 
    round((round(sum(c.cb_price2_id*h.hold_amount)/sum(c.cb_price2_id/(1+c.cb_mov2_id)*h.hold_amount),4)-1)*100,2) || '%' as '日收益率',
    
    round(sum(round(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy, 3)), 2) as '累积收益',   
    round(sum(round(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy, 3)) /sum(h.sum_buy - h.sum_sell) * 100, 2) || '%' as 累积收益率
from hold_bond h , changed_bond c 
where h.bond_code = c.bond_code and hold_owner='me' GROUP by account order by 投入金额 DESC        
        """)

        rows = []
        dict_rows = []
        # 增加合计行
        total_money = 0
        assets_money = 0
        total_profit = 0
        total_now_profit = 0
        total_now_profit_rate = 0
        total_amount = 0
        total_num = 0

        money_rows = []
        for row in cur.fetchall():
            rows.append(row)
            dict_row = db_utils.get_dict_row(cur, row)
            dict_rows.append(dict_row)
            asset_row = dict_row['市值']
            money_row = dict_row['投入金额']
            money_rows.append(money_row)
            total_money += money_row
            assets_money += asset_row
            total_profit += dict_row['累积收益']
            total_now_profit += dict_row['日收益']
            total_num += dict_row['个数']
            total_amount += dict_row['个数'] * dict_row['数量']

        money_rows.reverse()
        new_rows = []
        for row in rows:
            money_row = money_rows.pop()
            new_row = row + (str(round(money_row/total_money*100, 2)) + '%',)
            new_rows.append(new_row)

        total_yield = round(total_profit / total_money * 100, 2)
        total_now_yield = round(total_now_profit / total_money * 100, 2)
        new_rows.append(['合计', total_num, total_amount, round(total_money, 2), round(assets_money, 2), round(total_now_profit, 2), str(round(total_now_yield, 2))+'%', round(total_profit, 2), str(total_yield) + '%', '100%'])

        pie_html = utils.echarts_html_utils.generate_pie_html(dict_rows, '账户', '投入金额')

        sum_html = utils.table_html_utils.generate_table_html("汇总", cur, '', need_title=False, ext_field_names=['投入占比'],
                                                              remark_fields=['日收益', '日收益率', '累积收益率', '累积收益'],
                                                              rows=new_rows, ignore_fields=['投入金额'],
                                                              is_login_user=is_login_user)

        # 用柱状图从大到小展示持有可转债涨跌幅情况
        scatter_html = utils.echarts_html_utils.generate_scatter_html_with_multi_tables(tables, select)

        html = """
            <br/>
            <br/>
            <br/>
            <br/>
            <center>
                """ + sum_html + pie_html + scatter_html + "<br/>"  + '<br/>' + """
            </center>
        """ + html

        return '我的账户', ''.join(nav_html_list), html

    except Exception as e:
        print("processing is failure. ", e)
        raise e


def generate_account_block(account, html, nav_html_list, tables, unit=100, is_login_user=False):
    cur = get_cursor("""
   SELECT h.id                                                              as hold_id,
       c.data_id                                                         as nid,
       c.bond_code,
       c.stock_code,
       c.cb_name_id                                                      as 名称,
       --c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
       --h.account as 账户,  
       case when h.hold_unit = :hold_unit then h.hold_amount / 10 else h.hold_amount END
           --case when h.hold_unit = 10 then  h.hold_amount/10 else  h.hold_amount END as 数量,
           --h.hold_amount
                                                                         as 持有数量,
       h.hold_price                                                      as '成本',
       round(c.cb_price2_id * h.hold_amount + sum_sell - sum_buy, 2) || '(' || round((c.cb_price2_id - h.hold_price) / c.cb_price2_id * 100, 2) || '%)' as 盈亏, 

       cb_price2_id                                                      as 转债价格,
       round(cb_premium_id * 100, 2) || '%'                              as 溢价率,
       --round((c.cb_price2_id * h.hold_amount - sum_buy)/sum_buy*100,2) || '%' as 收益率,
       --remain_amount as '余额(亿元)', 
       --round(cb_trade_amount2_id * 100,2) || '%' as '换手率(%)',
       round(cb_mov2_id * 100, 2) || '%'                                 as 可转债涨跌,
       round(cb_mov_id * 100, 2) || '%'                                  as 正股涨跌,
       --round(bt_yield*100,2) || '%' as 到期收益率, round(cb_price2_id + cb_premium_id * 100,2) as 双低值, 
       --round(cb_to_share_shares * 100,2)  as '余额/股本(%)',

       --rating as '信用', duration as 续存期, cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.account as 账户, 
       h.strategy_type                                                   as 策略,
       h.memo                                                            as 备注
from changed_bond c left join 
     stock_report s on c.stock_code = s.stock_code,
     hold_bond h
WHERE c.bond_code = h.bond_code
  and h.hold_owner = 'me'
  and h.account = :account
order by 持有数量, h.bond_code
        """, {'hold_unit':unit, 'account':account})
    return utils.table_html_utils.generate_table_html(account, cur, html, nav_html_list=nav_html_list, tables=tables,
                                                      remark_fields=['盈亏', '正股涨跌', '溢价率', '可转债涨跌'],
                                                      field_links={"成本": link_maker},
                                                      is_login_user=is_login_user)


def link_maker(data, record):
    return "<a href='/edit_hold_bond_by_id.html/" + str(record.get('hold_id')) + "/'>" + data + "</a>"

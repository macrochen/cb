# 目前市面上各种策略(高收益, 双低, 活性债, 回售)的数据视图展示


# 需导入要用到的库文件
import json

from prettytable import from_db_cursor

import utils.table_html_utils
import utils.trade_utils
from models import db, Config
from utils import html_utils
from utils.echarts_html_utils import generate_scatter_html_with_one_table, generate_scatter_html_with_multi_tables
from utils.html_utils import default_get_label


# config = {'type': [
#     '双低策略',
#     '高收益策略',
#     '回售策略',
#     # '活性债策略',
#     '低余额策略',
#     '低溢价率策略',
#     # '溢价率折价策略',
#     # '高收益率策略',
#     # '下修博弈策略',
#     # '广撒网策略',
#     '快到期保本策略',
#     '正股优选策略',
#     '高成长策略',
#     '股性策略',
#     # '换手率排行榜',
#     # '正股涨幅榜',
#     # '妖债策略',
#     # '抄作业',
#     # '非200不卖',
#     # '自选集',
#     '凌波双低轮动',
# ],
# }


def draw_view(user_id):
    use_personal_features = user_id is not None

    html = ''
    tables = {}

    nav_html_list = ['<li><a href="/">Home</a></li>']
    try:

        # =========强赎中=========
        sql = """
    SELECT  c.data_id as nid, e.hold_id, c.bond_code, c.stock_code, c.cb_name_id as 名称, --enforce_get as 强赎状态, 
    cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率,
    round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌,remain_amount as '余额(亿元)',  
    c.stock_name as 正股名称, c.industry as '行业',c.sub_industry as '子行业',round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
    strftime('%Y-%m-%d', c.enforce_last_date) as 最后交易日,
    c.enforce_price as 强赎价格
        --,c.declare_desc as 强赎详情
    from (select * from changed_bond where enforce_get in ('强赎中')) c left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code)  
             ) e 
        on c.bond_code = e.bond_code
    order by c.enforce_last_date
            """
        # 加几个换行避免顶部的菜单遮住title
        html += "<center>=========<font size=4><b>强赎中</b></font>=========</br></br></center>"
        html = generate_strategy_html(sql, "强赎中转债", html, tables, nav_html_list=nav_html_list,
                                      use_personal_features=use_personal_features)

        # =========(即将)满足强赎=========
        sql = """
    SELECT  c.data_id as nid, e.hold_id, c.bond_code, c.stock_code, c.cb_name_id as 名称, --enforce_get as 强赎状态, 
    cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率,
    round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌,remain_amount as '余额(亿元)',  
    c.stock_name as 正股名称, c.industry as '行业',c.sub_industry as '子行业',round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
    strftime('%Y-%m-%d', c.enforce_start_date) as 强赎起始日,
    strftime('%Y-%m-%d', c.enforce_stop_date) as 不强赎截止日
        --,c.declare_desc as 强赎详情
    from (select * from changed_bond where enforce_get in ('满足强赎') and not declare_desc like '%已过%'and not declare_desc like '%超过一个月未公告%') c left join 
        (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
            from hold_bond 
            where id in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code)  
             ) e 
        on c.bond_code = e.bond_code
    order by c.enforce_stop_date 
            """
        # 加几个换行避免顶部的菜单遮住title
        html += "<center>=========<font size=4><b>(即将)满足强赎</b></font>=========</br></br></center>"
        html = generate_strategy_html(sql, "满足强赎转债", html, tables, nav_html_list=nav_html_list,
                                      use_personal_features=use_personal_features)

        # =========公告不强赎=========
        sql = """
        SELECT  c.data_id as nid, e.hold_id, c.bond_code, c.stock_code, c.cb_name_id as 名称, --enforce_get as 强赎状态, 
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率,
    round(cb_mov2_id * 100, 2) || '%' as 可转债涨跌,remain_amount as '余额(亿元)',  
    c.stock_name as 正股名称, c.industry as '行业',c.sub_industry as '子行业',round(cb_mov_id * 100, 2) || '%' as 正股涨跌, 
    strftime('%Y-%m-%d', c.enforce_start_date) as 强赎起始日,
    strftime('%Y-%m-%d', c.enforce_stop_date) as 不强赎截止日
        --,c.declare_desc as 强赎详情
        from (select * from changed_bond where enforce_get in ('公告不强赎')) c left join 
            (select id as hold_id, bond_code, cb_name_id, hold_price, hold_amount 
                from hold_bond 
                where id in (SELECT min(id) from hold_bond where hold_owner = 'me' and hold_amount > 0 group by bond_code)  
                 ) e 
            on c.bond_code = e.bond_code
        order by c.enforce_stop_date
                """
        # 加几个换行避免顶部的菜单遮住title
        html += "<center>=========<font size=4><b>公告不强赎</b></font>=========</br></br></center>"
        html = generate_strategy_html(sql, "公告不强赎转债", html, tables, nav_html_list=nav_html_list,
                                      use_personal_features=use_personal_features)

        scatter_html = generate_scatter_html_with_multi_tables(tables, title="强赎可转债分布情况")

        html = """
                    <br/>
                    <br/>
                    <br/>
                    <br/>
                    <br/>
                    <center>
                        """ + scatter_html + "<br/><br/>" + """
                    </center>
                """ + html

        return '市场策略', ''.join(nav_html_list), html

    except Exception as e:
        print("processing is failure. " + str(e), e)
        raise e


def generate_strategy_html(sql, type, html, tables, nav_html_list=None, remark_fields=[],
                           use_personal_features=False):

    cur = db.session.execute(sql)

    table = from_db_cursor(cur.cursor)
    if len(table._rows) == 0:
        return html

    if tables is not None:
        tables[type] = table

    html_utils.add_nav_html(nav_html_list, type)

    html += """
    <div id=\"""" + type + """\">
        """ + utils.table_html_utils.build_table_html(table, remark_fields, ignore_fields=['持有数量'], is_login_user=use_personal_features, table_rows_size=6) + """
    </div>
    """

    return html


if __name__ == "__main__":
    utils.trade_utils.calc_mid_data()

    draw_market_view(True)
    print("processing is successful")

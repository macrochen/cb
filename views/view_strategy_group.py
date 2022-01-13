# 目前市面上各种策略(高收益, 双低, 活性债, 回售)的数据视图展示


# 需导入要用到的库文件
import json
import math
import threading

from prettytable import from_db_cursor

import utils.table_html_utils
import utils.trade_utils
from models import db, Config
from utils import html_utils, db_utils
from utils.bond_utils import is_too_expensive, parse_bond_ids_params
from utils.db_utils import get_record, get_cursor

from utils.echarts_html_utils import generate_scatter_html_with_multi_tables
from views import view_strategy_group_yield

global_test_context = threading.local()
global_test_context.need_check_double_low = True

strategy_config = {
    '高收益率策略': {
        "id": "2",
        "period": 15,
        "count": 5,
        "max_price": 130,
        "max_rise": 30,
        "need_check_double_low": False,
        "desc": "到期收益率从大到小排序选取前5, 15个交易日轮动",
        "new_sql": """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id
        from changed_bond
              where cb_price2_id < 130
                and enforce_get not in ('强赎中') or enforce_get is NULL
              order by AT_yield desc 
              limit 5""",
        "buy_sql": lambda s_ids: """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id
          from changed_bond
          where bond_code not in (""" + s_ids + """)
                and enforce_get not in ('强赎中') or enforce_get is NULL
          order by AT_yield desc 
          limit :count """,
        "view_sort": " order by AT_yield desc "
    },
    '低溢价率策略': {
        "id": "1",
        "period": 15,
        "count": 5,
        "max_price": 20000,
        "max_rise": 30,
        "need_check_double_low": False,
        "desc": "溢价率从小到大排序选取前5, 15个交易日轮动",
        "new_sql": """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id
              from changed_bond
              where enforce_get not in ('强赎中') or enforce_get is NULL
              order by cb_premium_id
              limit 5""",
        "buy_sql": lambda s_ids: """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id
          from changed_bond
          where bond_code not in (""" + s_ids + """)
                and enforce_get not in ('强赎中') or enforce_get is NULL
          order by cb_premium_id
          limit :count """,
        "view_sort": " order by cb_premium_id "
    },
    '低余额+双低策略': {
        "id": "3",
        "period": 20,
        "count": 5,
        "max_price": 200,
        "max_rise": 30,
        "need_check_double_low": True,
        "desc": "先根据余额从小到大排序取前30, 再从中根据双低值从小到大排序取前5, 20个交易日轮动",
        "new_sql": """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id, remain_amount
        from (select *
              from changed_bond
              where cb_price2_id < 200
                and enforce_get not in ('强赎中') or enforce_get is NULL
              order by remain_amount
              limit 30)
        order by cb_price2_id + cb_premium_id * 100, remain_amount
        limit 5""",
        "buy_sql": lambda s_ids: """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id
            from (select *
                  from changed_bond
                  where bond_code not in (""" + s_ids + """)
                    and enforce_get not in ('强赎中') or enforce_get is NULL
                    and cb_price2_id < 200
                    and cb_price2_id + cb_premium_id * 100 < 150
                  order by remain_amount
                  limit 30)
            order by cb_price2_id + cb_premium_id * 100, remain_amount
            limit :count """,
        "view_sort": " order by cb_price2_id + cb_premium_id * 100, remain_amount "
    },
    '低溢价率+双低策略': {
        "id": "4",
        "period": 10,
        "count": 15,
        "max_price": 200,
        "max_rise": 30,
        "need_check_double_low": True,
        "desc": "先根据溢价率从小到大排序取前30, 再从中根据双低值从小到大排序取前15, 10个交易日轮动",
        "new_sql": """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id
        from (select *
              from changed_bond
              where cb_price2_id < 200
                and enforce_get not in ('强赎中') or enforce_get is NULL
              order by cb_premium_id
              limit 30)
        order by cb_price2_id + cb_premium_id * 100, cb_premium_id
        limit 15""",
        "buy_sql": lambda s_ids: """
        select bond_code, cb_name_id, cb_price2_id, cb_premium_id
            from (select *
                  from changed_bond
                  where bond_code not in (""" + s_ids + """)
                    and enforce_get not in ('强赎中') or enforce_get is NULL
                    and cb_price2_id < 200
                    and cb_price2_id + cb_premium_id * 100 < 150
                  order by cb_premium_id
                  limit 30)
            order by cb_price2_id + cb_premium_id * 100, cb_premium_id
            limit :count """,
        "view_sort": " order by cb_price2_id + cb_premium_id * 100, cb_premium_id "

    },
}


def init_strategy_groups():
    # 初始化(第一次用到), 收盘后

    for strategy_name, config in strategy_config.items():
        id = config['id']
        global_test_context.need_check_double_low = config['need_check_double_low']
        total_money = 1000000
        with db_utils.get_connect() as con:
            cur = con.cursor()

            if has_been_executed_by_name(cur, id, strategy_name):
                continue

            new_rows = get_new_rows(cur, strategy_name)

            # 没找到可转债, 或者太贵了, 不满足轮动条件, 不买
            if len(new_rows) == 0 or _is_too_expensive(new_rows):
                return

            # 等权分配资金买入
            remain_money, _1, _2 = do_buy_bonds(cur, new_rows, total_money, strategy_name)
            save_yield_rate(cur, id, strategy_name, total_money, remain_money)

            print(strategy_name + " has been initialized.")


def save_yield_rate(cur, id, strategy_name, total_money, remain_money=0, day_rate=0, all_rate=0, period=1):
    # 更新收益率
    sql = None
    if has_been_executed(cur):
        sql = """
            update strategy_group_yield set 
                strategy_""" + id + """=:strategy_name, 
                total_money_""" + id + """=:total_money, 
                remain_money_""" + id + """=:remain_money, 
                day_rate_""" + id + """=:day_rate, 
                all_rate_""" + id + """=:all_rate, 
                period_""" + id + """=:period
                where date = date()"""
    else:
        sql = """
            insert into strategy_group_yield (
                strategy_""" + id + """, 
                total_money_""" + id + """, 
                remain_money_""" + id + """, 
                day_rate_""" + id + """, 
                all_rate_""" + id + """, 
                period_""" + id + """, 
                date)
                values (:strategy_name, :total_money, :remain_money, :day_rate, :all_rate, :period, date())"""

    result = cur.execute(sql,
                         {'strategy_name': strategy_name,
                          'total_money': total_money,
                          'remain_money': remain_money,
                          "day_rate": day_rate,
                          "all_rate": all_rate,
                          "period": period
                          })
    if result.rowcount != 1:
        raise Exception("update strategy_group_yield is failure. strategy_name:" + strategy_name)


def _is_too_expensive(rows):
    if global_test_context.need_check_double_low is False:
        return False

    return is_too_expensive(rows)


def has_been_executed_by_name(cur, id, strategy_name):
    cur.execute("select count(*) from strategy_group_yield where strategy_" + id + "=:strategy_name",
                {"strategy_name": strategy_name})
    count = cur.fetchone()[0]
    return count > 0


def has_been_executed(cur):
    cur.execute("select count(*) from strategy_group_yield where date = date()")
    count = cur.fetchone()[0]
    return count > 0


def has_been_executed_today(cur, id, strategy_name):
    cur.execute("select count(*) from strategy_group_yield where strategy_" + id + "=:strategy_name and date = date()",
                {"strategy_name": strategy_name})
    count = cur.fetchone()[0]
    return count > 0


def update_groups():
    """收盘后定时更新组合"""
    for strategy_name, config in strategy_config.items():
        global_test_context.need_check_double_low = config['need_check_double_low']
        global_test_context.max_price = config['max_price']
        global_test_context.max_rise = config['max_rise']
        global_test_context.buy_sql = config['buy_sql']
        update_group(config['id'], strategy_name, config['period'])


def update_group(id, strategy_name, roll_period):
    # 检查是否到了轮动调仓的时候
    with db_utils.get_connect() as con:
        cur = con.cursor()
        if has_been_executed_today(cur, id, strategy_name):
            return

        # 前一个交易日的收益信息
        yield_row = get_previous_yield(cur, id, strategy_name)
        if yield_row is None:
            return

        old_remain_money = yield_row[0]
        period = yield_row[2]
        if period >= roll_period:
            # 开启一轮新的轮动
            new_total_money, new_remain_money = start_roll_bonds(cur, strategy_name, old_remain_money)
            # 更新收益数据
            calc_and_save_yield_rate(cur, id, strategy_name, yield_row=yield_row,
                                     new_total_money=new_total_money,
                                     new_remain_money=new_remain_money,
                                     period=0)
        else:
            do_update_group(cur, id, strategy_name, yield_row=yield_row)


def get_new_rows(cur, strategy_name):
    cur.execute(strategy_config[strategy_name]["new_sql"])
    rows = cur.fetchall()
    return rows


def do_buy_bonds(cur, new_rows, total_money, strategy_name, exclude_codes=[], size=None):
    # 一份的金额
    size = size if size is not None else len(new_rows)
    percent = round(1 / size * 100, 2)
    part = round(total_money * 1 / len(new_rows), 2)

    buy_total_money = 0
    for new_row in new_rows:
        bond_code = new_row[0]
        if bond_code in exclude_codes:
            continue

        bond_name = new_row[1]
        price = new_row[2]
        premium = new_row[3]
        amount = math.floor(part / (price * 10)) * 10
        result = cur.execute("""
            insert into strategy_group (strategy_name, bond_code, bond_name, price, amount, premium, create_date, modify_date, before_percent, after_percent, desc) values 
            (:strategy_name, :bond_code, :bond_name, :price, :amount, :premium, date(), date(), 0, :percent, '建仓')
        """, {'strategy_name': strategy_name, 'bond_code': bond_code, 'bond_name': bond_name, "amount": amount,
              'price': price, 'premium': premium, "percent": percent})
        if result.rowcount != 1:
            raise Exception(
                "insert strategy_group is failure.strategy_name:" + strategy_name + ", bond_code:" + str(bond_code))

        save_snapshot(cur, strategy_name, bond_code, price)

        buy_total_money += round(amount * price, 2)

    buy_total_money = round(buy_total_money, 2)

    # 剩下的零头
    return round(total_money - buy_total_money, 2), percent, part


def save_snapshot(cur, strategy_name, bond_code, old_price):
    result = cur.execute("""
        insert into strategy_group_snapshot (strategy_name, bond_code, bond_name, old_price, price, amount, premium, date, before_percent, after_percent, desc) 
        select strategy_name, bond_code, bond_name, """ + old_price + """ as old_price, price, amount, premium, date() as date, before_percent, after_percent, desc from strategy_group
        where strategy_name=:strategy_name and bond_code=:bond_code and modify_date=date()
            """,
                         {'strategy_name': strategy_name, 'bond_code': bond_code, })
    if result.rowcount != 1:
        raise Exception(
            "insert strategy_group_snapshot is failure.strategy_name:" + strategy_name + ", bond_code:" + str(
                bond_code))


def start_roll_bonds(cur, strategy_name, remain_money):
    # 拿到组合转债信息
    group_id_dict = get_group_bonds(cur, strategy_name)

    # 计算最新的总资产(包括余额)
    new_total_money = calc_current_total_money(cur, remain_money, strategy_name)

    # 新的组合转债
    new_rows = get_new_rows(cur, strategy_name)

    update_ids = []
    add_ids = []
    new_id_price_pair = {}
    old_id_price_pair = {}
    for new_row in new_rows:
        new_id = new_row[0]
        price = new_row[2]
        if new_id in list(group_id_dict.keys()):
            # 重合的更新
            update_ids.append(new_id)
            new_id_price_pair[new_id] = price
            old_id_price_pair[new_id] = group_id_dict[new_id][2]
            del group_id_dict[new_id]
        else:
            add_ids.append(new_id)

    # 剩下的卖出清仓
    for bond_code, group in group_id_dict.items():
        sell_bond(cur, bond_code, group[4], strategy_name, '轮动卖出', group[2])

    # 分配资金
    # 新增的买入建仓
    remain_money, percent, part = do_buy_bonds(cur, new_rows, new_total_money, strategy_name,
                                               exclude_codes=update_ids)
    # 已有的进行调仓
    change_position(cur, new_id_price_pair, old_id_price_pair, part, percent, strategy_name, update_ids)
    return new_total_money, remain_money


def change_position(cur, new_id_price_pair, old_id_price_pair, part, percent, strategy_name, update_ids):
    for update_id in update_ids:
        new_price = new_id_price_pair[update_id]
        old_price = old_id_price_pair[update_id]
        new_amount = math.floor(part / (new_price * 10)) * 10

        result = cur.execute("""
        update strategy_group set 
            amount=:amount, 
            price=:price,
            before_percent=after_percent,
            after_percent=:after_percent,
            modify_date=date(),
            desc='轮动调仓'
        where strategy_name=:strategy_name and bond_code=:bond_code""",
                             {"strategy_name": strategy_name,
                              "bond_code": update_id,
                              "amount": new_amount,
                              "price": new_price,
                              "after_percent": percent,
                              }
                             )
        if result.rowcount != 1:
            raise Exception(
                "update strategy_group is failure. param:strategy_name=" + strategy_name + ", bond_code=" + str(
                    update_id))

        save_snapshot(cur, strategy_name, update_id, old_price)


def do_update_group(cur, id, strategy_name, yield_row=None):
    # 组合转债
    group_bonds = get_group_bonds(cur, strategy_name)
    if len(group_bonds) > 0:

        params, s_ids = do_parse_ids(group_bonds)

        # 组合转债的最新数据
        current_rows = get_current_rows(cur, s_ids, params)
        if len(current_rows) == 0 or len(group_bonds) != len(current_rows):
            # 有问题, 要查一下
            raise Exception(
                'bond is different. group_bonds:' + str(group_bonds) + ", current_rows:" + str(current_rows))

        # 更新组合占比
        update_percent(cur, current_rows, group_bonds, strategy_name)

        # 计算收益率
        all_rate, day_rate, new_total_money, remain_money, period = calc_and_save_yield_rate(cur, id, strategy_name,
                                                                                             yield_row)

        if _is_too_expensive(current_rows):
            # 组合太贵了, 清仓
            clean_bonds(cur, id, strategy_name, new_total_money, all_rate, day_rate, period)
            return

        # 看看是否有要卖出轮换的
        sell_num, sell_total_money = do_sell_bonds(cur, current_rows, group_bonds, strategy_name)
        # 不需要轮换
        if sell_total_money == 0:
            return

        new_remain_money = sell_total_money + remain_money
        new_rows = get_buy_rows(cur, params, s_ids, sell_num)
        # 如果没有找到, 说明太贵了, 没有可买入的
        # fixme 什么时候补充未买入的?
        if len(new_rows) > 0:
            new_remain_money, _1, _2 = do_buy_bonds(cur, new_rows, new_remain_money, strategy_name,
                                                    size=len(current_rows))

        update_remain_money(cur, id, strategy_name, new_remain_money)


def update_percent(cur, current_rows, group_bonds, strategy_name):
    total_money = get_current_total_money(current_rows, group_bonds)
    for row in current_rows:
        bond_code = row[0]
        price = row[2]
        bond = group_bonds[bond_code]
        amount = bond[3]
        percent = round(round(price * amount, 2) / total_money * 100, 2)
        sql = """update strategy_group 
            set after_percent=:after_percent, modify_date=date()
            where strategy_name=:strategy_name
                and bond_code=:bond_code
            """
        result = cur.execute(sql, {"after_percent": percent, "strategy_name": strategy_name, "bond_code": bond_code})
        if result.rowcount != 1:
            raise Exception(
                "update percent is failure. strategy_name:" + strategy_name + ", bond_code:" + bond_code)


def get_current_total_money(current_rows, group_bonds):
    total_money = 0
    for row in current_rows:
        bond_code = row[0]
        price = row[2]
        bond = group_bonds[bond_code]
        amount = bond[3]
        total_money += round(price * amount, 2)
    return total_money


def do_parse_ids(group_bonds):
    params = {}
    ids = []
    for key in group_bonds.keys():
        ids.append(key)
    s_ids = parse_bond_ids_params(ids, params)
    return params, s_ids


def do_sell_bonds(cur, current_rows, group_bonds, strategy_name):
    # 看是否需轮换可转债
    sell_num = 0
    sell_total_money = 0
    for current_row in current_rows:
        bond_code = current_row[0]
        price = current_row[2]
        group_bond = group_bonds[bond_code]
        amount = group_bond[3]
        old_price = group_bond[2]
        before_percent = group_bond[4]
        if price >= global_test_context.max_price:
            sell_num += 1
            sell_total_money += price * amount
            sell_bond(cur, bond_code, before_percent, strategy_name, "价格超过" + str(global_test_context.max_price) + "卖出", old_price)
        elif current_row[4] == '强赎中':
            sell_num += 1
            sell_total_money += price * amount
            sell_bond(cur, bond_code, before_percent, strategy_name, "强赎卖出", old_price)
        else:
            # 一周涨幅超过30%
            # 查7天(5个交易日)前的历史交易价格
            # 还需要和建仓的时间比较一下, 取最近的那个
            # 因为可能有一种情况, 买入的时候, 涨幅就已经超过最大涨幅(30%), 这样就会出现买入后就马上卖出
            create_date = group_bond[5]
            pre_price_row = get_pre_price_row(bond_code)
            pre_price = pre_price_row[0]
            if create_date > pre_price_row[1]:
                pre_price = group_bond[2]
            if round((price - pre_price) / price * 100, 2) >= global_test_context.max_rise:
                sell_num += 1
                sell_total_money += price * amount
                sell_bond(cur, bond_code, before_percent, strategy_name,
                          "涨幅超过" + str(global_test_context.max_rise) + "%卖出", old_price)
    return sell_num, sell_total_money


def update_remain_money(cur, id, strategy_name, remain_money):
    # 更新一下零头
    result = cur.execute(
        """update strategy_group_yield set remain_money_""" + id + """=:remain_money where strategy_""" + id + """=:strategy_name and date = date()""",
        {'strategy_name': strategy_name, 'remain_money': remain_money}
    )
    if result.rowcount != 1:
        raise Exception('update_remain_money is failure. strategy_name' + strategy_name)


def get_buy_rows(cur, params, s_ids, sell_num):
    params.setdefault("count", sell_num)
    sql = global_test_context.buy_sql(s_ids)
    cur.execute(sql, params)
    buy_rows = cur.fetchall()
    return buy_rows


def sell_bond(cur, bond_code, before_percent, strategy_name, desc, old_price):
    result = cur.execute("""
                        update strategy_group 
                        set after_percent=0, desc=:desc, before_percent=:before_percent, modify_date=date()
                        where strategy_name=:strategy_name 
                            and bond_code=:bond_code""",
                         {
                             'strategy_name': strategy_name,
                             'bond_code': bond_code,
                             'desc': desc,
                             'before_percent': before_percent,
                         })
    if result.rowcount != 1:
        raise Exception("sell bond is failure. strategy_name:" + strategy_name + ", bond_code:" + bond_code)

    # 作为快照存一份
    save_snapshot(cur, strategy_name, bond_code, old_price)


def get_pre_price_row(bond_id):
    with db_utils.get_daily_connect() as con_daily:
        cur_daily = con_daily.cursor()
        cur_daily.execute("""
            select price, last_chg_dt
            from cb_history
            where bond_id = :bond_id
              and last_chg_dt in (select last_chg_dt
                                  from (SELECT DISTINCT last_chg_dt
                                        from cb_history
                                        where bond_id = :bond_id
                                          and last_chg_dt < date()
                                        order by last_chg_dt desc
                                        limit 5)
                                  limit 1)                                                            
                            """, {"bond_id": bond_id})
        return cur_daily.fetchone()


def get_group_bonds(cur, strategy_name):
    # fixme 注意字段顺序调整, 需要检查是否影响后面的代码
    sql = """select bond_code, bond_name, price, amount, after_percent, create_date 
    from strategy_group 
    where strategy_name=:strategy_name and after_percent > 0
        """
    cur.execute(sql, {'strategy_name': strategy_name})
    rows = cur.fetchall()
    group_bonds = {}
    for group_row in rows:
        group_bonds[group_row[0]] = group_row
    return group_bonds


def get_current_rows(cur, s_ids, params):
    sql = """select bond_code, cb_name_id, cb_price2_id, cb_premium_id, enforce_get 
    from changed_bond 
    where bond_code in (""" + s_ids + """)"""
    cur.execute(sql, params)
    current_rows = cur.fetchall()
    return current_rows


def calc_and_save_yield_rate(cur, id, strategy_name, yield_row=None,
                             new_total_money=None,
                             new_remain_money=None,
                             period=None):
    # 获取前一个交易日的收益信息
    total_money = yield_row[1]
    period = yield_row[2] if period is None else period

    # 计算当前交易日的市值
    if new_total_money is None:
        new_remain_money = remain_money = yield_row[0]
        new_total_money = calc_current_total_money(cur, remain_money, strategy_name)

    day_rate = round((new_total_money - total_money) / total_money * 100, 2)
    all_rate = round((new_total_money - 1000000) / 1000000 * 100, 2)

    # 保存
    save_yield_rate(cur, id, strategy_name, total_money, new_remain_money, day_rate=day_rate, all_rate=all_rate,
                    period=period + 1)

    return all_rate, day_rate, new_total_money, new_remain_money, period


def calc_current_total_money(cur, remain_money, strategy_name):
    cur.execute("""select sum(a.amount*cb.cb_price2_id) from strategy_group a 
                    left join changed_bond cb 
                        on a.bond_code = cb.bond_code 
                        where strategy_name =:strategy_name and a.after_percent > 0 
                """, {'strategy_name': strategy_name})
    current_money = cur.fetchone()[0]
    new_total_money = current_money + remain_money
    return new_total_money


def get_previous_yield(cur, id, strategy_name):
    cur.execute("""select remain_money_""" + id + """, total_money_""" + id + """, period_""" + id + """ 
    from strategy_group_yield 
    where strategy_""" + id + """=:strategy_name 
        and date = (select max(date) from strategy_group_yield where strategy_""" + id + """=:strategy_name)""",
                {"strategy_name": strategy_name})
    return cur.fetchone()


def clean_bonds(cur, id, strategy_name, total_money, all_rate, day_rate, period):
    # 盘后处理, 更新组合
    result = cur.execute(
        """update strategy_group 
        set before_percent=after_percent, 
            after_percent=0, 
            modify_date=date(), 
            desc='高估清仓' 
        where strategy_name=:strategy_name""",
        {'strategy_name': strategy_name}
    )
    if result.rowcount <= 0:
        raise Exception(
            "clean all bond is failure. strategy_name:" + strategy_name + ", result:" + str(result))
    # 更新收益率
    save_yield_rate(cur, id, strategy_name, total_money, day_rate=day_rate, all_rate=all_rate, period=period + 1)


def draw_view(user_id):
    use_personal_features = user_id is not None

    html = ''

    nav_html_list = ['<li><a href="/">Home</a></li>']
    tables = {}
    try:
        for strategy_name, config in strategy_config.items():
            table = get_strategy_table(strategy_name, config)
            html += generate_strategy_table_html(strategy_name, config, table, tables, nav_html_list,
                                                 use_personal_features=use_personal_features)

        scatter_html = generate_scatter_html_with_multi_tables(tables, title="组合策略可转债分布情况",
                                                               # subtitle='每种策略选取top10, 按日/周/月轮动',
                                                               use_personal_features=use_personal_features,
                                                               price_field_name='当前价')

        html = """
                    <center>
                        """ + scatter_html + "<br/><br/>" + """
                    </center>
                """ + html

        html_utils.add_nav_html(nav_html_list, '策略组合收益率')
        html += "<br/><div id='策略组合收益率'>" + view_strategy_group_yield.draw_view() + "</div>"

        return '策略组合轮动', ''.join(nav_html_list), html

    except Exception as e:
        print("processing is failure. " + str(e), e)
        raise e


def get_strategy_table(strategy_name, config):
    sql = """
        select data_id                                                     as nid,
               b.bond_code,
               stock_code,
               bond_name                                                   as 名称,
               round(cb_mov2_id * 100, 2) || '%'                           as 可转债涨跌,
               b.cb_price2_id                                              as 当前价,
               price                                                       as 买入价,
               round(cb_premium_id * 100, 2) || '%'                        as 溢价率,
               round(cb_price2_id + cb_premium_id * 100, 2)                as 双低值,
               round(cb_mov_id * 100, 2) || '%'                            as 正股涨跌,
               remain_amount                                               as '余额(亿元)',
               round(bT_yield*100, 2) || '%'                               as '税前收益率',
               round(cb_ma20_deviate * 100, 2) || '%'                      as ma20乖离率,
               round((b.cb_price2_id - a.price) / a.price * 100, 2) || '%' as 盈亏,
               amount                                                      as 持有数量,
               create_date                                                 as 建仓时间,
               after_percent || '%'                                        as 占比,
               stock_name                                                  as 正股名称,
               industry                                                    as '行业',
               sub_industry                                                as '子行业'
        from strategy_group a
                 left join changed_bond b on a.bond_code = b.bond_code
        where strategy_name = :strategy_name
          and after_percent > 0
"""
    sql += config['view_sort']
    params = {'strategy_name': strategy_name}
    return get_table(sql, params)


def get_roll_table(strategy_name, date):
    sql = """
        select data_id                                                     as nid,
               a.bond_code,
               stock_code,
               bond_name                                                   as 名称,
               case when old_price = price or old_price is NULL then price 
               else old_price || '->' ||  price end                        as 价格,
               round(premium * 100, 2) || '%'                              as 溢价率,
               amount                                                      as 持有数量,
               before_percent || '%->' || after_percent || '%'             as 占比,
               desc                                                        as 描述
        from strategy_group_snapshot a
                 left join changed_bond b on a.bond_code = b.bond_code
        where strategy_name = :strategy_name and date=:date
"""
    params = {'strategy_name': strategy_name, 'date': date}
    return get_table(sql, params)


def get_strategy_list():
    row = db.session.query(Config).filter(
        Config.group == 'public_strategy_type_list', Config.key == 'strategy_type', Config.is_delete == 0).first()
    strategy_list = json.loads(row.value)
    return strategy_list


def generate_strategy_table_html(strategy_name, config, table, tables,
                                 nav_html_list=None, remark_fields=['轮动', 'ma20乖离率'],
                                 use_personal_features=False):
    html_utils.add_nav_html(nav_html_list, strategy_name)

    roll_html = generate_roll_record_html(remark_fields, strategy_name)

    if len(table._rows) == 0:
        return "<div id=" + strategy_name + ">" + \
               "</br><center>=========<font size=4><b>" + strategy_name + "</b></font>=========</center>" + \
               "<center><font size=2>(按双低值>150为高估标准, 暂停买入)</font></center>" + \
               roll_html + \
               "</div>"

    if tables is not None:
        tables[strategy_name] = table

    yield_rate = get_yield_rate_of_strategy(table)

    yield_html = '当日涨跌: ' + str(yield_rate) + '%<br/>'

    tables_html = utils.table_html_utils.build_table_html(table, remark_fields, ignore_fields=['持有数量'],
                                                          is_login_user=use_personal_features, table_rows_size=6)
    return "<div id=" + strategy_name + ">" + \
           "</br><center>=========<font size=4><b>" + strategy_name + "</b></font>=========</center>" + \
           "<center><font size=2>(" + config['desc'] + ")</font></center>" + \
           yield_html + tables_html + roll_html + "</div>"


def generate_roll_record_html(remark_fields, strategy_name):
    sql = """SELECT date 
        from strategy_group_snapshot 
        WHERE strategy_name = :strategy_name  
        group by date"""
    cur = db.session.execute(sql, {"strategy_name": strategy_name})
    date_rows = cur.fetchall()
    roll_html = ''
    if len(date_rows) > 0:
        roll_html += """
        <br/>调仓记录: <br/>
        <div class="panel-group" id="accordion">
        """

        for row in date_rows:
            collapse_id = strategy_name.replace('+', '_') + row[0].replace("-", "_")
            collapse_name = row[0]
            roll_table = get_roll_table(strategy_name, row[0])
            roll_table_html = utils.table_html_utils.build_table_html(roll_table, remark_fields, ignore_fields=['持有数量'],
                                                                      table_rows_size=6)
            roll_html += """
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#accordion"
                               href="#{collapse_id}">
                                {collapse_name}
                            </a>
                        </h4>
                    </div>
                    <div id="{collapse_id}" class="panel-collapse collapse">
                        <div class="panel-body">
                            {collapse_content}
                        </div>
                    </div>
                </div>            
            """.format(collapse_id=collapse_id, collapse_name=collapse_name, collapse_content=roll_table_html)

        roll_html += "</div>"
    return roll_html


def get_table(sql, params):
    cur = db.session.execute(sql, params)
    return from_db_cursor(cur.cursor)


def get_yield_rate_of_strategy(table):
    value = 0
    cost = 0
    for row in table._rows:
        record = get_record(table, row)
        amount = record.get('持有数量')
        _当前价 = record.get('当前价')
        if _当前价 is None:
            continue

        price = float(_当前价)
        rate = float(record.get('可转债涨跌').replace('%', '')) / 100
        cost += price / (1 + rate) * amount
        value += price * amount
    return round((value - cost) / cost * 100, 2)


if __name__ == "__main__":
    # utils.trade_utils.calc_mid_data()
    # do_update_groups()
    # init_strategy_groups()
    update_groups()
    # draw_market_view(True)
    print("processing is successful")

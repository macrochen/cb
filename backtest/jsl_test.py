import datetime
import json
import threading

from prettytable import from_json

from backtest.test_utils import get_next_day, calc_test_result, create_test_result, do_push_bond, \
    get_total_money, update_bond, get_pre_total_money
from backtest.view_test import generate_line_html, generate_timeline_html
from utils import db_utils
from utils.bond_utils import is_too_expensive, parse_bond_ids_params, add_roll_row_with_bond
from utils.table_html_utils import build_table_html

global_test_context = threading.local()


def test(start, end=None):
    # {"yyyy-mm-dd":{"xxx":100},{"yyy":200}}
    start_total_money = 1000000
    group, start, remain_money = start_roll(start, start_total_money)
    if group is None:
        return {}, {}, 0

    add_time_data(start, group)

    test_result = create_test_result(start, start_total_money, remain_money, group,
                                     global_test_context.one_strategy_with_one_scenario)

    previous_day = start
    next_day = get_next_day(start)
    if next_day is None:
        raise Exception('not found next day with ' + str(start))

    end = datetime.datetime.now() if end is None else end
    # 轮动周期
    roll_period = global_test_context.roll_period
    # 轮动周期计数器(启动时已经执行了一次)
    roll_counter = 1
    # 交易次数
    trade_times = 0
    break_roll = False
    trade_day = next_day
    while str(trade_day) <= str(end):
        while roll_counter < roll_period and not break_roll and (trade_day is not None and str(trade_day) <= str(end)):

            break_roll, previous_day = do_trade(trade_day, group, previous_day, test_result)

            add_time_data(trade_day, group)

            # previous_day = trade_day
            trade_day = get_next_day(trade_day)
            roll_counter += 1
            trade_times += 1

            # 当轮动到期或者高估时, 提前终止轮动, 重新开启一轮
            # if roll_counter > roll_period or break_roll or trade_day is None or str(trade_day) > str(end):
            #     print('stop')
            #     break

        if trade_day is None or str(trade_day) > str(end):
            break

        group, trade_day = new_roll(trade_day, previous_day, group, test_result)
        trade_times += 1

        add_time_data(trade_day, group)

        previous_day = trade_day
        trade_day = get_next_day(trade_day)
        roll_counter = 1
        if trade_day is None:
            break

    return test_result['rows'], test_result.get('roll_rows'), trade_times


def add_time_data(day, group):
    if global_test_context.need_time_data is False or group is None:
        return

    data = {}
    for bond_id, bond in group.items():
        data.setdefault(bond['bond_nm'], bond['price'])
        # data.setdefault(bond['bond_nm'], int(bond['price'] * bond['amount']))
        # data.setdefault(bond['bond_nm'], int(bond['price']))
    # sorted_data = sorted(data.items(), key=lambda i: i[1])
    global_test_context.time_data.setdefault(day, data)


def get_hold_row_total_money(group, current_day, previous_day, test_result):
    if len(group) == 0:
        return test_result['rows'][previous_day]['total_money']

    params = {"current": current_day, }
    keys = sorted(group.keys())
    ids = parse_bond_ids_params(keys, params)
    with db_utils.get_daily_connect() as con:
        cur = con.cursor()
        cur.execute("""
                select a.bond_id,
                       a.bond_nm,
                       a.price,
                       a.premium_rt
                from cb_history a
                where a.bond_id in (""" + ids + """)
                  and a.last_chg_dt = :current         
                    """, params)
        new_rows = cur.fetchall()
        # 异常数据, 跳过
        if new_rows is None:
            raise Exception('not get new rows. params:' + str(params))

        # 有可能那天停牌了, 导致两边数据不一致
        if len(new_rows) != len(group):
            print("data is conflict. current_day:" + str(current_day) + ", group size:" + str(
                len(group)) + ", new_row size:" + str(len(new_rows)))

        total_money = test_result.get('remain_money')
        id_rows = {}
        for row in new_rows:
            bond_id = row[0]
            id_rows[bond_id] = row

        for bond_id, bond in group.items():
            row = id_rows.get(bond_id)
            price = bond['price'] if row is None else row[2]
            total_money += round(price * bond.get("amount"), 2)
        return round(total_money, 2)


def do_trade(current_day, group, previous_day, test_result):
    # 用来和七天前的价格进行比较, 如果涨幅过大(30%), 提前止盈
    params = {"current": current_day,
              "pre_day": global_test_context.pre_day,
              'max_price': global_test_context.max_price,
              }
    keys = sorted(group.keys())
    ids = parse_bond_ids_params(keys, params)
    with db_utils.get_daily_connect() as con:
        cur = con.cursor()
        new_rows = get_hold_rows(cur, ids, params)
        # 异常数据, 跳过
        if new_rows is None:
            print('not get new rows. params:' + str(params))

            return False, previous_day, get_pre_total_money(previous_day, test_result)
        # 有可能那天停牌了, 导致两边数据不一致
        if len(new_rows) != len(group):
            print("data is conflict. current_day:" + str(current_day) + ", group size:" + str(
                len(group)) + ", new_row size:" + str(len(new_rows)))

        # 为了计算盈亏, 主要更新价格
        update_bond(group, new_rows)

        total_money = get_total_money(group, test_result)
        calc_test_result(test_result, total_money, current_day, previous_day)

        # 太贵了, 清仓(并没有实际的卖出操作, 只是总金额不再随价格变动)
        if global_test_context.need_check_double_low and \
                is_too_expensive(new_rows, group, global_test_context.max_double_low, current_day, test_result,
                                 need_roll_row=global_test_context.one_strategy_with_one_scenario):
            print("clean all bonds at " + str(current_day) + " bonds:" + str(new_rows))

            return True, current_day

        # 根据条件对转债进行轮换(不影响当天收益)
        break_roll = exchange_bond(cur, current_day, group, ids, params, new_rows, test_result)
        return break_roll, current_day


def get_hold_rows(cur, ids, params):
    # fixme cb_enforece 退市时间不准, 直接用最后交易时间更新
    # UPDATE cb_enforce
    # SET delist_dt = (SELECT max(last_chg_dt)
    #                  FROM cb_history
    #                  WHERE cb_history.bond_id = cb_enforce.bond_id
    #                  group by cb_history.bond_id
    #                  order by last_chg_dt)
    cur.execute("""
        select a.bond_id,
               a.bond_nm,
               a.price,
               a.premium_rt,
               c.is_delist,
               b.price                                       as pre_price,
               round((a.price - b.price) / b.price * 100, 2) as rise_rate
        from cb_history a
                 left join (select *
                            from cb_history
                            where last_chg_dt = (SELECT last_chg_dt
                                                 FROM (SELECT DISTINCT (last_chg_dt)
                                                       FROM cb_history
                                                       WHERE last_chg_dt < :current
                                                       ORDER BY last_chg_dt DESC
                                                       LIMIT :pre_day)
                                                 ORDER BY last_chg_dt
                                                 LIMIT 1)) b on a.bond_id = b.bond_id
                 left join (select bond_id, 1 as is_delist
                            from cb_enforce
                            where delist_dt <= :current) c on a.bond_id = c.bond_id
        where a.bond_id in (""" + ids + """)
          and a.last_chg_dt = :current         
            """, params)
    rows = cur.fetchall()

    return rows


def exchange_bond(cur, current_day, group, ids, params, new_rows, test_result):
    # 止盈满足卖出条件的转债
    pop_num, pop_total_money = pop_bond(group, new_rows, current_day, test_result)

    # 组合没变化, 无需重新分配资金
    if pop_num == 0:
        return False

    # 持有的所有现金
    total_money = pop_total_money + test_result.get('remain_money')
    # 新加入了转债, 分配资金
    return push_bond(group, cur, pop_num, ids, params, total_money, test_result, current_day, len(new_rows))


def push_bond(group, cur, buy_num, exclude_ids, params, total_money, test_result, current_day, row_size):
    # 卖出几只, 就买入几只
    params.setdefault("count", buy_num)
    push_rows = global_test_context.get_push_rows(cur, exclude_ids, params)

    # 没有找到满足条件的转债, 一个也不买, 下一个交易日重新开仓
    if len(push_rows) == 0:
        print("not find bond to push with:" + str(params))
        return True

    remain_money = do_push_bond(group, push_rows, total_money, row_size=row_size)

    for row in push_rows:
        bond_id = row[0]
        bond = group[bond_id]
        if bond is not None:
            _add_roll_row_to(test_result, current_day, bond_id, bond, '买入')
        else:
            print("not find bond in group by bond_id" + str(bond_id) + ", group:" + str(group))

    # 对新的组合再次检查, 看是否满足条件
    expensive = global_test_context.need_check_double_low and is_too_expensive(None, group,
                                                                               global_test_context.max_double_low)
    if expensive is False:
        # 只有继续下一个交易,才需要更新剩下的零头
        test_result['remain_money'] = remain_money
    return expensive


def pop_bond(group, new_rows, current_day, test_result):
    sell_total_money = 0
    total_money = 0
    sell_num = 0

    # 应该group已经用rows更新过了, 所以直接用group判断
    if global_test_context.need_check_double_low and is_too_expensive(None, group, global_test_context.max_double_low):
        return len(new_rows), total_money

    for new_row in new_rows:
        bond_id = new_row[0]
        bond = group.get(bond_id)
        bond_nm = bond['bond_nm']
        new_price = new_row[2]

        if new_price is None:
            print("price is None in row:" + str(new_row))
            new_price = bond.get("price")

        total_money += new_price * bond.get("amount")
        max_price = global_test_context.max_price
        max_rise = global_test_context.max_rise

        # 价格超过200的轮出
        if new_price >= max_price:
            print("pop bond:" + bond_nm + " when price >=" + str(max_price) + " at " + str(current_day))
            sell_total_money += new_price * bond.get("amount")
            group.pop(bond_id)
            sell_num += 1

            _add_roll_row_to(test_result, current_day, bond_id, bond, '价格超过' + str(max_price) + "卖出")
        # 强赎/退市的轮出
        elif new_row[4] is not None and new_row[4] == 1:
            print("pop bond:" + bond_nm + " when delist or enforce at " + str(current_day))
            sell_total_money += new_price * bond.get("amount")
            group.pop(bond_id)
            sell_num += 1
            _add_roll_row_to(test_result, current_day, bond_id, bond, '退市卖出')
        # 一周涨幅超过30%的轮出
        elif new_row[6] is not None and new_row[6] >= max_rise:
            print("pop bond:" + bond_nm + " when raise " + str(max_rise) + "% at " + str(current_day))
            sell_total_money += new_price * bond.get("amount")
            group.pop(bond_id)
            sell_num += 1
            _add_roll_row_to(test_result, current_day, bond_id, bond, '涨幅超过' + str(max_rise) + "%卖出")

    return sell_num, sell_total_money


def _add_roll_row_to(test_result, current_day, bond_id, bond, desc, old_bond=None):
    if global_test_context.one_strategy_with_one_scenario is False:
        return

    add_roll_row_with_bond(test_result, current_day, bond_id, bond, desc, old_bond=old_bond)


def new_roll(new_day, previous_day, old_group, test_result):
    total_money = get_hold_row_total_money(old_group, new_day, previous_day, test_result)
    new_group, new_day, remain_money = start_roll(new_day, total_money, old_group)

    # 需要比较两个group来记录调仓信息
    add_roll_row_when_new_roll(new_day, new_group, old_group, test_result)

    # 在新一轮中, 金额不变, 只是重新分配了一下
    calc_test_result(test_result, total_money, new_day, previous_day)
    if remain_money is not None:
        test_result['remain_money'] = remain_money

    # if sorted(group.keys()) != sorted(old_group.keys()):
    #     print("begin new roll. group:\n" + str(sorted(group.items())) + "\n" + str(sorted(old_group.items())))
    return new_group, new_day


def add_roll_row_when_new_roll(new_day, new_group, old_group, test_result):
    # 已经到结束日了
    if new_group is None:
        return

    for bond_id, old_bond in old_group.items():
        new_bond = new_group.get(bond_id)
        if new_bond is None:
            # 被轮出了
            _add_roll_row_to(test_result, new_day, bond_id, old_bond, '轮动卖出')
        elif new_bond['percent'] != old_bond['old_percent']:
            # 调仓
            _add_roll_row_to(test_result, new_day, bond_id, new_bond, '轮动调仓', old_bond=old_bond)
    for bond_id, new_bond in new_group.items():
        old_bond = old_group.get(bond_id)
        if old_bond is None:
            # 建仓
            _add_roll_row_to(test_result, new_day, bond_id, new_bond, '轮动买入')


def start_roll(current_day, total_money, old_group=None):
    # 买入的组合转债信息 {code:{amount:xxx}}
    group = {}
    with db_utils.get_daily_connect() as con:
        cur = con.cursor()
        rows = global_test_context.get_start_rows(cur, current_day)

        # 没找到可转债, 或者太贵了, 不满足轮动条件, 不买, 进入下一个交易日
        if len(rows) == 0 or \
                (global_test_context.need_check_double_low and
                 is_too_expensive(rows, max_double_low=global_test_context.max_double_low)):
            # 取下一个交易日
            next_day = get_next_day(current_day, cur)
            if next_day is not None:
                return start_roll(next_day, total_money, old_group)
            else:
                # 已经到结束日了
                print('not found next day by ' + str(current_day))
                return None, current_day, None

        # 等权分配资金
        remain_money = do_push_bond(group, rows, total_money, old_group=old_group)

    return group, current_day, remain_money


def test_group(start,
               end=None,
               roll_period=10,
               bond_count=15,
               strategy_types=['低溢价策略', '低余额+低溢价+双低策略', '低余额+双低策略', '低溢价+双低策略', '双低策略', '高收益率策略', '低价格策略', '三低策略'],
               is_multi_scenarios=False,
               pre_day=5,
               max_rise=30,
               max_price=None,
               max_double_low=None,
               select_sql=None,
               exchange_sql=None,
               is_save_test_result=False
               ):
    global_test_context.need_check_double_low = True
    global_test_context.roll_period = roll_period
    global_test_context.bond_count = bond_count
    global_test_context.pre_day = pre_day
    global_test_context.max_rise = max_rise
    global_test_context.max_double_low = max_double_low
    global_test_context.select_sql = select_sql
    global_test_context.exchange_sql = exchange_sql
    global_test_context.max_price = max_price
    # if len(strategy_types) == 1:
    #     global_test_context.max_price = max_price

    if end is None:
        end = datetime.datetime.now()

    new_rows = init_rows(start, end)
    line_names = [] if is_multi_scenarios else strategy_types

    title = strategy_types[0] + "回测结果" if is_multi_scenarios else None
    roll_period = None if is_multi_scenarios else roll_period

    global_test_context.one_strategy_with_one_scenario = len(strategy_types) == 1 and is_multi_scenarios is False

    # 没啥意思, 屏蔽掉
    global_test_context.need_time_data = global_test_context.one_strategy_with_one_scenario
    if global_test_context.need_time_data:
        global_test_context.time_data = {}

    roll_rows = None
    trade_times = 0
    for strategy_type in strategy_types:
        roll_maker = None
        if strategy_type == '低溢价策略':
            roll_maker = low_premium_roll
        elif strategy_type == '低余额+低溢价+双低策略':
            roll_maker = low_remain_plus_premium_plus_double_low_roll
        elif strategy_type == '低余额+双低策略':
            roll_maker = low_remain_plus_double_low_roll
        elif strategy_type == '低溢价+双低策略':
            roll_maker = low_premium_plus_double_low_roll
        elif strategy_type == '双低策略':
            roll_maker = double_low_roll
        elif strategy_type == '高收益率策略':
            roll_maker = high_yield_roll
        elif strategy_type == '低价格策略':
            roll_maker = low_price_roll
        elif strategy_type == '三低策略':
            roll_maker = three_low_roll

        if roll_maker is not None:
            roll_rows, trade_times = roll_by_strategy(roll_maker, start, end, is_multi_scenarios, line_names, new_rows)

    html = generate_line_html(new_rows, roll_period, start, end, bond_count, line_names, title=title,
                              max_price=global_test_context.max_price,
                              max_double_low=global_test_context.max_double_low)

    html += generate_roll_html(roll_rows, trade_times)

    # 如果是新的策略, 保存到db之前, 必须先手工添加一条记录, 因为这里的save是update操作
    if is_save_test_result:
        do_save_back_test_result(strategy_types[0], html)

    if global_test_context.need_time_data:
        html += '<br/><br/>' + generate_timeline_html(global_test_context.time_data)

    return html


def generate_roll_html(roll_rows, trade_times):
    if roll_rows is None:
        return ''
    clean_num = 0
    roll_num = 0
    create_roll_num = 0
    over_rise_num = 0
    roll_row_html = """<div class="panel-group" id="accordion">"""
    sorted_items = sorted(roll_rows.items(), key=lambda item: item[0], reverse=True)
    for date, rows in sorted_items:
        d = date.strftime('%Y-%m-%d')
        collapse_id = d.replace("-", "_")
        if '高估清仓' in rows[1]['desc']:
            d += ' [清仓]'
            clean_num += 1
        elif '轮动' in rows[1]['desc']:
            i = 0
            for row in rows:
                # del row['price']
                del row['old_price']
                # del row['premium']
                del row['old_premium']
                del row['old_amount']
                del row['old_percent']
                if row['desc'] == '轮动买入' or row['desc'] == '':
                    i += 1
            if len(rows) == i:
                d += ' [建仓]'
                create_roll_num += 1
            else:
                d += ' [定时调仓]'
                roll_num += 1
        elif '建仓' in rows[1]['desc']:
            d += ' [建仓]'
            create_roll_num += 1
        else:
            if '超过' in rows[1]['desc']:
                d += ' [超涨调仓]'
                over_rise_num += 1
        collapse_name = d
        rows = sorted(rows, key=lambda x: x['desc'])
        roll_table = from_json(json.dumps(rows))
        roll_table_html = build_table_html(roll_table, table_rows_size=6)
        roll_row_html += """
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

    roll_row_html += "</div>"
    html = "<br/>调仓记录: (共" + str(trade_times) + "个交易日, 建仓:" + str(create_roll_num) + "次, 定时调仓:" + str(
        roll_num) + "次, 超涨调仓:" + str(
        over_rise_num) + "次, 清仓:" + str(
        clean_num) + "次)<br/>" + roll_row_html
    return html


def low_price_roll(new_rows, start, end=None):
    old_max_price = set_max_price(130)
    old_max_double_low = set_max_double_low(150)

    global_test_context.need_check_double_low = False
    global_test_context.get_start_rows = low_price_get_start_rows
    global_test_context.get_push_rows = low_price_get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def high_yield_roll(new_rows, start, end=None):
    old_max_price = set_max_price(130)
    old_max_double_low = set_max_double_low(150)
    global_test_context.need_check_double_low = False
    global_test_context.get_start_rows = high_ytm_get_start_rows
    global_test_context.get_push_rows = high_ytm_get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def double_low_roll(new_rows, start, end=None):
    old_max_price = set_max_price(130)
    old_max_double_low = set_max_double_low(150)
    global_test_context.get_start_rows = double_low_get_start_rows
    global_test_context.get_push_rows = double_low_get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def three_low_roll(new_rows, start, end=None):
    old_max_price = set_max_price(2000)
    old_max_double_low = set_max_double_low(2000)

    global_test_context.get_start_rows = three_low_get_start_rows
    global_test_context.get_push_rows = three_low_get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def low_premium_plus_double_low_roll(new_rows, start, end=None):
    old_max_price = set_max_price(200)
    old_max_double_low = set_max_double_low(150)
    global_test_context.get_start_rows = get_start_rows
    global_test_context.get_push_rows = get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def low_remain_plus_double_low_roll(new_rows, start, end=None):
    old_max_price = set_max_price(200)
    old_max_double_low = set_max_double_low(150)
    global_test_context.get_start_rows = low_remain_get_start_rows
    global_test_context.get_push_rows = low_remain_get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def low_remain_plus_premium_plus_double_low_roll(new_rows, start, end=None):
    old_max_price = set_max_price(200)
    old_max_double_low = set_max_double_low(150)
    global_test_context.get_start_rows = low_remain_premium_get_start_rows
    global_test_context.get_push_rows = low_remain_premium_get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def low_premium_roll(new_rows, start, end):
    old_max_price = set_max_price(2000)
    old_max_double_low = set_max_double_low(2000)
    global_test_context.need_check_double_low = False
    global_test_context.get_start_rows = low_premium_get_start_rows
    global_test_context.get_push_rows = low_premium_get_push_rows
    result = fill_rate(new_rows, start, end)

    # 避免多个策略同时回测相互影响
    reset_max_value(old_max_price, old_max_double_low)

    return result


def reset_max_value(old_max_price, old_max_double_low):
    global_test_context.max_price = old_max_price
    global_test_context.max_double_low = old_max_double_low


def set_max_double_low(max_double_low):
    no_max_double_low_attr = is_no_max_double_low_attr()
    old_max_double_low = None
    if no_max_double_low_attr is False:
        old_max_double_low = global_test_context.max_double_low
    global_test_context.max_double_low = max_double_low if no_max_double_low_attr else global_test_context.max_double_low
    return old_max_double_low


def set_max_price(max_price):
    no_max_price_attr = is_no_max_price_attr()
    old_max_price = None
    if no_max_price_attr is False:
        old_max_price = global_test_context.max_price
    global_test_context.max_price = max_price if no_max_price_attr else global_test_context.max_price
    return old_max_price


def is_no_max_double_low_attr():
    return not hasattr(global_test_context, 'max_double_low') or global_test_context.max_double_low is None


def is_no_max_price_attr():
    return not hasattr(global_test_context, 'max_price') or global_test_context.max_price is None


def roll_by_strategy(roll_maker, start, end, is_multi_scenarios, line_names, new_rows):
    if is_multi_scenarios:
        roll_pre_line(line_names, new_rows, 1, 5, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 1, 10, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 1, 15, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 1, 20, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 5, 5, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 5, 10, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 5, 15, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 5, 20, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 10, 5, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 10, 10, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 10, 15, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 10, 20, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 15, 5, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 15, 10, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 15, 15, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 15, 20, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 20, 5, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 20, 10, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 20, 15, start, end, roll_maker)
        roll_pre_line(line_names, new_rows, 20, 20, start, end, roll_maker)
        return None, None
    else:
        return roll_maker(new_rows, start, end)


def roll_pre_line(line_names, new_rows, period, count, start, end, roll_maker):
    name = str(count) + "只转债" + str(period) + "日轮动"
    line_names.append(name)
    global_test_context.roll_period = period
    global_test_context.bond_count = count
    roll_maker(new_rows, start, end)


def fill_rate(new_rows, start, end=None):
    rows, roll_rows, trade_times = test(start, end)
    rate_value = 0
    day_rate_value = 0
    # fixme 这里先写死, 总投入可能做成一个配置变量
    total_money = 1000000
    for day, rates in new_rows.items():
        rate = rows.get(day)
        if rate is not None:
            rate_value = rate['all_rate']
            day_rate_value = rate['day_rate']
            total_money = rate["total_money"]
        rates.append([rate_value, total_money, day_rate_value])
    return roll_rows, trade_times


def init_rows(start, end):
    new_rows = {}
    for i in range((end - start).days + 1):
        day = start + datetime.timedelta(days=i)
        new_rows.setdefault(day, [])
    return new_rows


def get_start_rows(cur, start):
    cur.execute("""
    select bond_id, bond_nm, price, premium_rt, round(price + premium_rt * 100, 2)
    from (select *
          from cb_history
          where price < :max_price
            and last_chg_dt = :start
            and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
          order by premium_rt
          limit 30)
    order by price + premium_rt * 100, premium_rt
    limit :count            
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count, 'max_price': global_test_context.max_price})
    rows = cur.fetchall()
    return rows


def get_push_rows(cur, ids, params):
    sql = """
        select bond_id, bond_nm,price, premium_rt, round(price + premium_rt * 100, 2)
            from (select *
                  from cb_history
                  where last_chg_dt = :current
                    and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
                    and bond_id not in (""" + ids + """)
                  order by premium_rt
                  limit 30)
            order by price + premium_rt * 100, premium_rt
            limit :count """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(
        ids=ids)
    cur.execute(sql, params)
    return cur.fetchall()


def low_remain_get_start_rows(cur, start):
    cur.execute("""
    select bond_id, bond_nm, price, premium_rt, round(price + premium_rt * 100, 2)
    from (select *
          from cb_history
          where price < :max_price
            and last_chg_dt = :start
            and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
          order by curr_iss_amt
          limit 30)
    order by price + premium_rt * 100, curr_iss_amt
    limit :count            
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count, 'max_price': global_test_context.max_price})
    rows = cur.fetchall()
    return rows


def low_remain_get_push_rows(cur, ids, params):
    sql = """
        select bond_id, bond_nm,price, premium_rt, round(price + premium_rt * 100, 2)
            from (select *
                  from cb_history
                  where last_chg_dt = :current
                    and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
                    and bond_id not in (""" + ids + """)
                  order by curr_iss_amt
                  limit 30)
            order by price + premium_rt * 100, curr_iss_amt
            limit :count """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(
        ids=ids)
    cur.execute(sql, params)
    return cur.fetchall()


def low_remain_premium_get_start_rows(cur, start):
    cur.execute("""
        select bond_id, bond_nm, price, premium_rt, round(price + premium_rt * 100, 2)
        from (select *
              from (select *
                    from cb_history
                    where price < :max_price
                      and last_chg_dt = :start
                      and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
                    order by premium_rt
                    limit 60)
              order by curr_iss_amt
              limit 30)
        order by price + premium_rt * 100, curr_iss_amt
        limit :count            
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count, 'max_price': global_test_context.max_price})
    rows = cur.fetchall()
    return rows


def low_remain_premium_get_push_rows(cur, ids, params):
    params.setdefault('max_price', global_test_context.max_price)
    cur.execute("""
        select bond_id, bond_nm, price, premium_rt, round(price + premium_rt * 100, 2)
        from (select *
              from (select *
                    from cb_history
                    where price < :max_price
                      and last_chg_dt = :current
                      and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
                    order by premium_rt
                    limit 60)
              where bond_id not in (""" + ids + """)
              order by curr_iss_amt
              limit 30)
        order by price + premium_rt * 100, curr_iss_amt
        limit :count """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(
        ids=ids), params)
    return cur.fetchall()


def double_low_get_start_rows(cur, start):
    cur.execute("""
    select bond_id, bond_nm, price, premium_rt, round(price + premium_rt * 100, 2)
          from cb_history
          where price < 130
            and last_chg_dt = :start
            and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
          order by price + premium_rt * 100, premium_rt
          limit :count            
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count})
    rows = cur.fetchall()
    return rows


def double_low_get_push_rows(cur, ids, params):
    cur.execute("""
        select bond_id, bond_nm,price, premium_rt, round(price + premium_rt * 100, 2)
                  from cb_history
                  where last_chg_dt = :current
                    and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
                    and bond_id not in (""" + ids + """)
                  order by price + premium_rt * 100, premium_rt
                  limit :count """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(
        ids=ids), params)
    return cur.fetchall()


def three_low_get_start_rows(cur, start):
    cur.execute("""
        select bond_id, bond_nm, price, premium_rt, round(price + premium_rt * 100, 2)
        from cb_history
        where price <=:max_price and last_chg_dt = :start
          and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
        order by price * (1 + premium_rt) * curr_iss_amt
        limit :count           
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count, 'max_price': global_test_context.max_price})
    rows = cur.fetchall()
    return rows


def three_low_get_push_rows(cur, ids, params):
    cur.execute("""
        select bond_id, bond_nm, price, premium_rt, round(price + premium_rt * 100, 2)
        from cb_history
        where price <=:max_price and last_chg_dt = :current
          and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
          and bond_id not in (""" + ids + """)
        order by price * (1 + premium_rt) * curr_iss_amt
        limit :count 
        """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(ids=ids), params)
    return cur.fetchall()


def high_ytm_get_start_rows(cur, start):
    cur.execute("""
    select bond_id, bond_nm, price, premium_rt
          from cb_history
          where price < 130
            and last_chg_dt = :start
            and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
          order by ytm_rt desc
          limit :count            
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count})
    rows = cur.fetchall()
    return rows


def high_ytm_get_push_rows(cur, ids, params):
    cur.execute("""
        select bond_id, bond_nm,price, premium_rt
                  from cb_history
                  where last_chg_dt = :current
                    and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
                    and bond_id not in (""" + ids + """)
                  order by ytm_rt desc
                  limit :count """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(
        ids=ids), params)
    return cur.fetchall()


def low_premium_get_start_rows(cur, start):
    cur.execute("""
    select bond_id, bond_nm, price, premium_rt
          from cb_history
          where last_chg_dt = :start
            and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
          order by premium_rt
          limit :count            
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count})
    rows = cur.fetchall()
    return rows


def low_premium_get_push_rows(cur, ids, params):
    cur.execute("""
        select bond_id, bond_nm,price, premium_rt
                  from cb_history
                  where last_chg_dt = :current
                    and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
                    and bond_id not in (""" + ids + """)
                  order by premium_rt
                  limit :count """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(
        ids=ids), params)
    return cur.fetchall()


def low_price_get_start_rows(cur, start):
    cur.execute("""
    select bond_id, bond_nm, price, premium_rt
          from cb_history
          where last_chg_dt = :start
            and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :start or delist_dt <= :start)
          order by price
          limit :count            
                """ if global_test_context.select_sql is None else global_test_context.select_sql,
                {"start": start, 'count': global_test_context.bond_count})
    rows = cur.fetchall()
    return rows


def low_price_get_push_rows(cur, ids, params):
    cur.execute("""
        select bond_id, bond_nm,price, premium_rt
                  from cb_history
                  where last_chg_dt = :current
                    and bond_id not in (SELECT bond_id from cb_enforce where enforce_dt <= :current or delist_dt <= :current)
                    and bond_id not in (""" + ids + """)
                  order by price
                  limit :count """ if global_test_context.exchange_sql is None else global_test_context.exchange_sql.format(
        ids=ids), params)
    return cur.fetchall()


def generate_long_year_back_test_data():
    start = datetime.datetime.strptime('2018-01-01', '%Y-%m-%d')
    end = None
    generate_test_data('long_year_back_test', start, end)


def generate_good_year_back_test_data():
    start = datetime.datetime.strptime('2021-01-01', '%Y-%m-%d')
    end = None
    generate_test_data('good_year_back_test', start, end)


def generate_bad_year_back_test_data():
    start = datetime.datetime.strptime('2018-01-01', '%Y-%m-%d')
    end = datetime.datetime.strptime('2019-01-01', '%Y-%m-%d')
    generate_test_data('bad_year_back_test', start, end)


def generate_test_data(name, start, end):
    content = '<br/><br/>'
    content += test_group(start, end=end, roll_period=1, bond_count=5)
    content += test_group(start, end=end, roll_period=1, bond_count=10)
    content += test_group(start, end=end, roll_period=1, bond_count=15)
    content += test_group(start, end=end, roll_period=1, bond_count=20)
    content += test_group(start, end=end, roll_period=5, bond_count=5)
    content += test_group(start, end=end, roll_period=5, bond_count=10)
    content += test_group(start, end=end, roll_period=5, bond_count=15)
    content += test_group(start, end=end, roll_period=5, bond_count=20)
    content += test_group(start, end=end, roll_period=10, bond_count=5)
    content += test_group(start, end=end, roll_period=10, bond_count=10)
    content += test_group(start, end=end, roll_period=10, bond_count=15)
    content += test_group(start, end=end, roll_period=10, bond_count=20)
    content += test_group(start, end=end, roll_period=15, bond_count=5)
    content += test_group(start, end=end, roll_period=15, bond_count=10)
    content += test_group(start, end=end, roll_period=15, bond_count=15)
    content += test_group(start, end=end, roll_period=15, bond_count=20)
    content += test_group(start, end=end, roll_period=20, bond_count=5)
    content += test_group(start, end=end, roll_period=20, bond_count=10)
    content += test_group(start, end=end, roll_period=20, bond_count=15)
    content += test_group(start, end=end, roll_period=20, bond_count=20)
    do_save_back_test_result(name, content)


def do_save_back_test_result(name, data):
    with db_utils.get_daily_connect() as con:
        cur = con.cursor()
        result = cur.execute("update cb_backtest_data set data=:data where name=:name", {"name": name, "data": data})
        if result.rowcount != 1:
            print('update cb_backtest_data is failure. row:' + name)
        else:
            print('update cb_backtest_data is successful. row:' + name)


if __name__ == "__main__":
    # date = datetime.datetime.strptime('2017-12-29', '%Y-%m-%d')
    # test(date)
    generate_good_year_back_test_data()
    generate_bad_year_back_test_data()
    generate_long_year_back_test_data()

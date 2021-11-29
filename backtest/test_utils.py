import datetime
import math

from utils import db_utils


# 获取下一个交易日
def get_next_day(current, cur=None):
    if cur is None:
        cur = db_utils.get_daily_connect().cursor()

    cur.execute("""
                SELECT min(DISTINCT (last_chg_dt))
                from cb_history
                where last_chg_dt > :current and price is not NULL
                order by last_chg_dt            
        """, {"current": current})
    next_day = cur.fetchone()[0]
    if next_day is not None:
        return datetime.datetime.strptime(next_day, '%Y-%m-%d %H:%M:%S')
    return None


# 解析group bond id参数
def parse_bond_ids_params(bond_ids, params):
    ids = ""
    first = True
    i = 0
    for bond_id in bond_ids:
        i += 1
        if first:
            first = False
        else:
            ids += ','
        ids += ':id_' + str(i)
        params.setdefault("id_" + str(i), bond_id)
    return ids


# 计算收益率并保存到结果中
def calc_test_result(test_result, current_total_money, current_day, previous_day):
    start_total_money = test_result.get("start_total_money")
    pre_total_money = get_pre_total_money(previous_day, test_result)
    day_rate = round(100 * (current_total_money - pre_total_money) / pre_total_money, 2)
    # if abs(day_rate) > 2:
    #     print("too big")

    all_rate = round(100 * (current_total_money - start_total_money) / start_total_money, 2)
    test_result['rows'].setdefault(current_day, {"total_money": current_total_money,
                                                 "day_rate": day_rate, "all_rate": all_rate})


def get_pre_total_money(previous_day, test_result):
    return test_result['rows'].get(previous_day).get("total_money")


def init_test_result(day, total_money, remain_money):
    return {
        "start_total_money": total_money,
        'remain_money': remain_money,
        'rows': {
            day: {
                'total_money': total_money,
                'day_rate': 0,
                'all_rate': 0
            }
        }
    }


def do_push_bond(group, rows, total_money):
    """注意row的顺序: bond_id, bond_nm, price, premium..."""

    # 一份的金额
    part = round(total_money * 1 / len(rows), 2)

    buy_total_money = 0
    for row in rows:
        bond_id = row[0]
        bond_nm = row[1]
        price = row[2]
        premium = row[3]
        amount = math.floor(part / (price * 10)) * 10
        buy_total_money += round(amount * price, 2)
        group.setdefault(bond_id, {'bond_nm': bond_nm, "amount": amount, 'price': price, 'premium': premium})

    buy_total_money = round(buy_total_money, 2)

    # 剩下的零头
    return round(total_money - buy_total_money, 2)


def get_total_money(group, test_result):
    total_money = test_result.get('remain_money')
    for bond in group.values():
        total_money += round(bond['price'] * bond.get("amount"), 2)
    return round(total_money, 2)


def update_bond(group, rows):
    for row in rows:
        bond = group.get(row[0])
        price = row[2]

        premium = row[3]
        # 异常数据, price可能为none
        if premium is not None:
            bond['premium'] = premium

        # 异常数据, price可能为none
        if price is not None:
            bond['price'] = price


def get_max_drawdown(x, rates, moneys):
    drawdowns = {}
    max_money = moneys[0]
    max_rate = rates[0]
    low_idx = 0
    high_idx = 0
    for i in range(len(rates)):
        if rates[i] >= max_rate:
            high_idx = i
            drawdowns[0] = {"low_idx": low_idx, "high_idx": high_idx}
            max_money = moneys[i]
            max_rate = rates[i]
        else:
            low_idx = i
            drawdown = round(max_money - moneys[i], 2)
            drawdowns[drawdown] = {"low_idx": low_idx, "high_idx": high_idx}
    max_drawdown = max(drawdowns.keys())
    idx = drawdowns[max_drawdown]
    high_value = moneys[idx['high_idx']]
    low_value = moneys[idx['low_idx']]
    max_drawdown_rate = round(max_drawdown / high_value * 100, 2)
    print(str(max_drawdown_rate) + "%:" + str(x[idx['high_idx']]) + "(" + str(high_value) + ")~" + str(
        x[idx['low_idx']]) + "(" + str(low_value) + ")")
    return max_drawdown_rate, idx['high_idx'], idx['low_idx'], max_rate


def get_back_test_data(name):
    with db_utils.get_daily_connect() as con:
        cur = con.cursor()
        cur.execute("select data from cb_backtest_data where name=:name", {"name": name})
        return cur.fetchone()[0]
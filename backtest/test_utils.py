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


def create_test_result(day, total_money, remain_money, group, need_roll_row):
    result = {
        "start_total_money": total_money,
        'remain_money': remain_money,
        'rows': {
            day: {
                'total_money': total_money,
                'day_rate': 0,
                'all_rate': 0
            }
        },
    }
    if need_roll_row:
        rows = []
        rows.append({'bond_id': '',
                     'bond_name': '',
                     'price': '',
                     'amount': '',
                     'premium': '',
                     'percent': '',
                     'desc': ''})
        for bond_id, bond in group.items():
            rows.append({'bond_id': bond_id,
                         'bond_name': bond['bond_nm'],
                         'price': bond['price'],
                         'amount': bond['amount'],
                         'premium': round(bond['premium'] * 100, 2),
                         'percent': bond['percent'],
                         'desc': '建仓'
                         })
        result['roll_rows'] = {
            day: rows
        }

    return result


def do_push_bond(group, rows, total_money, row_size=None, old_group=None):
    """注意row的顺序: bond_id, bond_nm, price, premium..."""

    # 一份的金额
    part = round(total_money * 1 / len(rows), 2)
    size = len(rows) if row_size is None else row_size
    percent = round(1 / size * 100, 2)

    buy_total_money = 0
    for row in rows:
        bond_id = row[0]
        bond_nm = row[1]
        price = row[2]
        premium = row[3]

        # 在原来的组合中存在的
        if old_group is not None and old_group.get(bond_id) is not None:
            old_price = old_group[bond_id]['old_price']
            old_premium = old_group[bond_id]['old_premium']
            old_percent = old_group[bond_id]['old_percent']
        else:
            old_price = row[2]
            old_premium = row[3]
            old_percent = percent

        amount = math.floor(part / (price * 10)) * 10
        buy_total_money += round(amount * price, 2)
        group.setdefault(bond_id,
                         {'bond_nm': bond_nm,
                          "amount": amount,
                          'price': price,
                          'old_price': old_price,
                          'premium': premium,
                          'old_premium': old_premium,
                          'percent': percent,
                          'old_percent': old_percent,
                          })

    buy_total_money = round(buy_total_money, 2)

    # 剩下的零头
    return round(total_money - buy_total_money, 2)


def get_total_money(group, test_result):
    total_money = test_result.get('remain_money')
    for bond in group.values():
        total_money += round(bond['price'] * bond.get("amount"), 2)
    return round(total_money, 2)


def update_bond(group, new_rows):
    new_total_money = get_new_total_money(group, new_rows)

    for new_row in new_rows:
        bond = group.get(new_row[0])
        new_price = new_row[2]
        bond['price'] = new_price
        bond['premium'] = new_row[3]
        bond['percent'] = round(round(new_price * bond['amount'], 2) / new_total_money * 100, 2)


def get_new_total_money(group, new_rows):
    new_total_money = 0
    for row in new_rows:
        bond_code = row[0]
        price = row[2]
        bond = group.get(bond_code)
        new_total_money += round(price * bond['amount'], 2)
    return new_total_money


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
        cur.execute("select data, desc from cb_backtest_data where name=:name", {"name": name})
        one = cur.fetchone()
        main_content = one[0]
        ref = one[1]
        return ('' if ref is None else "策略参考: &nbsp;" + ref) + main_content

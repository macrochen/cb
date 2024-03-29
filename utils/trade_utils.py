import urllib.request as request
from datetime import datetime, timedelta

# https://www.jisilu.cn/data/cbnew/cb_index/
# 转股价格中位数
# 转股溢价率中位数
# 到期收益率中位数
from utils.db_utils import get_cursor

MID_X = 124.08
MID_Y = 33.4
MID_YIELD = -3.92


def get_date_type():
    date = datetime.now().strftime('%Y-%m-%d')
    url = 'http://tool.bitefu.net/jiari/?d=' + date
    try:
        resp = request.urlopen(url, timeout=5)
        content = resp.read()
        if content:
            try:
                day_type = int(content)
            except ValueError:
                return -1
            else:
                return day_type
    except Exception as e:
        print("get_date_type is timeout", e)

    return -1


def is_trade_date():
    weekday = datetime.now().isoweekday()
    if weekday <= 5 and get_date_type() == 0:
        return True
    else:
        return False


# fixme 不包括节假日的简单处理
# 指定天数后的交易日(跳过周末)
def get_trade_date(delta_day):
    trade_date = get_non_weekday(datetime.now())

    for i in range(delta_day):
        # 把周末跳过去
        trade_date = get_non_weekday(trade_date + timedelta(days=1))

    return trade_date


def get_non_weekday(_date):
    weekday = _date.isoweekday()
    while weekday > 5:  # 是周末
        _date = _date + timedelta(days=1)
        weekday = _date.isoweekday()
    return _date


def calc_trade_fee(account, is_sh_market, trade_num):
    fee = 0
    if account == '银河':
        if is_sh_market:  # 沪市百万分之5
            fee = trade_num * 0.000005
        else:  # 沪市十万分之5
            fee = trade_num * 0.00005
    else:
        if is_sh_market:  # 沪市百万分之5
            fee = trade_num * 0.000005
        else:  # 沪市十万分之8
            fee = trade_num * 0.00008
        # 不足0.5按0.5收
        if fee < 0.5:
            fee = 0.5
    fee = round(fee, 2)
    return fee


def rebuild_stock_code(stock_code):
    # 沪市A股票买卖的代码是以600、601或603打头, 688创业板
    # 深市A股票买卖的代码是以000打头, 中小板股票代码以002打头, 创业板股票代码以300打头
    if stock_code.startswith('600') or stock_code.startswith('601') or \
            stock_code.startswith('605') or stock_code.startswith('603') or stock_code.startswith('688'):
        stock_code = 'SH' + stock_code
    elif stock_code.startswith('000') or stock_code.startswith('001') or stock_code.startswith(
            '002') or stock_code.startswith('300'):
        stock_code = 'SZ' + stock_code
    else:
        raise Exception("未知股票类型。" + stock_code)
    return stock_code


def rebuild_bond_code(bond_code):
    market = 'sz'
    if bond_code.startswith('11'):
        market = 'sh'
    return market + bond_code

def calc_mid_data_with_avg_premium():
    row = _get_mid_data()

    return row[0], row[1], row[2]


def calc_mid_data():
    row = _get_mid_data()
    return row[0], row[1]


def _get_mid_data():
    cur = get_cursor("""
SELECT mid_price, mid_premium, avg_premium
from (
         SELECT round(AVG(cb_price2_id), 2) as mid_price, row_number() OVER () as rn
         FROM (SELECT cb_price2_id
               FROM changed_bond
               ORDER BY cb_price2_id
               LIMIT 2 - (SELECT COUNT(*) FROM changed_bond) % 2 -- odd 1, even 2
                   OFFSET (SELECT (COUNT(*) - 1) / 2
                           FROM changed_bond))) a
         left join(
    SELECT round(AVG(cb_premium_id) * 100, 2) as mid_premium, row_number() OVER () as rn
    FROM (SELECT cb_premium_id
          FROM changed_bond
          ORDER BY cb_premium_id
          LIMIT 2 - (SELECT COUNT(*) FROM changed_bond) % 2 -- odd 1, even 2
              OFFSET (SELECT (COUNT(*) - 1) / 2
                      FROM changed_bond))) b
                  on a.rn = b.rn,
     (select 1 as rn, round(avg(cb_premium_id)*100,2) as avg_premium from changed_bond) c
where a.rn = c.rn
    
    """)
    global MID_X, MID_Y
    row = cur.fetchone()
    MID_X = row[0]
    MID_Y = row[1]
    avg_premium = row[2]
    print('init mid data is successful.MID_X:' + str(MID_X) + ', MID_Y:' + str(MID_Y))
    return row


def get_ymd():
    today = datetime.now()
    ymd = today.strftime('%Y-%m-%d')
    return ymd


def calc_hold_price(hold_bond, direction, trade_amount, trade_price):
    # 交易金额
    trade_num = round(float(trade_price) * int(trade_amount), 3)
    fee = calc_trade_fee(hold_bond.account, hold_bond.hold_unit == 10, trade_num)
    # 持仓成本
    cost_num = hold_bond.sum_buy - hold_bond.sum_sell + fee
    if direction == 'buy':
        hold_bond.hold_amount += int(trade_amount)
        hold_bond.sum_buy += trade_num + fee
        hold_bond.today_sum_buy += trade_num + fee
        cost_num += trade_num
    elif direction == 'sell':
        hold_bond.hold_amount -= int(trade_amount)
        hold_bond.sum_sell += trade_num - fee
        hold_bond.today_sum_sell += trade_num - fee
        cost_num -= trade_num
    # 重新计算持有价格: 持仓成本/持仓数量
    if hold_bond.hold_amount == 0:
        hold_bond.hold_price = 0
    else:
        hold_bond.hold_price = round(cost_num / hold_bond.hold_amount, 3)
    return fee


# 撤销重新计算金额, 价格
def re_calc_hold_price(hold_bond, trade_history):
    trade_amount = trade_history.amount
    trade_price = trade_history.price

    # 交易金额
    trade_num = round(float(trade_price) * int(trade_amount), 3)
    # 无论买卖, 费用都会加在持有成本上, 所以要减掉
    hold_bond.sum_buy -= trade_history.fee
    hold_bond.today_sum_buy -= trade_history.fee

    # 如果原来是卖出, 交易金额会加在sum_sell上, 这里要减掉, 因为trade_amount是负数, 直接加上即可
    if trade_amount < 0:
        hold_bond.sum_sell += trade_num
        hold_bond.today_sum_sell += trade_num
        hold_bond.hold_amount -= trade_amount  # 数量加回去
    else:
        # 如果是买入, 交易金额会加在sum_buy上, 这里要减掉
        hold_bond.sum_buy -= trade_num
        hold_bond.today_sum_buy -= trade_num
        hold_bond.hold_amount -= trade_amount  # 数量减掉

    # 重新计算持仓成本

    # 持仓金额
    cost_num = hold_bond.sum_buy - hold_bond.sum_sell
    # 重新计算持有价格: 持仓成本/持仓数量
    if hold_bond.hold_amount == 0:
        hold_bond.hold_price = 0
    else:
        hold_bond.hold_price = round(cost_num / hold_bond.hold_amount, 3)

if __name__ == "__main__":
    print(get_trade_date(3))
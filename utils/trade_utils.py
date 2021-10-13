import sqlite3
import urllib.request as request
from datetime import datetime

#https://www.jisilu.cn/data/cbnew/cb_index/
#转股价格中位数
#转股溢价率中位数
#到期收益率中位数
from utils.db_utils import get_connect

MID_X = 124.08
MID_Y = 33.4
MID_YIELD = -3.92

def get_date_type():
    date = datetime.now().strftime('%Y-%m-%d')
    url = 'http://tool.bitefu.net/jiari/?d=' + date
    resp = request.urlopen(url, timeout=3)
    content = resp.read()
    if content:
        try:
            day_type = int(content)
        except ValueError:
            return -1
        else:
            return day_type

    return -1


def is_trade_date():
    weekday = datetime.now().isoweekday()
    if weekday <= 5 and get_date_type() == 0:
        return True
    else:
        return False


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


def calc_mid_data():

    # 打开文件数据库
    con_file = get_connect()
    cur = con_file.cursor()
    cur.execute("""
SELECT mid_price, mid_premium from (
    SELECT  AVG(cb_price2_id)  as mid_price, row_number() OVER () as rn
    FROM (SELECT cb_price2_id
          FROM changed_bond
          ORDER BY cb_price2_id
          LIMIT 2 - (SELECT COUNT(*) FROM changed_bond) % 2    -- odd 1, even 2
          OFFSET (SELECT (COUNT(*) - 1) / 2
                  FROM changed_bond))) a
left join(
    SELECT AVG(cb_premium_id)*100 as mid_premium, row_number() OVER () as rn
    FROM (SELECT cb_premium_id
          FROM changed_bond
          ORDER BY cb_premium_id
          LIMIT 2 - (SELECT COUNT(*) FROM changed_bond) % 2    -- odd 1, even 2
          OFFSET (SELECT (COUNT(*) - 1) / 2
                  FROM changed_bond)) ) b			 
on a.rn = b.rn
    
    """)
    global MID_X, MID_Y
    row = cur.fetchone()
    MID_X = row[0]
    MID_Y = row[1]
    print('init mid data is successful.MID_X:' + str(MID_X) + ', MID_Y:' + str(MID_Y))

    # for row in rows:

        # if key == 'mid_premium':
        #     MID_Y = value
        # elif key == 'mid_price':
        #     MID_X = value
        # elif key == 'mid_yield':
        #     mid_yield = value
        # else:
        #     raise Exception('unknow key:' + key)

    # return mid_y, mid_x #, mid_yield


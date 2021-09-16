#抓取集思录的数据(实时, 仅部分实时数据)

import json
import time
import requests
import sqlite3

userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36"
header = {
    "Referer": "https://www.jisilu.cn/data/cbnew/",
    'User-Agent': userAgent,
    'Cookie': "kbzw__Session=5u6136maucteofr8hv36qpm9k7; kbz_newcookie=1; kbzw_r_uname=macrochen; kbzw__user_login=7Obd08_P1ebax9aX5MPZ0-ba293PkZyh6dbc7OPm1Nq_1KKq2sSkktnepaGrpKeZrpSsraqxlaeT2q_Wnd-l2MWsmJiyoO3K1L_RpKagrKWuk5ecpMy01r6bruPz3tXlzaaXpJGXn8DZxNnP6Ojo0bSMwNDqxuOXwNnEkLDHmc2JqpzWk6rAqKCTudHgzdnQ2svE1euRq5SupaaugZisvM3CtaWM48vhxpe-2NvM34qUvN3b6Nncka-RpaehrJWjkaKyqInMzd3D6MqmrKavj6OX; Hm_lvt_164fe01b1433a19b507595a43bf58262=1619880428,1620457500; Hm_lpvt_164fe01b1433a19b507595a43bf58262=1620978364"
}


def get_content():
    url = "https://www.jisilu.cn/data/cbnew/cb_list/?___jsl=LST___t=" + str(int(round(time.time() * 1000))) + "&btype=C"

    response = requests.get(url, headers=header)
    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)

    content = response.text

    return parse_content(content)


def parse_content(content):
    data = json.loads(content)

    print("load data is successful")

    # 所有数据行
    rows = data['rows']

    if len(rows) == 0:
        print("未获取到数据。")

    if len(rows) == 30:
        # print("目前是游客身份，只能获取30条记录，请先登录")
        raise Exception("目前是游客身份，只能获取30条记录，请先登录")

    return build_rows(rows)

def build_rows(rows):
    new_rows = []
    # 遍历所有行
    for row in rows:
        new_row = {}
        try:
            build_row(new_row, row['cell'])
        except Exception as e:
            print("数据解析出错.row=" + str(new_row), e)
            raise e

        new_rows.append(new_row)
    return new_rows

def build_row(row, cell):

    row['cb_name_id'] = cell['bond_nm']

    # 建立映射转换关系
    row['bond_code'] = cell['bond_id']
    # 转债价格
    row['cb_price2_id'] = cell['price']
    # 可转债涨跌  需要将百分数转换成小数
    row['cb_mov2_id'] = percentage2float(cell, 'increase_rt')
    # 正股涨跌  需要将百分数转换成小数
    row['cb_mov_id'] = percentage2float(cell, 'sincrease_rt')
    # 正股价格
    row['stock_price_id'] = cell['sprice']
    # 转股价值
    row['cb_value_id'] = cell['convert_value']
    # 转股溢价率  需要将百分数转换成小数
    row['cb_premium_id'] = percentage2float(cell, 'premium_rt')
    # 转债余额
    row['remain_amount'] = cell['curr_iss_amt']
    # 转债成交额  jsl单位是万元, 要转换成百万
    row['cb_trade_amount_id'] = round(float(cell['volume'])/100, 1)
    # 可转债换手率  需要将百分数转换成小数
    if cell['turnover_rt'] is not None:
        row['cb_trade_amount2_id'] = round(float(cell['turnover_rt'])/100, 3)
    else:
        print(cell['bond_nm'] + "可转债换手率为空")
    # 税前收益率  需要将百分数转换成小数
    # fixme 目前看到的数据不正确, 舍弃
    # row['bt_yield'] = percentage2float(cell, 'ytm_rt')
    # if row['bt_yield'] is None or row['bt_yield'] == '-':
    #     print(cell['bond_nm'] + "税前收益率为空:" + cell['ytm_rt'])

    return row


# 百分比转换成小数
def percentage2float(cell, name, default_value=0):
    text = cell[name]
    if text.endswith("%"):
        # 去掉千分位
        if text.find(","):
            text = text.replace(",", "")
        return round(float(text.strip("%")) / 100, 5)
    else:
        print(cell['bond_nm'] + "没有找到对应的值。 name：" + name)
        return default_value

def update_db(rows):
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    try:

        for row in rows:
            # execute执行脚本
           result = con_file.execute("""update changed_bond 
                set cb_price2_id = ?,
                cb_mov2_id = ?,
                cb_mov_id = ?,
                stock_price_id = ?,
                cb_value_id = ?,
                cb_premium_id = ?,
                remain_amount = ?,
                cb_trade_amount_id = ?,
                cb_trade_amount2_id = ?
                --,
                --bt_yield = ?
                where bond_code = ?""",
                (row["cb_price2_id"], row["cb_mov2_id"], row["cb_mov_id"], row["stock_price_id"], row["cb_value_id"],
              row["cb_premium_id"], row["remain_amount"], row["cb_trade_amount_id"], row.get('cb_trade_amount2_id'),
              #row["bt_yield"],
                 row["bond_code"]))
           if result.rowcount == 0:
                print("not update cb:" + row['cb_name_id'])

    except Exception as e:
        # cur_file.close()
        # con_file.close()
        print("db操作出现异常", e)
        raise e
    finally:
        con_file.commit()
        con_file.close()

def fetch_data():
    rows = get_content()

    print("begin to update database.")
    update_db(rows)
    print("可转债数据抓取更新完成")
    return 'OK'

def fetch_data_from_source_code(source_code):
    rows = parse_content(source_code)

    print("begin to update database.")
    update_db(rows)
    print("可转债数据抓取更新完成")
    return 'OK'

if __name__ == "__main__":
    fetch_data()

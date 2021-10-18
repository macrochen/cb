#抓取集思录的数据(实时, 仅部分实时数据)

import json
import re
import time

import requests

from utils.db_utils import get_cursor, execute_sql_with_rowcount

userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36"
header = {
    "Referer": "https://www.jisilu.cn/data/cbnew/",
    'User-Agent': userAgent,
    'Cookie': "kbzw__Session=5u6136maucteofr8hv36qpm9k7; kbz_newcookie=1; kbzw_r_uname=macrochen; kbzw__user_login=7Obd08_P1ebax9aX5MPZ0-ba293PkZyh6dbc7OPm1Nq_1KKq2sSkktnepaGrpKeZrpSsraqxlaeT2q_Wnd-l2MWsmJiyoO3K1L_RpKagrKWuk5ecpMy01r6bruPz3tXlzaaXpJGXn8DZxNnP6Ojo0bSMwNDqxuOXwNnEkLDHmc2JqpzWk6rAqKCTudHgzdnQ2svE1euRq5SupaaugZisvM3CtaWM48vhxpe-2NvM34qUvN3b6Nncka-RpaehrJWjkaKyqInMzd3D6MqmrKavj6OX; Hm_lvt_164fe01b1433a19b507595a43bf58262=1619880428,1620457500; Hm_lpvt_164fe01b1433a19b507595a43bf58262=1620978364"
}


def get_content():
    # https://32.push2.eastmoney.com/api/qt/clist/get?cb=jQuery1124045700749086112435_1634389030530&pn=3&pz=100&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f243&fs=b:MK0354&fields=f2,f3,f12,f14,f229,f230,f237&_=1634389030541
    url = "http://32.push2.eastmoney.com/api/qt/clist/get?cb=jQuery1124045700749086112435_" + str(int(round(time.time() * 1000))) + "&pn=1&pz=400&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f243&fs=b:MK0354&fields=f2,f3,f12,f14,f229,f230,f237&_=" + str(int(round(time.time() * 1000)))

    response = requests.get(url)
    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)

    content = response.text

    return parse_content(content)


def parse_content(content):
    data = None
    try:
        data = json.loads(re.match(".*?({.*}).*", content, re.S).group(1))
    except:
        raise ValueError('Invalid Input')

    print("load data is successful")

    # 所有数据行
    rows = data['data']['diff']

    if len(rows) == 0:
        print("未获取到数据。")

    # if len(rows) == 30:
    #     # print("目前是游客身份，只能获取30条记录，请先登录")
    #     raise Exception("目前是游客身份，只能获取30条记录，请先登录")

    return build_rows(rows)

def build_rows(rows):
    new_rows = []
    # 遍历所有行
    for row in rows:
        new_row = {}
        try:
            build_row(new_row, row)
        except Exception as e:
            print("数据解析出错.row=" + str(new_row), e)
            raise e

        new_rows.append(new_row)
    return new_rows

def build_row(row, cell):

    row['cb_name_id'] = cell['f14']
    # 建立映射转换关系
    row['bond_code'] = cell['f12']
    # 转债价格
    if cell['f2'] != '-':
        row['cb_price2_id'] = cell['f2']
    # 可转债涨跌  需要将百分数转换成小数
    if cell['f3'] != '-':
        row['cb_mov2_id'] = round(cell['f3']/100, 4)
    # 正股涨跌  需要将百分数转换成小数
    if cell['f230'] != '-':
        row['cb_mov_id'] = round(cell['f230']/100, 4)
    # 正股价格
    if cell['f229'] != '-':
        row['stock_price_id'] = round(cell['f229']/100, 4)
    # 转股溢价率  需要将百分数转换成小数
    if cell['f237'] != '-':
        row['cb_premium_id'] = round(cell['f237']/100, 4)

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
    try:

        for row in rows:
            # execute执行脚本
           rowcount = execute_sql_with_rowcount("""update changed_bond 
                set cb_price2_id = :cb_price2_id,
                cb_mov2_id = :cb_mov2_id,
                cb_mov_id = :cb_mov_id,
                stock_price_id = :stock_price_id,
                cb_premium_id = :cb_premium_id
                where bond_code = :bond_code""",
                                                {'cb_price2_id': row.get('cb_price2_id', None),
                 'cb_mov2_id': row.get('cb_mov2_id', None),
                 'cb_mov_id': row.get('cb_mov_id', None),
                 'stock_price_id': row.get('stock_price_id', None),
                 'cb_premium_id': row.get('cb_premium_id', None),
                 'bond_code': row['bond_code']}
                                                )
           if rowcount == 0:
                print("not update cb:" + row['cb_name_id'])

    except Exception as e:
        print("db操作出现异常", e)
        raise e


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
    # fetch_data()
    print(str(time.time()*1000))
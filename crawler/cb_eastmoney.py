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
        new_row = None
        try:
            new_row = build_row(row)
        except Exception as e:
            print("数据解析出错.row=" + str(new_row), e)
            raise e

        if new_row is not None:
            new_rows.append(new_row)

    return new_rows

def build_row(cell):
    row = {}
    row['cb_name_id'] = cell['f14']
    # 建立映射转换关系
    row['bond_code'] = cell['f12']
    key = None
    try:
        # 转债价格
        if cell['f2'] != '-':
            row['cb_price2_id'] = cell['f2']
        else:
            key = 'cb_price2_id'
            return None

        # 可转债涨跌  需要将百分数转换成小数
        if cell['f3'] != '-':
            row['cb_mov2_id'] = round(cell['f3']/100, 4)
        else:
            row['cb_mov2_id'] = 0
            # key = 'cb_mov2_id'
            # return None

        # 正股涨跌  需要将百分数转换成小数
        if cell['f230'] != '-':
            row['cb_mov_id'] = round(cell['f230']/100, 4)
        else:
            row['cb_mov_id'] = 0
            # key = 'cb_mov_id'
            # return None

        # 正股价格
        if cell['f229'] != '-':
            row['stock_price_id'] = round(cell['f229']/100, 4)
        else:
            key = 'stock_price_id'
            return None

        # 转股溢价率  需要将百分数转换成小数
        if cell['f237'] != '-':
            row['cb_premium_id'] = round(cell['f237']/100, 4)
        else:
            key = 'cb_premium_id'
            return None
    finally:
        if key is not None:
            print('update row is invalid. field_name:' + key + ', bond_code:' + row['cb_name_id'])

    return row


def update_db(rows):
    try:
        i = 0
        for row in rows:
            cur = get_cursor("select count(*) from changed_bond where bond_code=:bond_code",
                             {'bond_code': row['bond_code']})
            one = cur.fetchone()
            if one[0] == 0:
                print("not update cb:" + row['cb_name_id'])
                continue

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
                print("not update cb:" + str(row))
            else:
                print("update cb:" + str(row))
                i += 1

        print('Successfully updated row count:' + str(i))
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
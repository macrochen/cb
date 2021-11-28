# 抓取宁稳网的数据(每天中午, 下午收盘更新, 非实时, 但是最全)
import json
import time
from datetime import datetime

import requests

from crawler import cb_ninwen
from utils import db_utils

header = {
    "Referer": "http://www.ninwin.cn/index.php?m=profile",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    'Cookie': "compare_dish=hide; kbzw__Session=5u6136maucteofr8hv36qpm9k7; kbzw_r_uname=macrochen; kbz_newcookie=1; kbzw__user_login=7Obd08_P1ebax9aX5MPZ0-ba293PkZyh6dbc7OPm1Nq_1KKq2sSkktnepaGrpKeZrpSsraqxlaeT2q_Wnd-l2MWsmJiyoO3K1L_RpKagrKWuk5ecpMy01r6bruPz3tXlzaaXpJGXn8DZxNnP6Ojo0bSMwNDqxuOXwNnEkLDHmc2JqpzWk6vArqCTudHgzdnQ2svE1euRq5SupaaugZisvM3CtaWM48vhxpe-2NvM34qUvN3b6Nncka-WpaehrJejmaKvronMzd3D6MqmrKavj6OX; Hm_lvt_164fe01b1433a19b507595a43bf58262=1636178776,1637297614,1637485490,1637487213; Hm_lpvt_164fe01b1433a19b507595a43bf58262=1637490410"
}


def get_cb_data(bond_id, last_date=None, bond_nm=None):
    url = "https://www.jisilu.cn/data/cbnew/detail_hist/" + bond_id

    response = requests.get(url, headers=header)
    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)

    content = response.text

    return parse_content(content, last_date, bond_nm)


def get_delisted_rows(last_date):
    url = "https://www.jisilu.cn/data/cbnew/delisted/"

    response = requests.get(url, headers=header)
    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)

    content = response.text

    return parse_content(content, last_date, last_date_field_name='delist_dt', row_builder=row_mapper)


def row_mapper(row, cell, bond_nm):
    row['bond_code'] = cell['bond_id']
    row['bond_nm'] = bond_nm


def get_data(url):
    response = requests.get(url, headers=header)
    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)

    content = response.text

    return parse_content(content)


def parse_content(content, last_date=None, bond_nm=None, last_date_field_name=None, row_builder=None):
    data = json.loads(content)

    print("load data is successful")

    # 所有数据行
    rows = data['rows']

    if len(rows) == 0:
        print("未获取到数据。")

    return build_rows(rows, last_date, bond_nm, last_date_field_name, row_builder)


def build_rows(rows, last_date, bond_nm=None, last_date_field_name=None, row_builder=None):
    new_rows = []
    # 遍历所有行
    for row in rows:
        new_row = {}
        try:
            # 只更新最新的记录
            cell = row['cell']
            if last_date is not None:
                if cell['last_chg_dt' if last_date_field_name is None else last_date_field_name] < last_date:
                    break

            if bond_nm is None:
                bond_nm = cell['bond_nm']

            if row_builder is None:
                build_row(new_row, cell, bond_nm)
            else:
                row_builder(new_row, cell, bond_nm)
        except Exception as e:
            print("数据解析出错.row=" + str(new_row), e)
            raise e

        new_rows.append(new_row)
    return new_rows


def build_row(row, cell, bond_nm):
    """
{
    "page": 1,
    "rows": [
        {
            "id": "113580",
            "cell": {
                "bond_id": "113580",
                "last_chg_dt": "2021-11-18",
                "ytm_rt": "-5.76%",
                "premium_rt": "-2.66%",
                "convert_value": "160.54",
                "price": "156.270",
                "volume": "17818.53",
                "stock_volume": 1103690,
                "curr_iss_amt": "0.033",
                "amt_change": 1,
                "turnover_rt": "3344.52"
            }
        }
    ],
    "total": 366
}
    """

    # 建立映射转换关系
    row['bond_id'] = cell['bond_id']
    row['bond_nm'] = bond_nm
    # 日期
    row['last_chg_dt'] = datetime.strptime(cell['last_chg_dt'], '%Y-%m-%d')
    # 到期税前收益率
    if cell['ytm_rt'] != '-':
        row['ytm_rt'] = percentage2float(cell, 'ytm_rt')
    # 转股溢价率  需要将百分数转换成小数
    if cell['premium_rt'] != '-':
        row['premium_rt'] = percentage2float(cell, 'premium_rt')
    # 转股价值
    if cell['convert_value'] != '-':
        row['convert_value'] = float(cell['convert_value'])
    # 转债价格
    if cell['price'] != '-':
        row['price'] = float(cell['price'])
    # 转债成交额  jsl单位是万元
    if cell['volume'] != '-':
        row['volume'] = float(cell['volume'])
    # 转债成交额  jsl单位是万元
    if cell['stock_volume'] != '-':
        row['stock_volume'] = cell['stock_volume']
    # 转债余额
    if cell['curr_iss_amt'] != '-':
        row['curr_iss_amt'] = float(cell['curr_iss_amt'])
    if cell['amt_change'] != '-':
        row['amt_change'] = cell['amt_change']
    # 可转债换手率  需要将百分数转换成小数
    if cell['turnover_rt'] is not None and cell['turnover_rt'] != '-':
        row['turnover_rt'] = round(float(cell['turnover_rt']) / 100, 3)
    else:
        print(cell['bond_id'] + "可转债换手率为空")

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


def do_fetch_data():

    last_date = get_last_date()

    # 上市中的
    rows = cb_ninwen.get_rows()

    add_rows(last_date, rows, 'cb_name_id')

    # 退市的
    rows = get_delisted_rows(last_date)

    add_rows(last_date, rows)


def add_rows(last_date, rows, bond_nm_field_name='bond_nm'):
    size = len(rows)
    i = 0
    for row in rows:
        # 异常后的判重处理
        # with db_utils.get_daily_connect() as con:
        #     cur = con.cursor()
        #     cur.execute("select count(*) from cb_history where bond_id=:bond_id", {"bond_id": bond_id})
        #     result = cur.fetchone()
        #     if result[0] > 0:
        #         continue
        bond_id = row['bond_code']
        bond_nm = row[bond_nm_field_name]
        cb_data = get_cb_data(str(bond_id), last_date, bond_nm)
        insert_db(cb_data)
        i += 1
        print("insert complete:" + str(i) + "/" + str(size))
        # 暂停3s再执行， 避免被网站屏蔽掉
        time.sleep(3)


def get_last_date():
    last_date = None
    with db_utils.get_daily_connect() as con:
        cur = con.cursor()
        cur.execute("SELECT last_chg_dt from cb_history order by last_chg_dt desc limit 1")
        last_date = cur.fetchone()[0]
    if last_date is None:
        print("last_date is None")
        raise Exception("last_date is None")
    return last_date


# 退市数据
delisted_data = {
    "page": 1,
    "rows": [
        {
            "id": "113580",
            "cell": {
                "bond_id": "113580",
                "bond_nm": "康隆转债",
                "price": "156.270",
                "stock_id": "603665",
                "stock_nm": "康隆达",
                "orig_iss_amt": "2.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.033",
                "issue_dt": "2020-04-23",
                "redeem_dt": "2021-11-18",
                "delist_dt": "2021-11-18",
                "maturity_dt": "2026-04-22",
                "listed_years": "1.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123102",
            "cell": {
                "bond_id": "123102",
                "bond_nm": "华自转债",
                "price": "263.000",
                "stock_id": "300490",
                "stock_nm": "华自科技",
                "orig_iss_amt": "6.700",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.385",
                "issue_dt": "2021-03-12",
                "redeem_dt": "2021-11-18",
                "delist_dt": "2021-11-18",
                "maturity_dt": "2027-03-11",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123069",
            "cell": {
                "bond_id": "123069",
                "bond_nm": "金诺转债",
                "price": "185.554",
                "stock_id": "300505",
                "stock_nm": "川金诺",
                "orig_iss_amt": "3.680",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.494",
                "issue_dt": "2020-10-16",
                "redeem_dt": "2021-11-05",
                "delist_dt": "2021-11-05",
                "maturity_dt": "2026-10-15",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110041",
            "cell": {
                "bond_id": "110041",
                "bond_nm": "蒙电转债",
                "price": "145.030",
                "stock_id": "600863",
                "stock_nm": "内蒙华电",
                "orig_iss_amt": "18.752",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.339",
                "issue_dt": "2017-12-21",
                "redeem_dt": "2021-11-04",
                "delist_dt": "2021-11-04",
                "maturity_dt": "2023-12-21",
                "listed_years": "3.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "132004",
            "cell": {
                "bond_id": "132004",
                "bond_nm": "15国盛EB",
                "price": "102.980",
                "stock_id": "600170",
                "stock_nm": "上海建工",
                "orig_iss_amt": "50.000",
                "put_iss_amt": "5.222",
                "curr_iss_amt": "44.778",
                "issue_dt": "2015-11-05",
                "redeem_dt": None,
                "delist_dt": "2021-11-04",
                "maturity_dt": "2021-11-05",
                "listed_years": "6.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "110033",
            "cell": {
                "bond_id": "110033",
                "bond_nm": "国贸转债",
                "price": "101.640",
                "stock_id": "600755",
                "stock_nm": "厦门国贸",
                "orig_iss_amt": "28.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.336",
                "issue_dt": "2016-01-05",
                "redeem_dt": "2021-11-04",
                "delist_dt": "2021-11-04",
                "maturity_dt": "2022-01-05",
                "listed_years": "5.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "132007",
            "cell": {
                "bond_id": "132007",
                "bond_nm": "16凤凰EB",
                "price": "104.950",
                "stock_id": "601928",
                "stock_nm": "凤凰传媒",
                "orig_iss_amt": "50.000",
                "put_iss_amt": "0.033",
                "curr_iss_amt": "49.967",
                "issue_dt": "2016-10-31",
                "redeem_dt": None,
                "delist_dt": "2021-10-29",
                "maturity_dt": "2021-10-31",
                "listed_years": "5.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "128018",
            "cell": {
                "bond_id": "128018",
                "bond_nm": "时达转债",
                "price": "101.155",
                "stock_id": "002527",
                "stock_nm": "新时达",
                "orig_iss_amt": "8.825",
                "put_iss_amt": "4.752",
                "curr_iss_amt": "1.453",
                "issue_dt": "2017-11-06",
                "redeem_dt": "2021-10-27",
                "delist_dt": "2021-10-27",
                "maturity_dt": "2023-11-06",
                "listed_years": "4.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "120003",
            "cell": {
                "bond_id": "120003",
                "bond_nm": "19华菱EB",
                "price": "131.599",
                "stock_id": "000932",
                "stock_nm": "华菱钢铁",
                "orig_iss_amt": "20.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "1.126",
                "issue_dt": "2019-11-25",
                "redeem_dt": "2021-10-21",
                "delist_dt": "2021-10-21",
                "maturity_dt": "2024-11-22",
                "listed_years": "1.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "120004",
            "cell": {
                "bond_id": "120004",
                "bond_nm": "20华菱EB",
                "price": "119.200",
                "stock_id": "000932",
                "stock_nm": "华菱钢铁",
                "orig_iss_amt": "15.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.687",
                "issue_dt": "2020-01-09",
                "redeem_dt": "2021-10-21",
                "delist_dt": "2021-10-21",
                "maturity_dt": "2025-01-08",
                "listed_years": "1.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123047",
            "cell": {
                "bond_id": "123047",
                "bond_nm": "久吾转债",
                "price": "216.198",
                "stock_id": "300631",
                "stock_nm": "久吾高科",
                "orig_iss_amt": "2.540",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.761",
                "issue_dt": "2020-03-20",
                "redeem_dt": "2021-10-20",
                "delist_dt": "2021-10-20",
                "maturity_dt": "2026-03-19",
                "listed_years": "1.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123051",
            "cell": {
                "bond_id": "123051",
                "bond_nm": "今天转债",
                "price": "105.200",
                "stock_id": "300532",
                "stock_nm": "今天国际",
                "orig_iss_amt": "2.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.703",
                "issue_dt": "2020-06-04",
                "redeem_dt": "2021-10-14",
                "delist_dt": "2021-10-14",
                "maturity_dt": "2026-06-03",
                "listed_years": "1.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123068",
            "cell": {
                "bond_id": "123068",
                "bond_nm": "弘信转债",
                "price": "104.000",
                "stock_id": "300657",
                "stock_nm": "弘信电子",
                "orig_iss_amt": "5.700",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.815",
                "issue_dt": "2020-10-15",
                "redeem_dt": "2021-10-11",
                "delist_dt": "2021-10-11",
                "maturity_dt": "2026-10-14",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113014",
            "cell": {
                "bond_id": "113014",
                "bond_nm": "林洋转债",
                "price": "165.360",
                "stock_id": "601222",
                "stock_nm": "林洋能源",
                "orig_iss_amt": "30.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.183",
                "issue_dt": "2017-10-27",
                "redeem_dt": "2021-09-28",
                "delist_dt": "2021-09-28",
                "maturity_dt": "2023-10-27",
                "listed_years": "3.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113572",
            "cell": {
                "bond_id": "113572",
                "bond_nm": "三祥转债",
                "price": "155.390",
                "stock_id": "603663",
                "stock_nm": "三祥新材",
                "orig_iss_amt": "2.050",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.088",
                "issue_dt": "2020-03-12",
                "redeem_dt": "2021-09-23",
                "delist_dt": "2021-09-23",
                "maturity_dt": "2026-03-11",
                "listed_years": "1.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123030",
            "cell": {
                "bond_id": "123030",
                "bond_nm": "九洲转债",
                "price": "234.500",
                "stock_id": "300040",
                "stock_nm": "九洲集团",
                "orig_iss_amt": "3.080",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.545",
                "issue_dt": "2019-08-20",
                "redeem_dt": "2021-09-14",
                "delist_dt": "2021-09-14",
                "maturity_dt": "2025-08-19",
                "listed_years": "2.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113612",
            "cell": {
                "bond_id": "113612",
                "bond_nm": "永冠转债",
                "price": "184.100",
                "stock_id": "603681",
                "stock_nm": "永冠新材",
                "orig_iss_amt": "5.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.148",
                "issue_dt": "2020-12-08",
                "redeem_dt": "2021-09-09",
                "delist_dt": "2021-09-09",
                "maturity_dt": "2026-12-07",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123079",
            "cell": {
                "bond_id": "123079",
                "bond_nm": "运达转债",
                "price": "271.000",
                "stock_id": "300772",
                "stock_nm": "运达股份",
                "orig_iss_amt": "5.770",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.431",
                "issue_dt": "2020-12-01",
                "redeem_dt": "2021-09-08",
                "delist_dt": "2021-09-08",
                "maturity_dt": "2026-11-30",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128051",
            "cell": {
                "bond_id": "128051",
                "bond_nm": "光华转债",
                "price": "184.600",
                "stock_id": "002741",
                "stock_nm": "光华科技",
                "orig_iss_amt": "2.493",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.354",
                "issue_dt": "2018-12-14",
                "redeem_dt": "2021-09-07",
                "delist_dt": "2021-09-07",
                "maturity_dt": "2024-12-14",
                "listed_years": "2.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123094",
            "cell": {
                "bond_id": "123094",
                "bond_nm": "星源转2",
                "price": "261.303",
                "stock_id": "300568",
                "stock_nm": "星源材质",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.532",
                "issue_dt": "2021-01-20",
                "redeem_dt": "2021-09-06",
                "delist_dt": "2021-09-06",
                "maturity_dt": "2027-01-19",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113012",
            "cell": {
                "bond_id": "113012",
                "bond_nm": "骆驼转债",
                "price": "152.250",
                "stock_id": "601311",
                "stock_nm": "骆驼股份",
                "orig_iss_amt": "7.170",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.024",
                "issue_dt": "2017-03-23",
                "redeem_dt": "2021-09-02",
                "delist_dt": "2021-09-02",
                "maturity_dt": "2023-03-24",
                "listed_years": "4.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113508",
            "cell": {
                "bond_id": "113508",
                "bond_nm": "新凤转债",
                "price": "116.860",
                "stock_id": "603225",
                "stock_nm": "新凤鸣",
                "orig_iss_amt": "21.530",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.067",
                "issue_dt": "2018-04-26",
                "redeem_dt": "2021-08-31",
                "delist_dt": "2021-08-31",
                "maturity_dt": "2024-04-25",
                "listed_years": "3.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123033",
            "cell": {
                "bond_id": "123033",
                "bond_nm": "金力转债",
                "price": "150.700",
                "stock_id": "300748",
                "stock_nm": "金力永磁",
                "orig_iss_amt": "4.350",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.590",
                "issue_dt": "2019-11-01",
                "redeem_dt": "2021-08-30",
                "delist_dt": "2021-08-30",
                "maturity_dt": "2025-10-31",
                "listed_years": "1.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128064",
            "cell": {
                "bond_id": "128064",
                "bond_nm": "司尔转债",
                "price": "162.200",
                "stock_id": "002538",
                "stock_nm": "司尔特",
                "orig_iss_amt": "8.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.229",
                "issue_dt": "2019-04-08",
                "redeem_dt": "2021-08-24",
                "delist_dt": "2021-08-24",
                "maturity_dt": "2025-04-08",
                "listed_years": "2.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113509",
            "cell": {
                "bond_id": "113509",
                "bond_nm": "新泉转债",
                "price": "213.700",
                "stock_id": "603179",
                "stock_nm": "新泉股份",
                "orig_iss_amt": "4.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.020",
                "issue_dt": "2018-06-04",
                "redeem_dt": "2021-08-17",
                "delist_dt": "2021-08-17",
                "maturity_dt": "2024-06-03",
                "listed_years": "3.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123066",
            "cell": {
                "bond_id": "123066",
                "bond_nm": "赛意转债",
                "price": "193.080",
                "stock_id": "300687",
                "stock_nm": "赛意信息",
                "orig_iss_amt": "3.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.365",
                "issue_dt": "2020-09-16",
                "redeem_dt": "2021-08-13",
                "delist_dt": "2021-08-13",
                "maturity_dt": "2026-09-15",
                "listed_years": "0.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123007",
            "cell": {
                "bond_id": "123007",
                "bond_nm": "道氏转债",
                "price": "196.100",
                "stock_id": "300409",
                "stock_nm": "道氏技术",
                "orig_iss_amt": "4.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.529",
                "issue_dt": "2017-12-28",
                "redeem_dt": "2021-08-12",
                "delist_dt": "2021-08-12",
                "maturity_dt": "2023-12-28",
                "listed_years": "3.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113040",
            "cell": {
                "bond_id": "113040",
                "bond_nm": "星宇转债",
                "price": "141.800",
                "stock_id": "601799",
                "stock_nm": "星宇股份",
                "orig_iss_amt": "15.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.075",
                "issue_dt": "2020-10-22",
                "redeem_dt": "2021-08-02",
                "delist_dt": "2021-08-02",
                "maturity_dt": "2026-10-21",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113611",
            "cell": {
                "bond_id": "113611",
                "bond_nm": "福20转债",
                "price": "181.530",
                "stock_id": "603806",
                "stock_nm": "福斯特",
                "orig_iss_amt": "17.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.131",
                "issue_dt": "2020-12-01",
                "redeem_dt": "2021-07-28",
                "delist_dt": "2021-07-28",
                "maturity_dt": "2026-11-30",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128032",
            "cell": {
                "bond_id": "128032",
                "bond_nm": "双环转债",
                "price": "173.021",
                "stock_id": "002472",
                "stock_nm": "双环传动",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.278",
                "issue_dt": "2017-12-25",
                "redeem_dt": "2021-07-27",
                "delist_dt": "2021-07-27",
                "maturity_dt": "2023-12-25",
                "listed_years": "3.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "127023",
            "cell": {
                "bond_id": "127023",
                "bond_nm": "华菱转2",
                "price": "141.582",
                "stock_id": "000932",
                "stock_nm": "华菱钢铁",
                "orig_iss_amt": "40.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "2.438",
                "issue_dt": "2020-10-23",
                "redeem_dt": "2021-07-15",
                "delist_dt": "2021-07-15",
                "maturity_dt": "2026-10-22",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113543",
            "cell": {
                "bond_id": "113543",
                "bond_nm": "欧派转债",
                "price": "185.100",
                "stock_id": "603833",
                "stock_nm": "欧派家居",
                "orig_iss_amt": "14.950",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.015",
                "issue_dt": "2019-08-16",
                "redeem_dt": "2021-07-09",
                "delist_dt": "2021-07-09",
                "maturity_dt": "2025-08-15",
                "listed_years": "1.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123058",
            "cell": {
                "bond_id": "123058",
                "bond_nm": "欣旺转债",
                "price": "142.500",
                "stock_id": "300207",
                "stock_nm": "欣旺达",
                "orig_iss_amt": "11.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.646",
                "issue_dt": "2020-07-14",
                "redeem_dt": "2021-07-05",
                "delist_dt": "2021-07-05",
                "maturity_dt": "2026-07-13",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110065",
            "cell": {
                "bond_id": "110065",
                "bond_nm": "淮矿转债",
                "price": "136.040",
                "stock_id": "600985",
                "stock_nm": "淮北矿业",
                "orig_iss_amt": "27.580",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.044",
                "issue_dt": "2019-12-23",
                "redeem_dt": "2021-07-01",
                "delist_dt": "2021-07-01",
                "maturity_dt": "2025-12-22",
                "listed_years": "1.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123029",
            "cell": {
                "bond_id": "123029",
                "bond_nm": "英科转债",
                "price": "1380.000",
                "stock_id": "300677",
                "stock_nm": "英科医疗",
                "orig_iss_amt": "4.700",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.028",
                "issue_dt": "2019-08-16",
                "redeem_dt": None,
                "delist_dt": "2021-06-28",
                "maturity_dt": "2025-08-15",
                "listed_years": "1.9",
                "delist_notes": "低于3千万"
            }
        },
        {
            "id": "113041",
            "cell": {
                "bond_id": "113041",
                "bond_nm": "紫金转债",
                "price": "144.390",
                "stock_id": "601899",
                "stock_nm": "紫金矿业",
                "orig_iss_amt": "60.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.192",
                "issue_dt": "2020-11-03",
                "redeem_dt": "2021-06-25",
                "delist_dt": "2021-06-25",
                "maturity_dt": "2025-11-02",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113559",
            "cell": {
                "bond_id": "113559",
                "bond_nm": "永创转债",
                "price": "175.980",
                "stock_id": "603901",
                "stock_nm": "永创智能",
                "orig_iss_amt": "5.120",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.053",
                "issue_dt": "2019-12-23",
                "redeem_dt": "2021-06-25",
                "delist_dt": "2021-06-25",
                "maturity_dt": "2025-12-22",
                "listed_years": "1.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "132006",
            "cell": {
                "bond_id": "132006",
                "bond_nm": "16皖新EB",
                "price": "110.600",
                "stock_id": "601801",
                "stock_nm": "皖新传媒",
                "orig_iss_amt": "25.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "25.000",
                "issue_dt": "2016-06-23",
                "redeem_dt": None,
                "delist_dt": "2021-06-22",
                "maturity_dt": "2021-06-23",
                "listed_years": "5.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "110031",
            "cell": {
                "bond_id": "110031",
                "bond_nm": "航信转债",
                "price": "106.700",
                "stock_id": "600271",
                "stock_nm": "航天信息",
                "orig_iss_amt": "24.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "23.983",
                "issue_dt": "2015-06-12",
                "redeem_dt": None,
                "delist_dt": "2021-05-28",
                "maturity_dt": "2021-06-12",
                "listed_years": "6.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "113564",
            "cell": {
                "bond_id": "113564",
                "bond_nm": "天目转债",
                "price": "100.180",
                "stock_id": "603136",
                "stock_nm": "天目湖",
                "orig_iss_amt": "3.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.114",
                "issue_dt": "2020-02-28",
                "redeem_dt": "2021-05-18",
                "delist_dt": "2021-05-18",
                "maturity_dt": "2026-02-27",
                "listed_years": "1.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128126",
            "cell": {
                "bond_id": "128126",
                "bond_nm": "赣锋转2",
                "price": "173.800",
                "stock_id": "002460",
                "stock_nm": "赣锋锂业",
                "orig_iss_amt": "21.080",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.815",
                "issue_dt": "2020-08-06",
                "redeem_dt": "2021-05-11",
                "delist_dt": "2021-05-11",
                "maturity_dt": "2026-08-05",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113557",
            "cell": {
                "bond_id": "113557",
                "bond_nm": "森特转债",
                "price": "191.200",
                "stock_id": "603098",
                "stock_nm": "森特股份",
                "orig_iss_amt": "6.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.056",
                "issue_dt": "2019-12-19",
                "redeem_dt": "2021-04-29",
                "delist_dt": "2021-04-29",
                "maturity_dt": "2025-12-18",
                "listed_years": "1.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110069",
            "cell": {
                "bond_id": "110069",
                "bond_nm": "瀚蓝转债",
                "price": "122.300",
                "stock_id": "600323",
                "stock_nm": "瀚蓝环境",
                "orig_iss_amt": "9.920",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.008",
                "issue_dt": "2020-04-07",
                "redeem_dt": "2021-04-27",
                "delist_dt": "2021-04-27",
                "maturity_dt": "2026-04-06",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113038",
            "cell": {
                "bond_id": "113038",
                "bond_nm": "隆20转债",
                "price": "166.130",
                "stock_id": "601012",
                "stock_nm": "隆基股份",
                "orig_iss_amt": "50.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.235",
                "issue_dt": "2020-07-31",
                "redeem_dt": "2021-03-30",
                "delist_dt": "2021-03-30",
                "maturity_dt": "2026-07-30",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128052",
            "cell": {
                "bond_id": "128052",
                "bond_nm": "凯龙转债",
                "price": "148.295",
                "stock_id": "002783",
                "stock_nm": "凯龙股份",
                "orig_iss_amt": "3.289",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.311",
                "issue_dt": "2018-12-21",
                "redeem_dt": "2021-03-23",
                "delist_dt": "2021-03-23",
                "maturity_dt": "2024-12-21",
                "listed_years": "2.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113029",
            "cell": {
                "bond_id": "113029",
                "bond_nm": "明阳转债",
                "price": "141.360",
                "stock_id": "601615",
                "stock_nm": "明阳智能",
                "orig_iss_amt": "17.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.051",
                "issue_dt": "2019-12-16",
                "redeem_dt": "2021-03-18",
                "delist_dt": "2021-03-18",
                "maturity_dt": "2025-12-15",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113590",
            "cell": {
                "bond_id": "113590",
                "bond_nm": "海容转债",
                "price": "156.190",
                "stock_id": "603187",
                "stock_nm": "海容冷链",
                "orig_iss_amt": "5.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.029",
                "issue_dt": "2020-06-29",
                "redeem_dt": "2021-03-05",
                "delist_dt": "2021-03-05",
                "maturity_dt": "2026-06-29",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113592",
            "cell": {
                "bond_id": "113592",
                "bond_nm": "安20转债",
                "price": "176.530",
                "stock_id": "603345",
                "stock_nm": "安井食品",
                "orig_iss_amt": "9.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.018",
                "issue_dt": "2020-07-08",
                "redeem_dt": "2021-03-05",
                "delist_dt": "2021-03-05",
                "maturity_dt": "2026-07-07",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128028",
            "cell": {
                "bond_id": "128028",
                "bond_nm": "赣锋转债",
                "price": "235.977",
                "stock_id": "002460",
                "stock_nm": "赣锋锂业",
                "orig_iss_amt": "9.280",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.539",
                "issue_dt": "2017-12-21",
                "redeem_dt": "2021-03-05",
                "delist_dt": "2021-03-05",
                "maturity_dt": "2023-12-21",
                "listed_years": "3.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113583",
            "cell": {
                "bond_id": "113583",
                "bond_nm": "益丰转债",
                "price": "111.900",
                "stock_id": "603939",
                "stock_nm": "益丰药房",
                "orig_iss_amt": "15.810",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.079",
                "issue_dt": "2020-06-01",
                "redeem_dt": "2021-03-04",
                "delist_dt": "2021-03-04",
                "maturity_dt": "2026-05-31",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "127008",
            "cell": {
                "bond_id": "127008",
                "bond_nm": "特发转债",
                "price": "132.331",
                "stock_id": "000070",
                "stock_nm": "特发信息",
                "orig_iss_amt": "4.194",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.433",
                "issue_dt": "2018-11-16",
                "redeem_dt": "2021-03-04",
                "delist_dt": "2021-03-04",
                "maturity_dt": "2023-11-16",
                "listed_years": "2.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128112",
            "cell": {
                "bond_id": "128112",
                "bond_nm": "歌尔转2",
                "price": "144.988",
                "stock_id": "002241",
                "stock_nm": "歌尔股份",
                "orig_iss_amt": "40.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.599",
                "issue_dt": "2020-06-12",
                "redeem_dt": "2021-03-02",
                "delist_dt": "2021-03-02",
                "maturity_dt": "2026-06-11",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128065",
            "cell": {
                "bond_id": "128065",
                "bond_nm": "雅化转债",
                "price": "205.000",
                "stock_id": "002497",
                "stock_nm": "雅化集团",
                "orig_iss_amt": "8.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.280",
                "issue_dt": "2019-04-16",
                "redeem_dt": "2021-03-01",
                "delist_dt": "2021-03-01",
                "maturity_dt": "2025-04-16",
                "listed_years": "1.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128010",
            "cell": {
                "bond_id": "128010",
                "bond_nm": "蔚蓝转债",
                "price": "108.790",
                "stock_id": "002245",
                "stock_nm": "蔚蓝锂芯",
                "orig_iss_amt": "5.100",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.385",
                "issue_dt": "2016-01-22",
                "redeem_dt": "2021-02-26",
                "delist_dt": "2021-02-26",
                "maturity_dt": "2022-01-22",
                "listed_years": "5.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123055",
            "cell": {
                "bond_id": "123055",
                "bond_nm": "晨光转债",
                "price": "128.800",
                "stock_id": "300138",
                "stock_nm": "晨光生物",
                "orig_iss_amt": "6.300",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.261",
                "issue_dt": "2020-06-17",
                "redeem_dt": "2021-02-24",
                "delist_dt": "2021-02-24",
                "maturity_dt": "2026-06-16",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128115",
            "cell": {
                "bond_id": "128115",
                "bond_nm": "巨星转债",
                "price": "309.910",
                "stock_id": "002444",
                "stock_nm": "巨星科技",
                "orig_iss_amt": "9.730",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.149",
                "issue_dt": "2020-06-24",
                "redeem_dt": "2021-02-23",
                "delist_dt": "2021-02-23",
                "maturity_dt": "2026-06-23",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123017",
            "cell": {
                "bond_id": "123017",
                "bond_nm": "寒锐转债",
                "price": "167.485",
                "stock_id": "300618",
                "stock_nm": "寒锐钴业",
                "orig_iss_amt": "4.400",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.317",
                "issue_dt": "2018-11-20",
                "redeem_dt": "2021-02-23",
                "delist_dt": "2021-02-23",
                "maturity_dt": "2024-11-20",
                "listed_years": "2.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113587",
            "cell": {
                "bond_id": "113587",
                "bond_nm": "泛微转债",
                "price": "138.420",
                "stock_id": "603039",
                "stock_nm": "泛微网络",
                "orig_iss_amt": "3.160",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.015",
                "issue_dt": "2020-06-15",
                "redeem_dt": "2021-02-22",
                "delist_dt": "2021-02-22",
                "maturity_dt": "2026-06-15",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128110",
            "cell": {
                "bond_id": "128110",
                "bond_nm": "永兴转债",
                "price": "280.502",
                "stock_id": "002756",
                "stock_nm": "永兴材料",
                "orig_iss_amt": "7.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.203",
                "issue_dt": "2020-06-09",
                "redeem_dt": "2021-02-22",
                "delist_dt": "2021-02-22",
                "maturity_dt": "2026-06-08",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113035",
            "cell": {
                "bond_id": "113035",
                "bond_nm": "福莱转债",
                "price": "244.780",
                "stock_id": "601865",
                "stock_nm": "福莱特",
                "orig_iss_amt": "14.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.028",
                "issue_dt": "2020-05-27",
                "redeem_dt": "2021-01-29",
                "delist_dt": "2021-01-29",
                "maturity_dt": "2026-05-26",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113556",
            "cell": {
                "bond_id": "113556",
                "bond_nm": "至纯转债",
                "price": "152.400",
                "stock_id": "603690",
                "stock_nm": "至纯科技",
                "orig_iss_amt": "3.560",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.064",
                "issue_dt": "2019-12-20",
                "redeem_dt": "2021-01-25",
                "delist_dt": "2021-01-25",
                "maturity_dt": "2025-12-19",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113586",
            "cell": {
                "bond_id": "113586",
                "bond_nm": "上机转债",
                "price": "417.350",
                "stock_id": "603185",
                "stock_nm": "上机数控",
                "orig_iss_amt": "6.650",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.027",
                "issue_dt": "2020-06-09",
                "redeem_dt": "2021-01-19",
                "delist_dt": "2021-01-19",
                "maturity_dt": "2026-06-08",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113008",
            "cell": {
                "bond_id": "113008",
                "bond_nm": "电气转债",
                "price": "106.480",
                "stock_id": "601727",
                "stock_nm": "上海电气",
                "orig_iss_amt": "60.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "13.422",
                "issue_dt": "2015-02-02",
                "redeem_dt": None,
                "delist_dt": "2021-01-18",
                "maturity_dt": "2021-02-02",
                "listed_years": "6.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "113032",
            "cell": {
                "bond_id": "113032",
                "bond_nm": "桐20转债",
                "price": "167.330",
                "stock_id": "601233",
                "stock_nm": "桐昆股份",
                "orig_iss_amt": "23.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.076",
                "issue_dt": "2020-03-02",
                "redeem_dt": "2021-01-13",
                "delist_dt": "2021-01-13",
                "maturity_dt": "2026-02-27",
                "listed_years": "0.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128019",
            "cell": {
                "bond_id": "128019",
                "bond_nm": "久立转2",
                "price": "150.730",
                "stock_id": "002318",
                "stock_nm": "久立特材",
                "orig_iss_amt": "10.400",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.297",
                "issue_dt": "2017-11-08",
                "redeem_dt": "2021-01-06",
                "delist_dt": "2021-01-06",
                "maturity_dt": "2023-11-08",
                "listed_years": "3.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113520",
            "cell": {
                "bond_id": "113520",
                "bond_nm": "百合转债",
                "price": "234.260",
                "stock_id": "603313",
                "stock_nm": "梦百合",
                "orig_iss_amt": "5.100",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.065",
                "issue_dt": "2018-11-08",
                "redeem_dt": "2021-01-06",
                "delist_dt": "2021-01-06",
                "maturity_dt": "2024-11-08",
                "listed_years": "2.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128104",
            "cell": {
                "bond_id": "128104",
                "bond_nm": "裕同转债",
                "price": "129.777",
                "stock_id": "002831",
                "stock_nm": "裕同科技",
                "orig_iss_amt": "14.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.733",
                "issue_dt": "2020-04-07",
                "redeem_dt": "2021-01-04",
                "delist_dt": "2021-01-04",
                "maturity_dt": "2026-04-06",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128102",
            "cell": {
                "bond_id": "128102",
                "bond_nm": "海大转债",
                "price": "172.800",
                "stock_id": "002311",
                "stock_nm": "海大集团",
                "orig_iss_amt": "28.300",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.194",
                "issue_dt": "2020-03-19",
                "redeem_dt": "2020-12-22",
                "delist_dt": "2020-12-22",
                "maturity_dt": "2026-03-18",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113562",
            "cell": {
                "bond_id": "113562",
                "bond_nm": "璞泰转债",
                "price": "132.140",
                "stock_id": "603659",
                "stock_nm": "璞泰来",
                "orig_iss_amt": "8.700",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.188",
                "issue_dt": "2020-01-02",
                "redeem_dt": "2020-12-18",
                "delist_dt": "2020-12-18",
                "maturity_dt": "2025-01-02",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123026",
            "cell": {
                "bond_id": "123026",
                "bond_nm": "中环转债",
                "price": "117.790",
                "stock_id": "300692",
                "stock_nm": "中环环保",
                "orig_iss_amt": "2.900",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.588",
                "issue_dt": "2019-06-10",
                "redeem_dt": "2020-12-14",
                "delist_dt": "2020-12-14",
                "maturity_dt": "2024-06-10",
                "listed_years": "1.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113581",
            "cell": {
                "bond_id": "113581",
                "bond_nm": "龙蟠转债",
                "price": "295.160",
                "stock_id": "603906",
                "stock_nm": "龙蟠科技",
                "orig_iss_amt": "4.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.024",
                "issue_dt": "2020-04-23",
                "redeem_dt": "2020-12-10",
                "delist_dt": "2020-12-10",
                "maturity_dt": "2026-04-22",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123036",
            "cell": {
                "bond_id": "123036",
                "bond_nm": "先导转债",
                "price": "165.870",
                "stock_id": "300450",
                "stock_nm": "先导智能",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.281",
                "issue_dt": "2019-12-11",
                "redeem_dt": "2020-12-09",
                "delist_dt": "2020-12-09",
                "maturity_dt": "2025-12-10",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "132005",
            "cell": {
                "bond_id": "132005",
                "bond_nm": "15国资EB",
                "price": "109.930",
                "stock_id": "601601",
                "stock_nm": "中国太保",
                "orig_iss_amt": "20.000",
                "put_iss_amt": "0.240",
                "curr_iss_amt": "0.162",
                "issue_dt": "2015-12-08",
                "redeem_dt": "2020-12-07",
                "delist_dt": "2020-12-07",
                "maturity_dt": "2020-12-08",
                "listed_years": "5.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "113555",
            "cell": {
                "bond_id": "113555",
                "bond_nm": "振德转债",
                "price": "417.870",
                "stock_id": "603301",
                "stock_nm": "振德医疗",
                "orig_iss_amt": "4.400",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.028",
                "issue_dt": "2019-12-19",
                "redeem_dt": "2020-12-03",
                "delist_dt": "2020-12-03",
                "maturity_dt": "2025-12-18",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113553",
            "cell": {
                "bond_id": "113553",
                "bond_nm": "金牌转债",
                "price": "128.460",
                "stock_id": "603180",
                "stock_nm": "金牌厨柜",
                "orig_iss_amt": "3.920",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.061",
                "issue_dt": "2019-12-13",
                "redeem_dt": "2020-12-03",
                "delist_dt": "2020-12-03",
                "maturity_dt": "2025-12-12",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123032",
            "cell": {
                "bond_id": "123032",
                "bond_nm": "万里转债",
                "price": "120.360",
                "stock_id": "300591",
                "stock_nm": "万里马",
                "orig_iss_amt": "1.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.582",
                "issue_dt": "2019-10-11",
                "redeem_dt": "2020-11-30",
                "delist_dt": "2020-11-30",
                "maturity_dt": "2025-10-10",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113020",
            "cell": {
                "bond_id": "113020",
                "bond_nm": "桐昆转债",
                "price": "163.640",
                "stock_id": "601233",
                "stock_nm": "桐昆股份",
                "orig_iss_amt": "38.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.380",
                "issue_dt": "2018-11-19",
                "redeem_dt": "2020-11-26",
                "delist_dt": "2020-11-26",
                "maturity_dt": "2024-11-19",
                "listed_years": "2.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113521",
            "cell": {
                "bond_id": "113521",
                "bond_nm": "科森转债",
                "price": "168.630",
                "stock_id": "603626",
                "stock_nm": "科森科技",
                "orig_iss_amt": "6.100",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.081",
                "issue_dt": "2018-11-16",
                "redeem_dt": "2020-11-26",
                "delist_dt": "2020-11-26",
                "maturity_dt": "2024-11-16",
                "listed_years": "2.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128058",
            "cell": {
                "bond_id": "128058",
                "bond_nm": "拓邦转债",
                "price": "151.980",
                "stock_id": "002139",
                "stock_nm": "拓邦股份",
                "orig_iss_amt": "5.730",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.114",
                "issue_dt": "2019-03-07",
                "redeem_dt": "2020-11-25",
                "delist_dt": "2020-11-25",
                "maturity_dt": "2025-03-07",
                "listed_years": "1.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "132013",
            "cell": {
                "bond_id": "132013",
                "bond_nm": "17宝武EB",
                "price": "102.980",
                "stock_id": "600019",
                "stock_nm": "宝钢股份",
                "orig_iss_amt": "150.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "150.000",
                "issue_dt": "2017-11-24",
                "redeem_dt": "2020-11-23",
                "delist_dt": "2020-11-23",
                "maturity_dt": "2020-11-24",
                "listed_years": "3.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "128099",
            "cell": {
                "bond_id": "128099",
                "bond_nm": "永高转债",
                "price": "117.880",
                "stock_id": "002641",
                "stock_nm": "永高股份",
                "orig_iss_amt": "7.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.225",
                "issue_dt": "2020-03-11",
                "redeem_dt": "2020-11-18",
                "delist_dt": "2020-11-18",
                "maturity_dt": "2026-03-10",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113571",
            "cell": {
                "bond_id": "113571",
                "bond_nm": "博特转债",
                "price": "139.420",
                "stock_id": "603916",
                "stock_nm": "苏博特",
                "orig_iss_amt": "6.970",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.026",
                "issue_dt": "2020-03-12",
                "redeem_dt": "2020-11-17",
                "delist_dt": "2020-11-17",
                "maturity_dt": "2026-03-11",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128098",
            "cell": {
                "bond_id": "128098",
                "bond_nm": "康弘转债",
                "price": "124.908",
                "stock_id": "002773",
                "stock_nm": "康弘药业",
                "orig_iss_amt": "16.300",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.076",
                "issue_dt": "2020-03-05",
                "redeem_dt": "2020-11-20",
                "delist_dt": "2020-11-09",
                "maturity_dt": "2026-03-05",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128067",
            "cell": {
                "bond_id": "128067",
                "bond_nm": "一心转债",
                "price": "141.000",
                "stock_id": "002727",
                "stock_nm": "一心堂",
                "orig_iss_amt": "6.030",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.101",
                "issue_dt": "2019-04-19",
                "redeem_dt": "2020-11-02",
                "delist_dt": "2020-10-19",
                "maturity_dt": "2025-04-19",
                "listed_years": "1.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128043",
            "cell": {
                "bond_id": "128043",
                "bond_nm": "东音转债",
                "price": "212.560",
                "stock_id": "002793",
                "stock_nm": "罗欣药业",
                "orig_iss_amt": "2.813",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.009",
                "issue_dt": "2018-08-02",
                "redeem_dt": "2020-11-02",
                "delist_dt": "2020-10-16",
                "maturity_dt": "2024-08-02",
                "listed_years": "2.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128092",
            "cell": {
                "bond_id": "128092",
                "bond_nm": "唐人转债",
                "price": "104.201",
                "stock_id": "002567",
                "stock_nm": "唐人神",
                "orig_iss_amt": "12.400",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.511",
                "issue_dt": "2019-12-30",
                "redeem_dt": "2020-10-09",
                "delist_dt": "2020-09-17",
                "maturity_dt": "2025-12-30",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113028",
            "cell": {
                "bond_id": "113028",
                "bond_nm": "环境转债",
                "price": "114.220",
                "stock_id": "601200",
                "stock_nm": "上海环境",
                "orig_iss_amt": "21.700",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.089",
                "issue_dt": "2019-06-18",
                "redeem_dt": "2020-09-17",
                "delist_dt": "2020-09-17",
                "maturity_dt": "2025-06-17",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113544",
            "cell": {
                "bond_id": "113544",
                "bond_nm": "桃李转债",
                "price": "119.480",
                "stock_id": "603866",
                "stock_nm": "桃李面包",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.098",
                "issue_dt": "2019-09-20",
                "redeem_dt": "2020-09-17",
                "delist_dt": "2020-09-17",
                "maturity_dt": "2025-09-19",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113547",
            "cell": {
                "bond_id": "113547",
                "bond_nm": "索发转债",
                "price": "140.660",
                "stock_id": "603612",
                "stock_nm": "索通发展",
                "orig_iss_amt": "9.450",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.081",
                "issue_dt": "2019-10-24",
                "redeem_dt": "2020-09-15",
                "delist_dt": "2020-09-15",
                "maturity_dt": "2025-10-23",
                "listed_years": "0.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113554",
            "cell": {
                "bond_id": "113554",
                "bond_nm": "仙鹤转债",
                "price": "145.270",
                "stock_id": "603733",
                "stock_nm": "仙鹤股份",
                "orig_iss_amt": "12.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.030",
                "issue_dt": "2019-12-16",
                "redeem_dt": "2020-09-10",
                "delist_dt": "2020-09-10",
                "maturity_dt": "2025-12-15",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128084",
            "cell": {
                "bond_id": "128084",
                "bond_nm": "木森转债",
                "price": "114.528",
                "stock_id": "002745",
                "stock_nm": "木林森",
                "orig_iss_amt": "26.600",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.285",
                "issue_dt": "2019-12-16",
                "redeem_dt": "2020-09-10",
                "delist_dt": "2020-09-10",
                "maturity_dt": "2025-12-16",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123037",
            "cell": {
                "bond_id": "123037",
                "bond_nm": "新莱转债",
                "price": "172.000",
                "stock_id": "300260",
                "stock_nm": "新莱应材",
                "orig_iss_amt": "2.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.202",
                "issue_dt": "2019-12-19",
                "redeem_dt": "2020-09-10",
                "delist_dt": "2020-09-10",
                "maturity_dt": "2025-12-18",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110042",
            "cell": {
                "bond_id": "110042",
                "bond_nm": "航电转债",
                "price": "116.320",
                "stock_id": "600372",
                "stock_nm": "中航电子",
                "orig_iss_amt": "24.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.120",
                "issue_dt": "2017-12-25",
                "redeem_dt": "2020-09-07",
                "delist_dt": "2020-09-07",
                "maturity_dt": "2023-12-24",
                "listed_years": "2.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "132012",
            "cell": {
                "bond_id": "132012",
                "bond_nm": "17巨化EB",
                "price": "101.970",
                "stock_id": "600160",
                "stock_nm": "巨化股份",
                "orig_iss_amt": "20.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "20.000",
                "issue_dt": "2017-09-04",
                "redeem_dt": None,
                "delist_dt": "2020-09-03",
                "maturity_dt": "2020-09-04",
                "listed_years": "3.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "113019",
            "cell": {
                "bond_id": "113019",
                "bond_nm": "玲珑转债",
                "price": "135.880",
                "stock_id": "601966",
                "stock_nm": "玲珑轮胎",
                "orig_iss_amt": "20.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.074",
                "issue_dt": "2018-03-01",
                "redeem_dt": "2020-09-03",
                "delist_dt": "2020-09-03",
                "maturity_dt": "2023-03-01",
                "listed_years": "2.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123020",
            "cell": {
                "bond_id": "123020",
                "bond_nm": "富祥转债",
                "price": "217.520",
                "stock_id": "300497",
                "stock_nm": "富祥药业",
                "orig_iss_amt": "4.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.120",
                "issue_dt": "2019-03-01",
                "redeem_dt": "2020-09-03",
                "delist_dt": "2020-09-03",
                "maturity_dt": "2025-03-01",
                "listed_years": "1.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113514",
            "cell": {
                "bond_id": "113514",
                "bond_nm": "威帝转债",
                "price": "123.340",
                "stock_id": "603023",
                "stock_nm": "威帝股份",
                "orig_iss_amt": "2.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.063",
                "issue_dt": "2018-07-20",
                "redeem_dt": "2020-08-28",
                "delist_dt": "2020-08-28",
                "maturity_dt": "2023-07-20",
                "listed_years": "2.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113031",
            "cell": {
                "bond_id": "113031",
                "bond_nm": "博威转债",
                "price": "120.910",
                "stock_id": "601137",
                "stock_nm": "博威合金",
                "orig_iss_amt": "12.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.086",
                "issue_dt": "2020-01-10",
                "redeem_dt": "2020-08-28",
                "delist_dt": "2020-08-28",
                "maturity_dt": "2025-01-09",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128086",
            "cell": {
                "bond_id": "128086",
                "bond_nm": "国轩转债",
                "price": "201.870",
                "stock_id": "002074",
                "stock_nm": "国轩高科",
                "orig_iss_amt": "18.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.331",
                "issue_dt": "2019-12-17",
                "redeem_dt": "2020-08-27",
                "delist_dt": "2020-08-27",
                "maturity_dt": "2025-12-17",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123041",
            "cell": {
                "bond_id": "123041",
                "bond_nm": "东财转2",
                "price": "194.000",
                "stock_id": "300059",
                "stock_nm": "东方财富",
                "orig_iss_amt": "73.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.499",
                "issue_dt": "2020-01-13",
                "redeem_dt": "2020-08-27",
                "delist_dt": "2020-08-27",
                "maturity_dt": "2026-01-12",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128045",
            "cell": {
                "bond_id": "128045",
                "bond_nm": "机电转债",
                "price": "131.210",
                "stock_id": "002013",
                "stock_nm": "中航机电",
                "orig_iss_amt": "21.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.029",
                "issue_dt": "2018-08-27",
                "redeem_dt": "2020-09-10",
                "delist_dt": "2020-08-27",
                "maturity_dt": "2024-08-27",
                "listed_years": "2.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113518",
            "cell": {
                "bond_id": "113518",
                "bond_nm": "顾家转债",
                "price": "177.680",
                "stock_id": "603816",
                "stock_nm": "顾家家居",
                "orig_iss_amt": "10.973",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.042",
                "issue_dt": "2018-09-11",
                "redeem_dt": "2020-08-27",
                "delist_dt": "2020-08-27",
                "maturity_dt": "2024-09-11",
                "listed_years": "2.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113022",
            "cell": {
                "bond_id": "113022",
                "bond_nm": "浙商转债",
                "price": "118.460",
                "stock_id": "601878",
                "stock_nm": "浙商证券",
                "orig_iss_amt": "35.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.277",
                "issue_dt": "2019-03-12",
                "redeem_dt": "2020-08-25",
                "delist_dt": "2020-08-25",
                "maturity_dt": "2025-03-12",
                "listed_years": "1.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123040",
            "cell": {
                "bond_id": "123040",
                "bond_nm": "乐普转债",
                "price": "118.000",
                "stock_id": "300003",
                "stock_nm": "乐普医疗",
                "orig_iss_amt": "7.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.680",
                "issue_dt": "2020-01-03",
                "redeem_dt": "2020-08-19",
                "delist_dt": "2020-08-19",
                "maturity_dt": "2025-01-02",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128088",
            "cell": {
                "bond_id": "128088",
                "bond_nm": "深南转债",
                "price": "133.400",
                "stock_id": "002916",
                "stock_nm": "深南电路",
                "orig_iss_amt": "15.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.131",
                "issue_dt": "2019-12-24",
                "redeem_dt": "2020-09-02",
                "delist_dt": "2020-08-19",
                "maturity_dt": "2025-12-24",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128089",
            "cell": {
                "bond_id": "128089",
                "bond_nm": "麦米转债",
                "price": "139.489",
                "stock_id": "002851",
                "stock_nm": "麦格米特",
                "orig_iss_amt": "6.550",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.014",
                "issue_dt": "2019-12-26",
                "redeem_dt": "2020-09-01",
                "delist_dt": "2020-08-18",
                "maturity_dt": "2025-12-25",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113558",
            "cell": {
                "bond_id": "113558",
                "bond_nm": "日月转债",
                "price": "150.440",
                "stock_id": "603218",
                "stock_nm": "日月股份",
                "orig_iss_amt": "12.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.042",
                "issue_dt": "2019-12-23",
                "redeem_dt": "2020-08-18",
                "delist_dt": "2020-08-18",
                "maturity_dt": "2025-12-22",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128059",
            "cell": {
                "bond_id": "128059",
                "bond_nm": "视源转债",
                "price": "133.000",
                "stock_id": "002841",
                "stock_nm": "视源股份",
                "orig_iss_amt": "9.420",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.012",
                "issue_dt": "2019-03-11",
                "redeem_dt": "2020-08-28",
                "delist_dt": "2020-08-14",
                "maturity_dt": "2025-03-11",
                "listed_years": "1.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113552",
            "cell": {
                "bond_id": "113552",
                "bond_nm": "克来转债",
                "price": "253.950",
                "stock_id": "603960",
                "stock_nm": "克来机电",
                "orig_iss_amt": "1.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.037",
                "issue_dt": "2019-12-02",
                "redeem_dt": "2020-08-06",
                "delist_dt": "2020-08-06",
                "maturity_dt": "2025-12-01",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128080",
            "cell": {
                "bond_id": "128080",
                "bond_nm": "顺丰转债",
                "price": "176.500",
                "stock_id": "002352",
                "stock_nm": "顺丰控股",
                "orig_iss_amt": "58.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "1.064",
                "issue_dt": "2019-11-18",
                "redeem_dt": "2020-08-03",
                "delist_dt": "2020-08-03",
                "maturity_dt": "2025-11-18",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113551",
            "cell": {
                "bond_id": "113551",
                "bond_nm": "福特转债",
                "price": "207.280",
                "stock_id": "603806",
                "stock_nm": "福斯特",
                "orig_iss_amt": "11.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.035",
                "issue_dt": "2019-11-18",
                "redeem_dt": "2020-07-15",
                "delist_dt": "2020-07-15",
                "maturity_dt": "2025-11-17",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128077",
            "cell": {
                "bond_id": "128077",
                "bond_nm": "华夏转债",
                "price": "169.380",
                "stock_id": "002928",
                "stock_nm": "华夏航空",
                "orig_iss_amt": "7.900",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.016",
                "issue_dt": "2019-10-16",
                "redeem_dt": "2020-07-28",
                "delist_dt": "2020-07-14",
                "maturity_dt": "2025-10-16",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128054",
            "cell": {
                "bond_id": "128054",
                "bond_nm": "中宠转债",
                "price": "182.499",
                "stock_id": "002891",
                "stock_nm": "中宠股份",
                "orig_iss_amt": "1.942",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.010",
                "issue_dt": "2019-02-15",
                "redeem_dt": "2020-07-14",
                "delist_dt": "2020-06-30",
                "maturity_dt": "2025-02-15",
                "listed_years": "1.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113515",
            "cell": {
                "bond_id": "113515",
                "bond_nm": "高能转债",
                "price": "130.360",
                "stock_id": "603588",
                "stock_nm": "高能环境",
                "orig_iss_amt": "8.400",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.080",
                "issue_dt": "2018-07-26",
                "redeem_dt": "2020-06-17",
                "delist_dt": "2020-06-17",
                "maturity_dt": "2024-07-26",
                "listed_years": "1.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113511",
            "cell": {
                "bond_id": "113511",
                "bond_nm": "千禾转债",
                "price": "202.820",
                "stock_id": "603027",
                "stock_nm": "千禾味业",
                "orig_iss_amt": "3.560",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.070",
                "issue_dt": "2018-06-20",
                "redeem_dt": "2020-05-28",
                "delist_dt": "2020-05-28",
                "maturity_dt": "2024-06-19",
                "listed_years": "1.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113503",
            "cell": {
                "bond_id": "113503",
                "bond_nm": "泰晶转债",
                "price": "125.470",
                "stock_id": "603738",
                "stock_nm": "泰晶科技",
                "orig_iss_amt": "2.150",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.092",
                "issue_dt": "2017-12-15",
                "redeem_dt": "2020-05-26",
                "delist_dt": "2020-05-26",
                "maturity_dt": "2023-12-15",
                "listed_years": "2.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128012",
            "cell": {
                "bond_id": "128012",
                "bond_nm": "辉丰转债",
                "price": "99.999",
                "stock_id": "002496",
                "stock_nm": "ST辉丰",
                "orig_iss_amt": "8.450",
                "put_iss_amt": "8.247",
                "curr_iss_amt": "0.203",
                "issue_dt": "2016-04-21",
                "redeem_dt": None,
                "delist_dt": "2020-05-25",
                "maturity_dt": "2022-04-21",
                "listed_years": "4.1",
                "delist_notes": "低于3千万"
            }
        },
        {
            "id": "113531",
            "cell": {
                "bond_id": "113531",
                "bond_nm": "百姓转债",
                "price": "130.030",
                "stock_id": "603883",
                "stock_nm": "老百姓",
                "orig_iss_amt": "3.270",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.021",
                "issue_dt": "2019-03-29",
                "redeem_dt": "2020-05-20",
                "delist_dt": "2020-05-20",
                "maturity_dt": "2024-03-28",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123021",
            "cell": {
                "bond_id": "123021",
                "bond_nm": "万信转2",
                "price": "154.020",
                "stock_id": "300168",
                "stock_nm": "万达信息",
                "orig_iss_amt": "12.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.013",
                "issue_dt": "2019-03-04",
                "redeem_dt": "2020-04-13",
                "delist_dt": "2020-04-13",
                "maturity_dt": "2025-03-03",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110050",
            "cell": {
                "bond_id": "110050",
                "bond_nm": "佳都转债",
                "price": "132.280",
                "stock_id": "600728",
                "stock_nm": "佳都科技",
                "orig_iss_amt": "8.747",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.184",
                "issue_dt": "2018-12-19",
                "redeem_dt": "2020-04-08",
                "delist_dt": "2020-04-08",
                "maturity_dt": "2024-12-18",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128055",
            "cell": {
                "bond_id": "128055",
                "bond_nm": "长青转2",
                "price": "116.100",
                "stock_id": "002391",
                "stock_nm": "长青股份",
                "orig_iss_amt": "9.138",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.154",
                "issue_dt": "2019-02-27",
                "redeem_dt": "2020-04-16",
                "delist_dt": "2020-04-02",
                "maturity_dt": "2025-02-27",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113517",
            "cell": {
                "bond_id": "113517",
                "bond_nm": "曙光转债",
                "price": "117.520",
                "stock_id": "603019",
                "stock_nm": "中科曙光",
                "orig_iss_amt": "11.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.312",
                "issue_dt": "2018-08-06",
                "redeem_dt": "2020-03-30",
                "delist_dt": "2020-03-30",
                "maturity_dt": "2024-08-06",
                "listed_years": "1.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128016",
            "cell": {
                "bond_id": "128016",
                "bond_nm": "雨虹转债",
                "price": "147.900",
                "stock_id": "002271",
                "stock_nm": "东方雨虹",
                "orig_iss_amt": "18.400",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.016",
                "issue_dt": "2017-09-25",
                "redeem_dt": "2020-04-13",
                "delist_dt": "2020-03-27",
                "maturity_dt": "2023-09-25",
                "listed_years": "2.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123019",
            "cell": {
                "bond_id": "123019",
                "bond_nm": "中来转债",
                "price": "106.302",
                "stock_id": "300393",
                "stock_nm": "中来股份",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "1.016",
                "issue_dt": "2019-02-25",
                "redeem_dt": "2020-03-25",
                "delist_dt": "2020-03-25",
                "maturity_dt": "2025-02-25",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113540",
            "cell": {
                "bond_id": "113540",
                "bond_nm": "南威转债",
                "price": "122.530",
                "stock_id": "603636",
                "stock_nm": "南威软件",
                "orig_iss_amt": "6.600",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.084",
                "issue_dt": "2019-07-15",
                "redeem_dt": "2020-03-24",
                "delist_dt": "2020-03-24",
                "maturity_dt": "2025-07-14",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113510",
            "cell": {
                "bond_id": "113510",
                "bond_nm": "再升转债",
                "price": "120.190",
                "stock_id": "603601",
                "stock_nm": "再升科技",
                "orig_iss_amt": "1.140",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.200",
                "issue_dt": "2018-06-19",
                "redeem_dt": "2020-03-24",
                "delist_dt": "2020-03-24",
                "maturity_dt": "2024-06-18",
                "listed_years": "1.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110046",
            "cell": {
                "bond_id": "110046",
                "bond_nm": "圆通转债",
                "price": "100.230",
                "stock_id": "600233",
                "stock_nm": "圆通速递",
                "orig_iss_amt": "36.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.861",
                "issue_dt": "2018-11-20",
                "redeem_dt": "2020-03-20",
                "delist_dt": "2020-03-20",
                "maturity_dt": "2024-11-19",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123009",
            "cell": {
                "bond_id": "123009",
                "bond_nm": "星源转债",
                "price": "108.369",
                "stock_id": "300568",
                "stock_nm": "星源材质",
                "orig_iss_amt": "4.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.529",
                "issue_dt": "2018-03-07",
                "redeem_dt": "2020-03-19",
                "delist_dt": "2020-03-19",
                "maturity_dt": "2024-03-07",
                "listed_years": "2.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128038",
            "cell": {
                "bond_id": "128038",
                "bond_nm": "利欧转债",
                "price": "249.005",
                "stock_id": "002131",
                "stock_nm": "利欧股份",
                "orig_iss_amt": "21.975",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.031",
                "issue_dt": "2018-03-22",
                "redeem_dt": "2020-03-30",
                "delist_dt": "2020-03-16",
                "maturity_dt": "2024-03-22",
                "listed_years": "2.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110054",
            "cell": {
                "bond_id": "110054",
                "bond_nm": "通威转债",
                "price": "107.500",
                "stock_id": "600438",
                "stock_nm": "通威股份",
                "orig_iss_amt": "50.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.205",
                "issue_dt": "2019-03-18",
                "redeem_dt": "2020-03-16",
                "delist_dt": "2020-03-16",
                "maturity_dt": "2025-03-18",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123016",
            "cell": {
                "bond_id": "123016",
                "bond_nm": "洲明转债",
                "price": "130.000",
                "stock_id": "300232",
                "stock_nm": "洲明科技",
                "orig_iss_amt": "5.480",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.086",
                "issue_dt": "2018-11-07",
                "redeem_dt": "2020-03-11",
                "delist_dt": "2020-03-11",
                "maturity_dt": "2024-11-07",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113539",
            "cell": {
                "bond_id": "113539",
                "bond_nm": "圣达转债",
                "price": "161.510",
                "stock_id": "603079",
                "stock_nm": "圣达生物",
                "orig_iss_amt": "2.990",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.033",
                "issue_dt": "2019-07-03",
                "redeem_dt": "2020-03-10",
                "delist_dt": "2020-03-10",
                "maturity_dt": "2025-07-02",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128061",
            "cell": {
                "bond_id": "128061",
                "bond_nm": "启明转债",
                "price": "149.640",
                "stock_id": "002439",
                "stock_nm": "启明星辰",
                "orig_iss_amt": "10.450",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.016",
                "issue_dt": "2019-03-27",
                "redeem_dt": "2020-03-17",
                "delist_dt": "2020-03-03",
                "maturity_dt": "2025-03-27",
                "listed_years": "0.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113522",
            "cell": {
                "bond_id": "113522",
                "bond_nm": "旭升转债",
                "price": "158.580",
                "stock_id": "603305",
                "stock_nm": "旭升股份",
                "orig_iss_amt": "4.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.026",
                "issue_dt": "2018-11-22",
                "redeem_dt": "2020-02-27",
                "delist_dt": "2020-02-27",
                "maturity_dt": "2024-11-22",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113538",
            "cell": {
                "bond_id": "113538",
                "bond_nm": "安图转债",
                "price": "187.090",
                "stock_id": "603658",
                "stock_nm": "安图生物",
                "orig_iss_amt": "6.830",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.032",
                "issue_dt": "2019-06-28",
                "redeem_dt": "2020-02-18",
                "delist_dt": "2020-02-18",
                "maturity_dt": "2025-06-27",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128060",
            "cell": {
                "bond_id": "128060",
                "bond_nm": "中装转债",
                "price": "166.600",
                "stock_id": "002822",
                "stock_nm": "中装建设",
                "orig_iss_amt": "5.250",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.037",
                "issue_dt": "2019-03-26",
                "redeem_dt": "2020-02-12",
                "delist_dt": "2020-02-12",
                "maturity_dt": "2025-03-26",
                "listed_years": "0.9",
                "delist_notes": "不足3000万"
            }
        },
        {
            "id": "123003",
            "cell": {
                "bond_id": "123003",
                "bond_nm": "蓝思转债",
                "price": "182.402",
                "stock_id": "300433",
                "stock_nm": "蓝思科技",
                "orig_iss_amt": "48.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.574",
                "issue_dt": "2017-12-08",
                "redeem_dt": "2020-02-07",
                "delist_dt": "2020-02-07",
                "maturity_dt": "2023-12-08",
                "listed_years": "2.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128068",
            "cell": {
                "bond_id": "128068",
                "bond_nm": "和而转债",
                "price": "129.030",
                "stock_id": "002402",
                "stock_nm": "和而泰",
                "orig_iss_amt": "5.470",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.032",
                "issue_dt": "2019-06-04",
                "redeem_dt": "2020-02-19",
                "delist_dt": "2020-02-05",
                "maturity_dt": "2025-06-04",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113523",
            "cell": {
                "bond_id": "113523",
                "bond_nm": "伟明转债",
                "price": "155.780",
                "stock_id": "603568",
                "stock_nm": "伟明环保",
                "orig_iss_amt": "6.700",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.027",
                "issue_dt": "2018-12-10",
                "redeem_dt": "2020-02-05",
                "delist_dt": "2020-02-05",
                "maturity_dt": "2024-12-10",
                "listed_years": "1.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128020",
            "cell": {
                "bond_id": "128020",
                "bond_nm": "水晶转债",
                "price": "134.000",
                "stock_id": "002273",
                "stock_nm": "水晶光电",
                "orig_iss_amt": "11.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "1.147",
                "issue_dt": "2017-11-17",
                "redeem_dt": "2020-02-13",
                "delist_dt": "2020-01-23",
                "maturity_dt": "2023-11-16",
                "listed_years": "2.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113533",
            "cell": {
                "bond_id": "113533",
                "bond_nm": "参林转债",
                "price": "142.290",
                "stock_id": "603233",
                "stock_nm": "大参林",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.168",
                "issue_dt": "2019-04-03",
                "redeem_dt": "2020-01-16",
                "delist_dt": "2020-01-16",
                "maturity_dt": "2025-04-02",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110049",
            "cell": {
                "bond_id": "110049",
                "bond_nm": "海尔转债",
                "price": "132.020",
                "stock_id": "600690",
                "stock_nm": "海尔智家",
                "orig_iss_amt": "30.075",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.090",
                "issue_dt": "2018-12-18",
                "redeem_dt": "2019-12-16",
                "delist_dt": "2019-12-16",
                "maturity_dt": "2024-12-17",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110030",
            "cell": {
                "bond_id": "110030",
                "bond_nm": "格力转债",
                "price": "105.690",
                "stock_id": "600185",
                "stock_nm": "格力地产",
                "orig_iss_amt": "9.800",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "4.251",
                "issue_dt": "2014-12-25",
                "redeem_dt": "2019-12-10",
                "delist_dt": "2019-12-10",
                "maturity_dt": "2019-12-25",
                "listed_years": "5.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "113529",
            "cell": {
                "bond_id": "113529",
                "bond_nm": "绝味转债",
                "price": "158.520",
                "stock_id": "603517",
                "stock_nm": "绝味食品",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.127",
                "issue_dt": "2019-03-11",
                "redeem_dt": "2019-11-21",
                "delist_dt": "2019-11-21",
                "maturity_dt": "2025-03-11",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113507",
            "cell": {
                "bond_id": "113507",
                "bond_nm": "天马转债",
                "price": "123.290",
                "stock_id": "603668",
                "stock_nm": "天马科技",
                "orig_iss_amt": "3.050",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.030",
                "issue_dt": "2018-04-17",
                "redeem_dt": "2019-11-18",
                "delist_dt": "2019-11-04",
                "maturity_dt": "2024-04-17",
                "listed_years": "1.6",
                "delist_notes": "不足3000万"
            }
        },
        {
            "id": "128047",
            "cell": {
                "bond_id": "128047",
                "bond_nm": "光电转债",
                "price": "129.027",
                "stock_id": "002179",
                "stock_nm": "中航光电",
                "orig_iss_amt": "13.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.023",
                "issue_dt": "2018-11-05",
                "redeem_dt": "2019-10-29",
                "delist_dt": "2019-10-15",
                "maturity_dt": "2024-11-05",
                "listed_years": "0.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "127009",
            "cell": {
                "bond_id": "127009",
                "bond_nm": "冰轮转债",
                "price": "130.799",
                "stock_id": "000811",
                "stock_nm": "冰轮环境",
                "orig_iss_amt": "5.091",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.016",
                "issue_dt": "2019-01-14",
                "redeem_dt": "2019-10-14",
                "delist_dt": "2019-10-14",
                "maturity_dt": "2025-01-14",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123001",
            "cell": {
                "bond_id": "123001",
                "bond_nm": "蓝标转债",
                "price": "135.998",
                "stock_id": "300058",
                "stock_nm": "蓝色光标",
                "orig_iss_amt": "14.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.020",
                "issue_dt": "2015-12-18",
                "redeem_dt": "2019-10-15",
                "delist_dt": "2019-10-10",
                "maturity_dt": "2021-12-18",
                "listed_years": "3.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128027",
            "cell": {
                "bond_id": "128027",
                "bond_nm": "崇达转债",
                "price": "123.000",
                "stock_id": "002815",
                "stock_nm": "崇达技术",
                "orig_iss_amt": "8.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.047",
                "issue_dt": "2017-12-15",
                "redeem_dt": "2019-10-23",
                "delist_dt": "2019-10-09",
                "maturity_dt": "2023-12-15",
                "listed_years": "1.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "127010",
            "cell": {
                "bond_id": "127010",
                "bond_nm": "平银转债",
                "price": "123.880",
                "stock_id": "000001",
                "stock_nm": "平安银行",
                "orig_iss_amt": "260.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.010",
                "issue_dt": "2019-01-21",
                "redeem_dt": "2019-09-18",
                "delist_dt": "2019-09-18",
                "maturity_dt": "2025-01-21",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113015",
            "cell": {
                "bond_id": "113015",
                "bond_nm": "隆基转债",
                "price": "154.190",
                "stock_id": "601012",
                "stock_nm": "隆基股份",
                "orig_iss_amt": "28.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.193",
                "issue_dt": "2017-11-02",
                "redeem_dt": "2019-09-03",
                "delist_dt": "2019-09-03",
                "maturity_dt": "2023-11-01",
                "listed_years": "1.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128024",
            "cell": {
                "bond_id": "128024",
                "bond_nm": "宁行转债",
                "price": "125.700",
                "stock_id": "002142",
                "stock_nm": "宁波银行",
                "orig_iss_amt": "100.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.108",
                "issue_dt": "2017-12-05",
                "redeem_dt": "2019-08-21",
                "delist_dt": "2019-08-21",
                "maturity_dt": "2023-12-05",
                "listed_years": "1.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110040",
            "cell": {
                "bond_id": "110040",
                "bond_nm": "生益转债",
                "price": "167.560",
                "stock_id": "600183",
                "stock_nm": "生益科技",
                "orig_iss_amt": "18.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.103",
                "issue_dt": "2017-11-24",
                "redeem_dt": "2019-07-31",
                "delist_dt": "2019-07-31",
                "maturity_dt": "2023-11-23",
                "listed_years": "1.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113513",
            "cell": {
                "bond_id": "113513",
                "bond_nm": "安井转债",
                "price": "141.290",
                "stock_id": "603345",
                "stock_nm": "安井食品",
                "orig_iss_amt": "5.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.038",
                "issue_dt": "2018-07-12",
                "redeem_dt": "2019-07-04",
                "delist_dt": "2019-07-04",
                "maturity_dt": "2024-07-12",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "120001",
            "cell": {
                "bond_id": "120001",
                "bond_nm": "16以岭EB",
                "price": "102.751",
                "stock_id": "002603",
                "stock_nm": "以岭药业",
                "orig_iss_amt": "8.000",
                "put_iss_amt": "7.837",
                "curr_iss_amt": "0.161",
                "issue_dt": "2016-04-18",
                "redeem_dt": "2019-06-27",
                "delist_dt": "2019-06-27",
                "maturity_dt": "2021-04-18",
                "listed_years": "3.2",
                "delist_notes": "不足2000万"
            }
        },
        {
            "id": "132010",
            "cell": {
                "bond_id": "132010",
                "bond_nm": "17桐昆EB",
                "price": "100.900",
                "stock_id": "601233",
                "stock_nm": "桐昆股份",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.265",
                "issue_dt": "2017-08-03",
                "redeem_dt": "2019-06-10",
                "delist_dt": "2019-06-10",
                "maturity_dt": "2020-08-03",
                "listed_years": "1.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113018",
            "cell": {
                "bond_id": "113018",
                "bond_nm": "常熟转债",
                "price": "131.630",
                "stock_id": "601128",
                "stock_nm": "常熟银行",
                "orig_iss_amt": "30.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.156",
                "issue_dt": "2018-01-19",
                "redeem_dt": "2019-05-16",
                "delist_dt": "2019-05-16",
                "maturity_dt": "2024-01-19",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123006",
            "cell": {
                "bond_id": "123006",
                "bond_nm": "东财转债",
                "price": "138.588",
                "stock_id": "300059",
                "stock_nm": "东方财富",
                "orig_iss_amt": "46.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.306",
                "issue_dt": "2017-12-20",
                "redeem_dt": "2019-05-10",
                "delist_dt": "2019-05-10",
                "maturity_dt": "2023-12-20",
                "listed_years": "1.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113506",
            "cell": {
                "bond_id": "113506",
                "bond_nm": "鼎信转债",
                "price": "128.200",
                "stock_id": "603421",
                "stock_nm": "鼎信通讯",
                "orig_iss_amt": "6.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.122",
                "issue_dt": "2018-04-16",
                "redeem_dt": "2019-04-26",
                "delist_dt": "2019-04-26",
                "maturity_dt": "2024-04-16",
                "listed_years": "1.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "123008",
            "cell": {
                "bond_id": "123008",
                "bond_nm": "康泰转债",
                "price": "168.658",
                "stock_id": "300601",
                "stock_nm": "康泰生物",
                "orig_iss_amt": "3.560",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.056",
                "issue_dt": "2018-02-01",
                "redeem_dt": "2019-05-06",
                "delist_dt": "2019-04-26",
                "maturity_dt": "2024-02-01",
                "listed_years": "1.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113512",
            "cell": {
                "bond_id": "113512",
                "bond_nm": "景旺转债",
                "price": "120.270",
                "stock_id": "603228",
                "stock_nm": "景旺电子",
                "orig_iss_amt": "9.780",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.176",
                "issue_dt": "2018-07-06",
                "redeem_dt": "2019-04-23",
                "delist_dt": "2019-04-23",
                "maturity_dt": "2024-07-06",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110032",
            "cell": {
                "bond_id": "110032",
                "bond_nm": "三一转债",
                "price": "176.090",
                "stock_id": "600031",
                "stock_nm": "三一重工",
                "orig_iss_amt": "45.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.094",
                "issue_dt": "2016-01-04",
                "redeem_dt": "2019-03-19",
                "delist_dt": "2019-03-19",
                "maturity_dt": "2022-01-04",
                "listed_years": "3.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113010",
            "cell": {
                "bond_id": "113010",
                "bond_nm": "江南转债",
                "price": "100.590",
                "stock_id": "601199",
                "stock_nm": "江南水务",
                "orig_iss_amt": "7.600",
                "put_iss_amt": "7.359",
                "curr_iss_amt": "0.241",
                "issue_dt": "2016-03-18",
                "redeem_dt": "2019-02-13",
                "delist_dt": "2019-01-29",
                "maturity_dt": "2022-03-18",
                "listed_years": "2.9",
                "delist_notes": "不足3000万"
            }
        },
        {
            "id": "132003",
            "cell": {
                "bond_id": "132003",
                "bond_nm": "15清控EB",
                "price": "99.930",
                "stock_id": "600109",
                "stock_nm": "国金证券",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "10.000",
                "issue_dt": "2015-10-26",
                "redeem_dt": "2018-10-25",
                "delist_dt": "2018-10-25",
                "maturity_dt": "2018-10-26",
                "listed_years": "3.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "132002",
            "cell": {
                "bond_id": "132002",
                "bond_nm": "15天集EB",
                "price": "100.000",
                "stock_id": "600535",
                "stock_nm": "天士力",
                "orig_iss_amt": "12.000",
                "put_iss_amt": "11.869",
                "curr_iss_amt": "0.131",
                "issue_dt": "2015-06-08",
                "redeem_dt": "2018-10-23",
                "delist_dt": "2018-10-23",
                "maturity_dt": "2020-06-08",
                "listed_years": "3.4",
                "delist_notes": "不足2000万"
            }
        },
        {
            "id": "123005",
            "cell": {
                "bond_id": "123005",
                "bond_nm": "万信转债",
                "price": "145.800",
                "stock_id": "300168",
                "stock_nm": "万达信息",
                "orig_iss_amt": "9.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.064",
                "issue_dt": "2017-12-19",
                "redeem_dt": "2018-08-20",
                "delist_dt": "2018-08-20",
                "maturity_dt": "2023-12-19",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110039",
            "cell": {
                "bond_id": "110039",
                "bond_nm": "宝信转债",
                "price": "141.390",
                "stock_id": "600845",
                "stock_nm": "宝信软件",
                "orig_iss_amt": "16.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.288",
                "issue_dt": "2017-11-17",
                "redeem_dt": "2018-07-06",
                "delist_dt": "2018-07-06",
                "maturity_dt": "2023-11-16",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "132001",
            "cell": {
                "bond_id": "132001",
                "bond_nm": "14宝钢EB",
                "price": "148.640",
                "stock_id": "601336",
                "stock_nm": "新华保险",
                "orig_iss_amt": "40.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "40.000",
                "issue_dt": "2014-12-10",
                "redeem_dt": "2017-12-08",
                "delist_dt": "2017-12-08",
                "maturity_dt": "2017-12-10",
                "listed_years": "3.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "128011",
            "cell": {
                "bond_id": "128011",
                "bond_nm": "汽模转债",
                "price": "121.501",
                "stock_id": "002510",
                "stock_nm": "天汽模",
                "orig_iss_amt": "4.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.000",
                "issue_dt": "2016-03-02",
                "redeem_dt": "2017-08-08",
                "delist_dt": "2017-08-08",
                "maturity_dt": "2022-03-02",
                "listed_years": "1.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128009",
            "cell": {
                "bond_id": "128009",
                "bond_nm": "歌尔转债",
                "price": "146.100",
                "stock_id": "002241",
                "stock_nm": "歌尔股份",
                "orig_iss_amt": "25.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.008",
                "issue_dt": "2014-12-12",
                "redeem_dt": "2017-06-30",
                "delist_dt": "2017-06-30",
                "maturity_dt": "2020-12-12",
                "listed_years": "2.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110035",
            "cell": {
                "bond_id": "110035",
                "bond_nm": "白云转债",
                "price": "138.390",
                "stock_id": "600004",
                "stock_nm": "白云机场",
                "orig_iss_amt": "35.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.192",
                "issue_dt": "2016-02-26",
                "redeem_dt": "2017-06-06",
                "delist_dt": "2017-06-06",
                "maturity_dt": "2021-02-26",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113501",
            "cell": {
                "bond_id": "113501",
                "bond_nm": "洛钼转债 ",
                "price": "130.550",
                "stock_id": "603993",
                "stock_nm": "洛阳钼业",
                "orig_iss_amt": "49.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.456",
                "issue_dt": "2014-12-02",
                "redeem_dt": None,
                "delist_dt": "2015-07-09",
                "maturity_dt": "2020-12-01",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113007",
            "cell": {
                "bond_id": "113007",
                "bond_nm": "吉视转债",
                "price": "100.180",
                "stock_id": "601929",
                "stock_nm": "吉视传媒",
                "orig_iss_amt": "17.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "6.472",
                "issue_dt": "2014-09-05",
                "redeem_dt": "2015-07-07",
                "delist_dt": "2015-07-07",
                "maturity_dt": "2020-09-05",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110023",
            "cell": {
                "bond_id": "110023",
                "bond_nm": "民生转债",
                "price": "119.660",
                "stock_id": "600016",
                "stock_nm": "民生银行",
                "orig_iss_amt": "200.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "1.620",
                "issue_dt": "2013-03-15",
                "redeem_dt": "2015-06-24",
                "delist_dt": "2015-06-24",
                "maturity_dt": "2019-03-15",
                "listed_years": "2.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128007",
            "cell": {
                "bond_id": "128007",
                "bond_nm": "通鼎转债",
                "price": "355.000",
                "stock_id": "002491",
                "stock_nm": "通鼎互联",
                "orig_iss_amt": "6.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.003",
                "issue_dt": "2014-08-15",
                "redeem_dt": "2015-07-07",
                "delist_dt": "2015-06-19",
                "maturity_dt": "2020-08-15",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128008",
            "cell": {
                "bond_id": "128008",
                "bond_nm": "齐峰转债",
                "price": "200.560",
                "stock_id": "002521",
                "stock_nm": "齐峰新材",
                "orig_iss_amt": "7.600",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.027",
                "issue_dt": "2014-09-15",
                "redeem_dt": "2015-06-05",
                "delist_dt": "2015-06-05",
                "maturity_dt": "2019-09-14",
                "listed_years": "0.7",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "125089",
            "cell": {
                "bond_id": "125089",
                "bond_nm": "深机转债",
                "price": "221.100",
                "stock_id": "000089",
                "stock_nm": "深圳机场",
                "orig_iss_amt": "20.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.026",
                "issue_dt": "2011-07-15",
                "redeem_dt": "2015-05-28",
                "delist_dt": "2015-05-28",
                "maturity_dt": "2017-07-14",
                "listed_years": "3.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "126729",
            "cell": {
                "bond_id": "126729",
                "bond_nm": "燕京转债",
                "price": "149.979",
                "stock_id": "000729",
                "stock_nm": "燕京啤酒",
                "orig_iss_amt": "11.300",
                "put_iss_amt": "2.623",
                "curr_iss_amt": "0.025",
                "issue_dt": "2010-10-15",
                "redeem_dt": "2015-06-04",
                "delist_dt": "2015-05-28",
                "maturity_dt": "2015-10-14",
                "listed_years": "4.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110029",
            "cell": {
                "bond_id": "110029",
                "bond_nm": "浙能转债",
                "price": "165.500",
                "stock_id": "600023",
                "stock_nm": "浙能电力 ",
                "orig_iss_amt": "100.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.180",
                "issue_dt": "2014-10-13",
                "redeem_dt": "2015-05-26",
                "delist_dt": "2015-05-26",
                "maturity_dt": "2020-10-12",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128002",
            "cell": {
                "bond_id": "128002",
                "bond_nm": "东华转债",
                "price": "341.000",
                "stock_id": "002065",
                "stock_nm": "东华软件",
                "orig_iss_amt": "10.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.001",
                "issue_dt": "2013-07-26",
                "redeem_dt": "2015-05-22",
                "delist_dt": "2015-05-20",
                "maturity_dt": "2019-07-26",
                "listed_years": "1.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128005",
            "cell": {
                "bond_id": "128005",
                "bond_nm": "齐翔转债",
                "price": "163.490",
                "stock_id": "002408",
                "stock_nm": "齐翔腾达",
                "orig_iss_amt": "12.400",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.001",
                "issue_dt": "2014-04-18",
                "redeem_dt": "2015-05-19",
                "delist_dt": "2015-05-19",
                "maturity_dt": "2019-04-17",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110012",
            "cell": {
                "bond_id": "110012",
                "bond_nm": "海运转债",
                "price": "206.460",
                "stock_id": "600798",
                "stock_nm": "宁波海运",
                "orig_iss_amt": "7.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.013",
                "issue_dt": "2011-01-07",
                "redeem_dt": "2015-05-11",
                "delist_dt": "2015-05-11",
                "maturity_dt": "2016-01-07",
                "listed_years": "4.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113006",
            "cell": {
                "bond_id": "113006",
                "bond_nm": "深燃转债",
                "price": "142.990",
                "stock_id": "601139",
                "stock_nm": "深圳燃气",
                "orig_iss_amt": "16.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.034",
                "issue_dt": "2013-12-13",
                "redeem_dt": "2015-04-30",
                "delist_dt": "2015-04-30",
                "maturity_dt": "2019-12-13",
                "listed_years": "1.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110011",
            "cell": {
                "bond_id": "110011",
                "bond_nm": "歌华转债",
                "price": "204.970",
                "stock_id": "600037",
                "stock_nm": "歌华有线",
                "orig_iss_amt": "16.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.136",
                "issue_dt": "2010-11-25",
                "redeem_dt": "2015-04-28",
                "delist_dt": "2015-04-28",
                "maturity_dt": "2016-11-25",
                "listed_years": "4.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110019",
            "cell": {
                "bond_id": "110019",
                "bond_nm": "恒丰转债",
                "price": "173.000",
                "stock_id": "600356",
                "stock_nm": "恒丰纸业",
                "orig_iss_amt": "4.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.004",
                "issue_dt": "2012-03-23",
                "redeem_dt": "2015-04-24",
                "delist_dt": "2015-04-24",
                "maturity_dt": "2017-03-23",
                "listed_years": "3.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110028",
            "cell": {
                "bond_id": "110028",
                "bond_nm": "冠城转债",
                "price": "177.490",
                "stock_id": "600067",
                "stock_nm": "冠城大通",
                "orig_iss_amt": "18.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.047",
                "issue_dt": "2014-07-18",
                "redeem_dt": "2015-04-23",
                "delist_dt": "2015-04-23",
                "maturity_dt": "2020-07-18",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128006",
            "cell": {
                "bond_id": "128006",
                "bond_nm": "长青转债",
                "price": "145.999",
                "stock_id": "002391",
                "stock_nm": "长青股份",
                "orig_iss_amt": "6.318",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.000",
                "issue_dt": "2014-07-09",
                "redeem_dt": "2015-04-15",
                "delist_dt": "2015-04-15",
                "maturity_dt": "2020-06-19",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110020",
            "cell": {
                "bond_id": "110020",
                "bond_nm": "南山转债",
                "price": "152.640",
                "stock_id": "600219",
                "stock_nm": "南山铝业",
                "orig_iss_amt": "60.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.084",
                "issue_dt": "2012-10-16",
                "redeem_dt": "2015-03-10",
                "delist_dt": "2015-03-10",
                "maturity_dt": "2018-10-16",
                "listed_years": "2.4",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113001",
            "cell": {
                "bond_id": "113001",
                "bond_nm": "中行转债",
                "price": "145.930",
                "stock_id": "601988",
                "stock_nm": "中国银行",
                "orig_iss_amt": "400.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.240",
                "issue_dt": "2010-06-02",
                "redeem_dt": "2015-03-06",
                "delist_dt": "2015-03-06",
                "maturity_dt": "2016-06-02",
                "listed_years": "4.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110022",
            "cell": {
                "bond_id": "110022",
                "bond_nm": "同仁转债",
                "price": "131.490",
                "stock_id": "600085",
                "stock_nm": "同仁堂",
                "orig_iss_amt": "12.050",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.045",
                "issue_dt": "2012-12-04",
                "redeem_dt": "2015-03-03",
                "delist_dt": "2015-03-03",
                "maturity_dt": "2017-12-04",
                "listed_years": "2.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110018",
            "cell": {
                "bond_id": "110018",
                "bond_nm": "国电转债",
                "price": "169.690",
                "stock_id": "600795",
                "stock_nm": "国电电力",
                "orig_iss_amt": "55.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.044",
                "issue_dt": "2011-08-19",
                "redeem_dt": "2015-02-26",
                "delist_dt": "2015-02-26",
                "maturity_dt": "2017-08-19",
                "listed_years": "3.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110027",
            "cell": {
                "bond_id": "110027",
                "bond_nm": "东方转债",
                "price": "159.570",
                "stock_id": "600875",
                "stock_nm": "东方电气",
                "orig_iss_amt": "40.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.036",
                "issue_dt": "2014-07-10",
                "redeem_dt": "2015-02-16",
                "delist_dt": "2015-02-16",
                "maturity_dt": "2020-07-10",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113002",
            "cell": {
                "bond_id": "113002",
                "bond_nm": "工行转债",
                "price": "132.380",
                "stock_id": "601398",
                "stock_nm": "工商银行",
                "orig_iss_amt": "250.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.150",
                "issue_dt": "2010-08-31",
                "redeem_dt": "2015-02-12",
                "delist_dt": "2015-02-12",
                "maturity_dt": "2016-08-31",
                "listed_years": "4.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110015",
            "cell": {
                "bond_id": "110015",
                "bond_nm": "石化转债",
                "price": "116.300",
                "stock_id": "600028",
                "stock_nm": "中国石化",
                "orig_iss_amt": "230.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.529",
                "issue_dt": "2011-02-23",
                "redeem_dt": "2015-02-11",
                "delist_dt": "2015-02-11",
                "maturity_dt": "2017-02-23",
                "listed_years": "4.0",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110017",
            "cell": {
                "bond_id": "110017",
                "bond_nm": "中海转债",
                "price": "115.000",
                "stock_id": "600026",
                "stock_nm": "中远海能",
                "orig_iss_amt": "39.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.344",
                "issue_dt": "2011-08-01",
                "redeem_dt": "2015-02-09",
                "delist_dt": "2015-02-09",
                "maturity_dt": "2017-08-01",
                "listed_years": "3.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "127002",
            "cell": {
                "bond_id": "127002",
                "bond_nm": "徐工转债",
                "price": "136.190",
                "stock_id": "000425",
                "stock_nm": "徐工机械",
                "orig_iss_amt": "25.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.031",
                "issue_dt": "2013-10-24",
                "redeem_dt": "2015-02-05",
                "delist_dt": "2015-02-05",
                "maturity_dt": "2019-10-24",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113005",
            "cell": {
                "bond_id": "113005",
                "bond_nm": "平安转债",
                "price": "167.570",
                "stock_id": "601318",
                "stock_nm": "中国平安",
                "orig_iss_amt": "260.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.338",
                "issue_dt": "2013-11-22",
                "redeem_dt": "2015-01-09",
                "delist_dt": "2015-01-09",
                "maturity_dt": "2019-11-22",
                "listed_years": "1.1",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110025",
            "cell": {
                "bond_id": "110025",
                "bond_nm": "国金转债",
                "price": "194.970",
                "stock_id": "600109",
                "stock_nm": "国金证券",
                "orig_iss_amt": "25.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.152",
                "issue_dt": "2014-05-14",
                "redeem_dt": "2014-12-29",
                "delist_dt": "2014-12-29",
                "maturity_dt": "2020-05-13",
                "listed_years": "0.6",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128004",
            "cell": {
                "bond_id": "128004",
                "bond_nm": "久立转债",
                "price": "143.000",
                "stock_id": "002318",
                "stock_nm": "久立特材",
                "orig_iss_amt": "4.870",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.009",
                "issue_dt": "2014-02-25",
                "redeem_dt": "2014-12-23",
                "delist_dt": "2014-12-23",
                "maturity_dt": "2020-02-24",
                "listed_years": "0.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110024",
            "cell": {
                "bond_id": "110024",
                "bond_nm": "隧道转债",
                "price": "153.060",
                "stock_id": "600820",
                "stock_nm": "隧道股份",
                "orig_iss_amt": "26.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.062",
                "issue_dt": "2013-09-13",
                "redeem_dt": "2014-12-11",
                "delist_dt": "2014-12-11",
                "maturity_dt": "2019-09-13",
                "listed_years": "1.2",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "113003",
            "cell": {
                "bond_id": "113003",
                "bond_nm": "重工转债",
                "price": "132.550",
                "stock_id": "601989",
                "stock_nm": "中国重工",
                "orig_iss_amt": "80.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.048",
                "issue_dt": "2012-06-04",
                "redeem_dt": "2014-11-28",
                "delist_dt": "2014-11-28",
                "maturity_dt": "2018-06-04",
                "listed_years": "2.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128003",
            "cell": {
                "bond_id": "128003",
                "bond_nm": "华天转债",
                "price": "154.001",
                "stock_id": "002185",
                "stock_nm": "华天科技",
                "orig_iss_amt": "4.610",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.013",
                "issue_dt": "2013-08-12",
                "redeem_dt": "2014-11-27",
                "delist_dt": "2014-11-27",
                "maturity_dt": "2019-08-12",
                "listed_years": "1.3",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "128001",
            "cell": {
                "bond_id": "128001",
                "bond_nm": "泰尔转债",
                "price": "134.122",
                "stock_id": "002347",
                "stock_nm": "泰尔股份",
                "orig_iss_amt": "3.200",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.018",
                "issue_dt": "2013-01-15",
                "redeem_dt": "2014-11-12",
                "delist_dt": "2014-11-10",
                "maturity_dt": "2018-01-08",
                "listed_years": "1.8",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110007",
            "cell": {
                "bond_id": "110007",
                "bond_nm": "博汇转债",
                "price": "108.610",
                "stock_id": "600966",
                "stock_nm": "博汇纸业",
                "orig_iss_amt": "9.750",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.145",
                "issue_dt": "2009-09-23",
                "redeem_dt": "2014-09-22",
                "delist_dt": "2014-09-05",
                "maturity_dt": "2014-09-23",
                "listed_years": "5.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "110016",
            "cell": {
                "bond_id": "110016",
                "bond_nm": "川投转债",
                "price": "159.000",
                "stock_id": "600674",
                "stock_nm": "川投能源",
                "orig_iss_amt": "21.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.332",
                "issue_dt": "2011-03-21",
                "redeem_dt": "2014-09-02",
                "delist_dt": "2014-09-02",
                "maturity_dt": "2017-03-21",
                "listed_years": "3.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "125887",
            "cell": {
                "bond_id": "125887",
                "bond_nm": "中鼎转债",
                "price": "142.000",
                "stock_id": "000887",
                "stock_nm": "中鼎股份",
                "orig_iss_amt": "3.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.015",
                "issue_dt": "2011-02-11",
                "redeem_dt": "2014-07-31",
                "delist_dt": "2014-07-31",
                "maturity_dt": "2016-02-11",
                "listed_years": "3.5",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110003",
            "cell": {
                "bond_id": "110003",
                "bond_nm": "新钢转债",
                "price": "106.550",
                "stock_id": "600782",
                "stock_nm": "新钢股份",
                "orig_iss_amt": "27.600",
                "put_iss_amt": "0.024",
                "curr_iss_amt": "27.576",
                "issue_dt": "2008-08-21",
                "redeem_dt": "2013-08-20",
                "delist_dt": "2013-08-06",
                "maturity_dt": "2013-08-20",
                "listed_years": "5.0",
                "delist_notes": "到期"
            }
        },
        {
            "id": "129031",
            "cell": {
                "bond_id": "129031",
                "bond_nm": "巨轮转2",
                "price": "131.500",
                "stock_id": "002031",
                "stock_nm": "巨轮智能",
                "orig_iss_amt": "3.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.022",
                "issue_dt": "2011-07-19",
                "redeem_dt": "2013-06-05",
                "delist_dt": "2013-06-05",
                "maturity_dt": "2016-07-18",
                "listed_years": "1.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "125731",
            "cell": {
                "bond_id": "125731",
                "bond_nm": "美丰转债",
                "price": "163.200",
                "stock_id": "000731",
                "stock_nm": "四川美丰",
                "orig_iss_amt": "6.500",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "0.022",
                "issue_dt": "2010-06-02",
                "redeem_dt": "2013-04-12",
                "delist_dt": "2013-04-12",
                "maturity_dt": "2015-06-02",
                "listed_years": "2.9",
                "delist_notes": "强赎"
            }
        },
        {
            "id": "110009",
            "cell": {
                "bond_id": "110009",
                "bond_nm": "双良转债",
                "price": "93.820",
                "stock_id": "600481",
                "stock_nm": "双良节能",
                "orig_iss_amt": "7.200",
                "put_iss_amt": "6.938",
                "curr_iss_amt": "0.261",
                "issue_dt": "2010-05-04",
                "redeem_dt": "2011-12-14",
                "delist_dt": "2011-12-14",
                "maturity_dt": "2015-05-04",
                "listed_years": "1.6",
                "delist_notes": "不足3000万"
            }
        },
        {
            "id": "123095",
            "cell": {
                "bond_id": "123095",
                "bond_nm": "日升转债",
                "price": "100.000",
                "stock_id": "300118",
                "stock_nm": "东方日升",
                "orig_iss_amt": "33.000",
                "put_iss_amt": "0.000",
                "curr_iss_amt": "33.000",
                "issue_dt": "2021-01-22",
                "redeem_dt": None,
                "delist_dt": None,
                "maturity_dt": "2027-01-21",
                "listed_years": None,
                "delist_notes": "撤销发行"
            }
        }
    ]
}


def do_fetch_data_delisted():
    rows = delisted_data['rows']
    size = len(rows)
    i = 0
    for row in rows:
        bond_id = row['id']
        bond_nm = row['bond_nm']
        # 异常后的判重处理
        # with db_utils.get_daily_connect() as con:
        #     cur = con.cursor()
        #     cur.execute("select count(*) from cb_history where bond_id=:bond_id", {"bond_id": bond_id})
        #     result = cur.fetchone()
        #     if result[0] > 0:
        #         continue
        cb_data = get_cb_data(bond_id, bond_nm)
        insert_db(cb_data)
        i += 1
        print("insert complete:" + str(i) + "/" + str(size))


cb_list_new = {
    "page": 1,
    "rows": [
        {
            "id": "111001",
            "cell": {
                "bond_id": "111001",
                "bond_nm": "山玻转债",
            }},
        {
            "id": "127047",
            "cell": {
                "bond_id": "127047",
                "bond_nm": "帝欧转债",
            }},
        {
            "id": "127051",
            "cell": {
                "bond_id": "127051",
                "bond_nm": "博杰转债",
            }},
        {
            "id": "123130",
            "cell": {
                "bond_id": "123130",
                "bond_nm": "设研转债",
            }},
        {
            "id": "127049",
            "cell": {
                "bond_id": "127049",
                "bond_nm": "希望转2",
            }},
        {
            "id": "127050",
            "cell": {
                "bond_id": "127050",
                "bond_nm": "麒麟转债",
            }},
        {
            "id": "110051",
            "cell": {
                "bond_id": "110051",
                "bond_nm": "中天转债",
            }},
        {
            "id": "128094",
            "cell": {
                "bond_id": "128094",
                "bond_nm": "星帅转债",
            }},
        {
            "id": "113614",
            "cell": {
                "bond_id": "113614",
                "bond_nm": "健20转债",
            }},
        {
            "id": "113603",
            "cell": {
                "bond_id": "113603",
                "bond_nm": "东缆转债",
            }},
        {
            "id": "128050",
            "cell": {
                "bond_id": "128050",
                "bond_nm": "钧达转债",
            }},
        {
            "id": "113607",
            "cell": {
                "bond_id": "113607",
                "bond_nm": "伟20转债",
            }},
        {
            "id": "113632",
            "cell": {
                "bond_id": "113632",
                "bond_nm": "鹤21转债",
            }},
        {
            "id": "128057",
            "cell": {
                "bond_id": "128057",
                "bond_nm": "博彦转债",
            }},
        {
            "id": "113504",
            "cell": {
                "bond_id": "113504",
                "bond_nm": "艾华转债",
            }},
        {
            "id": "123081",
            "cell": {
                "bond_id": "123081",
                "bond_nm": "精研转债",
            }},
        {
            "id": "123086",
            "cell": {
                "bond_id": "123086",
                "bond_nm": "海兰转债",
            }},
        {
            "id": "128085",
            "cell": {
                "bond_id": "128085",
                "bond_nm": "鸿达转债",
            }},
        {
            "id": "113541",
            "cell": {
                "bond_id": "113541",
                "bond_nm": "荣晟转债",
            }},
        {
            "id": "123067",
            "cell": {
                "bond_id": "123067",
                "bond_nm": "斯莱转债",
            }},
        {
            "id": "123092",
            "cell": {
                "bond_id": "123092",
                "bond_nm": "天壕转债",
            }},
        {
            "id": "128013",
            "cell": {
                "bond_id": "128013",
                "bond_nm": "洪涛转债",
            }},
        {
            "id": "113534",
            "cell": {
                "bond_id": "113534",
                "bond_nm": "鼎胜转债",
            }},
        {
            "id": "123070",
            "cell": {
                "bond_id": "123070",
                "bond_nm": "鹏辉转债",
            }},
        {
            "id": "128082",
            "cell": {
                "bond_id": "128082",
                "bond_nm": "华锋转债",
            }},
        {
            "id": "128145",
            "cell": {
                "bond_id": "128145",
                "bond_nm": "日丰转债",
            }},
        {
            "id": "123083",
            "cell": {
                "bond_id": "123083",
                "bond_nm": "朗新转债",
            }},
        {
            "id": "113591",
            "cell": {
                "bond_id": "113591",
                "bond_nm": "胜达转债",
            }},
        {
            "id": "113528",
            "cell": {
                "bond_id": "113528",
                "bond_nm": "长城转债",
            }},
        {
            "id": "113016",
            "cell": {
                "bond_id": "113016",
                "bond_nm": "小康转债",
            }},
        {
            "id": "128128",
            "cell": {
                "bond_id": "128128",
                "bond_nm": "齐翔转2",
            }},
        {
            "id": "123071",
            "cell": {
                "bond_id": "123071",
                "bond_nm": "天能转债",
            }},
        {
            "id": "113548",
            "cell": {
                "bond_id": "113548",
                "bond_nm": "石英转债",
            }},
        {
            "id": "132014",
            "cell": {
                "bond_id": "132014",
                "bond_nm": "18中化EB",
            }},
        {
            "id": "128096",
            "cell": {
                "bond_id": "128096",
                "bond_nm": "奥瑞转债",
            }},
        {
            "id": "128111",
            "cell": {
                "bond_id": "128111",
                "bond_nm": "中矿转债",
            }},
        {
            "id": "123085",
            "cell": {
                "bond_id": "123085",
                "bond_nm": "万顺转2",
            }},
        {
            "id": "123111",
            "cell": {
                "bond_id": "123111",
                "bond_nm": "东财转3",
            }},
        {
            "id": "128081",
            "cell": {
                "bond_id": "128081",
                "bond_nm": "海亮转债",
            }},
        {
            "id": "113568",
            "cell": {
                "bond_id": "113568",
                "bond_nm": "新春转债",
            }},
        {
            "id": "113585",
            "cell": {
                "bond_id": "113585",
                "bond_nm": "寿仙转债",
            }},
        {
            "id": "123028",
            "cell": {
                "bond_id": "123028",
                "bond_nm": "清水转债",
            }},
        {
            "id": "123012",
            "cell": {
                "bond_id": "123012",
                "bond_nm": "万顺转债",
            }},
        {
            "id": "132018",
            "cell": {
                "bond_id": "132018",
                "bond_nm": "G三峡EB1",
            }},
        {
            "id": "113537",
            "cell": {
                "bond_id": "113537",
                "bond_nm": "文灿转债",
            }},
        {
            "id": "128103",
            "cell": {
                "bond_id": "128103",
                "bond_nm": "同德转债",
            }},
        {
            "id": "110083",
            "cell": {
                "bond_id": "110083",
                "bond_nm": "苏租转债",
            }},
        {
            "id": "123109",
            "cell": {
                "bond_id": "123109",
                "bond_nm": "昌红转债",
            }},
        {
            "id": "123089",
            "cell": {
                "bond_id": "123089",
                "bond_nm": "九洲转2",
            }},
        {
            "id": "110071",
            "cell": {
                "bond_id": "110071",
                "bond_nm": "湖盐转债",
            }},
        {
            "id": "113051",
            "cell": {
                "bond_id": "113051",
                "bond_nm": "节能转债",
            }},
        {
            "id": "128093",
            "cell": {
                "bond_id": "128093",
                "bond_nm": "百川转债",
            }},
        {
            "id": "128113",
            "cell": {
                "bond_id": "128113",
                "bond_nm": "比音转债",
            }},
        {
            "id": "128106",
            "cell": {
                "bond_id": "128106",
                "bond_nm": "华统转债",
            }},
        {
            "id": "110058",
            "cell": {
                "bond_id": "110058",
                "bond_nm": "永鼎转债",
            }},
        {
            "id": "123080",
            "cell": {
                "bond_id": "123080",
                "bond_nm": "海波转债",
            }},
        {
            "id": "113631",
            "cell": {
                "bond_id": "113631",
                "bond_nm": "皖天转债",
            }},
        {
            "id": "128143",
            "cell": {
                "bond_id": "128143",
                "bond_nm": "锋龙转债",
            }},
        {
            "id": "128100",
            "cell": {
                "bond_id": "128100",
                "bond_nm": "搜特转债",
            }},
        {
            "id": "113579",
            "cell": {
                "bond_id": "113579",
                "bond_nm": "健友转债",
            }},
        {
            "id": "113025",
            "cell": {
                "bond_id": "113025",
                "bond_nm": "明泰转债",
            }},
        {
            "id": "128017",
            "cell": {
                "bond_id": "128017",
                "bond_nm": "金禾转债",
            }},
        {
            "id": "113525",
            "cell": {
                "bond_id": "113525",
                "bond_nm": "台华转债",
            }},
        {
            "id": "128046",
            "cell": {
                "bond_id": "128046",
                "bond_nm": "利尔转债",
            }},
        {
            "id": "127029",
            "cell": {
                "bond_id": "127029",
                "bond_nm": "中钢转债",
            }},
        {
            "id": "113039",
            "cell": {
                "bond_id": "113039",
                "bond_nm": "嘉泽转债",
            }},
        {
            "id": "128130",
            "cell": {
                "bond_id": "128130",
                "bond_nm": "景兴转债",
            }},
        {
            "id": "113505",
            "cell": {
                "bond_id": "113505",
                "bond_nm": "杭电转债",
            }},
        {
            "id": "127011",
            "cell": {
                "bond_id": "127011",
                "bond_nm": "中鼎转2",
            }},
        {
            "id": "118000",
            "cell": {
                "bond_id": "118000",
                "bond_nm": "嘉元转债",
            }},
        {
            "id": "127040",
            "cell": {
                "bond_id": "127040",
                "bond_nm": "国泰转债",
            }},
        {
            "id": "111000",
            "cell": {
                "bond_id": "111000",
                "bond_nm": "起帆转债",
            }},
        {
            "id": "123052",
            "cell": {
                "bond_id": "123052",
                "bond_nm": "飞鹿转债",
            }},
        {
            "id": "123042",
            "cell": {
                "bond_id": "123042",
                "bond_nm": "银河转债",
            }},
        {
            "id": "113626",
            "cell": {
                "bond_id": "113626",
                "bond_nm": "伯特转债",
            }},
        {
            "id": "113009",
            "cell": {
                "bond_id": "113009",
                "bond_nm": "广汽转债",
            }},
        {
            "id": "123098",
            "cell": {
                "bond_id": "123098",
                "bond_nm": "一品转债",
            }},
        {
            "id": "123112",
            "cell": {
                "bond_id": "123112",
                "bond_nm": "万讯转债",
            }},
        {
            "id": "123043",
            "cell": {
                "bond_id": "123043",
                "bond_nm": "正元转债",
            }},
        {
            "id": "113615",
            "cell": {
                "bond_id": "113615",
                "bond_nm": "金诚转债",
            }},
        {
            "id": "113048",
            "cell": {
                "bond_id": "113048",
                "bond_nm": "晶科转债",
            }},
        {
            "id": "127042",
            "cell": {
                "bond_id": "127042",
                "bond_nm": "嘉美转债",
            }},
        {
            "id": "110077",
            "cell": {
                "bond_id": "110077",
                "bond_nm": "洪城转债",
            }},
        {
            "id": "113034",
            "cell": {
                "bond_id": "113034",
                "bond_nm": "滨化转债",
            }},
        {
            "id": "113026",
            "cell": {
                "bond_id": "113026",
                "bond_nm": "核能转债",
            }},
        {
            "id": "128119",
            "cell": {
                "bond_id": "128119",
                "bond_nm": "龙大转债",
            }},
        {
            "id": "123084",
            "cell": {
                "bond_id": "123084",
                "bond_nm": "高澜转债",
            }},
        {
            "id": "128109",
            "cell": {
                "bond_id": "128109",
                "bond_nm": "楚江转债",
            }},
        {
            "id": "113545",
            "cell": {
                "bond_id": "113545",
                "bond_nm": "金能转债",
            }},
        {
            "id": "123053",
            "cell": {
                "bond_id": "123053",
                "bond_nm": "宝通转债",
            }},
        {
            "id": "128140",
            "cell": {
                "bond_id": "128140",
                "bond_nm": "润建转债",
            }},
        {
            "id": "123046",
            "cell": {
                "bond_id": "123046",
                "bond_nm": "天铁转债",
            }},
        {
            "id": "128078",
            "cell": {
                "bond_id": "128078",
                "bond_nm": "太极转债",
            }},
        {
            "id": "128101",
            "cell": {
                "bond_id": "128101",
                "bond_nm": "联创转债",
            }},
        {
            "id": "123103",
            "cell": {
                "bond_id": "123103",
                "bond_nm": "震安转债",
            }},
        {
            "id": "123087",
            "cell": {
                "bond_id": "123087",
                "bond_nm": "明电转债",
            }},
        {
            "id": "123100",
            "cell": {
                "bond_id": "123100",
                "bond_nm": "朗科转债",
            }},
        {
            "id": "118002",
            "cell": {
                "bond_id": "118002",
                "bond_nm": "天合转债",
            }},
        {
            "id": "123097",
            "cell": {
                "bond_id": "123097",
                "bond_nm": "美力转债",
            }},
        {
            "id": "110061",
            "cell": {
                "bond_id": "110061",
                "bond_nm": "川投转债",
            }},
        {
            "id": "128091",
            "cell": {
                "bond_id": "128091",
                "bond_nm": "新天转债",
            }},
        {
            "id": "113536",
            "cell": {
                "bond_id": "113536",
                "bond_nm": "三星转债",
            }},
        {
            "id": "113609",
            "cell": {
                "bond_id": "113609",
                "bond_nm": "永安转债",
            }},
        {
            "id": "110048",
            "cell": {
                "bond_id": "110048",
                "bond_nm": "福能转债",
            }},
        {
            "id": "113567",
            "cell": {
                "bond_id": "113567",
                "bond_nm": "君禾转债",
            }},
        {
            "id": "113550",
            "cell": {
                "bond_id": "113550",
                "bond_nm": "常汽转债",
            }},
        {
            "id": "123027",
            "cell": {
                "bond_id": "123027",
                "bond_nm": "蓝晓转债",
            }},
        {
            "id": "123078",
            "cell": {
                "bond_id": "123078",
                "bond_nm": "飞凯转债",
            }},
        {
            "id": "128075",
            "cell": {
                "bond_id": "128075",
                "bond_nm": "远东转债",
            }},
        {
            "id": "128073",
            "cell": {
                "bond_id": "128073",
                "bond_nm": "哈尔转债",
            }},
        {
            "id": "113600",
            "cell": {
                "bond_id": "113600",
                "bond_nm": "新星转债",
            }},
        {
            "id": "110079",
            "cell": {
                "bond_id": "110079",
                "bond_nm": "杭银转债",
            }},
        {
            "id": "123063",
            "cell": {
                "bond_id": "123063",
                "bond_nm": "大禹转债",
            }},
        {
            "id": "123050",
            "cell": {
                "bond_id": "123050",
                "bond_nm": "聚飞转债",
            }},
        {
            "id": "113593",
            "cell": {
                "bond_id": "113593",
                "bond_nm": "沪工转债",
            }},
        {
            "id": "123073",
            "cell": {
                "bond_id": "123073",
                "bond_nm": "同和转债",
            }},
        {
            "id": "123035",
            "cell": {
                "bond_id": "123035",
                "bond_nm": "利德转债",
            }},
        {
            "id": "113599",
            "cell": {
                "bond_id": "113599",
                "bond_nm": "嘉友转债",
            }},
        {
            "id": "123057",
            "cell": {
                "bond_id": "123057",
                "bond_nm": "美联转债",
            }},
        {
            "id": "113577",
            "cell": {
                "bond_id": "113577",
                "bond_nm": "春秋转债",
            }},
        {
            "id": "127020",
            "cell": {
                "bond_id": "127020",
                "bond_nm": "中金转债",
            }},
        {
            "id": "110074",
            "cell": {
                "bond_id": "110074",
                "bond_nm": "精达转债",
            }},
        {
            "id": "113570",
            "cell": {
                "bond_id": "113570",
                "bond_nm": "百达转债",
            }},
        {
            "id": "113629",
            "cell": {
                "bond_id": "113629",
                "bond_nm": "泉峰转债",
            }},
        {
            "id": "127030",
            "cell": {
                "bond_id": "127030",
                "bond_nm": "盛虹转债",
            }},
        {
            "id": "123045",
            "cell": {
                "bond_id": "123045",
                "bond_nm": "雷迪转债",
            }},
        {
            "id": "123031",
            "cell": {
                "bond_id": "123031",
                "bond_nm": "晶瑞转债",
            }},
        {
            "id": "110066",
            "cell": {
                "bond_id": "110066",
                "bond_nm": "盛屯转债",
            }},
        {
            "id": "110081",
            "cell": {
                "bond_id": "110081",
                "bond_nm": "闻泰转债",
            }},
        {
            "id": "127043",
            "cell": {
                "bond_id": "127043",
                "bond_nm": "川恒转债",
            }},
        {
            "id": "128121",
            "cell": {
                "bond_id": "128121",
                "bond_nm": "宏川转债",
            }},
        {
            "id": "113621",
            "cell": {
                "bond_id": "113621",
                "bond_nm": "彤程转债",
            }},
        {
            "id": "123022",
            "cell": {
                "bond_id": "123022",
                "bond_nm": "长信转债",
            }},
        {
            "id": "127026",
            "cell": {
                "bond_id": "127026",
                "bond_nm": "超声转债",
            }},
        {
            "id": "128107",
            "cell": {
                "bond_id": "128107",
                "bond_nm": "交科转债",
            }},
        {
            "id": "123114",
            "cell": {
                "bond_id": "123114",
                "bond_nm": "三角转债",
            }},
        {
            "id": "113030",
            "cell": {
                "bond_id": "113030",
                "bond_nm": "东风转债",
            }},
        {
            "id": "123099",
            "cell": {
                "bond_id": "123099",
                "bond_nm": "普利转债",
            }},
        {
            "id": "128076",
            "cell": {
                "bond_id": "128076",
                "bond_nm": "金轮转债",
            }},
        {
            "id": "123074",
            "cell": {
                "bond_id": "123074",
                "bond_nm": "隆利转债",
            }},
        {
            "id": "113602",
            "cell": {
                "bond_id": "113602",
                "bond_nm": "景20转债",
            }},
        {
            "id": "128048",
            "cell": {
                "bond_id": "128048",
                "bond_nm": "张行转债",
            }},
        {
            "id": "128144",
            "cell": {
                "bond_id": "128144",
                "bond_nm": "利民转债",
            }},
        {
            "id": "123118",
            "cell": {
                "bond_id": "123118",
                "bond_nm": "惠城转债",
            }},
        {
            "id": "113027",
            "cell": {
                "bond_id": "113027",
                "bond_nm": "华钰转债",
            }},
        {
            "id": "113549",
            "cell": {
                "bond_id": "113549",
                "bond_nm": "白电转债",
            }},
        {
            "id": "128095",
            "cell": {
                "bond_id": "128095",
                "bond_nm": "恩捷转债",
            }},
        {
            "id": "128137",
            "cell": {
                "bond_id": "128137",
                "bond_nm": "洁美转债",
            }},
        {
            "id": "110043",
            "cell": {
                "bond_id": "110043",
                "bond_nm": "无锡转债",
            }},
        {
            "id": "123091",
            "cell": {
                "bond_id": "123091",
                "bond_nm": "长海转债",
            }},
        {
            "id": "110057",
            "cell": {
                "bond_id": "110057",
                "bond_nm": "现代转债",
            }},
        {
            "id": "123129",
            "cell": {
                "bond_id": "123129",
                "bond_nm": "锦鸡转债",
            }},
        {
            "id": "123060",
            "cell": {
                "bond_id": "123060",
                "bond_nm": "苏试转债",
            }},
        {
            "id": "123110",
            "cell": {
                "bond_id": "123110",
                "bond_nm": "九典转债",
            }},
        {
            "id": "123120",
            "cell": {
                "bond_id": "123120",
                "bond_nm": "隆华转债",
            }},
        {
            "id": "110063",
            "cell": {
                "bond_id": "110063",
                "bond_nm": "鹰19转债",
            }},
        {
            "id": "128087",
            "cell": {
                "bond_id": "128087",
                "bond_nm": "孚日转债",
            }},
        {
            "id": "113011",
            "cell": {
                "bond_id": "113011",
                "bond_nm": "光大转债",
            }},
        {
            "id": "110047",
            "cell": {
                "bond_id": "110047",
                "bond_nm": "山鹰转债",
            }},
        {
            "id": "128141",
            "cell": {
                "bond_id": "128141",
                "bond_nm": "旺能转债",
            }},
        {
            "id": "128066",
            "cell": {
                "bond_id": "128066",
                "bond_nm": "亚泰转债",
            }},
        {
            "id": "127045",
            "cell": {
                "bond_id": "127045",
                "bond_nm": "牧原转债",
            }},
        {
            "id": "128090",
            "cell": {
                "bond_id": "128090",
                "bond_nm": "汽模转2",
            }},
        {
            "id": "123121",
            "cell": {
                "bond_id": "123121",
                "bond_nm": "帝尔转债",
            }},
        {
            "id": "127028",
            "cell": {
                "bond_id": "127028",
                "bond_nm": "英特转债",
            }},
        {
            "id": "127005",
            "cell": {
                "bond_id": "127005",
                "bond_nm": "长证转债",
            }},
        {
            "id": "113049",
            "cell": {
                "bond_id": "113049",
                "bond_nm": "长汽转债",
            }},
        {
            "id": "128025",
            "cell": {
                "bond_id": "128025",
                "bond_nm": "特一转债",
            }},
        {
            "id": "123127",
            "cell": {
                "bond_id": "123127",
                "bond_nm": "耐普转债",
            }},
        {
            "id": "128097",
            "cell": {
                "bond_id": "128097",
                "bond_nm": "奥佳转债",
            }},
        {
            "id": "128129",
            "cell": {
                "bond_id": "128129",
                "bond_nm": "青农转债",
            }},
        {
            "id": "128134",
            "cell": {
                "bond_id": "128134",
                "bond_nm": "鸿路转债",
            }},
        {
            "id": "110055",
            "cell": {
                "bond_id": "110055",
                "bond_nm": "伊力转债",
            }},
        {
            "id": "127035",
            "cell": {
                "bond_id": "127035",
                "bond_nm": "濮耐转债",
            }},
        {
            "id": "113527",
            "cell": {
                "bond_id": "113527",
                "bond_nm": "维格转债",
            }},
        {
            "id": "123115",
            "cell": {
                "bond_id": "123115",
                "bond_nm": "捷捷转债",
            }},
        {
            "id": "113610",
            "cell": {
                "bond_id": "113610",
                "bond_nm": "灵康转债",
            }},
        {
            "id": "113619",
            "cell": {
                "bond_id": "113619",
                "bond_nm": "世运转债",
            }},
        {
            "id": "113565",
            "cell": {
                "bond_id": "113565",
                "bond_nm": "宏辉转债",
            }},
        {
            "id": "128029",
            "cell": {
                "bond_id": "128029",
                "bond_nm": "太阳转债",
            }},
        {
            "id": "128040",
            "cell": {
                "bond_id": "128040",
                "bond_nm": "华通转债",
            }},
        {
            "id": "127038",
            "cell": {
                "bond_id": "127038",
                "bond_nm": "国微转债",
            }},
        {
            "id": "113582",
            "cell": {
                "bond_id": "113582",
                "bond_nm": "火炬转债",
            }},
        {
            "id": "113044",
            "cell": {
                "bond_id": "113044",
                "bond_nm": "大秦转债",
            }},
        {
            "id": "113588",
            "cell": {
                "bond_id": "113588",
                "bond_nm": "润达转债",
            }},
        {
            "id": "123024",
            "cell": {
                "bond_id": "123024",
                "bond_nm": "岱勒转债",
            }},
        {
            "id": "128034",
            "cell": {
                "bond_id": "128034",
                "bond_nm": "江银转债",
            }},
        {
            "id": "127048",
            "cell": {
                "bond_id": "127048",
                "bond_nm": "中大转债",
            }},
        {
            "id": "123048",
            "cell": {
                "bond_id": "123048",
                "bond_nm": "应急转债",
            }},
        {
            "id": "123025",
            "cell": {
                "bond_id": "123025",
                "bond_nm": "精测转债",
            }},
        {
            "id": "110075",
            "cell": {
                "bond_id": "110075",
                "bond_nm": "南航转债",
            }},
        {
            "id": "127027",
            "cell": {
                "bond_id": "127027",
                "bond_nm": "靖远转债",
            }},
        {
            "id": "113616",
            "cell": {
                "bond_id": "113616",
                "bond_nm": "韦尔转债",
            }},
        {
            "id": "110056",
            "cell": {
                "bond_id": "110056",
                "bond_nm": "亨通转债",
            }},
        {
            "id": "113033",
            "cell": {
                "bond_id": "113033",
                "bond_nm": "利群转债",
            }},
        {
            "id": "110070",
            "cell": {
                "bond_id": "110070",
                "bond_nm": "凌钢转债",
            }},
        {
            "id": "113628",
            "cell": {
                "bond_id": "113628",
                "bond_nm": "晨丰转债",
            }},
        {
            "id": "113502",
            "cell": {
                "bond_id": "113502",
                "bond_nm": "嘉澳转债",
            }},
        {
            "id": "110053",
            "cell": {
                "bond_id": "110053",
                "bond_nm": "苏银转债",
            }},
        {
            "id": "123061",
            "cell": {
                "bond_id": "123061",
                "bond_nm": "航新转债",
            }},
        {
            "id": "113047",
            "cell": {
                "bond_id": "113047",
                "bond_nm": "旗滨转债",
            }},
        {
            "id": "128074",
            "cell": {
                "bond_id": "128074",
                "bond_nm": "游族转债",
            }},
        {
            "id": "128037",
            "cell": {
                "bond_id": "128037",
                "bond_nm": "岩土转债",
            }},
        {
            "id": "127036",
            "cell": {
                "bond_id": "127036",
                "bond_nm": "三花转债",
            }},
        {
            "id": "128033",
            "cell": {
                "bond_id": "128033",
                "bond_nm": "迪龙转债",
            }},
        {
            "id": "127039",
            "cell": {
                "bond_id": "127039",
                "bond_nm": "北港转债",
            }},
        {
            "id": "110080",
            "cell": {
                "bond_id": "110080",
                "bond_nm": "东湖转债",
            }},
        {
            "id": "113546",
            "cell": {
                "bond_id": "113546",
                "bond_nm": "迪贝转债",
            }},
        {
            "id": "123062",
            "cell": {
                "bond_id": "123062",
                "bond_nm": "三超转债",
            }},
        {
            "id": "113024",
            "cell": {
                "bond_id": "113024",
                "bond_nm": "核建转债",
            }},
        {
            "id": "127037",
            "cell": {
                "bond_id": "127037",
                "bond_nm": "银轮转债",
            }},
        {
            "id": "123125",
            "cell": {
                "bond_id": "123125",
                "bond_nm": "元力转债",
            }},
        {
            "id": "127018",
            "cell": {
                "bond_id": "127018",
                "bond_nm": "本钢转债",
            }},
        {
            "id": "128133",
            "cell": {
                "bond_id": "128133",
                "bond_nm": "奇正转债",
            }},
        {
            "id": "113516",
            "cell": {
                "bond_id": "113516",
                "bond_nm": "苏农转债",
            }},
        {
            "id": "113598",
            "cell": {
                "bond_id": "113598",
                "bond_nm": "法兰转债",
            }},
        {
            "id": "123105",
            "cell": {
                "bond_id": "123105",
                "bond_nm": "拓尔转债",
            }},
        {
            "id": "128053",
            "cell": {
                "bond_id": "128053",
                "bond_nm": "尚荣转债",
            }},
        {
            "id": "127014",
            "cell": {
                "bond_id": "127014",
                "bond_nm": "北方转债",
            }},
        {
            "id": "113630",
            "cell": {
                "bond_id": "113630",
                "bond_nm": "赛伍转债",
            }},
        {
            "id": "110045",
            "cell": {
                "bond_id": "110045",
                "bond_nm": "海澜转债",
            }},
        {
            "id": "118001",
            "cell": {
                "bond_id": "118001",
                "bond_nm": "金博转债",
            }},
        {
            "id": "113050",
            "cell": {
                "bond_id": "113050",
                "bond_nm": "南银转债",
            }},
        {
            "id": "123075",
            "cell": {
                "bond_id": "123075",
                "bond_nm": "贝斯转债",
            }},
        {
            "id": "123106",
            "cell": {
                "bond_id": "123106",
                "bond_nm": "正丹转债",
            }},
        {
            "id": "113013",
            "cell": {
                "bond_id": "113013",
                "bond_nm": "国君转债",
            }},
        {
            "id": "123038",
            "cell": {
                "bond_id": "123038",
                "bond_nm": "联得转债",
            }},
        {
            "id": "110060",
            "cell": {
                "bond_id": "110060",
                "bond_nm": "天路转债",
            }},
        {
            "id": "113601",
            "cell": {
                "bond_id": "113601",
                "bond_nm": "塞力转债",
            }},
        {
            "id": "123082",
            "cell": {
                "bond_id": "123082",
                "bond_nm": "北陆转债",
            }},
        {
            "id": "123002",
            "cell": {
                "bond_id": "123002",
                "bond_nm": "国祯转债",
            }},
        {
            "id": "128042",
            "cell": {
                "bond_id": "128042",
                "bond_nm": "凯中转债",
            }},
        {
            "id": "123107",
            "cell": {
                "bond_id": "123107",
                "bond_nm": "温氏转债",
            }},
        {
            "id": "127024",
            "cell": {
                "bond_id": "127024",
                "bond_nm": "盈峰转债",
            }},
        {
            "id": "123014",
            "cell": {
                "bond_id": "123014",
                "bond_nm": "凯发转债",
            }},
        {
            "id": "127003",
            "cell": {
                "bond_id": "127003",
                "bond_nm": "海印转债",
            }},
        {
            "id": "113037",
            "cell": {
                "bond_id": "113037",
                "bond_nm": "紫银转债",
            }},
        {
            "id": "113524",
            "cell": {
                "bond_id": "113524",
                "bond_nm": "奇精转债",
            }},
        {
            "id": "128039",
            "cell": {
                "bond_id": "128039",
                "bond_nm": "三力转债",
            }},
        {
            "id": "123088",
            "cell": {
                "bond_id": "123088",
                "bond_nm": "威唐转债",
            }},
        {
            "id": "127022",
            "cell": {
                "bond_id": "127022",
                "bond_nm": "恒逸转债",
            }},
        {
            "id": "128021",
            "cell": {
                "bond_id": "128021",
                "bond_nm": "兄弟转债",
            }},
        {
            "id": "128120",
            "cell": {
                "bond_id": "128120",
                "bond_nm": "联诚转债",
            }},
        {
            "id": "127032",
            "cell": {
                "bond_id": "127032",
                "bond_nm": "苏行转债",
            }},
        {
            "id": "127012",
            "cell": {
                "bond_id": "127012",
                "bond_nm": "招路转债",
            }},
        {
            "id": "123054",
            "cell": {
                "bond_id": "123054",
                "bond_nm": "思特转债",
            }},
        {
            "id": "128127",
            "cell": {
                "bond_id": "128127",
                "bond_nm": "文科转债",
            }},
        {
            "id": "123116",
            "cell": {
                "bond_id": "123116",
                "bond_nm": "万兴转债",
            }},
        {
            "id": "110082",
            "cell": {
                "bond_id": "110082",
                "bond_nm": "宏发转债",
            }},
        {
            "id": "113046",
            "cell": {
                "bond_id": "113046",
                "bond_nm": "金田转债",
            }},
        {
            "id": "127034",
            "cell": {
                "bond_id": "127034",
                "bond_nm": "绿茵转债",
            }},
        {
            "id": "128071",
            "cell": {
                "bond_id": "128071",
                "bond_nm": "合兴转债",
            }},
        {
            "id": "128063",
            "cell": {
                "bond_id": "128063",
                "bond_nm": "未来转债",
            }},
        {
            "id": "110067",
            "cell": {
                "bond_id": "110067",
                "bond_nm": "华安转债",
            }},
        {
            "id": "113606",
            "cell": {
                "bond_id": "113606",
                "bond_nm": "荣泰转债",
            }},
        {
            "id": "113608",
            "cell": {
                "bond_id": "113608",
                "bond_nm": "威派转债",
            }},
        {
            "id": "113561",
            "cell": {
                "bond_id": "113561",
                "bond_nm": "正裕转债",
            }},
        {
            "id": "128056",
            "cell": {
                "bond_id": "128056",
                "bond_nm": "今飞转债",
            }},
        {
            "id": "127033",
            "cell": {
                "bond_id": "127033",
                "bond_nm": "中装转2",
            }},
        {
            "id": "110068",
            "cell": {
                "bond_id": "110068",
                "bond_nm": "龙净转债",
            }},
        {
            "id": "123059",
            "cell": {
                "bond_id": "123059",
                "bond_nm": "银信转债",
            }},
        {
            "id": "128108",
            "cell": {
                "bond_id": "128108",
                "bond_nm": "蓝帆转债",
            }},
        {
            "id": "127006",
            "cell": {
                "bond_id": "127006",
                "bond_nm": "敖东转债",
            }},
        {
            "id": "123023",
            "cell": {
                "bond_id": "123023",
                "bond_nm": "迪森转债",
            }},
        {
            "id": "113535",
            "cell": {
                "bond_id": "113535",
                "bond_nm": "大业转债",
            }},
        {
            "id": "113618",
            "cell": {
                "bond_id": "113618",
                "bond_nm": "美诺转债",
            }},
        {
            "id": "128122",
            "cell": {
                "bond_id": "128122",
                "bond_nm": "兴森转债",
            }},
        {
            "id": "110073",
            "cell": {
                "bond_id": "110073",
                "bond_nm": "国投转债",
            }},
        {
            "id": "128135",
            "cell": {
                "bond_id": "128135",
                "bond_nm": "洽洽转债",
            }},
        {
            "id": "123096",
            "cell": {
                "bond_id": "123096",
                "bond_nm": "思创转债",
            }},
        {
            "id": "128083",
            "cell": {
                "bond_id": "128083",
                "bond_nm": "新北转债",
            }},
        {
            "id": "128079",
            "cell": {
                "bond_id": "128079",
                "bond_nm": "英联转债",
            }},
        {
            "id": "128035",
            "cell": {
                "bond_id": "128035",
                "bond_nm": "大族转债",
            }},
        {
            "id": "128049",
            "cell": {
                "bond_id": "128049",
                "bond_nm": "华源转债",
            }},
        {
            "id": "123123",
            "cell": {
                "bond_id": "123123",
                "bond_nm": "江丰转债",
            }},
        {
            "id": "128023",
            "cell": {
                "bond_id": "128023",
                "bond_nm": "亚太转债",
            }},
        {
            "id": "110064",
            "cell": {
                "bond_id": "110064",
                "bond_nm": "建工转债",
            }},
        {
            "id": "123077",
            "cell": {
                "bond_id": "123077",
                "bond_nm": "汉得转债",
            }},
        {
            "id": "110034",
            "cell": {
                "bond_id": "110034",
                "bond_nm": "九州转债",
            }},
        {
            "id": "113532",
            "cell": {
                "bond_id": "113532",
                "bond_nm": "海环转债",
            }},
        {
            "id": "123049",
            "cell": {
                "bond_id": "123049",
                "bond_nm": "维尔转债",
            }},
        {
            "id": "127013",
            "cell": {
                "bond_id": "127013",
                "bond_nm": "创维转债",
            }},
        {
            "id": "127041",
            "cell": {
                "bond_id": "127041",
                "bond_nm": "弘亚转债",
            }},
        {
            "id": "123128",
            "cell": {
                "bond_id": "123128",
                "bond_nm": "首华转债",
            }},
        {
            "id": "123124",
            "cell": {
                "bond_id": "123124",
                "bond_nm": "晶瑞转2",
            }},
        {
            "id": "123010",
            "cell": {
                "bond_id": "123010",
                "bond_nm": "博世转债",
            }},
        {
            "id": "128131",
            "cell": {
                "bond_id": "128131",
                "bond_nm": "崇达转2",
            }},
        {
            "id": "113623",
            "cell": {
                "bond_id": "113623",
                "bond_nm": "凤21转债",
            }},
        {
            "id": "113036",
            "cell": {
                "bond_id": "113036",
                "bond_nm": "宁建转债",
            }},
        {
            "id": "127017",
            "cell": {
                "bond_id": "127017",
                "bond_nm": "万青转债",
            }},
        {
            "id": "113043",
            "cell": {
                "bond_id": "113043",
                "bond_nm": "财通转债",
            }},
        {
            "id": "110062",
            "cell": {
                "bond_id": "110062",
                "bond_nm": "烽火转债",
            }},
        {
            "id": "123004",
            "cell": {
                "bond_id": "123004",
                "bond_nm": "铁汉转债",
            }},
        {
            "id": "123104",
            "cell": {
                "bond_id": "123104",
                "bond_nm": "卫宁转债",
            }},
        {
            "id": "128116",
            "cell": {
                "bond_id": "128116",
                "bond_nm": "瑞达转债",
            }},
        {
            "id": "123122",
            "cell": {
                "bond_id": "123122",
                "bond_nm": "富瀚转债",
            }},
        {
            "id": "110038",
            "cell": {
                "bond_id": "110038",
                "bond_nm": "济川转债",
            }},
        {
            "id": "127025",
            "cell": {
                "bond_id": "127025",
                "bond_nm": "冀东转债",
            }},
        {
            "id": "123113",
            "cell": {
                "bond_id": "123113",
                "bond_nm": "仙乐转债",
            }},
        {
            "id": "127044",
            "cell": {
                "bond_id": "127044",
                "bond_nm": "蒙娜转债",
            }},
        {
            "id": "123126",
            "cell": {
                "bond_id": "123126",
                "bond_nm": "瑞丰转债",
            }},
        {
            "id": "132022",
            "cell": {
                "bond_id": "132022",
                "bond_nm": "20广版EB",
            }},
        {
            "id": "128036",
            "cell": {
                "bond_id": "128036",
                "bond_nm": "金农转债",
            }},
        {
            "id": "123090",
            "cell": {
                "bond_id": "123090",
                "bond_nm": "三诺转债",
            }},
        {
            "id": "127016",
            "cell": {
                "bond_id": "127016",
                "bond_nm": "鲁泰转债",
            }},
        {
            "id": "127046",
            "cell": {
                "bond_id": "127046",
                "bond_nm": "百润转债",
            }},
        {
            "id": "128105",
            "cell": {
                "bond_id": "128105",
                "bond_nm": "长集转债",
            }},
        {
            "id": "128142",
            "cell": {
                "bond_id": "128142",
                "bond_nm": "新乳转债",
            }},
        {
            "id": "123018",
            "cell": {
                "bond_id": "123018",
                "bond_nm": "溢利转债",
            }},
        {
            "id": "127031",
            "cell": {
                "bond_id": "127031",
                "bond_nm": "洋丰转债",
            }},
        {
            "id": "113042",
            "cell": {
                "bond_id": "113042",
                "bond_nm": "上银转债",
            }},
        {
            "id": "123039",
            "cell": {
                "bond_id": "123039",
                "bond_nm": "开润转债",
            }},
        {
            "id": "113530",
            "cell": {
                "bond_id": "113530",
                "bond_nm": "大丰转债",
            }},
        {
            "id": "128139",
            "cell": {
                "bond_id": "128139",
                "bond_nm": "祥鑫转债",
            }},
        {
            "id": "113045",
            "cell": {
                "bond_id": "113045",
                "bond_nm": "环旭转债",
            }},
        {
            "id": "110072",
            "cell": {
                "bond_id": "110072",
                "bond_nm": "广汇转债",
            }},
        {
            "id": "113622",
            "cell": {
                "bond_id": "113622",
                "bond_nm": "杭叉转债",
            }},
        {
            "id": "113624",
            "cell": {
                "bond_id": "113624",
                "bond_nm": "正川转债",
            }},
        {
            "id": "128022",
            "cell": {
                "bond_id": "128022",
                "bond_nm": "众信转债",
            }},
        {
            "id": "123034",
            "cell": {
                "bond_id": "123034",
                "bond_nm": "通光转债",
            }},
        {
            "id": "113620",
            "cell": {
                "bond_id": "113620",
                "bond_nm": "傲农转债",
            }},
        {
            "id": "123011",
            "cell": {
                "bond_id": "123011",
                "bond_nm": "德尔转债",
            }},
        {
            "id": "123108",
            "cell": {
                "bond_id": "123108",
                "bond_nm": "乐普转2",
            }},
        {
            "id": "127007",
            "cell": {
                "bond_id": "127007",
                "bond_nm": "湖广转债",
            }},
        {
            "id": "127015",
            "cell": {
                "bond_id": "127015",
                "bond_nm": "希望转债",
            }},
        {
            "id": "128114",
            "cell": {
                "bond_id": "128114",
                "bond_nm": "正邦转债",
            }},
        {
            "id": "128026",
            "cell": {
                "bond_id": "128026",
                "bond_nm": "众兴转债",
            }},
        {
            "id": "128124",
            "cell": {
                "bond_id": "128124",
                "bond_nm": "科华转债",
            }},
        {
            "id": "128123",
            "cell": {
                "bond_id": "128123",
                "bond_nm": "国光转债",
            }},
        {
            "id": "113021",
            "cell": {
                "bond_id": "113021",
                "bond_nm": "中信转债",
            }},
        {
            "id": "113566",
            "cell": {
                "bond_id": "113566",
                "bond_nm": "翔港转债",
            }},
        {
            "id": "113563",
            "cell": {
                "bond_id": "113563",
                "bond_nm": "柳药转债",
            }},
        {
            "id": "128014",
            "cell": {
                "bond_id": "128014",
                "bond_nm": "永东转债",
            }},
        {
            "id": "113542",
            "cell": {
                "bond_id": "113542",
                "bond_nm": "好客转债",
            }},
        {
            "id": "123044",
            "cell": {
                "bond_id": "123044",
                "bond_nm": "红相转债",
            }},
        {
            "id": "113578",
            "cell": {
                "bond_id": "113578",
                "bond_nm": "全筑转债",
            }},
        {
            "id": "123119",
            "cell": {
                "bond_id": "123119",
                "bond_nm": "康泰转2",
            }},
        {
            "id": "128069",
            "cell": {
                "bond_id": "128069",
                "bond_nm": "华森转债",
            }},
        {
            "id": "127019",
            "cell": {
                "bond_id": "127019",
                "bond_nm": "国城转债",
            }},
        {
            "id": "123076",
            "cell": {
                "bond_id": "123076",
                "bond_nm": "强力转债",
            }},
        {
            "id": "113017",
            "cell": {
                "bond_id": "113017",
                "bond_nm": "吉视转债",
            }},
        {
            "id": "128030",
            "cell": {
                "bond_id": "128030",
                "bond_nm": "天康转债",
            }},
        {
            "id": "128015",
            "cell": {
                "bond_id": "128015",
                "bond_nm": "久其转债",
            }},
        {
            "id": "128136",
            "cell": {
                "bond_id": "128136",
                "bond_nm": "立讯转债",
            }},
        {
            "id": "132009",
            "cell": {
                "bond_id": "132009",
                "bond_nm": "17中油EB",
            }},
        {
            "id": "128070",
            "cell": {
                "bond_id": "128070",
                "bond_nm": "智能转债",
            }},
        {
            "id": "110059",
            "cell": {
                "bond_id": "110059",
                "bond_nm": "浦发转债",
            }},
        {
            "id": "113604",
            "cell": {
                "bond_id": "113604",
                "bond_nm": "多伦转债",
            }},
        {
            "id": "128132",
            "cell": {
                "bond_id": "128132",
                "bond_nm": "交建转债",
            }},
        {
            "id": "123056",
            "cell": {
                "bond_id": "123056",
                "bond_nm": "雪榕转债",
            }},
        {
            "id": "113627",
            "cell": {
                "bond_id": "113627",
                "bond_nm": "太平转债",
            }},
        {
            "id": "128044",
            "cell": {
                "bond_id": "128044",
                "bond_nm": "岭南转债",
            }},
        {
            "id": "128072",
            "cell": {
                "bond_id": "128072",
                "bond_nm": "翔鹭转债",
            }},
        {
            "id": "132015",
            "cell": {
                "bond_id": "132015",
                "bond_nm": "18中油EB",
            }},
        {
            "id": "110052",
            "cell": {
                "bond_id": "110052",
                "bond_nm": "贵广转债",
            }},
        {
            "id": "113575",
            "cell": {
                "bond_id": "113575",
                "bond_nm": "东时转债",
            }},
        {
            "id": "110076",
            "cell": {
                "bond_id": "110076",
                "bond_nm": "华海转债",
            }},
        {
            "id": "113519",
            "cell": {
                "bond_id": "113519",
                "bond_nm": "长久转债",
            }},
        {
            "id": "128118",
            "cell": {
                "bond_id": "128118",
                "bond_nm": "瀛通转债",
            }},
        {
            "id": "123101",
            "cell": {
                "bond_id": "123101",
                "bond_nm": "拓斯转债",
            }},
        {
            "id": "128125",
            "cell": {
                "bond_id": "128125",
                "bond_nm": "华阳转债",
            }},
        {
            "id": "113597",
            "cell": {
                "bond_id": "113597",
                "bond_nm": "佳力转债",
            }},
        {
            "id": "128138",
            "cell": {
                "bond_id": "128138",
                "bond_nm": "侨银转债",
            }},
        {
            "id": "123072",
            "cell": {
                "bond_id": "123072",
                "bond_nm": "乐歌转债",
            }},
        {
            "id": "113625",
            "cell": {
                "bond_id": "113625",
                "bond_nm": "江山转债",
            }},
        {
            "id": "123117",
            "cell": {
                "bond_id": "123117",
                "bond_nm": "健帆转债",
            }},
        {
            "id": "113594",
            "cell": {
                "bond_id": "113594",
                "bond_nm": "淳中转债",
            }},
        {
            "id": "123093",
            "cell": {
                "bond_id": "123093",
                "bond_nm": "金陵转债",
            }},
        {
            "id": "113573",
            "cell": {
                "bond_id": "113573",
                "bond_nm": "纵横转债",
            }},
        {
            "id": "128117",
            "cell": {
                "bond_id": "128117",
                "bond_nm": "道恩转债",
            }},
        {
            "id": "127021",
            "cell": {
                "bond_id": "127021",
                "bond_nm": "特发转2",
            }},
        {
            "id": "123064",
            "cell": {
                "bond_id": "123064",
                "bond_nm": "万孚转债",
            }},
        {
            "id": "113605",
            "cell": {
                "bond_id": "113605",
                "bond_nm": "大参转债",
            }},
        {
            "id": "113589",
            "cell": {
                "bond_id": "113589",
                "bond_nm": "天创转债",
            }},
        {
            "id": "113595",
            "cell": {
                "bond_id": "113595",
                "bond_nm": "花王转债",
            }},
        {
            "id": "113526",
            "cell": {
                "bond_id": "113526",
                "bond_nm": "联泰转债",
            }},
        {
            "id": "113569",
            "cell": {
                "bond_id": "113569",
                "bond_nm": "科达转债",
            }},
        {
            "id": "127004",
            "cell": {
                "bond_id": "127004",
                "bond_nm": "模塑转债",
            }},
        {
            "id": "123065",
            "cell": {
                "bond_id": "123065",
                "bond_nm": "宝莱转债",
            }},
        {
            "id": "113584",
            "cell": {
                "bond_id": "113584",
                "bond_nm": "家悦转债",
            }},
        {
            "id": "110044",
            "cell": {
                "bond_id": "110044",
                "bond_nm": "广电转债",
            }},
        {
            "id": "113574",
            "cell": {
                "bond_id": "113574",
                "bond_nm": "华体转债",
            }},
        {
            "id": "128041",
            "cell": {
                "bond_id": "128041",
                "bond_nm": "盛路转债",
            }},
        {
            "id": "113576",
            "cell": {
                "bond_id": "113576",
                "bond_nm": "起步转债",
            }},
        {
            "id": "113596",
            "cell": {
                "bond_id": "113596",
                "bond_nm": "城地转债",
            }},
        {
            "id": "132011",
            "cell": {
                "bond_id": "132011",
                "bond_nm": "17浙报EB",
            }},
        {
            "id": "128062",
            "cell": {
                "bond_id": "128062",
                "bond_nm": "亚药转债",
            }},
        {
            "id": "123013",
            "cell": {
                "bond_id": "123013",
                "bond_nm": "横河转债",
            }},
        {
            "id": "123015",
            "cell": {
                "bond_id": "123015",
                "bond_nm": "蓝盾转债",
            }}
    ],
    "total": 389
}


def do_set_bond_nm_delisted(list_data):
    rows = list_data['rows']
    size = len(rows)
    i = 0
    for row in rows:
        cell = row['cell']
        with db_utils.get_daily_connect() as con:
            cur = con.cursor()
            result = cur.execute(
                """update cb_history set bond_nm=:bond_nm where bond_id=:bond_id""",
                {"bond_id": cell["bond_id"], "bond_nm": cell["bond_nm"]})
            if result.rowcount < 1:
                print('update db_history is failure. row:' + cell['bond_nm'] + ", " + cell["bond_id"])
            else:
                i += 1

        print("update complete:" + str(i) + "/" + str(size))


# 添加退市日期
def set_delist_dt():
    rows = delisted_data['rows']
    for row in rows:
        cell = row['cell']
        err_row = cell
        try:
            i = 0
            with db_utils.get_daily_connect() as con:
                cur = con.cursor()
                result = cur.execute(
                    """update cb_enforce set delist_dt=:delist_dt where bond_id=:bond_id""",
                    {"bond_id": cell["bond_id"], "delist_dt": datetime.strptime(cell['delist_dt'], '%Y-%m-%d')})
                if result.rowcount != 1:
                    print('update cb_enforce is failure. row:' + cell['bond_id'])
                else:
                    i += 1

            print("update bond_id:" + str(cell["bond_id"]) + " is complete. count:" + str(i))

        except Exception as e:
            print("db操作出现异常. err_row" + str(err_row), e)
            raise e


# 添加退市日期
def insert_delist_data():
    rows = delisted_data['rows']
    for row in rows:
        cell = row['cell']
        i = 0
        bond_id = cell["bond_id"]
        with db_utils.get_daily_connect() as con:
            cur = con.cursor()

            cur.execute("""select * from cb_enforce where bond_id = :bond_id""",
                        {"bond_id": bond_id})
            one = cur.fetchone()
            if one is not None:
                print('row:' + str(cell) + " has existed.")
                continue

            if cell.get('delist_dt') is None:
                print("data is error. cell:" + str(cell))
                continue

            result = cur.execute(
                """insert into cb_enforce (bond_id, bond_name, delist_dt)values (:bond_id, :bond_name, :delist_dt)""",
                {"bond_id": bond_id, "bond_name": cell["bond_nm"],
                 "delist_dt": datetime.strptime(cell['delist_dt'], '%Y-%m-%d')})
            if result.rowcount != 1:
                print('insert cb_enforce is failure. row:' + str(cell))
            else:
                i += 1

        print("insert bond_id:" + str(bond_id) + " is complete. count:" + str(i))


def insert_db(rows):
    if len(rows) == 0:
        return

    err_row = None
    try:
        i = 0
        with db_utils.get_daily_connect() as con:
            cur = con.cursor()
            for row in rows:
                # 过滤掉可交换债
                if row.get("price") is None or row.get("price") == 0 or 'EB' in row["bond_nm"]:
                    continue

                err_row = row
                result = cur.execute(
                    """insert into cb_history(bond_id, bond_nm, last_chg_dt, ytm_rt, premium_rt, convert_value, price, volume, stock_volume, curr_iss_amt, amt_change, turnover_rt) 
                    values(:bond_id, :bond_nm, :last_chg_dt, :ytm_rt, :premium_rt, :convert_value, :price, :volume, :stock_volume, :curr_iss_amt, :amt_change, :turnover_rt)""",
                    {"bond_id": row["bond_id"], "bond_nm": row["bond_nm"], "last_chg_dt": row["last_chg_dt"], "ytm_rt": row.get("ytm_rt"),
                     "premium_rt": row.get("premium_rt"), "convert_value": row.get("convert_value"),
                     "price": row.get("price"),
                     "volume": row.get("volume"), "stock_volume": row.get("stock_volume"),
                     "curr_iss_amt": row.get("curr_iss_amt"),
                     "amt_change": row.get("amt_change"), "turnover_rt": row.get("turnover_rt")})
                if result.rowcount != 1:
                    print('insert db_history is failure. row:' + row['last_chg_dt'])
                else:
                    i += 1

        print("insert bond_id:" + str(row["bond_id"]) + " is complete. count:" + str(i))

    except Exception as e:
        print("db操作出现异常. err_row" + str(err_row), e)
        raise e


def fetch_data():
    # do_fetch_data_delisted()
    do_fetch_data()
    # set_delist_dt()
    # do_set_bond_nm_delisted(cb_list_new)
    # insert_delist_data()
    return 'OK'


if __name__ == "__main__":
    fetch_data()

    print("可转债数据抓取更新完成")

# 抓取宁稳网的数据(每天中午, 下午收盘更新, 非实时, 但是最全)


from datetime import datetime
import json
import re
import time
from itertools import product

import bs4
import requests
from pypinyin import pinyin, Style

from utils import db_utils
from utils.db_utils import get_cursor
from utils.trade_utils import get_trade_date

header = {
    "Referer": "http://www.ninwin.cn/index.php?m=profile",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    # 'Cookie': "csrf_token=8919ea04925831e8; __51cke__=; P0s_winduser=RaqSRnBfFwDoLZv5tGFqXXLD4fXwVZQynHEOTJOsq1fzXIiXiCJW%2FWYIGis%3D; P0s_cbQuestion=1; __tins__4771153=%7B%22sid%22%3A%201631088120422%2C%20%22vd%22%3A%207%2C%20%22expires%22%3A%201631089976917%7D; __51laig__=234; PHPSESSID=jpl3tag9rff4l4mtdndsm36n44; P0s_visitor=Ncd58ncEEFs83Y9d2knG3OnEWpLyZm3YRPK8yFD6ja5fvV52; P0s_lastvisit=242%091631159109%09%2Findex.php%3Fm%3DmyAdmin%26c%3Dlog"
}


def get_cb_delist_json():
    return [
        {
            "data_id": "449",
            "cb_num_id": "1",
            "cb_name_id": "康隆转债",
            "bond_code": "113580",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "613",
            "cb_num_id": "2",
            "cb_name_id": "华自转债",
            "bond_code": "123102",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "538",
            "cb_num_id": "3",
            "cb_name_id": "金诺转债",
            "bond_code": "123069",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "50",
            "cb_num_id": "5",
            "cb_name_id": "国贸转债",
            "bond_code": "110033",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "102",
            "cb_num_id": "6",
            "cb_name_id": "蒙电转债",
            "bond_code": "110041",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "77",
            "cb_num_id": "8",
            "cb_name_id": "时达转债",
            "bond_code": "128018",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "362",
            "cb_num_id": "9",
            "cb_name_id": "19华菱EB",
            "bond_code": "120003",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "399",
            "cb_num_id": "10",
            "cb_name_id": "20华菱EB",
            "bond_code": "120004",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "428",
            "cb_num_id": "11",
            "cb_name_id": "久吾转债",
            "bond_code": "123047",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "458",
            "cb_num_id": "12",
            "cb_name_id": "今天转债",
            "bond_code": "123051",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "537",
            "cb_num_id": "13",
            "cb_name_id": "弘信转债",
            "bond_code": "123068",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "73",
            "cb_num_id": "14",
            "cb_name_id": "林洋转债",
            "bond_code": "113014",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "421",
            "cb_num_id": "15",
            "cb_name_id": "三祥转债",
            "bond_code": "113572",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "334",
            "cb_num_id": "16",
            "cb_name_id": "九洲转债",
            "bond_code": "123030",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "573",
            "cb_num_id": "17",
            "cb_name_id": "永冠转债",
            "bond_code": "113612",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "566",
            "cb_num_id": "18",
            "cb_name_id": "运达转债",
            "bond_code": "123079",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "179",
            "cb_num_id": "19",
            "cb_name_id": "光华转债",
            "bond_code": "128051",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "598",
            "cb_num_id": "20",
            "cb_name_id": "星源转2",
            "bond_code": "123094",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "64",
            "cb_num_id": "21",
            "cb_name_id": "骆驼转债",
            "bond_code": "113012",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "124",
            "cb_num_id": "22",
            "cb_name_id": "新凤转债",
            "bond_code": "113508",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "353",
            "cb_num_id": "23",
            "cb_name_id": "金力转债",
            "bond_code": "123033",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "300",
            "cb_num_id": "24",
            "cb_name_id": "司尔转债",
            "bond_code": "128064",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "125",
            "cb_num_id": "25",
            "cb_name_id": "新泉转债",
            "bond_code": "113509",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "530",
            "cb_num_id": "26",
            "cb_name_id": "赛意转债",
            "bond_code": "123066",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "106",
            "cb_num_id": "27",
            "cb_name_id": "道氏转债",
            "bond_code": "123007",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "544",
            "cb_num_id": "28",
            "cb_name_id": "星宇转债",
            "bond_code": "113040",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "568",
            "cb_num_id": "29",
            "cb_name_id": "福20转债",
            "bond_code": "113611",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "101",
            "cb_num_id": "30",
            "cb_name_id": "双环转债",
            "bond_code": "128032",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "546",
            "cb_num_id": "31",
            "cb_name_id": "华菱转2",
            "bond_code": "127023",
            "cb_delist_cause_id": "涨超125强赎"
        },
        {
            "data_id": "330",
            "cb_num_id": "32",
            "cb_name_id": "欧派转债",
            "bond_code": "113543",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "488",
            "cb_num_id": "33",
            "cb_name_id": "欣旺转债",
            "bond_code": "123058",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "384",
            "cb_num_id": "34",
            "cb_name_id": "淮矿转债",
            "bond_code": "110065",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "332",
            "cb_num_id": "35",
            "cb_name_id": "英科转债",
            "bond_code": "123029",
            "cb_delist_cause_id": "最低规模强赎"
        },
        {
            "data_id": "382",
            "cb_num_id": "36",
            "cb_name_id": "永创转债",
            "bond_code": "113559",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "553",
            "cb_num_id": "37",
            "cb_name_id": "紫金转债",
            "bond_code": "113041",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "408",
            "cb_num_id": "40",
            "cb_name_id": "天目转债",
            "bond_code": "113564",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "514",
            "cb_num_id": "41",
            "cb_name_id": "赣锋转2",
            "bond_code": "128126",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "377",
            "cb_num_id": "42",
            "cb_name_id": "森特转债",
            "bond_code": "113557",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "433",
            "cb_num_id": "43",
            "cb_name_id": "瀚蓝转债",
            "bond_code": "110069",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "512",
            "cb_num_id": "44",
            "cb_name_id": "隆20转债",
            "bond_code": "113038",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "185",
            "cb_num_id": "45",
            "cb_name_id": "凯龙转债",
            "bond_code": "128052",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "371",
            "cb_num_id": "46",
            "cb_name_id": "明阳转债",
            "bond_code": "113029",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "98",
            "cb_num_id": "47",
            "cb_name_id": "赣锋转债",
            "bond_code": "128028",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "477",
            "cb_num_id": "48",
            "cb_name_id": "海容转债",
            "bond_code": "113590",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "485",
            "cb_num_id": "49",
            "cb_name_id": "安20转债",
            "bond_code": "113592",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "169",
            "cb_num_id": "50",
            "cb_name_id": "特发转债",
            "bond_code": "127008",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "456",
            "cb_num_id": "51",
            "cb_name_id": "益丰转债",
            "bond_code": "113583",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "468",
            "cb_num_id": "52",
            "cb_name_id": "歌尔转2",
            "bond_code": "128112",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "307",
            "cb_num_id": "53",
            "cb_name_id": "雅化转债",
            "bond_code": "128065",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "53",
            "cb_num_id": "54",
            "cb_name_id": "蔚蓝转债",
            "bond_code": "128010",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "472",
            "cb_num_id": "55",
            "cb_name_id": "晨光转债",
            "bond_code": "123055",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "172",
            "cb_num_id": "56",
            "cb_name_id": "寒锐转债",
            "bond_code": "123017",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "474",
            "cb_num_id": "57",
            "cb_name_id": "巨星转债",
            "bond_code": "128115",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "465",
            "cb_num_id": "58",
            "cb_name_id": "永兴转债",
            "bond_code": "128110",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "469",
            "cb_num_id": "59",
            "cb_name_id": "泛微转债",
            "bond_code": "113587",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "454",
            "cb_num_id": "60",
            "cb_name_id": "福莱转债",
            "bond_code": "113035",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "380",
            "cb_num_id": "61",
            "cb_name_id": "至纯转债",
            "bond_code": "113556",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "463",
            "cb_num_id": "62",
            "cb_name_id": "上机转债",
            "bond_code": "113586",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "410",
            "cb_num_id": "64",
            "cb_name_id": "桐20转债",
            "bond_code": "113032",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "78",
            "cb_num_id": "65",
            "cb_name_id": "久立转2",
            "bond_code": "128019",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "166",
            "cb_num_id": "66",
            "cb_name_id": "百合转债",
            "bond_code": "113520",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "434",
            "cb_num_id": "67",
            "cb_name_id": "裕同转债",
            "bond_code": "128104",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "426",
            "cb_num_id": "68",
            "cb_name_id": "海大转债",
            "bond_code": "128102",
            "cb_delist_cause_id": "涨超120强赎"
        },
        {
            "data_id": "394",
            "cb_num_id": "69",
            "cb_name_id": "璞泰转债",
            "bond_code": "113562",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "316",
            "cb_num_id": "70",
            "cb_name_id": "中环转债",
            "bond_code": "123026",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "451",
            "cb_num_id": "71",
            "cb_name_id": "龙蟠转债",
            "bond_code": "113581",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "367",
            "cb_num_id": "72",
            "cb_name_id": "先导转债",
            "bond_code": "123036",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "370",
            "cb_num_id": "74",
            "cb_name_id": "金牌转债",
            "bond_code": "113553",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "379",
            "cb_num_id": "75",
            "cb_name_id": "振德转债",
            "bond_code": "113555",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "340",
            "cb_num_id": "76",
            "cb_name_id": "万里转债",
            "bond_code": "123032",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "168",
            "cb_num_id": "77",
            "cb_name_id": "科森转债",
            "bond_code": "113521",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "170",
            "cb_num_id": "78",
            "cb_name_id": "桐昆转债",
            "bond_code": "113020",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "275",
            "cb_num_id": "79",
            "cb_name_id": "拓邦转债",
            "bond_code": "128058",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "418",
            "cb_num_id": "81",
            "cb_name_id": "永高转债",
            "bond_code": "128099",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "422",
            "cb_num_id": "82",
            "cb_name_id": "博特转债",
            "bond_code": "113571",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "413",
            "cb_num_id": "83",
            "cb_name_id": "康弘转债",
            "bond_code": "128098",
            "cb_delist_cause_id": "涨超125强赎"
        },
        {
            "data_id": "310",
            "cb_num_id": "84",
            "cb_name_id": "一心转债",
            "bond_code": "128067",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "155",
            "cb_num_id": "85",
            "cb_name_id": "东音转债",
            "bond_code": "128043",
            "cb_delist_cause_id": "最低规模强赎"
        },
        {
            "data_id": "320",
            "cb_num_id": "86",
            "cb_name_id": "环境转债",
            "bond_code": "113028",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "337",
            "cb_num_id": "87",
            "cb_name_id": "桃李转债",
            "bond_code": "113544",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "391",
            "cb_num_id": "88",
            "cb_name_id": "唐人转债",
            "bond_code": "128092",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "348",
            "cb_num_id": "89",
            "cb_name_id": "索发转债",
            "bond_code": "113547",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "372",
            "cb_num_id": "90",
            "cb_name_id": "木森转债",
            "bond_code": "128084",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "373",
            "cb_num_id": "91",
            "cb_name_id": "仙鹤转债",
            "bond_code": "113554",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "378",
            "cb_num_id": "92",
            "cb_name_id": "新莱转债",
            "bond_code": "123037",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "103",
            "cb_num_id": "93",
            "cb_name_id": "航电转债",
            "bond_code": "110042",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "111",
            "cb_num_id": "94",
            "cb_name_id": "玲珑转债",
            "bond_code": "113019",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "270",
            "cb_num_id": "95",
            "cb_name_id": "富祥转债",
            "bond_code": "123020",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "140",
            "cb_num_id": "97",
            "cb_name_id": "威帝转债",
            "bond_code": "113514",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "398",
            "cb_num_id": "98",
            "cb_name_id": "博威转债",
            "bond_code": "113031",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "160",
            "cb_num_id": "99",
            "cb_name_id": "机电转债",
            "bond_code": "128045",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "161",
            "cb_num_id": "100",
            "cb_name_id": "顾家转债",
            "bond_code": "113518",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "375",
            "cb_num_id": "101",
            "cb_name_id": "国轩转债",
            "bond_code": "128086",
            "cb_delist_cause_id": "涨超125强赎"
        },
        {
            "data_id": "400",
            "cb_num_id": "102",
            "cb_name_id": "东财转2",
            "bond_code": "123041",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "279",
            "cb_num_id": "103",
            "cb_name_id": "浙商转债",
            "bond_code": "113022",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "386",
            "cb_num_id": "104",
            "cb_name_id": "深南转债",
            "bond_code": "128088",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "396",
            "cb_num_id": "105",
            "cb_name_id": "乐普转债",
            "bond_code": "123040",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "383",
            "cb_num_id": "106",
            "cb_name_id": "日月转债",
            "bond_code": "113558",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "389",
            "cb_num_id": "107",
            "cb_name_id": "麦米转债",
            "bond_code": "128089",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "277",
            "cb_num_id": "108",
            "cb_name_id": "视源转债",
            "bond_code": "128059",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "364",
            "cb_num_id": "109",
            "cb_name_id": "克来转债",
            "bond_code": "113552",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "359",
            "cb_num_id": "110",
            "cb_name_id": "顺丰转债",
            "bond_code": "128080",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "360",
            "cb_num_id": "111",
            "cb_name_id": "福特转债",
            "bond_code": "113551",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "343",
            "cb_num_id": "112",
            "cb_name_id": "华夏转债",
            "bond_code": "128077",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "254",
            "cb_num_id": "113",
            "cb_name_id": "中宠转债",
            "bond_code": "128054",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "142",
            "cb_num_id": "114",
            "cb_name_id": "高能转债",
            "bond_code": "113515",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "131",
            "cb_num_id": "115",
            "cb_name_id": "千禾转债",
            "bond_code": "113511",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "93",
            "cb_num_id": "116",
            "cb_name_id": "泰晶转债",
            "bond_code": "113503",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "293",
            "cb_num_id": "117",
            "cb_name_id": "百姓转债",
            "bond_code": "113531",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "272",
            "cb_num_id": "119",
            "cb_name_id": "万信转 2",
            "bond_code": "123021",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "183",
            "cb_num_id": "120",
            "cb_name_id": "佳都转债",
            "bond_code": "110050",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "266",
            "cb_num_id": "121",
            "cb_name_id": "长青转 2",
            "bond_code": "128055",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "156",
            "cb_num_id": "122",
            "cb_name_id": "曙光转债",
            "bond_code": "113517",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "72",
            "cb_num_id": "123",
            "cb_name_id": "雨虹转债",
            "bond_code": "128016",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "265",
            "cb_num_id": "124",
            "cb_name_id": "中来转债",
            "bond_code": "123019",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "130",
            "cb_num_id": "125",
            "cb_name_id": "再升转债",
            "bond_code": "113510",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "327",
            "cb_num_id": "126",
            "cb_name_id": "南威转债",
            "bond_code": "113540",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "171",
            "cb_num_id": "127",
            "cb_name_id": "圆通转债",
            "bond_code": "110046",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "116",
            "cb_num_id": "128",
            "cb_name_id": "星源转债",
            "bond_code": "123009",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "120",
            "cb_num_id": "129",
            "cb_name_id": "利欧转债",
            "bond_code": "128038",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "283",
            "cb_num_id": "130",
            "cb_name_id": "通威转债",
            "bond_code": "110054",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "165",
            "cb_num_id": "131",
            "cb_name_id": "洲明转债",
            "bond_code": "123016",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "325",
            "cb_num_id": "132",
            "cb_name_id": "圣达转债",
            "bond_code": "113539",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "291",
            "cb_num_id": "133",
            "cb_name_id": "启明转债",
            "bond_code": "128061",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "174",
            "cb_num_id": "134",
            "cb_name_id": "旭升转债",
            "bond_code": "113522",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "323",
            "cb_num_id": "135",
            "cb_name_id": "安图转债",
            "bond_code": "113538",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "289",
            "cb_num_id": "136",
            "cb_name_id": "中装转债",
            "bond_code": "128060",
            "cb_delist_cause_id": "最低规模强赎"
        },
        {
            "data_id": "91",
            "cb_num_id": "137",
            "cb_name_id": "蓝思转债",
            "bond_code": "123003",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "177",
            "cb_num_id": "138",
            "cb_name_id": "伟明转债",
            "bond_code": "113523",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "315",
            "cb_num_id": "139",
            "cb_name_id": "和而转债",
            "bond_code": "128068",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "82",
            "cb_num_id": "140",
            "cb_name_id": "水晶转债",
            "bond_code": "128020",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "297",
            "cb_num_id": "141",
            "cb_name_id": "参林转债",
            "bond_code": "113533",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "182",
            "cb_num_id": "142",
            "cb_name_id": "海尔转债",
            "bond_code": "110049",
            "cb_delist_cause_id": "涨超120强赎"
        },
        {
            "data_id": "278",
            "cb_num_id": "144",
            "cb_name_id": "绝味转债",
            "bond_code": "113529",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "123",
            "cb_num_id": "145",
            "cb_name_id": "天马转债",
            "bond_code": "113507",
            "cb_delist_cause_id": "最低规模强赎"
        },
        {
            "data_id": "163",
            "cb_num_id": "146",
            "cb_name_id": "光电转债",
            "bond_code": "128047",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "186",
            "cb_num_id": "147",
            "cb_name_id": "冰轮转债",
            "bond_code": "127009",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "48",
            "cb_num_id": "148",
            "cb_name_id": "蓝标转债",
            "bond_code": "123001",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "94",
            "cb_num_id": "149",
            "cb_name_id": "崇达转债",
            "bond_code": "128027",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "187",
            "cb_num_id": "150",
            "cb_name_id": "平银转债",
            "bond_code": "127010",
            "cb_delist_cause_id": "涨超120强赎"
        },
        {
            "data_id": "75",
            "cb_num_id": "151",
            "cb_name_id": "隆基转债",
            "bond_code": "113015",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "89",
            "cb_num_id": "152",
            "cb_name_id": "宁行转债",
            "bond_code": "128024",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "83",
            "cb_num_id": "153",
            "cb_name_id": "生益转债",
            "bond_code": "110040",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "136",
            "cb_num_id": "154",
            "cb_name_id": "安井转债",
            "bond_code": "113513",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "57",
            "cb_num_id": "155",
            "cb_name_id": "16以岭EB",
            "bond_code": "120001",
            "cb_delist_cause_id": "最低规模强赎"
        },
        {
            "data_id": "159",
            "cb_num_id": "156",
            "cb_name_id": "17桐昆EB",
            "bond_code": "132010",
            "cb_delist_cause_id": "涨超120强赎"
        },
        {
            "data_id": "107",
            "cb_num_id": "157",
            "cb_name_id": "常熟转债",
            "bond_code": "113018",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "97",
            "cb_num_id": "158",
            "cb_name_id": "东财转债",
            "bond_code": "123006",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "112",
            "cb_num_id": "159",
            "cb_name_id": "康泰转债",
            "bond_code": "123008",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "122",
            "cb_num_id": "160",
            "cb_name_id": "鼎信转债",
            "bond_code": "113506",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "135",
            "cb_num_id": "161",
            "cb_name_id": "景旺转债",
            "bond_code": "113512",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "49",
            "cb_num_id": "162",
            "cb_name_id": "三一转债",
            "bond_code": "110032",
            "cb_delist_cause_id": "涨超130强赎"
        },
        {
            "data_id": "56",
            "cb_num_id": "163",
            "cb_name_id": "江南转债",
            "bond_code": "113010",
            "cb_delist_cause_id": "最低规模强赎"
        }
    ]


def get_cb_enforce_json():
    return [{"bond_code": "113580", "cb_name_id": "康隆转债", "enforce_dt": "2021-11-01"}, {"bond_code": "123102", "cb_name_id": "华自转债", "enforce_dt": "2021-10-20"}, {"bond_code": "123069", "cb_name_id": "金诺转债", "enforce_dt": "2021-07-30"}, {"bond_code": "110033", "cb_name_id": "国贸转债", "enforce_dt": "2021-09-27"}, {"bond_code": "110041", "cb_name_id": "蒙电转债", "enforce_dt": "2021-09-30"}, {"bond_code": "128018", "cb_name_id": "时达转债", "enforce_dt": "2021-09-17"}, {"bond_code": "120003", "cb_name_id": "19华菱EB", "enforce_dt": "2021-09-16"}, {"bond_code": "120004", "cb_name_id": "20华菱EB", "enforce_dt": "2021-09-16"}, {"bond_code": "123047", "cb_name_id": "久吾转债", "enforce_dt": "2021-07-02"}, {"bond_code": "123051", "cb_name_id": "今天转债", "enforce_dt": "2021-09-16"}, {"bond_code": "123068", "cb_name_id": "弘信转债", "enforce_dt": "2021-09-17"}, {"bond_code": "113014", "cb_name_id": "林洋转债", "enforce_dt": "2021-09-03"}, {"bond_code": "113572", "cb_name_id": "三祥转债", "enforce_dt": "2021-08-30"}, {"bond_code": "123030", "cb_name_id": "九洲转债", "enforce_dt": "2020-09-18"}, {"bond_code": "113612", "cb_name_id": "永冠转债", "enforce_dt": "2021-08-17"}, {"bond_code": "123079", "cb_name_id": "运达转债", "enforce_dt": "2021-07-29"}, {"bond_code": "128051", "cb_name_id": "光华转债", "enforce_dt": "2021-07-28"}, {"bond_code": "123094", "cb_name_id": "星源转2", "enforce_dt": "2021-08-16"}, {"bond_code": "113012", "cb_name_id": "骆驼转债", "enforce_dt": "2021-08-11"}, {"bond_code": "113508", "cb_name_id": "新凤转债", "enforce_dt": "2021-07-27"}, {"bond_code": "123033", "cb_name_id": "金力转债", "enforce_dt": "2021-07-30"}, {"bond_code": "128064", "cb_name_id": "司尔转债", "enforce_dt": "2021-07-28"}, {"bond_code": "113509", "cb_name_id": "新泉转债", "enforce_dt": "2020-06-05"}, {"bond_code": "123066", "cb_name_id": "赛意转债", "enforce_dt": "2021-06-15"}, {"bond_code": "123007", "cb_name_id": "道氏转债", "enforce_dt": "2021-07-16"}, {"bond_code": "113040", "cb_name_id": "星宇转债", "enforce_dt": "2021-06-30"}, {"bond_code": "113611", "cb_name_id": "福20转债", "enforce_dt": "2021-07-02"}, {"bond_code": "128032", "cb_name_id": "双环转债", "enforce_dt": "2021-06-30"}, {"bond_code": "127023", "cb_name_id": "华菱转2", "enforce_dt": "2021-05-18"}, {"bond_code": "113543", "cb_name_id": "欧派转债", "enforce_dt": "2020-08-25"}, {"bond_code": "123058", "cb_name_id": "欣旺转债", "enforce_dt": "2021-06-16"}, {"bond_code": "110065", "cb_name_id": "淮矿转债", "enforce_dt": "2021-06-07"}, {"bond_code": "123029", "cb_name_id": "英科转债", "enforce_dt": "2020-03-16"}, {"bond_code": "113559", "cb_name_id": "永创转债", "enforce_dt": "2021-06-04"}, {"bond_code": "113041", "cb_name_id": "紫金转债", "enforce_dt": "2021-05-31"}, {"bond_code": "113564", "cb_name_id": "天目转债", "enforce_dt": "2021-04-06"}, {"bond_code": "128126", "cb_name_id": "赣锋转2", "enforce_dt": "2021-03-11"}, {"bond_code": "113557", "cb_name_id": "森特转债", "enforce_dt": "2021-03-31"}, {"bond_code": "110069", "cb_name_id": "瀚蓝转债", "enforce_dt": "2021-03-23"}, {"bond_code": "113038", "cb_name_id": "隆20转债", "enforce_dt": "2021-03-08"}, {"bond_code": "128052", "cb_name_id": "凯龙转债", "enforce_dt": "2019-07-18"}, {"bond_code": "113029", "cb_name_id": "明阳转债", "enforce_dt": "2020-10-29"}, {"bond_code": "128028", "cb_name_id": "赣锋转债", "enforce_dt": "2020-07-21"}, {"bond_code": "113590", "cb_name_id": "海容转债", "enforce_dt": "2021-01-25"}, {"bond_code": "113592", "cb_name_id": "安20转债", "enforce_dt": "2021-02-04"}, {"bond_code": "127008", "cb_name_id": "特发转债", "enforce_dt": "2019-06-13"}, {"bond_code": "113583", "cb_name_id": "益丰转债", "enforce_dt": "2021-02-01"}, {"bond_code": "128112", "cb_name_id": "歌尔转2", "enforce_dt": "2021-01-04"}, {"bond_code": "128065", "cb_name_id": "雅化转债", "enforce_dt": "2020-11-16"}, {"bond_code": "128010", "cb_name_id": "蔚蓝转债", "enforce_dt": "2021-01-29"}, {"bond_code": "123055", "cb_name_id": "晨光转债", "enforce_dt": "2021-01-14"}, {"bond_code": "123017", "cb_name_id": "寒锐转债", "enforce_dt": "2020-01-15"}, {"bond_code": "128115", "cb_name_id": "巨星转债", "enforce_dt": "2021-01-25"}, {"bond_code": "128110", "cb_name_id": "永兴转债", "enforce_dt": "2021-01-06"}, {"bond_code": "113587", "cb_name_id": "泛微转债", "enforce_dt": "2021-01-12"}, {"bond_code": "113035", "cb_name_id": "福莱转债", "enforce_dt": "2020-12-24"}, {"bond_code": "113556", "cb_name_id": "至纯转债", "enforce_dt": "2020-07-20"}, {"bond_code": "113586", "cb_name_id": "上机转债", "enforce_dt": "2021-01-06"}, {"bond_code": "113032", "cb_name_id": "桐20转债", "enforce_dt": "2020-12-04"}, {"bond_code": "128019", "cb_name_id": "久立转2", "enforce_dt": "2020-11-25"}, {"bond_code": "113520", "cb_name_id": "百合转债", "enforce_dt": "2019-12-20"}, {"bond_code": "128104", "cb_name_id": "裕同转债", "enforce_dt": "2020-11-05"}, {"bond_code": "128102", "cb_name_id": "海大转债", "enforce_dt": "2020-10-26"}, {"bond_code": "113562", "cb_name_id": "璞泰转债", "enforce_dt": "2020-10-16"}, {"bond_code": "123026", "cb_name_id": "中环转债", "enforce_dt": "2020-09-02"}, {"bond_code": "113581", "cb_name_id": "龙蟠转债", "enforce_dt": "2020-11-19"}, {"bond_code": "123036", "cb_name_id": "先导转债", "enforce_dt": "2020-10-30"}, {"bond_code": "113553", "cb_name_id": "金牌转债", "enforce_dt": "2020-08-31"}, {"bond_code": "113555", "cb_name_id": "振德转债", "enforce_dt": "2020-07-20"}, {"bond_code": "123032", "cb_name_id": "万里转债", "enforce_dt": "2020-11-02"}, {"bond_code": "113521", "cb_name_id": "科森转债", "enforce_dt": "2020-02-12"}, {"bond_code": "113020", "cb_name_id": "桐昆转债", "enforce_dt": "2020-11-12"}, {"bond_code": "128058", "cb_name_id": "拓邦转债", "enforce_dt": "2020-11-03"}, {"bond_code": "128099", "cb_name_id": "永高转债", "enforce_dt": "2020-10-28"}, {"bond_code": "113571", "cb_name_id": "博特转债", "enforce_dt": "2020-10-19"}, {"bond_code": "128098", "cb_name_id": "康弘转债", "enforce_dt": "2020-10-12"}, {"bond_code": "128067", "cb_name_id": "一心转债", "enforce_dt": "2020-09-09"}, {"bond_code": "128043", "cb_name_id": "东音转债", "enforce_dt": "2019-05-22"}, {"bond_code": "113028", "cb_name_id": "环境转债", "enforce_dt": "2020-08-19"}, {"bond_code": "113544", "cb_name_id": "桃李转债", "enforce_dt": "2020-09-07"}, {"bond_code": "128092", "cb_name_id": "唐人转债", "enforce_dt": "2020-08-03"}, {"bond_code": "113547", "cb_name_id": "索发转债", "enforce_dt": "2020-08-03"}, {"bond_code": "128084", "cb_name_id": "木森转债", "enforce_dt": "2020-08-10"}, {"bond_code": "113554", "cb_name_id": "仙鹤转债", "enforce_dt": "2020-07-29"}, {"bond_code": "123037", "cb_name_id": "新莱转债", "enforce_dt": "2020-07-20"}, {"bond_code": "110042", "cb_name_id": "航电转债", "enforce_dt": "2020-08-25"}, {"bond_code": "113019", "cb_name_id": "玲珑转债", "enforce_dt": "2020-08-14"}, {"bond_code": "123020", "cb_name_id": "富祥转债", "enforce_dt": "2020-02-03"}, {"bond_code": "113514", "cb_name_id": "威帝转债", "enforce_dt": "2020-08-05"}, {"bond_code": "113031", "cb_name_id": "博威转债", "enforce_dt": "2020-08-06"}, {"bond_code": "128045", "cb_name_id": "机电转债", "enforce_dt": "2020-07-29"}, {"bond_code": "113518", "cb_name_id": "顾家转债", "enforce_dt": "2020-07-22"}, {"bond_code": "128086", "cb_name_id": "国轩转债", "enforce_dt": "2020-07-16"}, {"bond_code": "123041", "cb_name_id": "东财转2", "enforce_dt": "2020-08-07"}, {"bond_code": "113022", "cb_name_id": "浙商转债", "enforce_dt": "2020-08-03"}, {"bond_code": "128088", "cb_name_id": "深南转债", "enforce_dt": "2020-07-21"}, {"bond_code": "123040", "cb_name_id": "乐普转债", "enforce_dt": "2020-07-30"}, {"bond_code": "113558", "cb_name_id": "日月转债", "enforce_dt": "2020-07-22"}, {"bond_code": "128089", "cb_name_id": "麦米转债", "enforce_dt": "2020-07-27"}, {"bond_code": "128059", "cb_name_id": "视源转债", "enforce_dt": "2020-07-22"}, {"bond_code": "113552", "cb_name_id": "克来转债", "enforce_dt": "2020-07-13"}, {"bond_code": "128080", "cb_name_id": "顺丰转债", "enforce_dt": "2020-07-02"}, {"bond_code": "113551", "cb_name_id": "福特转债", "enforce_dt": "2020-06-19"}, {"bond_code": "128077", "cb_name_id": "华夏转债", "enforce_dt": "2020-06-16"}, {"bond_code": "128054", "cb_name_id": "中宠转债", "enforce_dt": "2020-06-03"}, {"bond_code": "113515", "cb_name_id": "高能转债", "enforce_dt": "2020-05-20"}, {"bond_code": "113511", "cb_name_id": "千禾转债", "enforce_dt": "2020-04-09"}, {"bond_code": "113503", "cb_name_id": "泰晶转债", "enforce_dt": "2020-05-07"}, {"bond_code": "113531", "cb_name_id": "百姓转债", "enforce_dt": "2020-04-24"}, {"bond_code": "123021", "cb_name_id": "万信转 2", "enforce_dt": "2020-03-03"}, {"bond_code": "110050", "cb_name_id": "佳都转债", "enforce_dt": "2020-03-18"}, {"bond_code": "128055", "cb_name_id": "长青转 2", "enforce_dt": "2020-03-06"}, {"bond_code": "113517", "cb_name_id": "曙光转债", "enforce_dt": "2020-03-06"}, {"bond_code": "128016", "cb_name_id": "雨虹转债", "enforce_dt": "2020-03-09"}, {"bond_code": "123019", "cb_name_id": "中来转债", "enforce_dt": "2020-03-03"}, {"bond_code": "113510", "cb_name_id": "再升转债", "enforce_dt": "2020-03-10"}, {"bond_code": "113540", "cb_name_id": "南威转债", "enforce_dt": "2020-03-04"}, {"bond_code": "110046", "cb_name_id": "圆通转债", "enforce_dt": "2020-02-21"}, {"bond_code": "123009", "cb_name_id": "星源转债", "enforce_dt": "2020-02-24"}, {"bond_code": "128038", "cb_name_id": "利欧转债", "enforce_dt": "2019-04-11"}, {"bond_code": "110054", "cb_name_id": "通威转债", "enforce_dt": "2020-03-04"}, {"bond_code": "123016", "cb_name_id": "洲明转债", "enforce_dt": "2020-01-16"}, {"bond_code": "113539", "cb_name_id": "圣达转债", "enforce_dt": "2020-02-24"}, {"bond_code": "128061", "cb_name_id": "启明转债", "enforce_dt": "2020-02-05"}, {"bond_code": "113522", "cb_name_id": "旭升转债", "enforce_dt": "2020-02-05"}, {"bond_code": "113538", "cb_name_id": "安图转债", "enforce_dt": "2020-02-04"}, {"bond_code": "128060", "cb_name_id": "中装转债", "enforce_dt": "2019-10-29"}, {"bond_code": "123003", "cb_name_id": "蓝思转债", "enforce_dt": "2019-12-26"}, {"bond_code": "113523", "cb_name_id": "伟明转债", "enforce_dt": "2020-01-16"}, {"bond_code": "128068", "cb_name_id": "和而转债", "enforce_dt": "2020-01-02"}, {"bond_code": "128020", "cb_name_id": "水晶转债", "enforce_dt": "2019-12-30"}, {"bond_code": "113533", "cb_name_id": "参林转债", "enforce_dt": "2020-01-03"}, {"bond_code": "110049", "cb_name_id": "海尔转债", "enforce_dt": "2019-11-22"}, {"bond_code": "113529", "cb_name_id": "绝味转债", "enforce_dt": "2019-10-14"}, {"bond_code": "113507", "cb_name_id": "天马转债", "enforce_dt": "2019-10-30"}, {"bond_code": "128047", "cb_name_id": "光电转债", "enforce_dt": "2019-09-16"}, {"bond_code": "127009", "cb_name_id": "冰轮转债", "enforce_dt": "2019-08-29"}, {"bond_code": "123001", "cb_name_id": "蓝标转债", "enforce_dt": "2019-09-06"}, {"bond_code": "128027", "cb_name_id": "崇达转债", "enforce_dt": "2019-09-10"}, {"bond_code": "127010", "cb_name_id": "平银转债", "enforce_dt": "2019-08-21"}, {"bond_code": "113015", "cb_name_id": "隆基转债", "enforce_dt": "2019-08-20"}, {"bond_code": "128024", "cb_name_id": "宁行转债", "enforce_dt": "2019-07-24"}, {"bond_code": "110040", "cb_name_id": "生益转债", "enforce_dt": "2019-07-18"}, {"bond_code": "113513", "cb_name_id": "安井转债", "enforce_dt": "2019-06-11"}, {"bond_code": "120001", "cb_name_id": "16以岭EB", "enforce_dt": "2019-06-22"}, {"bond_code": "132010", "cb_name_id": "17桐昆EB", "enforce_dt": "2019-04-10"}, {"bond_code": "113018", "cb_name_id": "常熟转债", "enforce_dt": "2019-03-19"}, {"bond_code": "123006", "cb_name_id": "东财转债", "enforce_dt": "2019-03-14"}, {"bond_code": "123008", "cb_name_id": "康泰转债", "enforce_dt": "2019-03-21"}, {"bond_code": "113506", "cb_name_id": "鼎信转债", "enforce_dt": "2019-04-08"}, {"bond_code": "113512", "cb_name_id": "景旺转债", "enforce_dt": "2019-04-03"}, {"bond_code": "110032", "cb_name_id": "三一转债", "enforce_dt": "2019-02-28"}, {"bond_code": "113010", "cb_name_id": "江南转债"}]


def get_cb_content():
    rows = get_cb_delist_json()
    size = len(rows)
    i = 0
    new_rows = []
    for row in rows:
        i += 1
        new_row = {'bond_code': row['bond_code'], 'cb_name_id': row['cb_name_id']}
        data_id = row['data_id']
        parse_cb_detail(new_row, data_id)
        new_rows.append(new_row)

        print("parse complete:" + str(i) + "/" + str(size))

        time.sleep(3)

    return new_rows


def parse_cb_detail(row, data_id):
    url = "https://www.ninwin.cn/index.php?m=cb&c=detail&a=detail&id=" + data_id
    text = get_text(url)

    soup = bs4.BeautifulSoup(text, "html5lib")
    div = list(soup.find_all('div', attrs={'class', 'th mobile_display_none'})[1].parent.children)[3]
    #                 强赎触发日：2020-10-29
    r = re.findall(r"强赎触发日：([\d\-]+)", div.text)
    if len(r) == 1:
        row["enforce_dt"] = r[0]  # datetime.strptime(r[0], '%Y-%m-%d')


def get_cb_delist_rows():
    url = "https://www.ninwin.cn/index.php?m=cb&a=past"

    text = get_text(url)

    soup = bs4.BeautifulSoup(text, "html5lib")
    table = soup.find_all('table')[1]
    attr_id = table.attrs['id']
    if 'cb_hq' not in attr_id:
        print("table元素找的不对。id必须为cb_hq，实为：" + attr_id)
        return
    # 所有数据行 <tr>
    trs = list(table.tbody.children)

    if len(trs) == 0:
        print("未获取到数据。")

    rows = build_rows(trs)

    return rows


def get_text(url):
    cookies = {}
    s = "csrf_token=8919ea04925831e8; __51cke__=; P0s_winduser=RaqSRnBfFwDoLZv5tGFqXXLD4fXwVZQynHEOTJOsq1fzXIiXiCJW%2FWYIGis%3D; P0s_cbQuestion=1; __tins__4771153=%7B%22sid%22%3A%201631088120422%2C%20%22vd%22%3A%207%2C%20%22expires%22%3A%201631089976917%7D; __51laig__=234; PHPSESSID=jpl3tag9rff4l4mtdndsm36n44; P0s_visitor=Ncd58ncEEFs83Y9d2knG3OnEWpLyZm3YRPK8yFD6ja5fvV52; P0s_lastvisit=242%091631159109%09%2Findex.php%3Fm%3DmyAdmin%26c%3Dlog"
    for ss in s.split(";"):
        name, value = ss.strip().split("=", 1)
        cookies[name] = value
    response = requests.get(url, headers=header, cookies=cookies)
    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)
    text = response.text
    return text


def build_rows(trs):
    rows = []
    # 遍历所有行
    count = 0
    for tr in trs:
        if type(tr) == bs4.element.NavigableString:
            continue

        count += 1
        row = {}
        row['data_id'] = tr.attrs['data-id']
        tds = tr.children
        i = 1
        for td in tds:
            # 过滤掉空行
            if type(td) == bs4.element.NavigableString:
                continue
            try:
                i = build_row(row, td, i)
            except Exception as e:
                print("数据解析出错.row=" + str(row), e)
                raise e

        # 只处理强赎退市转债
        if '强赎' not in row.get('cb_delist_cause_id'):
            print('no enforce:' + str(row))
            continue

        rows.append(row)

    print('count:' + str(count))
    return rows


def build_row(row, td, i):
    cls = td.attrs['class']
    text = td.text.strip()
    # cb_num_id
    if 'cb_num_id' in cls:
        row['cb_num_id'] = text
    # bond_code
    elif 'bond_code_id' in cls and i < 2:
        # stock code也是bond_code_id
        i += 1
        if text.startswith('1'):
            row['bond_code'] = text
    # bond_code
    elif 'cb_delist_cause_id' in cls:
        row['cb_delist_cause_id'] = text
    # cb_name_id
    elif 'cb_name_id' in cls:
        text = text.replace('!', '')
        text = text.replace('*', '')
        row['cb_name_id'] = text

    return i


def insert_db(rows):
    err_row = None
    try:
        i = 0
        with db_utils.get_daily_connect() as con:
            cur = con.cursor()
            for row in rows:
                err_row = row
                enforce_dt = row.get('enforce_dt')
                if enforce_dt is None:
                    print("not enforce_dt value." + str(row))
                    continue
                result = cur.execute("""insert into cb_enforce (bond_id, bond_name, enforce_dt) VALUES (:bond_id, :bond_name, :enforce_dt)""",
                                     {'enforce_dt': datetime.strptime(enforce_dt, '%Y-%m-%d'), 'bond_id': row.get('bond_code'), 'bond_name': row.get('cb_name_id')})
                if result.rowcount != 1:
                    print('insert cb_enforce is failure. row:' + str(row))
                else:
                    i += 1

        print("insert complete. count:" + str(i))

    except Exception as e:
        print("db操作出现异常. err_row" + str(err_row), e)
        raise e
    finally:
        # 暂停3s再执行， 避免被网站屏蔽掉
        time.sleep(3)


def update_db(rows):
    err_row = None
    try:
        i = 0
        with db_utils.get_daily_connect() as con:
            cur = con.cursor()
            for row in rows:
                err_row = row
                enforce_dt = row.get('enforce_dt')
                if enforce_dt is None:
                    print("not enforce_dt value." + str(row))
                    continue
                result = cur.execute("""update cb_history set is_enforce=1 where bond_id=:bond_id and last_chg_dt=:enforce_dt""",
                                     {'enforce_dt': datetime.strptime(enforce_dt, '%Y-%m-%d'), 'bond_id': row.get('bond_code')})
                if result.rowcount != 1:
                    print('update cb_history is failure. row:' + str(row))
                else:
                    i += 1

        print("update complete. count:" + str(i))

    except Exception as e:
        print("db操作出现异常. err_row" + str(err_row), e)
        raise e
    finally:
        # 暂停3s再执行， 避免被网站屏蔽掉
        time.sleep(3)


def fetch_data():
    # rows = get_cb_delist_rows()
    # rows = get_cb_content()
    rows = get_cb_enforce_json()
    # update_db(rows)
    insert_db(rows)
    # print(json.dumps(rows, ensure_ascii=False))
    # update_db(rows)
    return 'OK'


if __name__ == "__main__":
    fetch_data()
    print("可转债数据抓取更新完成")

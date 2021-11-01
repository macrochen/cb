#抓取宁稳网的数据(每天中午, 下午收盘更新, 非实时, 但是最全)

import datetime
import re
import sqlite3
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


def get_content():
    url = "http://www.ninwin.cn/index.php?m=cb&a=cb_all&show_cb_only=Y&show_listed_only=Y"

    cookies = {}
    s = "csrf_token=8919ea04925831e8; __51cke__=; P0s_winduser=RaqSRnBfFwDoLZv5tGFqXXLD4fXwVZQynHEOTJOsq1fzXIiXiCJW%2FWYIGis%3D; P0s_cbQuestion=1; __tins__4771153=%7B%22sid%22%3A%201631088120422%2C%20%22vd%22%3A%207%2C%20%22expires%22%3A%201631089976917%7D; __51laig__=234; PHPSESSID=jpl3tag9rff4l4mtdndsm36n44; P0s_visitor=Ncd58ncEEFs83Y9d2knG3OnEWpLyZm3YRPK8yFD6ja5fvV52; P0s_lastvisit=242%091631159109%09%2Findex.php%3Fm%3DmyAdmin%26c%3Dlog"
    for ss in s.split(";"):
        name, value = ss.strip().split("=", 1)
        cookies[name] = value

    response = requests.get(url, headers=header, cookies=cookies)
    code = response.status_code
    if code != 200:
        print("获取数据失败， 状态码：" + code)

    soup = bs4.BeautifulSoup(response.text, "html5lib")
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

    # print(rows)

    return rows


def build_rows(trs):
    rows = []
    # 遍历所有行
    for tr in trs:
        row = {}
        row['data_id'] = tr.attrs['data-id']
        tds = tr.children
        for td in tds:
            # 过滤掉空行
            if type(td) == bs4.element.NavigableString:
                continue
            try:
                build_row(row, td)
            except Exception as e:
                print("数据解析出错.row=" + str(row), e)
                raise e
        rows.append(row)
    return rows


def dayYear2Year(text):
    # 把含有天的转成年
    if text.endswith('天'):
        years = '0'
        if text.find('年') > -1:
            ss = text.split('年')
            years = ss[0].replace('年', '')
            days = ss[1].replace('天', '')
        else:
            days = text.replace('天', '')

        text = int(years) + round(float(days) / 365.0, 2)
    else:
        text = text.replace('年', '')

    return text

def buildTag(row, td):
    if type(td.next) == bs4.element.NavigableString:
        return

    # 检查所满足的各种条件
    tags = list(td.next())
    if len(tags) > 0:
        for tag in tags:
            if tag.text == '!':
                # 强赎中(将退市)
                if tag.attrs['style'].find('color:red') > -1:
                    row['enforce_get'] = '强赎中'
                # 满足强赎条件
                if tag.attrs['style'].find('color:Fuchsia') > -1:
                    row['enforce_get'] = '满足强赎'
                # 公告不强赎条件
                if tag.attrs['style'].find('color:gray') > -1:
                    row['enforce_get'] = '公告不强赎'
                # 满足回售条件
                if tag.attrs['style'].find('color:#3cb371') > -1:
                    row['buy_back'] = 1
                # 满足下修条件
                if tag.attrs['style'].find('color:blue') > -1:
                    row['down_revise'] = 1


def build_row(row, td):
    cls = td.attrs['class']
    text = td.text.strip()
    # cb_num_id
    if 'cb_num_id' in cls:
        row['cb_num_id'] = text
    # bond_code
    elif 'bond_code_id' in cls and 'bond_code' in cls:
        row['bond_code'] = text
    # cb_name_id
    elif 'cb_name_id' in cls:
        buildTag(row, td)
        text = text.replace('!', '')
        text = text.replace('*', '')
        row['cb_name_id'] = text
        parse_enforce_data(row, td)
        add_pinyin_field(row, text)
    # bond_date_id
    elif 'bond_date_id' in cls:
        # 今日上市需要转换成当前日期
        if '今日上市' == text:
            text = datetime.datetime.now().strftime("%Y-%m-%d")

        row['bond_date_id'] = text

        # 计算续存期
        d = datetime.datetime.strptime(text, '%Y-%m-%d')
        row['duration'] = round((datetime.datetime.now() - d).days/365, 2)
    # stock_code
    elif 'stock_code' in cls:
        row['stock_code'] = text
    # stock_name
    elif 'stock_name' in cls:
        row['stock_name'] = text
    # industry
    elif 'industry' in cls:
        # fixme 子行业和行业没法区分
        if 'industry' in row:
            row['sub_industry'] = text
        else:
            row['industry'] = text
    # cb_price2_id
    elif 'cb_price2_id' in cls:
        # fixme 剩余本息和转债价格无法区分
        if 'cb_price2_id' in row:
            row['cb_price3_id'] = text
        else:
            row['cb_price2_id'] = text
    # cb_mov2_id
    elif 'cb_mov2_id' in cls:
        # fixme 涨跌幅和日内套利无法区分
        if 'cb_mov2_id' in row:
            row['cb_mov3_id'] = percentage2float(row['cb_name_id'], 'cb_mov3_id', text)
        else:
            row['cb_mov2_id'] = percentage2float(row['cb_name_id'], 'cb_mov2_id', text)
    # stock_price_id
    elif 'stock_price_id' in cls:
        # remain_amount
        if 'remain_amount' in cls:
            row['remain_amount'] = text
        else:
            row['stock_price_id'] = text
    # cb_mov_id
    elif 'cb_mov_id' in cls:
        row['cb_mov_id'] = percentage2float(row['cb_name_id'], 'cb_mov_id', text)
    # cb_strike_id
    elif 'cb_strike_id' in cls:
        row['cb_strike_id'] = text
    # cb_premium_id
    elif 'cb_premium_id' in cls:
        row['cb_premium_id'] = percentage2float(row['cb_name_id'], 'cb_premium_id', text)
    # cb_value_id
    elif 'cb_value_id' in cls:
        # fixme 依赖字段顺序（转股价值，ma20乖离率）
        # npv_red
        if 'npv_red' in cls:
            row['npv_red'] = text
        # npv_value
        elif 'npv_value' in cls:
            row['npv_value'] = text
        elif not 'cb_value_id' in row:
            row['cb_value_id'] = text
        else:
            row['cb_ma20_deviate'] = percentage2float(row['cb_name_id'], 'cb_ma20_deviate', text)
    # cb_t_id
    elif 'cb_t_id' in cls:
        # bond_t1
        if 'bond_t1' in cls:
            row['bond_t1'] = dayYear2Year(text)
        # red_t
        elif 'red_t' in cls:
            row['red_t'] = dayYear2Year(text)
        else:
            row['cb_t_id'] = text

    # todo 增加一个续存期字段

    # cb_trade_amount_id
    elif 'cb_trade_amount_id' in cls:
        # fixme 转债成交额和换手率无法区分
        if 'cb_trade_amount_id' in row:
            row['cb_trade_amount2_id'] = percentage2float(row['cb_name_id'], 'cb_trade_amount2_id', text)
        else:
            row['cb_trade_amount_id'] = text
    # cb_to_share
    elif 'cb_to_share' in cls:
        row['cb_to_share'] = percentage2float(row['cb_name_id'], 'cb_to_share', text)
    # cb_to_share_shares
    elif 'cb_to_share_shares' in cls:
        row['cb_to_share_shares'] = percentage2float(row['cb_name_id'], 'cb_to_share_shares', text)
    # market_cap
    elif 'market_cap' in cls:
        row['market_cap'] = text
    # cb_elasticity_id
    elif 'cb_elasticity_id' in cls:
        # fixme 这里依赖字段顺序
        if not 'stock_pb' in row:
            row['stock_pb'] = text
        elif not 'elasticity' in row:
            row['elasticity'] = text
        elif not 'cb_ol_rank' in row:
            row['cb_ol_rank'] = text
        elif not 'cb_nl_rank' in row:
            row['cb_nl_rank'] = text
        elif not 'cb_hot' in row:
            row['cb_hot'] = text
        else:
            print("存在未知的class为cb_elasticity_id的td， 内容为：" + td)
    # BT_yield
    elif 'BT_yield' in cls:
        row['BT_yield'] = percentage2float(row['cb_name_id'], 'BT_yield', text)
    # AT_yield
    elif 'AT_yield' in cls:
        row['AT_yield'] = percentage2float(row['cb_name_id'], 'AT_yield', text)
    # BT_red
    elif 'BT_red' in cls:
        title = td.attrs['title']
        # fixme 数据格式变了, 临时处理一下, 可能根据th来判断更合适
        if title.find('税后回售收益率') == -1:
            row['AT_red'] = percentage2float(row['cb_name_id'], 'BT_red', text)
        else:
            row['BT_red'] = percentage2float(row['cb_name_id'], 'BT_red', text)
    # AT_red
    elif 'AT_red' in cls:
        row['AT_red'] = percentage2float(row['cb_name_id'], 'AT_red', text)
    # rating
    elif 'rating' in cls:
        row['rating'] = text
    # discount_rate
    elif 'discount_rate' in cls:
        row['discount_rate'] = percentage2float(row['cb_name_id'], 'discount_rate', text)
    # cb_wa_id
    elif 'cb_wa_id' in cls:
        # fixme 新式双低， 老式双低
        if 'cb_ol_value' in row:
            row['cb_nl_value'] = text
        else:
            row['cb_ol_value'] = text
    else:
        print("未知的数据， 内容为：" + td)

    return row


def parse_enforce_data(row, td):
    children = list(td.children)
    if len(children) > 1:
        title = children[1].attrs['title']
        if title is not None and title.strip(' ') != '':
            # 公告不强赎
            # 2021-08-23已满足强赎条件，且公司已经发出公告，2021-12-12前暂不行使强赎权利！
            r = re.findall(r"([\d\-]+)已满足强赎条件，且公司已经发出公告，([\d\-]+)前暂不行使强赎权利！", title)
            if len(r) == 1:
                row["enforce_start_date"] = datetime.datetime.strptime(r[0][0], '%Y-%m-%d')
                row["enforce_stop_date"] = datetime.datetime.strptime(r[0][1], '%Y-%m-%d')

            # 满足强赎
            # 最快2个交易日后可能满足强赎条件！
            r = re.findall(r"最快(\d+)个交易日后可能满足强赎条件！", title)
            if len(r) == 1:
                row["enforce_start_date"] = get_trade_date(int(r[0]))
            # 2021-08-24已满足强赎条件，且不强赎承诺截止日2021-08-23已过！
            r = re.findall(r"([\d\-]+)已满足强赎条件，且不强赎承诺截止日([\d\-]+)已过！", title)
            if len(r) == 1:
                row["enforce_start_date"] = datetime.datetime.strptime(r[0][0], '%Y-%m-%d')
                row["enforce_stop_date"] = datetime.datetime.strptime(r[0][1], '%Y-%m-%d')
            # 2021-07-20已满足强赎条件，且距离不强赎承诺截止日2021-11-03仅剩3个交易日了！
            r = re.findall(r"([\d\-]+)已满足强赎条件，且距离不强赎承诺截止日([\d\-]+)仅剩(\d+)个交易日了！", title)
            if len(r) == 1:
                row["enforce_start_date"] = datetime.datetime.strptime(r[0][0], '%Y-%m-%d')
                row["enforce_stop_date"] = datetime.datetime.strptime(r[0][1], '%Y-%m-%d')
            # 2021-09-16已满足强赎条件，且满足强赎条件后，超过一个月未公告是否行使强赎权利！
            r = re.findall(r"([\d\-]+)已满足强赎条件，且满足强赎条件后，超过一个月未公告是否行使强赎权利！", title)
            if len(r) == 1:
                row["enforce_start_date"] = datetime.datetime.strptime(r[0], '%Y-%m-%d')

            # 强赎中
            # 2021-10-29已满足强赎条件，且公司已经发出公告，将行使强赎权利！
            r = re.findall(r"([\d\-]+)已满足强赎条件，且公司已经发出公告，将行使强赎权利！", title)
            if len(r) == 1:
                row["enforce_start_date"] = datetime.datetime.strptime(r[0], '%Y-%m-%d')
            # 2021-09-30已满足强赎条件，且最后交易日：2021-11-04，最后转股日：2021-11-04，赎回价格：101.307！
            r = re.findall(r"([\d\-]+)已满足强赎条件，且最后交易日：([\d\-]+)，最后转股日：([\d\-]+)，赎回价格：([\d\\.]+)！", title)
            if len(r) == 1:
                row["enforce_start_date"] = datetime.datetime.strptime(r[0][0], '%Y-%m-%d')
                row["enforce_last_date"] = datetime.datetime.strptime(r[0][1], '%Y-%m-%d')
                row["enforce_price"] = float(r[0][3])

            row['declare_desc'] = title.replace('\n', '')


def add_pinyin_field(row, text):
    # 增加拼音首字母处理
    o = pinyin(text, heteronym=True, style=Style.FIRST_LETTER)
    ps = []
    for i in product(*o):  # 用笛卡尔积解决多音字问题
        if type(i) == tuple:
            ps.append(''.join(list(i)))
        else:
            ps.append(''.join[i])
    row['pinyin'] = ','.join(ps)


# 百分比转换成小数
def percentage2float(bond_name, name, text):
    if text.endswith("%"):
        # 去掉千分位, 去掉>, <符号
        text = text.replace(',', '')
        text = text.replace('>', '')
        text = text.replace('<', '')
        return round(float(text.strip("%")) / 100, 5)
    else:
        print("没有找到对应的值。 name：" + name + ' in bond: ' + bond_name)
        return None


def create_db():
    # 使用:memory:标识打开的是内存数据库
    # con = sqlite3.connect(":memory:")

    with db_utils.get_connect() as con:
        # 使用executescript可以执行多个脚本
        con.executescript("""
            drop table if exists changed_bond;
            create table if not exists changed_bond(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cb_num_id int NOT NULL,
                bond_code text NOT NULL, 
                cb_name_id text NOT NULL,
                bond_date_id text NOT NULL,
                stock_code text NOT NULL,
                stock_name text NOT NULL,
                industry text NOT NULL,
                sub_industry text NOT NULL,
                cb_price2_id real NOT NULL,
                cb_mov2_id real NOT NULL,
                cb_mov3_id real NOT NULL,
                stock_price_id real NOT NULL,
                cb_mov_id real NOT NULL,
                cb_price3_id real NOT NULL,
                cb_strike_id real NOT NULL,
                cb_premium_id real NOT NULL,
                cb_value_id real NOT NULL,
                cb_t_id text NOT NULL,
                bond_t1 text NOT NULL,
                red_t text NOT NULL,
                remain_amount real NOT NULL,
                cb_trade_amount_id real NOT NULL,
                cb_trade_amount2_id real NOT NULL,
                cb_to_share real NOT NULL,
                cb_to_share_shares real NOT NULL,
                market_cap real NOT NULL,
                stock_pb real NOT NULL,
                BT_yield real NOT NULL,
                AT_yield real NOT NULL,
                BT_red real,
                AT_red real,
                npv_red real NOT NULL,
                npv_value real NOT NULL,
                rating text NOT NULL,
                discount_rate real NOT NULL,
                elasticity real NOT NULL,
                cb_ol_value real NOT NULL,
                cb_ol_rank int NOT NULL,
                cb_nl_value real NOT NULL,
                cb_nl_rank int NOT NULL,
                cb_ma20_deviate real NOT NULL,
                cb_hot int NOT NULL,
                duration real,
                enforce_get text,
                buy_back int,
                down_revise int,
                data_id INTEGER,
                pinyin text,
                declare_desc text,
                enforce_start_date date, -- 强赎起始日
                enforce_stop_date date, -- 不强赎截止日
                enforce_declare_date date, -- 强赎宣告日
                enforce_last_date date, -- 强赎最后交易日
                enforce_price real -- 强赎价格
                )""")


def insert_db(rows):
    err_row = None
    try:

        for row in rows:
            err_row = row
            # execute执行脚本 cb_num_id
            get_cursor("""insert into 
            changed_bond( cb_num_id, bond_code, cb_name_id, bond_date_id, stock_code, stock_name, industry, sub_industry, cb_price2_id, cb_mov2_id, cb_mov3_id, stock_price_id, cb_mov_id, cb_price3_id, cb_strike_id, cb_premium_id, cb_value_id, cb_t_id, bond_t1, red_t, remain_amount, cb_trade_amount_id, cb_trade_amount2_id, cb_to_share, cb_to_share_shares, market_cap, stock_pb, BT_yield, AT_yield, BT_red, AT_red, npv_red, npv_value, rating, discount_rate, elasticity, cb_ol_value, cb_ol_rank, cb_nl_value, cb_nl_rank, cb_ma20_deviate, cb_hot, duration, enforce_get, buy_back, down_revise, data_id, pinyin, 
            declare_desc, enforce_start_date, enforce_stop_date, enforce_declare_date, enforce_last_date, enforce_price)
            values(:cb_num_id,:bond_code,:cb_name_id,:bond_date_id,:stock_code,:stock_name,:industry,:sub_industry,:cb_price2_id,:cb_mov2_id,:cb_mov3_id,:stock_price_id,:cb_mov_id,:cb_price3_id,:cb_strike_id,:cb_premium_id,:cb_value_id,:cb_t_id,:bond_t1,:red_t,:remain_amount,:cb_trade_amount_id,:cb_trade_amount2_id,:cb_to_share,:cb_to_share_shares,:market_cap,:stock_pb,:BT_yield,:AT_yield,:BT_red,:AT_red,:npv_red,:npv_value,:rating,:discount_rate,:elasticity,:cb_ol_value,:cb_ol_rank,:cb_nl_value,:cb_nl_rank,:cb_ma20_deviate,:cb_hot,:duration,:enforce_get,:buy_back,:down_revise,:data_id, :pinyin, 
            :declare_desc, :enforce_start_date, :enforce_stop_date, :enforce_declare_date, :enforce_last_date, :enforce_price)""",
                       {'cb_num_id' : row['cb_num_id'], 'bond_code' : row['bond_code'], 'cb_name_id' : row['cb_name_id'], 'bond_date_id' : row['bond_date_id'], 'stock_code' : row['stock_code'],
                          'stock_name' : row['stock_name'], 'industry' : row['industry'], 'sub_industry' : row['sub_industry'], 'cb_price2_id' : row['cb_price2_id'],
                          'cb_mov2_id' : row['cb_mov2_id'], 'cb_mov3_id' : row['cb_mov3_id'], 'stock_price_id' : row['stock_price_id'], 'cb_mov_id' : row['cb_mov_id'],
                          'cb_price3_id' : row['cb_price3_id'], 'cb_strike_id' : row['cb_strike_id'], 'cb_premium_id' : row['cb_premium_id'], 'cb_value_id' : row['cb_value_id'],
                          'cb_t_id' : row['cb_t_id'], 'bond_t1' : row['bond_t1'], 'red_t' : row['red_t'], 'remain_amount' : row['remain_amount'], 'cb_trade_amount_id' : row['cb_trade_amount_id'],
                          'cb_trade_amount2_id' : row['cb_trade_amount2_id'], 'cb_to_share' : row['cb_to_share'], 'cb_to_share_shares' : row['cb_to_share_shares'], 'market_cap' : row['market_cap'],
                          'stock_pb' : row['stock_pb'], 'BT_yield' : row['BT_yield'], 'AT_yield' : row['AT_yield'], 'BT_red' : row['BT_red'], 'AT_red' : row['AT_red'],
                          'npv_red' : row['npv_red'], 'npv_value' : row['npv_value'], 'rating' : row['rating'], 'discount_rate' : row['discount_rate'], 'elasticity' : row['elasticity'],
                          'cb_ol_value' : row['cb_ol_value'], 'cb_ol_rank' : row['cb_ol_rank'], 'cb_nl_value' : row['cb_nl_value'], 'cb_nl_rank' : row['cb_nl_rank'],
                          'cb_ma20_deviate' : row['cb_ma20_deviate'], 'cb_hot' : row['cb_hot'], 'duration' : row['duration'], 'enforce_get' : row.get('enforce_get'),
                          'buy_back': row.get('buy_back'), 'down_revise' : row.get('down_revise'), 'data_id' : row['data_id'], 'pinyin': row['pinyin'],
                          'declare_desc' : row.get('declare_desc'), 'enforce_start_date': row.get('enforce_start_date'),
                          'enforce_stop_date' : row.get('enforce_stop_date'),'enforce_declare_date' : row.get('enforce_declare_date'),
                          'enforce_last_date' : row.get('enforce_last_date'),'enforce_price' : row.get('enforce_price'),
                        }
            )
    except Exception as e:
        # cur_file.close()
        print("db操作出现异常. err_row" + str(err_row), e)
        raise e

def fetch_data():
    create_db()
    rows = get_content()
    insert_db(rows)
    return 'OK'

if __name__ == "__main__":
    # fetch_data()
    print("可转债数据抓取更新完成")

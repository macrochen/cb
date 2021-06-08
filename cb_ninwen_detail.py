#抓取宁稳网的数据(每天中午, 下午收盘更新, 非实时, 但是最全)

import datetime
import time
from io import StringIO

import requests
import bs4
import html5lib
from lxml import etree
import sqlite3

from selenium import webdriver
import re
userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36"
header = {
    "Referer": "http://www.ninwin.cn/index.php?m=profile",
    'User-Agent': userAgent,
    'Cookie': "csrf_token=4d924a8e39c98eee; __51cke__=; P0s_Pw_verify_code=lNwst736TYc%3D; P0s_winduser=RaqSRnBfFwDoLZv5tGFqXXLD4fXwVZQynHEOTJOsq1fzXIiXiCJW%2FWYIGis%3D; P0s_visitor=Cmse9dUtYW7cclzpENrqCj4gRIGuNSePKoJ%2Bng6EdKzPslngncrLoDtmlqg%3D; __tins__4771153=%7B%22sid%22%3A%201615874339009%2C%20%22vd%22%3A%204%2C%20%22expires%22%3A%201615876387793%7D; __51laig__=98; P0s_lastvisit=269%091615874605%09%2Findex.php%3Fm%3DmyAdmin%26c%3Dlog"
}

driver = None
def getContent(bond_num):
    url = "http://www.ninwin.cn/index.php?m=cb&c=detail&a=detail&id=" + str(bond_num)

    driver.get(url)

    row = {}

    table = driver.find_element_by_class_name("content_tab")
    s = table.text

    r = re.findall(r"各期利息：(\d+\.?\d*，\d+\.?\d*，\d+\.?\d*，\d+\.?\d*，\d+\.?\d*，\d+\.?\d*)\n", s)
    if len(r) == 1:
        ss = r[0].split('，')
        if len(ss) == 6:
            row['interest'] = ','.join(ss)

    r = re.findall(r"下修条件：连续(\d+)个交易日中至少(\d+)个交易日收盘价格低于当期转股价格的(\d+)%\n", s)
    if len(r) == 1:
        row["down_revise_term"] = ','.join(r[0])

    r = re.findall(r"强赎条件：连续(\d+)个交易日中至少(\d+)个交易日收盘价格不低于当期转股价格的(\d+)%，或者余额小于(\d+)万元\n", s)
    if len(r) == 1:
        row["enforce_get_term"] = ','.join(r[0])

    r = re.findall(r"回售条件：最后(\d+)年，连续(\d+)个交易日收盘价格低于当期转股价格的(\d+)%\n", s)
    if len(r) == 1:
        row["buy_back_term"] = ','.join(r[0])

    r = re.findall(r"(担保：.*)\n", s)
    if len(r) == 1:
        if r[0] in ['担保：', '担保：无', '担保：未提供担保。', '担保：不提供担保。', '担保：不提供担保', '担保：本次发行的可转债未提供担保。', '担保：无担保']:
            row["ensure"] = '无'
        else:
            row["ensure"] = '无'

    return row


def buildRows(trs):
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
                buildRow(row, td)
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

def buildRow(row, td):
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
        row['cb_name_id'] = text.replace('*', '')
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
            row['cb_mov3_id'] = percentage2float('cb_mov3_id', text)
        else:
            row['cb_mov2_id'] = percentage2float('cb_mov2_id', text)
    # stock_price_id
    elif 'stock_price_id' in cls:
        # remain_amount
        if 'remain_amount' in cls:
            row['remain_amount'] = text
        else:
            row['stock_price_id'] = text
    # cb_mov_id
    elif 'cb_mov_id' in cls:
        row['cb_mov_id'] = percentage2float('cb_mov_id', text)
    # cb_strike_id
    elif 'cb_strike_id' in cls:
        row['cb_strike_id'] = text
    # cb_premium_id
    elif 'cb_premium_id' in cls:
        row['cb_premium_id'] = percentage2float('cb_premium_id', text)
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
            row['cb_ma20_deviate'] = percentage2float('cb_ma20_deviate', text)
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
            row['cb_trade_amount2_id'] = percentage2float('cb_trade_amount2_id', text)
        else:
            row['cb_trade_amount_id'] = text
    # cb_to_share
    elif 'cb_to_share' in cls:
        row['cb_to_share'] = percentage2float('cb_to_share', text)
    # cb_to_share_shares
    elif 'cb_to_share_shares' in cls:
        row['cb_to_share_shares'] = percentage2float('cb_to_share_shares', text)
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
        row['BT_yield'] = percentage2float('BT_yield', text)
    # AT_yield
    elif 'AT_yield' in cls:
        row['AT_yield'] = percentage2float('AT_yield', text)
    # BT_red
    elif 'BT_red' in cls:
        row['BT_red'] = percentage2float('BT_red', text)
    # AT_red
    elif 'AT_red' in cls:
        row['AT_red'] = percentage2float('AT_red', text)
    # rating
    elif 'rating' in cls:
        row['rating'] = text
    # discount_rate
    elif 'discount_rate' in cls:
        row['discount_rate'] = percentage2float('discount_rate', text)
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


# 百分比转换成小数
def percentage2float(name, text):
    if text.endswith("%"):
        # 去掉千分位
        if text.find(","):
            text = text.replace(",", "")
        return round(float(text.strip("%")) / 100, 5)
    else:
        print("没有找到对应的值。 name：" + name)
        return None




def insertDb(rows):
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    try:

        for row in rows:
            # execute执行脚本
            con_file.execute("""insert into changed_bond(cb_num_id,bond_code,cb_name_id,bond_date_id,stock_code,stock_name,industry,sub_industry,cb_price2_id,cb_mov2_id,cb_mov3_id,stock_price_id,cb_mov_id,cb_price3_id,cb_strike_id,cb_premium_id,cb_value_id,cb_t_id,bond_t1,red_t,remain_amount,cb_trade_amount_id,cb_trade_amount2_id,cb_to_share,cb_to_share_shares,market_cap,stock_pb,BT_yield,AT_yield,BT_red,AT_red,npv_red,npv_value,rating,discount_rate,elasticity,cb_ol_value,cb_ol_rank,cb_nl_value,cb_nl_rank,cb_ma20_deviate,cb_hot,duration,enforce_get,buy_back,down_revise,data_id)
                             values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                             (row["cb_num_id"], row["bond_code"], row["cb_name_id"], row["bond_date_id"], row["stock_code"],
                              row["stock_name"], row["industry"], row["sub_industry"], row["cb_price2_id"],
                              row["cb_mov2_id"], row["cb_mov3_id"], row["stock_price_id"], row["cb_mov_id"],
                              row["cb_price3_id"], row["cb_strike_id"], row["cb_premium_id"], row["cb_value_id"],
                              row["cb_t_id"], row["bond_t1"], row["red_t"], row["remain_amount"], row["cb_trade_amount_id"],
                              row["cb_trade_amount2_id"], row["cb_to_share"], row["cb_to_share_shares"], row["market_cap"],
                              row["stock_pb"], row["BT_yield"], row["AT_yield"], row["BT_red"], row["AT_red"],
                              row["npv_red"], row["npv_value"], row["rating"], row["discount_rate"], row["elasticity"],
                              row["cb_ol_value"], row["cb_ol_rank"], row["cb_nl_value"], row["cb_nl_rank"],
                              row["cb_ma20_deviate"], row["cb_hot"], row["duration"], row.get("enforce_get"), row.get("buy_back"), row.get("down_revise"), row['data_id'])
                             )
        con_file.commit()
        con_file.close()
    except Exception as e:
        # cur_file.close()
        con_file.close()
        print("db操作出现异常", e)

def fetch_data():
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    try:
        # 遍历整个可转债列表, 拿到bond_num
        bond_cursor = con_file.execute("""SELECT data_id, bond_code, cb_name_id from changed_bond""")
        i = 0
        for bond_row in bond_cursor:
            num_id = bond_row[0]
            bond_code = bond_row[1]
            bond_name = bond_row[2]

            bond_ex_cursor = con_file.execute("""SELECT id from changed_bond_extend where bond_num = ?""", (num_id,))
            ex_list = list(bond_ex_cursor)
            if len(ex_list) == 0:
                # 检查是否存在extend信息, 没有则去抓数据
                row = getContent(num_id)
                # 插入数据
                con_file.execute("""insert into changed_bond_extend(bond_num, bond_code, 
                interest, ensure, enforce_get_term, buy_back_term, down_revise_term)
                                        values(?,?,?,?,?,?,?)""",
                                 (num_id, bond_code,
                                  row.get('interest'),
                                  row.get('ensure'),
                                  row.get('enforce_get_term'),
                                  row.get('buy_back_term'),
                                  row.get('down_revise_term'),
                                  )
                                 )
                print("insert " + bond_name + " is successful. count:" + str(i + 1))
                i += 1
                # 暂停5s再执行， 避免被网站屏蔽掉
                time.sleep(5)
    except Exception as e:
        # con_file.close()
        print("db操作出现异常" + str(e), e)
    except TimeoutError as e:
        print("网络超时, 请手工重试")
    finally:
        con_file.commit()
        con_file.close()

if __name__ == "__main__":

    options = webdriver.ChromeOptions()
    options.add_argument('user-agent="' + userAgent + '"')
    options.add_argument('Referer="http://www.ninwin.cn/index.php?m=profile"')

    driver = webdriver.Chrome(options=options)

    driver.implicitly_wait(10)
    fetch_data()

    driver.close()

    print("可转债数据抓取更新完成")

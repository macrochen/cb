# 从东方财富抓正股的相关数据
import datetime
import json
import time

import requests
import bs4
import html5lib
from lxml import etree
import sqlite3

import common
from selenium import webdriver

driver = None


def update_stock_sum():
    # 遍历可转债列表
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    try:
        # 查询可转债
        bond_cursor = con_file.execute("""SELECT bond_code, cb_name_id, stock_code, stock_name from changed_bond""")
        # 当前日月
        y = datetime.datetime.now().year
        m = datetime.datetime.now().month
        d = datetime.datetime.now().day
        t = datetime.datetime(y, m, d)
        # 记录更新时间(秒)
        s = (t - datetime.datetime(1970, 1, 1)).total_seconds()

        i = 0
        for bond_row in bond_cursor:
            stock_code = bond_row[2]
            stock_name = bond_row[3]

            stock_cursor = con_file.execute("""SELECT modify_date from stock_report where stock_code = ?""", [stock_code])
            stocks = list(stock_cursor)
            if len(stocks) == 0:
                continue

            # 已经更新了
            if stocks[0][0] is not None and stocks[0][0] >= s:
                continue

            row = get_stock_sum(stock_code)

            result = con_file.execute("""update stock_report set pe = ?, 
                net_asset = ?, 
                gross_rate = ?, 
                avg_market_cap = ?, 
                avg_roe = ?, 
                avg_net_profit_ratio = ?, 
                avg_gross_rate = ?, 
                avg_pb = ?, 
                avg_pe = ?, 
                avg_net_margin = ?, 
                avg_net_asset = ?, 
                rank_roe = ?, 
                rank_net_profit_ratio = ?, 
                rank_gross_rate = ?, 
                rank_pb = ?, 
                rank_pe = ?, 
                rank_net_margin = ?, 
                rank_net_asset = ?, 
                rank_market_cap = ?, 
                level_roe = ?, 
                level_market_cap = ?, 
                level_net_asset = ?, 
                level_net_margin = ?, 
                level_pe = ?, 
                level_pb = ?, 
                level_gross_rate = ?, 
                level_net_profit_ratio = ?, 
                modify_date = ? where stock_code = ?""",
                             (
                                row['pe'],
                                row['net_asset'],
                                row['gross_rate'],
                                row['avg_market_cap'],
                                row['avg_roe'],
                                row['avg_net_profit_ratio'],
                                row['avg_gross_rate'],
                                row['avg_pb'],
                                row['avg_pe'],
                                row['avg_net_margin'],
                                row['avg_net_asset'],
                                row['rank_roe'],
                                row['rank_net_profit_ratio'],
                                row['rank_gross_rate'],
                                row['rank_pb'],
                                row['rank_pe'],
                                row['rank_net_margin'],
                                row['rank_net_asset'],
                                row['rank_market_cap'],
                                row['level_roe'],
                                row['level_market_cap'],
                                row['level_net_asset'],
                                row['level_net_margin'],
                                row['level_pe'],
                                row['level_pb'],
                                row['level_gross_rate'],
                                row['level_net_profit_ratio'],
                              s, stock_code)
                             )
            if result.rowcount == 0:
                print("not update stock:" + stock_name)
            else:
                print("update " + stock_name + " is successful. count:" + str(i + 1))

            # 暂停5s再执行， 避免被网站屏蔽掉
            time.sleep(5)
            i += 1

        print("共处理" + str(i) + "条记录")

    except Exception as e:
        # con_file.close()
        print("db操作出现异常" + str(e), e)
    except TimeoutError as e:
        print("网络超时, 请手工重试")
    finally:
        con_file.commit()
        con_file.close()


def modify_data_unit_error():
    # 遍历可转债列表
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    try:

        i = 0

        stock_cursor = con_file.execute("""SELECT bond_code, avg_net_margin, stock_name from stock_report""")
        stocks = list(stock_cursor)

        for stock in stocks:
            bond_code = stock[0]
            avg_net_margin = stock[1]
            stock_name = stock[2]

            if not isinstance(avg_net_margin, str) or not avg_net_margin.endswith('万'):
                continue

            avg_net_margin = change_data_unit(avg_net_margin, no_clean_text)

            con_file.execute("""update stock_report set avg_net_margin = ? where bond_code = ?""",
                             (avg_net_margin, bond_code))

            i += 1
            print("update " + stock_name + " is successful. count:" + str(i))

        print("共处理" + str(i) + "条记录")

    except Exception as e:
        # con_file.close()
        print("db操作出现异常" + str(e), e)
    except TimeoutError as e:
        print("网络超时, 请手工重试")
    finally:
        con_file.commit()
        con_file.close()


def get_sum_data(driver):
    row = {}

    tbody = driver.find_element_by_id("cwzbDataBox")
    # 4个tr: 公司信息, 行业均值, 行业排名, 分位信息
    trs = tbody.find_elements_by_tag_name('tr')

    j = 0
    for tr in trs:
        j += 1
        # 公司信息
        if j == 1:
            i = 0
            tds = tr.find_elements_by_tag_name('td')
            for td in tds:

                i += 1
                # 第1列丢弃
                if i in (1, 2, 4, 6, 8, 9):
                    continue

                s = clean_text(td)
                # 第2列: 总市值 from jsl
                # 第3列: 净资产
                if i == 3:
                    row['net_asset'] = s
                # 第4列: 净利润 from xueqiu
                # 第5列: 动态市盈率
                elif i == 5:
                    row['pe'] = s
                # 第6列: 市净率 from xueqiu
                # 第7列: 毛利率
                elif i == 7:
                    row['gross_rate'] = s
                # 第8列: 净利率 from xueqiu 利润率
                # 第9列: ROE(加权净资产收益率) from xueqiu
        # 行业均值
        elif j == 2:
            i = 0
            tds = tr.find_elements_by_tag_name('td')
            for td in tds:
                i += 1
                # 第1列丢弃
                if i == 1:
                    continue

                s = clean_text(td)
                # 第2列: 总市值 from jsl
                if i == 2:
                    row['avg_market_cap'] = s
                # 第3列: 净资产
                elif i == 3:
                    row['avg_net_asset'] = s
                # 第4列: 净利润 from xueqiu
                elif i == 4:
                    row['avg_net_margin'] = s
                # 第5列: 动态市盈率 from xueqiu
                elif i == 5:
                    row['avg_pe'] = s
                # 第6列: 市净率 from xueqiu
                elif i == 6:
                    row['avg_pb'] = s
                # 第7列: 毛利率
                elif i == 7:
                    row['avg_gross_rate'] = s
                # 第8列: 净利率 from xueqiu 利润率
                elif i == 8:
                    row['avg_net_profit_ratio'] = s
                # 第9列: ROE(加权净资产收益率) from xueqiu
                elif i == 9:
                    row['avg_roe'] = s
        # 行业排名
        elif j == 3:
            i = 0
            tds = tr.find_elements_by_tag_name('td')
            for td in tds:
                i += 1
                # 第1列丢弃
                if i == 1:
                    continue

                s = clean_text(td)
                # 第2列: 总市值 from jsl
                if i == 2:
                    row['rank_market_cap'] = s
                # 第3列: 净资产
                elif i == 3:
                    row['rank_net_asset'] = s
                # 第4列: 净利润 from xueqiu
                elif i == 4:
                    row['rank_net_margin'] = s
                # 第5列: 动态市盈率 from xueqiu
                elif i == 5:
                    row['rank_pe'] = s
                # 第6列: 市净率 from xueqiu
                elif i == 6:
                    row['rank_pb'] = s
                # 第7列: 毛利率
                elif i == 7:
                    row['rank_gross_rate'] = s
                # 第8列: 净利率 from xueqiu 利润率
                elif i == 8:
                    row['rank_net_profit_ratio'] = s
                # 第9列: ROE(加权净资产收益率) from xueqiu
                elif i == 9:
                    row['rank_roe'] = s
        # 分位信息
        elif j == 4:
            i = 0
            tds = tr.find_elements_by_tag_name('td')
            for td in tds:
                i += 1
                # 第1列丢弃
                if i == 1:
                    continue

                p = td.find_element_by_tag_name('p')
                s = p.text.strip()
                # 第2列: 总市值 from jsl
                if i == 2:
                    row['level_market_cap'] = s
                # 第3列: 净资产
                elif i == 3:
                    row['level_net_asset'] = s
                # 第4列: 净利润 from xueqiu
                elif i == 4:
                    row['level_net_margin'] = s
                # 第5列: 动态市盈率 from xueqiu
                elif i == 5:
                    row['level_pe'] = s
                # 第6列: 市净率 from xueqiu
                elif i == 6:
                    row['level_pb'] = s
                # 第7列: 毛利率
                elif i == 7:
                    row['level_gross_rate'] = s
                # 第8列: 净利率 from xueqiu 利润率
                elif i == 8:
                    row['level_net_profit_ratio'] = s
                # 第9列: ROE(加权净资产收益率) from xueqiu
                elif i == 9:
                    row['level_roe'] = s
    return row


def clean_text(td):
    s = td.text.strip()
    return change_data_unit(s)


default_clean_text = lambda s: s.replace('亿', '').replace('%', '')

no_clean_text = lambda s: s


def change_data_unit(s, default_change=default_clean_text):
    if s.endswith('万'):
        # 把万转成亿
        s = s.replace('万', '')
        return round(float(s) / 10000, 3)
    else:
        return default_change(s)


def get_stock_sum(stock_code):
    stock_code = common.rebuild_stock_code(stock_code)

    url = "http://quote.eastmoney.com/" + stock_code + '.html'

    # fixme 需要把chromedriver放到/usr/local/bin目录下
    # 创建可见的Chrome浏览器， 方便调试

    driver.get(url)

    return get_sum_data(driver)


if __name__ == "__main__":
    driver = webdriver.Chrome()

    driver.implicitly_wait(10)

    update_stock_sum()
    driver.close()
    # modify_data_unit_error()

# 从东方财富抓正股的相关数据
import datetime
import re
import time

import sqlite3

import common
from selenium import webdriver

driver = None



def do_update_stock_sum():
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
                print("not update stock:" + stock_name + ' in stock_report')
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

# 更新概念题材的配置信息
def update_theme_config():
    # 打开配置文件数据库表
    # 打开东财题材列表(5日, 10日)页面, 抓取数据
    # 删除已有的题材概念信息
    # 更新题材概念信息
    # 关闭数据库

    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    try:
        # 删除已有的数据
        result = con_file.execute("""delete from config where key = 'gn_1' """)
        if result.rowcount == 0:
            print("not delete gn_1 config")
        else:
            print("delete old gn_1 is successful. count:" + str(result.rowcount))

        # 删除已有的数据
        result = con_file.execute("""delete from config where key = 'gn_5' """)
        if result.rowcount == 0:
            print("not delete gn_5 config")
        else:
            print("delete old gn_5 is successful. count:" + str(result.rowcount))

        result = con_file.execute("""delete from config where key = 'gn_10' """)
        if result.rowcount == 0:
            print("not delete gn_10 config")
        else:
            print("delete old gn_10 is successful. count:" + str(result.rowcount))

        i = 0
        # 添加当日数据
        rows = fetch_theme_data(3, '')
        for row in rows:
            result = con_file.execute("""insert into config(order_index,key,value,field_name)values(?, 'gn_1', ?, 'theme')""",
                                      (row[0], row[1])
                                      )
            if result.rowcount == 0:
                print("not insert gn_1 config:" + row)
            else:
                print("insert gn_1 is successful. count:" + str(i + 1))
            i += 1

        # 暂停5s再执行， 避免被网站屏蔽掉
        time.sleep(5)

        # 添加5日数据
        rows = fetch_theme_data(5, '_5')
        for row in rows:
            result = con_file.execute("""insert into config(order_index,key,value,field_name)values(?, 'gn_5', ?, 'theme')""",
                                      (row[0], row[1])
                                      )
            if result.rowcount == 0:
                print("not insert gn_5 config:" + row)
            else:
                print("insert gn_5 is successful. count:" + str(i + 1))
            i += 1

        # 暂停5s再执行， 避免被网站屏蔽掉
        time.sleep(5)

        # 添加10日数据
        rows = fetch_theme_data(10, '_10')
        for row in rows:
            result = con_file.execute("""insert into config(order_index,key,value,field_name)values(?, 'gn_10', ?, 'theme')""",
                                      (row[0], row[1])
                                      )
            if result.rowcount == 0:
                print("not insert gn_10 config:" + row)
            else:
                print("insert gn_10 is successful. count:" + str(i + 1))
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

def update_stock_theme():
    # 遍历可转债列表
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    try:
        # 查询可转债
        bond_cursor = con_file.execute("""SELECT bond_code, cb_name_id, stock_code, stock_name from changed_bond""")

        i = 0
        for bond_row in bond_cursor:
            bond_code = bond_row[0]
            stock_code = bond_row[2]
            stock_name = bond_row[3]

            theme = fetch_stock_theme(stock_code)

            result = con_file.execute("""update changed_bond_extend set theme = ? where bond_code = ?""",
                             (theme, bond_code)
                             )
            if result.rowcount == 0:
                print("not update stock:" + stock_name + ' in changed_bond_extend')
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

        stock_cursor = con_file.execute("""SELECT avg_net_margin, stock_name from stock_report""")
        stocks = list(stock_cursor)

        for stock in stocks:
            avg_net_margin = stock[1]
            stock_name = stock[2]

            if not isinstance(avg_net_margin, str) or not avg_net_margin.endswith('万'):
                continue

            avg_net_margin = change_data_unit(avg_net_margin, no_clean_text)

            con_file.execute("""update stock_report set avg_net_margin = ? where stock_name = ?""",
                             (avg_net_margin, stock_name))

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

# http://data.eastmoney.com/bkzj/gn_5.html
def fetch_theme_data(count, days):
    rows = []
    url = "http://data.eastmoney.com/bkzj/gn" + days + ".html"

    # fixme 需要把chromedriver放到/usr/local/bin目录下
    # 创建可见的Chrome浏览器， 方便调试

    driver.get(url)

    # div = driver.find_elements_by_class_name("dataview-body")[0]

    # trs = driver.find_elements_by_xpath("//div[@class='dataview-body']/table/tbody/tr")
    # 所有的概念行数据
    # trs = div.find_elements_by_xpath('./table/tbody/tr')
    # print('trs len:' + str(len(trs)))
    # # 只取前n的数据
    #
    # counts_a = len(driver.find_elements_by_class('class_name'))
    # for i in range(counts_a):
    #     driver.find_elements_by_xpath('//a[@class="class_name"][i+1]')

    keys = ['转债标的','标准普尔','富时罗素','上证380','央视50_','中证500','深成500','融资融券','上证180_','HS300_','MSCI中国','深股通','创业板综','沪股通']

    for i in range(count):

        # div = driver.find_elements_by_class_name("dataview-body")[0]
        # trs = driver.find_elements_by_xpath("//div[@class='dataview-body']/table/tbody/tr")
        # print('tr len:' + str(len(div.find_elements_by_xpath('./table/tbody/tr'))))
        # s = div.find_elements_by_xpath('./table/tbody/tr[' + str(i+1) + ']')[0].text
        # s = trs[i].text
        s = driver.find_element_by_xpath("//div[@class='dataview-body']/table/tbody/tr[" + str(i+1) + "]").text
        # 排序 题材名 涨幅 净额(亿|万)
        # [('1', 'CAR-T细胞疗法', '4.22%', '19.68')]
        try:
            ss = re.findall(r"(\d+) (.*) 大单详情  股吧 (\d+.?\d*%) (\d+.?\d*)(亿|万)", s)
            ignore = False
            for key in keys:
                if key in ss[0]:
                    ignore = True

            if ignore:
                continue

            rows.append(ss[0])
        except Exception as e:
            # 有时候出现跌幅的数据, 直接忽略掉
            print('count:' + str(count) + ', i:' + str(i) + 's:' + s + ', e:' + str(e))
            # raise e


    return rows

# 抓取题材信息
# http://f10.eastmoney.com/f10_v2/CoreConception.aspx?code=sz002472
def fetch_stock_theme(stock_code):

    stock_code = common.rebuild_stock_code(stock_code)

    url = "http://f10.eastmoney.com/f10_v2/CoreConception.aspx?code=" + stock_code

    # fixme 需要把chromedriver放到/usr/local/bin目录下
    # 创建可见的Chrome浏览器， 方便调试

    driver.get(url)

    divs = driver.find_elements_by_class_name("p_div")

    s = divs[0].text
    ss = re.findall(r"要点一:所属板块 (.*)", s)
    if len(ss) != 1:
        raise Exception("没有找到股票的题材信息:" + s)
    return ss[0]


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

def fetch_data():
    driver = webdriver.Chrome()

    driver.implicitly_wait(10)

    print('更新股票的关键指标信息')
    do_update_stock_sum()

    # print('更新概念题材信息')
    # update_stock_theme()

    # print('更新题材概念配置信息')
    # update_theme_config()

    driver.close()
    # modify_data_unit_error()
    return 'OK'

if __name__ == "__main__":
    fetch_data()

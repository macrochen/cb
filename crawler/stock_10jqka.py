# 从同花顺抓正股的相关数据
import datetime
import re
import sqlite3
import time

from selenium import webdriver

from utils.db_utils import get_connect

driver = None


def update_stock_sum():
    # 遍历可转债列表
    # 打开文件数据库
    con_file = get_connect()

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
            if stocks[0][0] is not None and stocks[0][0] > s:
                continue

            row = get_stock_sum(stock_code)

            result = con_file.execute("""update stock_report set 
                stock_total = ?, 
                stock_level = ?, 
                trade_suggest = ?, 
                fact_trend = ?, 
                fact_money = ?, 
                fact_news = ?, 
                fact_industry = ?, 
                fact_base = ?, 
                modify_date = ? where stock_code = ?""",
             (
                 row['stock_total'],
                 row['stock_level'],
                 row['trade_suggest'],
                 row['fact_trend'],
                 row['fact_money'],
                 row['fact_news'],
                 row['fact_industry'],
                 row['fact_base'],
              s, stock_code)
             )
            if result.rowcount == 0:
                print("not update stock:" + stock_name)
            else:
                print("update " + stock_name + " is successful. count:" + str(i + 1))

            # 暂停5s再执行， 避免被网站屏蔽掉
            time.sleep(3)
            i += 1

        print("共处理" + str(i) + "条记录")

    except Exception as e:
        # con_file.close()
        print("db操作出现异常" + str(e), e)
        raise e
    except TimeoutError as e:
        print("网络超时, 请手工重试")
        raise e

    finally:
        con_file.commit()
        con_file.close()


def get_sum_data(driver):
    row = {}

    box = driver.find_element_by_class_name("box1")

    # 综合评分, 全市场位置
    div = box.find_element_by_class_name('stocktotal')
    # 综合诊断：5.5分 打败了52%的股票！
    list = re.findall(r"\d+\.?\d*", div.text)

    row['stock_total'] = list[0]
    row['stock_level'] = list[1]

    # 操作建议
    span = box.find_element_by_class_name('cur')
    row['trade_suggest'] = span.text

    # 技术面, 资金面, 消息面, 赛道行业, 基本面得分
    divs = box.find_elements_by_class_name('label')
    row['fact_trend'] = divs[0].text.replace('分', '')
    row['fact_money'] = divs[1].text.replace('分', '')
    row['fact_news'] = divs[2].text.replace('分', '')
    row['fact_industry'] = divs[3].text.replace('分', '')
    row['fact_base'] = divs[4].text.replace('分', '')

    return row


def get_stock_sum(stock_code):
    # http://doctor.10jqka.com.cn/002002/
    url = "http://doctor.10jqka.com.cn/" + stock_code

    # fixme 需要把chromedriver放到/usr/local/bin目录下
    driver.get(url)

    return get_sum_data(driver)


def fetch_data():
    driver = webdriver.Chrome()

    driver.implicitly_wait(10)

    update_stock_sum()
    # print(get_stock_sum('002002'))
    driver.close()
    # modify_data_unit_error()
    return 'OK'

if __name__ == "__main__":
    fetch_data()

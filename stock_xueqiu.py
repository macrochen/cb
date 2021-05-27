# 从雪球抓正股的相关数据
import datetime
import json
import time

import requests
import bs4
import html5lib
from lxml import etree
import sqlite3

import common

header = {
    "origin": "https://xueqiu.com",
    "Referer": "https://xueqiu.com",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
    'Cookie': "aliyungf_tc=AQAAAEiUhlwL1gcAfkp4KtSXEQtnlZoE; __utmc=1; __utmz=1.1598963525.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); device_id=24700f9f1986800ab4fcc880530dd0ed; s=df1gw1c0ee; bid=1ed9409e593e78e912960284cfcd25ac_kmpw61pm; Hm_lvt_1db88642e346389874251b5a1eded6e3=1619750392; __utma=1.479761015.1598963525.1617020762.1619750392.7; acw_tc=2760820416202904715137216e07c8ffbb213964918733cc1d4bb3af58de55; remember=1; xq_a_token=3c59ab655f8b90a05ffac42f26934b9a22ad0844; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjIzOTM1NDMwMjAsImlzcyI6InVjIiwiZXhwIjoxNjIyMzQyMzg5LCJjdG0iOjE2MjAyOTA5Mjk4MjAsImNpZCI6ImQ5ZDBuNEFadXAifQ.M2jpA5t9HzUZs1KXVT202Hu1xvWHbpBJqPHlYatDQzUfcOzBfCiscfaAUVB58EQiMEzDPDEWAj51Kgmfsj4YnwflOKIAbT0UTvdP2RXs3w-Nf3jJ1eRjZfNiZ8dwlJmrCLL8kekdc01PGfauMtJ_rncgOGANlzJj4MZHcMGM_jWVdHlD-yQdRvbp6yVir6D_pkYq41VrXJ40nv_B3x73i9JspRfyFTfSWgwIytyzRPk1TRWyEJKi41ITWIE8GPALLVQSGCYYpAnfdGd83nENI-7HMmZSOoleESQS2vQcZrGyk9RzVw2pqPUbCGJmN_82d4qsOc-60w0wNRqy2CdyfA; xqat=3c59ab655f8b90a05ffac42f26934b9a22ad0844; xq_r_token=d4d67031d59d9d635ece80e39d3ba96005e492d1; xq_is_login=1; u=2393543020; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1620290932"
}

def createDb():

    con = sqlite3.connect("db/cb.db3")
    # 只执行一次
    con.executescript("""
        drop table if exists stock_report;
        create table if not exists stock_report(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bond_code text NOT NULL, 
            cb_name_id text NOT NULL,
            
            stock_code text NOT NULL,
            stock_name text NOT NULL,
            
            last_date text NOT NULL,
            
            revenue real,
            qoq_revenue_rate real,
            yoy_revenue_rate real,
            
            net real,
            qoq_net_rate real,
            yoy_net_rate real,
            
            margin real,
            qoq_margin_rate real,
            yoy_margin_rate real,
            
            roe real,
            qoq_roe_rate real,
            yoy_roe_rate real,
            
            al_ratio real,
            qoq_rl_ratio_rate real,
            yoy_al_ratio_rate real,
            
            pe real
            
            )""")

    con.commit()
    con.close()
    print("create db is successful")


def getContent():
    # test data

    # soup = bs4.BeautifulSoup(s, "html5lib")
    # ss = soup.text

    # print(ss)

    # 遍历可转债列表
    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    try:

        # 当前报告期
        report_date = get_report_date()

        # 查询可转债

        bond_cursor = con_file.execute("""
            SELECT bond_code, cb_name_id, stock_code, stock_name from changed_bond
        """)

        i = 0
        for bond_row in bond_cursor:

            bond_code = bond_row[0]
            stock_code = bond_row[2]
            stock_name = bond_row[3]

            stock_cursor = con_file.execute("SELECT bond_code, stock_code, last_date from stock_report where bond_code = " + bond_code)

            stocks = list(stock_cursor)
            # 还没添加正股财务指标信息
            if len(stocks) == 0:
                earnings = getEarnings(stock_code)
                # 新增
                con_file.execute("""insert into stock_report(bond_code,cb_name_id,stock_code,stock_name,
                            last_date,
                            revenue,qoq_revenue_rate,yoy_revenue_rate,
                            net,qoq_net_rate,yoy_net_rate,
                            margin,qoq_margin_rate,yoy_margin_rate,
                            roe,qoq_roe_rate,yoy_roe_rate,
                            al_ratio,qoq_rl_ratio_rate,yoy_al_ratio_rate)
                         values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                 (bond_row[0], bond_row[1], bond_row[2], bond_row[3],
                                  earnings.lastDate,

                                  earnings.revenue,
                                  earnings.qoqRevenueRate,
                                  earnings.yoyRevenueRate,

                                  earnings.net,
                                  earnings.qoqNetRate,
                                  earnings.yoyNetRate,

                                  earnings.margin,
                                  earnings.qoqMarginRate,
                                  earnings.yoyMarginRate,

                                  earnings.roe,
                                  earnings.qoqRoeRate,
                                  earnings.yoyRoeRate,

                                  earnings.alRatio,
                                  earnings.qoqAlRatioRate,
                                  earnings.yoyAlRatioRate
                                  )
                                 )
                print("insert " + stock_name + " is successful. count:" + str(i+1))
                # 暂停10s再执行， 避免被网站屏蔽掉
                time.sleep(20)
                i += 1
            else:
                # todo 补充前面几年/季度的财务数据
                # fixme 为了解决中途被中断， 继续执行时， 简化处理不更新
                # continue
                last_date = stocks[0][2]

                if last_date != report_date:
                    earnings = getEarnings(stock_code)
                    con_file.execute("""update stock_report
                                set last_date = ?,
                                revenue = ?,qoq_revenue_rate = ?,yoy_revenue_rate = ?,
                                net = ?,qoq_net_rate = ?,yoy_net_rate = ?,
                                margin = ?,qoq_margin_rate = ?,yoy_margin_rate = ?,
                                roe = ?,qoq_roe_rate = ?,yoy_roe_rate = ?,
                                al_ratio = ?,qoq_rl_ratio_rate = ?,yoy_al_ratio_rate = ?
                             where bond_code = ?""",
                                     (earnings.lastDate,

                                      earnings.revenue,
                                      earnings.qoqRevenueRate,
                                      earnings.yoyRevenueRate,

                                      earnings.net,
                                      earnings.qoqNetRate,
                                      earnings.yoyNetRate,

                                      earnings.margin,
                                      earnings.qoqMarginRate,
                                      earnings.yoyMarginRate,

                                      earnings.roe,
                                      earnings.qoqRoeRate,
                                      earnings.yoyRoeRate,

                                      earnings.alRatio,
                                      earnings.qoqAlRatioRate,
                                      earnings.yoyAlRatioRate,

                                      bond_code
                                      )
                                     )
                    print("update " + stock_name + " is successful. count:" + str(i+1))
                    # 暂停10s再执行， 避免被网站屏蔽掉
                    time.sleep(20)
                    i += 1

        print("共处理" + str(i) + "条记录")

    except Exception as e:
        con_file.close()
        print("db操作出现异常" + str(e), e)
    finally:
        con_file.commit()
        con_file.close()


def get_report_date():
    # 计算最近的报告期
    report_dates = {331: '03-31', 630: '06-30', 930: '09-30', 1231: '12-31'}
    # 当前日月
    y = datetime.datetime.now().year
    m = datetime.datetime.now().month
    d = datetime.datetime.now().day
    current = m * 100 + d
    count = 0
    for key, value in report_dates.items():
        if key < current:
            count += 1
            continue

        return str(y) + "-" + list(report_dates.values())[count - 1]

    raise Exception('计算报告期错误')


def getData(url):
    i = 0
    while i < 3:
        try:
            response = requests.get(url=url, headers=header, timeout=5)
            code = response.status_code
            if code != 200:
                print("获取数据失败， 状态码：" + str(code))

            return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            i += 1
            print("connect occur error. retry time: " + str(i) + "e" + str(e))

    raise TimeoutError

def getEarnings(stock_code):
    stock_code = common.rebuild_stock_code(stock_code)

    url = "https://stock.xueqiu.com/v5/stock/finance/cn/indicator.json?symbol=" + stock_code + "&type=all&is_detail=true&count=5&timestamp=" + str(int(round(time.time() * 1000)))
    # # response = requests.get(url=url)

    data = getData(url)
    row = data['data']['list'][0]
    # print(row)
    pre_row = data['data']['list'][4]

    earnings = Earnings()

    earnings.lastDate = time.strftime("%Y-%m-%d", time.localtime(row['report_date']/1000))
    # 营收
    earnings.revenue = round(row['total_revenue'][0]/100000000, 2)
    # 同比增长率
    earnings.yoyRevenueRate = round(row['total_revenue'][1]*100, 2)

    # 净利润
    earnings.net = round(row['net_profit_atsopc'][0]/100000000, 2)
    # 同比增长率
    earnings.yoyNetRate = round(row['net_profit_atsopc'][1]*100, 2)

    # 利润率
    earnings.margin = round(row['net_profit_atsopc'][0]/row['total_revenue'][0]*100, 2)
    pre_margin = round(pre_row['net_profit_atsopc'][0] / pre_row['total_revenue'][0] * 100, 2)
    # 同比增长率
    earnings.yoyMarginRate = round((earnings.margin - pre_margin)/pre_margin * 100, 2)

    # 资产负债率
    earnings.alRatio = round(row['asset_liab_ratio'][0], 2)
    # 同比增长率
    earnings.yoyAlRatioRate = round(row['asset_liab_ratio'][1]*100, 2)

    # roe
    earnings.roe = row['avg_roe'][0]
    # 同比增长率
    earnings.yoyRoeRate = round(row['avg_roe'][1]*100, 2)

    # print(earnings)
    return earnings

def noConvert(val):
    return val

def convert(val):
    return round(val/10000, 4)

#每一条财报记录
class Record:
    # 当前报告期的值
    lastValue = 0
    # 上一年的值
    yoyValue = 0
    # 同比增长率
    yoyRate = 0

    # 前一个财报值
    preValue = 0

    # 当前季度值
    curQoqValue = 0
    # 前一个季度值
    preQoqValue = 0

    # 环比增长率
    qoqRate = 0

    def parseData(self, tds, convert=noConvert):
        # 最近的值
        self.lastValue = convert(float(tds[0].text.replace(',', '')))
        # 上一年的值
        self.yoyValue = convert(float(tds[4].text.replace(',', '')))
        # 同比增长率
        self.yoyRate = round((self.lastValue - self.yoyValue)*100 / self.yoyValue, 2)

        # 前一个财报值
        self.preValue = convert(float(tds[1].text.replace(',', '')))
        # 当前季度值
        self.curQoqValue = round(self.lastValue - self.preValue, 4)
        # 前前一个财报值
        prePreValue = convert(float(tds[2].text.replace(',', '')))
        # 前一个季度值
        self.preQoqValue = round(self.preValue - prePreValue, 4)

        # 环比增长率
        self.qoqRate = round((self.curQoqValue - self.preQoqValue)*100 / self.preQoqValue, 2)

# 财报信息
class Earnings:
    lastDate = ''
    # 营收
    revenue = 0
    # 当季
    curQoqRevenue = 0
    # 上一季
    preQoqRevenue = 0
    # 上一年
    yoyRevenue = 0
    # 环比
    qoqRevenueRate = 0
    # 同比
    yoyRevenueRate = 0

    def calcRevenue(self, tds):
        record = Record()
        record.parseData(tds, convert)
        self.revenue = record.lastValue
        self.curQoqRevenue = record.curQoqValue
        self.preQoqRevenue = record.preQoqValue
        self.yoyRevenue = record.yoyValue
        self.qoqRevenueRate = record.qoqRate
        self.yoyRevenueRate = record.yoyRate

    # 净利润
    net = 0
    # 当季
    curQoqNet = 0
    # 上季
    preQoqNet = 0
    # 上一年
    yoyNet = 0
    # 环比
    qoqNetRate = 0
    # 同比
    yoyNetRate = 0

    def calcNet(self, tds):
        record = Record()
        record.parseData(tds, convert)
        self.net = record.lastValue
        self.curQoqNet = record.curQoqValue
        self.preQoqNet = record.preQoqValue
        self.yoyNet = record.yoyValue
        self.qoqNetRate = record.qoqRate
        self.yoyNetRate = record.yoyRate

    # 利润率
    margin = 0
    # 当季
    curQoqMargin = 0
    # 上一季
    preQoqMargin = 0
    # 上一年
    yoyMargin = 0
    # 环比
    qoqMarginRate = 0
    # 同比
    yoyMarginRate = 0

    def calcMargin(self):
        self.margin = round(self.net * 100 / self.revenue, 2)

        # 当前季的利润率 = 当前季度利润/当前季度营收
        self.curQoqMargin = round(self.curQoqNet * 100 / self.curQoqRevenue, 2)
        # 上一季度利润率 = 上一季度利润/上一季度营收
        self.preQoqMargin = round(self.preQoqNet * 100 / self.preQoqRevenue, 2)

        # 环比 = (当前季 - 上一季)/上一季
        self.qoqMarginRate = round((self.curQoqMargin - self.preQoqMargin) * 100 / self.preQoqMargin, 2)

        # 上一年利润率 = 上一年利润/上一年营收
        self.yoyMargin = round(self.yoyNet * 100 / self.yoyRevenue, 2)
        # 同比 = (当前利润率 - 上一年利润率)/上一年利润率
        self.yoyMarginRate = round((self.margin - self.yoyMargin) * 100 / self.yoyMargin, 2)

    # 净资产收益率
    roe = 0
    # 环比
    qoqRoeRate = 0
    # 同比
    yoyRoeRate = 0

    def calcRoe(self, tds):
        record = Record()
        record.parseData(tds)
        self.roe = record.lastValue
        self.qoqRoeRate = record.qoqRate
        self.yoyRoeRate = record.yoyRate

    # 资产负债率
    alRatio = 0
    # 环比
    qoqAlRatioRate = 0
    # 同比
    yoyAlRatioRate = 0

    def calcAlRatio(self, assetsTds, debtTds):
        # 总资产
        record1 = Record()
        record1.parseData(assetsTds, convert)
        assets = record1.lastValue
        # 总负债
        record2 = Record()
        record2.parseData(debtTds, convert)
        debt = record2.lastValue

        #资产负债率
        self.alRatio = round(debt * 100 / assets, 2)

        #环比
        #当季负债率
        curQoqRatio = round(record2.curQoqValue * 100 / record1.curQoqValue, )
        #上季负债率
        preQoqRatio = round(record2.preQoqValue * 100 / record1.preQoqValue, 2)
        self.qoqAlRatioRate = round((curQoqRatio - preQoqRatio) * 100/preQoqRatio, 2)

        #同比
        #上一年
        yoyAlRatio = round(record2.yoyValue * 100 / record1.yoyValue, 2)
        self.yoyAlRatioRate = round((self.alRatio - yoyAlRatio) * 100 / yoyAlRatio, 2)

if __name__ == "__main__":
    # createDb()
    getContent()

    # getEarnings('600061')

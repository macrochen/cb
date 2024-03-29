# 从雪球抓正股的相关数据
import datetime
import json
import time

import requests

from utils import trade_utils, db_utils
from utils.db_utils import get_cursor
from utils.task_utils import *

header = {
    "origin": "https://xueqiu.com",
    "Referer": "https://xueqiu.com",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
    'Cookie': "aliyungf_tc=AQAAAEiUhlwL1gcAfkp4KtSXEQtnlZoE; __utmc=1; s=df1gw1c0ee; bid=1ed9409e593e78e912960284cfcd25ac_kmpw61pm; snbim_minify=true; xq_is_login=1; device_id=c34b51214fd6837799a41c7d130ffa00; u=2393543020; xq_a_token=bc1d0d5a798994377839ac6ef4482049da20635c; xqat=bc1d0d5a798994377839ac6ef4482049da20635c; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjIzOTM1NDMwMjAsImlzcyI6InVjIiwiZXhwIjoxNjM3MjAwNTQ4LCJjdG0iOjE2MzQ2MDg1NDg3NTUsImNpZCI6ImQ5ZDBuNEFadXAifQ.dfZA0AVFto0RrbkQIcbdjD-M2-FXzTyE1RkYzfAlmsVMFoG_YHwUolXE5z8Gq8rF2NeVz7DlupuDy-ozTeQ7EqS1qCFGv9VSWYD0IssFk4lvvYhjEs8QC3mjC_AxCtwR4KsUJP8GgvX45nt2c20kNaa_PJW_5Hwsa8qsqjjat2yq4wNy17PWqQnqZ-L24UkdjbzpOrr2BnkPJqTi_AKhNijrwT6UWqJ8_of0o7WejOLKClrM2cmyWtW8YYNZE7kaWwFx7bV7r3CAW9R8tgieOI_dhWcsZCc8tbbKhK4_Xx5mehxAqdIGa2rR_--sBKxprsd4P-zTJrjhmLxoAWpCaw; xq_r_token=2776fc5ffe147f1af61ffbe96202ae4fd6b51665; __utma=1.479761015.1598963525.1635569326.1635766060.48; __utmz=1.1635766060.48.19.utmcsr=localhost:8080|utmccn=(referral)|utmcmd=referral|utmcct=/; Hm_lvt_1db88642e346389874251b5a1eded6e3=1635231661,1635569325,1635766060,1635826354; acw_tc=3ccdc14516358412138375706e456b619e8340f8c18b5e6be56fb0fbf44111; is_overseas=0; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1635841221"
}

def create_db():

    with db_utils.get_connect() as con:
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

    print("create db is successful")


def fetch_data(task_name):

    # 遍历可转债列表

    stock_name = ''
    stock_code = None
    earnings = None

    task = None
    try:

        # 当前报告期
        report_date = get_report_date()

        # 查询可转债

        bond_cursor = get_cursor("""
            SELECT bond_code, cb_name_id, stock_code, stock_name from changed_bond
        """)
        rows = bond_cursor.fetchall()
        task, status = new_or_update_task(len(rows), task_name)
        if status == -1:  # 有任务在执行
            return

        i = 0
        for bond_row in rows:
            process_task_when_normal(task, 1)

            stock_code = bond_row[2]
            stock_name = bond_row[3]

            stock_cursor = get_cursor("SELECT last_date from stock_report where stock_code = '" + stock_code + "'")

            stocks = list(stock_cursor)
            # 还没添加正股财务指标信息
            if len(stocks) == 0:
                earnings = get_earnings(stock_code)
                # 新增

                rowcount = db_utils.execute_sql_with_rowcount("""insert into stock_report(stock_code,stock_name,
                                            last_date,
                                            revenue,qoq_revenue_rate,yoy_revenue_rate,
                                            net,qoq_net_rate,yoy_net_rate,
                                            margin,qoq_margin_rate,yoy_margin_rate,
                                            roe,qoq_roe_rate,yoy_roe_rate,
                                            al_ratio,qoq_rl_ratio_rate,yoy_al_ratio_rate)
                         values(:stock_code,:stock_name,
                            :last_date,
                            :revenue,:qoq_revenue_rate,:yoy_revenue_rate,
                            :net,:qoq_net_rate,:yoy_net_rate,
                            :margin,:qoq_margin_rate,:yoy_margin_rate,
                            :roe,:qoq_roe_rate,:yoy_roe_rate,
                            :al_ratio,:qoq_rl_ratio_rate,:yoy_al_ratio_rate)""",
                                                              {'stock_code':bond_row[2], 'stock_name':bond_row[3],
                                  'last_date':earnings.lastDate,

                                  'revenue':earnings.revenue,
                                  'qoq_revenue_rate':earnings.qoqRevenueRate,
                                  'yoy_revenue_rate':earnings.yoyRevenueRate,

                                  'net':earnings.net,
                                  'qoq_net_rate':earnings.qoqNetRate,
                                  'yoy_net_rate':earnings.yoyNetRate,

                                  'margin':earnings.margin,
                                  'qoq_margin_rate':earnings.qoqMarginRate,
                                  'yoy_margin_rate':earnings.yoyMarginRate,

                                  'roe':earnings.roe,
                                  'qoq_roe_rate':earnings.qoqRoeRate,
                                  'yoy_roe_rate':earnings.yoyRoeRate,

                                  'al_ratio':earnings.alRatio,
                                  'qoq_rl_ratio_rate':earnings.qoqAlRatioRate,
                                  'yoy_al_ratio_rate':earnings.yoyAlRatioRate,
                                  }
                                                              )
                if rowcount == 0:
                    print("insert " + stock_name + " is failure. count:" + str(i+1))
                else:
                    print("insert " + stock_name + " is successful. count:" + str(i+1))
            else:
                # todo 补充前面几年/季度的财务数据
                # fixme 为了解决中途被中断， 继续执行时， 简化处理不更新
                # continue
                last_date = stocks[0][0]

                if last_date != report_date:
                    earnings = get_earnings(stock_code)
                    rowcount = db_utils.execute_sql_with_rowcount("""update stock_report
                                set last_date = :last_date,
                                revenue = :revenue,qoq_revenue_rate = :qoq_revenue_rate,yoy_revenue_rate = :yoy_revenue_rate,
                                net = :net,qoq_net_rate = :qoq_net_rate,yoy_net_rate = :yoy_net_rate,
                                margin = :margin,qoq_margin_rate = :qoq_margin_rate,yoy_margin_rate = :yoy_margin_rate,
                                roe = :roe,qoq_roe_rate = :qoq_roe_rate,yoy_roe_rate = :yoy_roe_rate,
                                al_ratio = :al_ratio,qoq_rl_ratio_rate = :qoq_rl_ratio_rate,yoy_al_ratio_rate = :yoy_al_ratio_rate
                             where stock_code = :stock_code""",
                                    {'last_date':earnings.lastDate,

                                      'revenue':earnings.revenue,
                                      'qoq_revenue_rate':earnings.qoqRevenueRate,
                                      'yoy_revenue_rate':earnings.yoyRevenueRate,

                                      'net':earnings.net,
                                      'qoq_net_rate':earnings.qoqNetRate,
                                      'yoy_net_rate':earnings.yoyNetRate,

                                      'margin':earnings.margin,
                                      'qoq_margin_rate':earnings.qoqMarginRate,
                                      'yoy_margin_rate':earnings.yoyMarginRate,

                                      'roe':earnings.roe,
                                      'qoq_roe_rate':earnings.qoqRoeRate,
                                      'yoy_roe_rate':earnings.yoyRoeRate,

                                      'al_ratio':earnings.alRatio,
                                      'qoq_rl_ratio_rate':earnings.qoqAlRatioRate,
                                      'yoy_al_ratio_rate':earnings.yoyAlRatioRate,

                                      'stock_code':stock_code
                                }
                                                                  )
                    if rowcount == 0:
                        print("update " + stock_name + " is failure. count:" + str(i+1))
                    else:
                        print("update " + stock_name + " is successful. count:" + str(i+1))
            # 暂停3s再执行， 避免被网站屏蔽掉
            time.sleep(3)
            i += 1

        ok_desc = "共处理" + str(i) + "条记录"
        print(ok_desc)
        process_task_when_finish(task, ok_desc)
    except Exception as e:
        print("db操作出现异常" + str(e) + ', stock_code: ' + stock_code + ', stock_name:' + stock_name + ', earnings:' + str(earnings), e)
        process_task_when_error(task, "db操作出现异常")
        raise e
    return 'OK'


def get_report_date():
    # 计算最近的报告期
    report_dates = {331: '03-31', 630: '06-30', 930: '09-30', 1231: '12-31'}
    # 当前日月
    y = datetime.now().year
    m = datetime.now().month
    d = datetime.now().day
    current = m * 100 + d
    count = 0
    for key, value in report_dates.items():
        if key < current:
            count += 1
            continue

        return str(y) + "-" + list(report_dates.values())[count - 1]

    raise Exception('计算报告期错误')


def get_data(url):
    i = 0
    while i < 3:
        try:
            response = requests.get(url=url, headers=header, timeout=5)
            code = response.status_code
            if code != 200:
                print("获取数据失败， 状态码：" + str(code) + ', url:' + url)

            return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            i += 1
            print("connect occur error. retry time: " + str(i) + "e" + str(e))

    raise TimeoutError


def get_earnings(stock_code):
    stock_code = trade_utils.rebuild_stock_code(stock_code)

    url = "https://stock.xueqiu.com/v5/stock/finance/cn/indicator.json?symbol=" + stock_code + "&type=all&is_detail=true&count=5&timestamp=" + str(int(round(time.time() * 1000)))
    # # response = requests.get(url=url)

    data = get_data(url)
    row = data['data']['list'][0]
    # print(row)
    pre_row = data['data']['list'][4]

    earnings = Earnings()

    earnings.lastDate = time.strftime("%Y-%m-%d", time.localtime(row['report_date']/1000))
    # 营收
    earnings.revenue = round(row['total_revenue'][0]/100000000, 2)
    # 同比增长率
    earnings.yoyRevenueRate = None if row['total_revenue'][1] is None else round(row['total_revenue'][1]*100, 2)

    # 净利润
    earnings.net = round(row['net_profit_atsopc'][0]/100000000, 2)
    # 同比增长率
    earnings.yoyNetRate = None if row['net_profit_atsopc'][1] is None else round(row['net_profit_atsopc'][1]*100, 2)

    # 利润率
    earnings.margin = round(row['net_profit_atsopc'][0]/row['total_revenue'][0]*100, 2)
    pre_margin = round(pre_row['net_profit_atsopc'][0] / pre_row['total_revenue'][0] * 100, 2)
    # 同比增长率
    earnings.yoyMarginRate = round((earnings.margin - pre_margin)/pre_margin * 100, 2)

    # 资产负债率
    earnings.alRatio = round(row['asset_liab_ratio'][0], 2)
    # 同比增长率
    earnings.yoyAlRatioRate = None if row['asset_liab_ratio'][1] is None else round(row['asset_liab_ratio'][1]*100, 2)

    # roe
    earnings.roe = row['avg_roe'][0]
    # 同比增长率
    earnings.yoyRoeRate = None if row['avg_roe'][1] is None else round(row['avg_roe'][1] * 100, 2)

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
    yoyRoeRate = None


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

    def __str__(self):
        return 'lastDate:' + self.lastDate + \
        ', revenue:' + str(self.revenue) + \
        ', curQoqRevenue:' + str(self.curQoqRevenue) + \
        ', preQoqRevenue:' + str(self.preQoqRevenue) + \
        ', yoyRevenue:' + str(self.yoyRevenue) + \
        ', qoqRevenueRate:' + str(self.qoqRevenueRate) + \
        ', yoyRevenueRate:' + str(self.yoyRevenueRate) + \
        ', net:' + str(self.net) + \
        ', curQoqNet:' + str(self.curQoqNet) + \
        ', preQoqNet:' + str(self.preQoqNet) + \
        ', yoyNet:' + str(self.yoyNet) + \
        ', qoqNetRate:' + str(self.qoqNetRate) + \
        ', yoyNetRate:' + str(self.yoyNetRate) + \
        ', margin:' + str(self.margin) + \
        ', curQoqMargin:' + str(self.curQoqMargin) + \
        ', preQoqMargin:' + str(self.preQoqMargin) + \
        ', yoyMargin:' + str(self.yoyMargin) + \
        ', qoqMarginRate:' + str(self.qoqMarginRate) + \
        ', yoyMarginRate:' + str(self.yoyMarginRate) + \
        ', roe:' + str(self.roe) + \
        ', qoqRoeRate:' + str(self.qoqRoeRate) + \
        ', yoyRoeRate:' + str(self.yoyRoeRate) + \
        ', alRatio:' + str(self.alRatio) + \
        ', qoqAlRatioRate:' + str(self.qoqAlRatioRate) + \
        ', yoyAlRatioRate:' + str(self.yoyAlRatioRate)

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
    print('更新正股财报信息')
    fetch_data()

    # getEarnings('600061')

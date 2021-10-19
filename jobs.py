# -*- coding: utf-8 -*-
import re
import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from crawler import cb_ninwen, crawler_utils
from models import InvestYield, db, HoldBond, HoldBondHistory
from utils import trade_utils
from utils.db_utils import get_cursor, execute_sql_with_rowcount
from utils.trade_utils import get_ymd, calc_mid_data


def init_job():
    scheduler = BackgroundScheduler()
    # 每天上午交易结束之后执行可转债数据同步
    scheduler.add_job(sync_cb_data_job, 'cron', hour='11', minute='35')
    # 每天下午交易结束之后执行可转债数据同步并更新收益率
    scheduler.add_job(update_data_job_when_trade_is_end, 'cron', hour='15', minute='35')
    scheduler.start()


def sync_cb_data_job():
    print("begin to sync data job...")
    try:
        # 检查是否交易日
        if trade_utils.is_trade_date() is False:
            return 'OK'

        # 先同步一下可转债数据
        cb_ninwen.fetch_data()
    except Exception as e:
        print('sync_cb_data_job is failure. ', e)


def update_data_job_when_trade_is_end():
    print('begin to update yield job...')
    try:
        do_update_data_when_trade_is_end()
    except Exception as e:
        print('update_bond_yield_job is failure', e)


def do_update_data_when_trade_is_end():
    # 检查是否交易日
    if trade_utils.is_trade_date() is False:
        return 'OK'

    # 更新当天的可转债数据
    cb_ninwen.fetch_data()

    ymd = get_ymd()

    # 将已全部卖掉(持有数量为0)的可转债归档
    archive_bond(ymd)

    # 更新当天的收益
    update_yield(ymd)

    # 更新可转债价格中位数
    update_cb_index()

    return 'OK'


def update_cb_index():
    mid_price, temp = calc_mid_data()
    # 检查当天记录已经存在, 存在则更新
    cur = get_cursor("select count(*) from cb_index_history where strftime('%Y-%m-%d', date) = strftime('%Y-%m-%d', date())")
    one = cur.fetchone()
    if one[0] == 0:
        count = execute_sql_with_rowcount("""insert into cb_index_history(mid_price) values(:mid_price)""",
                   {'mid_price': mid_price})
        if count == 1:
            print('insert today\'s mid_price is successful.')
    else:
        count = execute_sql_with_rowcount("""update cb_index_history set mid_price=:mid_price where strftime('%Y-%m-%d', date) = strftime('%Y-%m-%d', date())""",
                                          {'mid_price': mid_price})
        if count == 1:
            print('update today\'s mid_price is successful.')


def update_yield(ymd):
    # 获取最新收益率
    day_yield, all_yield = calc_yield()
    # 获取可转债等权, 沪深300涨跌幅信息 from: https://www.ninwin.cn/index.php?m=cb&c=idx
    cb_day_yield, hs_day_yield = get_up_down_data()
    # 去掉时分秒
    d = datetime.strptime(ymd, '%Y-%m-%d')
    s = int(time.mktime(d.timetuple()))
    # 获取上一个交易日的净值, 计算今天的净值
    previous = db.session.query(InvestYield).filter(InvestYield.date < s).order_by(InvestYield.date.desc()).first()
    if previous is None:
        raise Exception('没找到前一个交易日的记录')
    my_net_value = previous.my_net_value + day_yield
    cb_net_value = previous.cb_net_value + cb_day_yield
    hs_net_value = previous.hs_net_value + hs_day_yield
    invest_yield = db.session.query(InvestYield).filter(InvestYield.date == s).first()
    if invest_yield is None:
        invest_yield = InvestYield()
        invest_yield.date = s
        invest_yield.date_string = ymd

        invest_yield.all_yield = all_yield
        invest_yield.day_yield = day_yield

        invest_yield.cb_day_yield = cb_day_yield
        invest_yield.hs_day_yield = hs_day_yield

        invest_yield.my_net_value = my_net_value
        invest_yield.cb_net_value = cb_net_value
        invest_yield.hs_net_value = hs_net_value
        db.session.add(invest_yield)
    else:
        invest_yield.all_yield = all_yield
        invest_yield.day_yield = day_yield

        invest_yield.cb_day_yield = cb_day_yield
        invest_yield.hs_day_yield = hs_day_yield

        invest_yield.my_net_value = my_net_value
        invest_yield.cb_net_value = cb_net_value
        invest_yield.hs_net_value = hs_net_value
    db.session.commit()


def archive_bond(ymd):
    bonds = db.session.query(HoldBond).filter(HoldBond.hold_amount == 0).all()
    if len(bonds) > 0:
        new_bonds = []
        for bond in bonds:
            history = HoldBondHistory()
            history.copy(bond)
            history.end_date = ymd
            new_bonds.append(history)

        # 保证数据一致性
        try:
            db.session.add_all(new_bonds)
            db.session.query(HoldBond).filter(HoldBond.hold_amount == 0).delete()
            db.session.commit()
        except Exception as err:
            print('move bond to history is failure: ex:' + str(err))
            db.session.rollback()


def get_up_down_data():
    driver = crawler_utils.get_chrome_driver("https://www.ninwin.cn/index.php?m=cb&c=idx", 15)

    div = driver.find_elements_by_xpath(
        "//div[contains(@style,'font-size: 12px;color: gray;margin: 10px 20px;clear: both')]")[0]

    # 最新涨跌：可转债等权：1.57%，上证转债：0.87%，正股等权：2.22%，沪深300：0.67%，中证500：1.33%说明快照'
    s = div.text
    cb_value = re.findall(r"可转债等权：(-?\d+\.?\d*)%", s)
    if len(cb_value) != 1:
        raise Exception("没有找到可转债等权:" + s)

    hs_value = re.findall(r"沪深300：(-?\d+\.?\d*)%", s)
    if len(hs_value) != 1:
        raise Exception("没有找到沪深300:" + s)

    driver.close()
    return float(cb_value[0]), float(hs_value[0])


def calc_yield():
    cur = get_cursor("""
SELECT    
	round(sum(round((c.cb_price2_id/(1+c.cb_mov2_id) * c.cb_mov2_id)*h.hold_amount, 2)) /    sum(h.sum_buy-h.sum_sell)*100,2)  as '日收益率',
	round(sum(round(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy, 3)) /sum(h.sum_buy - h.sum_sell) * 100, 2)  as 累积收益率
from (select hold_amount, sum_buy, hold_owner, bond_code, sum_sell from hold_bond union select hold_amount, sum_buy, hold_owner, bond_code, sum_sell from hold_bond_history) h , changed_bond c 
where h.bond_code = c.bond_code and hold_owner='me'
        """)

    row = cur.fetchone()
    day_yield = row[0]
    all_yield = row[1]
    return day_yield, all_yield


if __name__ == "__main__":
    sync_cb_data_job()

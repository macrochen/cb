# -*- coding: utf-8 -*-
import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

import cb_ninwen
import common
import trade_utils
from models import InvestYield, db


def init_job():
    scheduler = BackgroundScheduler()
    # 每天上午交易结束之后执行可转债数据同步
    scheduler.add_job(sync_cb_data_job, 'cron', hour='11', minute='35')
    # 每天下午交易结束之后执行可转债数据同步并更新收益率
    scheduler.add_job(update_bond_yield_job, 'cron', hour='15', minute='35')
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



def update_bond_yield_job():
    print('begin to update yield job...')
    try:
        do_update_bond_yield()
    except Exception as e:
        print('update_bond_yield_job is failure', e)


def do_update_bond_yield():
    # 检查是否交易日
    if trade_utils.is_trade_date() is False:
        return 'OK'

    # 先同步一下可转债数据
    cb_ninwen.fetch_data()

    # 获取最新收益率
    day_yield, all_yield = common.calc_yield()

    # 获取可转债等权, 沪深300涨跌幅信息 from: https://www.ninwin.cn/index.php?m=cb&c=idx
    cb_day_yield, hs_day_yield = common.get_up_down_data()

    # 去掉时分秒
    today = datetime.now()
    ymd = today.strftime('%Y-%m-%d')
    d = datetime.strptime(ymd, '%Y-%m-%d')
    s = int(time.mktime(d.timetuple()))

    # 获取上一个交易日的净值, 计算今天的净值
    previous = db.session.query(InvestYield).filter(InvestYield.date < s).first()
    if previous is None:
        raise Exception('没找到前一个交易日的记录')
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

        invest_yield.cb_net_value = cb_net_value
        invest_yield.hs_net_value = hs_net_value
        db.session.add(invest_yield)
    else:
        invest_yield.all_yield = all_yield
        invest_yield.day_yield = day_yield

        invest_yield.cb_day_yield = cb_day_yield
        invest_yield.hs_day_yield = hs_day_yield

        invest_yield.cb_net_value = cb_net_value
        invest_yield.hs_net_value = hs_net_value

    db.session.commit()

    return 'OK'

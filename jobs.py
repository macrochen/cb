# -*- coding: utf-8 -*-
import re
import time
from datetime import datetime, date

from apscheduler.schedulers.background import BackgroundScheduler

from backtest.jsl_test import generate_long_year_back_test_data, generate_good_year_back_test_data, test_group
from crawler import cb_ninwen, crawler_utils, cb_jsl_daily, stock_10jqka
from models import InvestYield, db, HoldBond, HoldBondHistory
from utils import trade_utils, db_utils
from utils.db_utils import get_cursor, execute_sql_with_rowcount
from utils.trade_utils import get_ymd, calc_mid_data, calc_mid_data_with_avg_premium
from views.view_strategy_group import update_groups


def init_job(app):
    scheduler = BackgroundScheduler()
    # 每天上午交易开始前执行初始化
    scheduler.add_job(update_data_job_before_trade_is_start, 'cron', hour='5', minute='0', args=[app])
    # 每天上午交易结束之后执行可转债数据同步
    scheduler.add_job(sync_cb_data_job, 'cron', hour='12', minute='0', args=[app])
    # 每天下午交易结束之后执行可转债数据同步并更新收益率
    scheduler.add_job(update_data_job_after_trade_is_end, 'cron', hour='15', minute='35', args=[app])
    
    # 每个周六爬一次数据
    scheduler.add_job(task_pre_week, 'cron', day_of_week="5", hour='15', minute='35', args=[app])

    scheduler.start()


def task_pre_week(app):
    print("begin to run task_pre_week job...")
    try:
        with app.app_context():
            # 更新回测数据
            generate_good_year_back_test_data()
            generate_long_year_back_test_data()

            strategy_types = ['低溢价策略', '低余额+低溢价+双低策略', '低余额+双低策略', '低溢价+双低策略', '双低策略', '高收益率策略', '低价格策略']
            start = datetime.strptime('2018-01-01', '%Y-%m-%d')
            for name in strategy_types:
                test_group(start, strategy_types=[name], is_single_strategy=True, is_save_test_result=True)
    except Exception as e:
        print('task_pre_week is failure. ', e)


def sync_cb_data_job(app):
    print("begin to sync data job...")
    try:

        with app.app_context():
            # 检查是否交易日
            if trade_utils.is_trade_date() is False:
                return 'OK'

            # 先同步一下可转债数据
            cb_ninwen.fetch_data()
    except Exception as e:
        print('sync_cb_data_job is failure. ', e)


def update_data_job_after_trade_is_end(app):
    print('begin to update data job...')
    try:
        with app.app_context():
            do_update_data_after_trade_is_end()
    except Exception as e:
        print('update_data_job_when_trade_is_end is failure', e)


def update_data_job_before_trade_is_start(app):
    print('begin to update data job...')
    try:
        with app.app_context():
            do_update_data_before_trade_is_start()
    except Exception as e:
        print('update_data_job_before_trade_is_start is failure', e)


def do_update_data_before_trade_is_start():
    # 检查是否交易日
    if trade_utils.is_trade_date() is False:
        return 'OK'

    # 初始化today_sum_buy, 将昨天收盘市值作为今天的开盘市值
    rowcount = db_utils.execute_sql_with_rowcount("""
        update hold_bond set modify_date = :modify_date, today_sum_sell = 0,
            today_sum_buy = (select round(c.cb_price2_id*hold_bond.hold_amount,2) 
                            from changed_bond c where c.bond_code = hold_bond.bond_code)
    """, {"modify_date": datetime.now()})
    if rowcount > 0:
        print('init today_sum_buy is successful. count:' + str(rowcount))
    
    # 更新一下正股诊断信息
    stock_10jqka.fetch_data()
    
    return 'OK'


def do_update_data_after_trade_is_end():
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

    # # 归档当前的组合策略数据
    # archive_top_bond()

    # 爬每日交易数据
    cb_jsl_daily.do_fetch_data()

    # 更新轮动组合数据
    update_groups()

    return 'OK'


def archive_top_bond():
    # 当日如果已经新增了策略的数据, 先删除
    rowcount = execute_sql_with_rowcount("""
    delete from changed_bond_top_history where create_date = :create_date
    """, {'create_date': date.today()})
    print("delete relevant strategy cb data for the day. count: " + str(rowcount))

    # 获取数据并插入
    # 双低
    rowcount = execute_sql_with_rowcount("""
insert into changed_bond_top_history
select c.*,
       date() as create_date,
       '双低策略' as strategy_name,
       d.sort_num+1 as sort_num
from changed_bond c,
     (select id,
             (select count(*)
              from (select cb_premium_id * 100 + cb_price2_id as sort_value, BT_yield
                    from changed_bond_view
                    order by cb_premium_id * 100 + cb_price2_id, BT_yield desc
                    limit 20) b
              where case
                        when a.sort_value > b.sort_value then true
                        when a.sort_value = b.sort_value then a.BT_yield < b.BT_yield
                        else false end) as sort_num
      from (select id, cb_premium_id * 100 + cb_price2_id as sort_value, BT_yield
            from changed_bond_view
            order by cb_premium_id * 100 + cb_price2_id, BT_yield desc
            limit 20) a) d
where c.id = d.id
order by d.sort_num
limit 20
    """)
    if rowcount == 20:
        print('insert double low strategy data is successful')
    # 低溢价
    rowcount = execute_sql_with_rowcount("""
insert into changed_bond_top_history
select c.*,
       date()         as create_date,
       '低溢价率策略'       as strategy_name,
       d.sort_num + 1 as sort_num
from changed_bond c,
     (select id,
             (select count(*)
              from (select cb_premium_id, cb_price2_id, remain_amount
                    from changed_bond_view
                    order by cb_premium_id, cb_price2_id, remain_amount
                    limit 35) b
              where case
                        when a.cb_premium_id > b.cb_premium_id then true
                        when a.cb_premium_id = b.cb_premium_id then a.cb_price2_id > b.cb_price2_id
                        else (case
                                  when a.cb_price2_id = b.cb_price2_id then a.remain_amount > b.remain_amount
                                  else false end)
                        end) as sort_num
      from (select id, cb_premium_id, cb_price2_id, remain_amount
            from changed_bond_view
            order by cb_premium_id, cb_price2_id, remain_amount
            limit 35) a) d
where c.id = d.id
order by d.sort_num
limit 35
        """)
    if rowcount == 35:
        print('insert low premium strategy data is successful')
    # 高收益率
    rowcount = execute_sql_with_rowcount("""
insert into changed_bond_top_history
select c.*,
       date()   as create_date,
       '高收益率策略' as strategy_name,
       d.sort_num+1 as sort_num
from changed_bond c,
     (select id,
             (select count(*)
              from (select BT_yield, cb_price2_id
                    from changed_bond_view
                    order by BT_yield desc, cb_price2_id
                    limit 15) b
              where case
                        when a.BT_yield < b.BT_yield then true
                        when a.BT_yield = b.BT_yield then a.cb_price2_id > b.cb_price2_id
                        else false end) as sort_num
      from (select id, BT_yield, cb_price2_id
            from changed_bond_view
            order by BT_yield desc, cb_price2_id
            limit 15) a) d
where c.id = d.id
order by d.sort_num
limit 15
        """)
    if rowcount == 15:
        print('insert hight yield strategy data is successful')


def update_cb_index():
    mid_price, temp, avg_premium = calc_mid_data_with_avg_premium()
    # 检查当天记录已经存在, 存在则更新
    cur = get_cursor(
        "select count(*) from cb_index_history where strftime('%Y-%m-%d', date) = strftime('%Y-%m-%d', date())")
    one = cur.fetchone()
    if one[0] == 0:
        count = execute_sql_with_rowcount(
            """insert into cb_index_history(mid_price, avg_premium) values(:mid_price, :avg_premium)""",
            {'mid_price': mid_price, 'avg_premium': avg_premium})
        if count == 1:
            print('insert today\'s mid_price is successful.')
    else:
        count = execute_sql_with_rowcount(
            """update cb_index_history set mid_price=:mid_price, avg_premium=:avg_premium where strftime('%Y-%m-%d', date) = strftime('%Y-%m-%d', date())""",
            {'mid_price': mid_price, 'avg_premium': avg_premium})
        if count == 1:
            print('update today\'s mid_price is successful.')


def update_yield(ymd):
    # 获取最新收益率
    # day_yield, all_yield = calc_yield()

    # 去掉时分秒
    s = get_seconds(ymd)
    # 获取上一个交易日的净值, 计算今天的净值
    previous = db.session.query(InvestYield).filter(InvestYield.date < s).order_by(InvestYield.date.desc()).first()
    if previous is None:
        raise Exception('没找到前一个交易日的记录')

    # 计算组合中各个策略日收益率

    invest_yield = db.session.query(InvestYield).filter(InvestYield.date == s).first()
    if invest_yield is None:
        invest_yield = InvestYield()
        invest_yield.date = s
        invest_yield.date_string = ymd

        build_invest_yield(invest_yield, previous)
        db.session.add(invest_yield)
    else:
        build_invest_yield(invest_yield, previous)

    db.session.commit()


def build_invest_yield(invest_yield, previous):
    my_real_profit, my_real_yield = calc_yield()
    # 获取可转债等权, 沪深300涨跌幅信息 from: https://www.ninwin.cn/index.php?m=cb&c=idx
    cb_day_yield, hs_day_yield = get_up_down_data()

    my_day_yield = round(my_real_yield - previous.my_real_yield, 2)

    invest_yield.my_real_yield = my_real_yield
    invest_yield.my_real_profit = my_real_profit
    invest_yield.my_today_profit = round(my_real_profit - (0 if previous.my_real_profit is None else previous.my_real_profit), 2)

    # 日收益率
    invest_yield.my_day_yield = my_day_yield
    invest_yield.cb_day_yield = cb_day_yield
    invest_yield.hs_day_yield = hs_day_yield
    # 累积收益率
    invest_yield.my_all_yield = round(previous.my_all_yield + my_day_yield, 2)
    invest_yield.cb_all_yield = round(previous.cb_all_yield + cb_day_yield, 2)
    invest_yield.hs_all_yield = round(previous.hs_all_yield + hs_day_yield, 2)

    # double_low, high_yield, low_premium = get_strategy_yield_rate()
    # # 日收益率
    # invest_yield.strategy_double_low_day_yield = double_low
    # invest_yield.strategy_high_yield_day_yield = high_yield
    # invest_yield.strategy_low_premium_day_yield = low_premium
    # # 累积收益率
    # invest_yield.strategy_double_low_all_yield = round(previous.strategy_double_low_all_yield + double_low, 2)
    # invest_yield.strategy_high_yield_all_yield = round(previous.strategy_high_yield_all_yield + high_yield, 2)
    # invest_yield.strategy_low_premium_all_yield = round(previous.strategy_low_premium_all_yield + low_premium, 2)


def get_seconds(ymd):
    d = datetime.strptime(ymd, '%Y-%m-%d')
    s = int(time.mktime(d.timetuple()))
    return s


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
            print('move bond to history is failure: ex:' + str(err), err)
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
SELECT round(sum(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy), 2) as 累积收益,   
	round(sum(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy)/sum(h.sum_buy) * 100, 2)  as 累积收益率
from (select hold_amount, sum_buy, hold_owner, bond_code, sum_sell from hold_bond union select hold_amount, sum_buy, hold_owner, bond_code, sum_sell from hold_bond_history) h , changed_bond c 
where h.bond_code = c.bond_code and hold_owner='me'
        """)

    row = cur.fetchone()
    return row[0], row[1]


if __name__ == "__main__":
    # sync_cb_data_job()
    # archive_top_bond()
    pass

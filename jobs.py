# -*- coding: utf-8 -*-
import re
import time
from datetime import datetime, date

from apscheduler.schedulers.background import BackgroundScheduler

from crawler import cb_ninwen, crawler_utils
from models import InvestYield, db, HoldBond, HoldBondHistory
from utils import trade_utils, db_utils
from utils.db_utils import get_cursor, execute_sql_with_rowcount
from utils.trade_utils import get_ymd, calc_mid_data
from views.view_strategy_group import get_strategy_yield_rate


def init_job(app):
    scheduler = BackgroundScheduler()
    # 每天上午交易开始前执行初始化
    scheduler.add_job(update_data_job_before_trade_is_start, 'cron', hour='8', minute='30', args=[app])
    # 每天上午交易结束之后执行可转债数据同步
    scheduler.add_job(sync_cb_data_job, 'cron', hour='11', minute='35', args=[app])
    # 每天下午交易结束之后执行可转债数据同步并更新收益率
    scheduler.add_job(update_data_job_after_trade_is_end, 'cron', hour='15', minute='35', args=[app])
    scheduler.start()


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

    # 初始化today_sum_buy
    # c.cb_price2_id = x * (1+mov)
    rowcount = db_utils.execute_sql_with_rowcount("""
        update hold_bond set today_sum_buy = (select round(c.cb_price2_id/(1+c.cb_mov2_id)*hold_bond.hold_amount,2) from changed_bond c where c.bond_code = hold_bond.bond_code)
    """)
    if rowcount > 0:
        print('init today_sum_buy is successful. count:' + str(rowcount))

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

    # 归档当前的组合策略数据
    archive_top_bond()

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
           strftime('%s', date()) as create_date_s,
           '双低策略' as strategy_name,
           d.sort_num
    from changed_bond c,
         (select id,
                 (select count(*)
                  from (select cb_price2_id + cb_premium_id * 100 as sort_value
                        from changed_bond_view
                        order by cb_price2_id + cb_premium_id * 100
                        limit 10) b
                  where a.sort_value >= b.sort_value) as sort_num
          from (select id, cb_price2_id, cb_premium_id, cb_price2_id + cb_premium_id * 100 as sort_value
                from changed_bond_view
                order by cb_price2_id + cb_premium_id * 100
                limit 10) a
          order by cb_price2_id + cb_premium_id * 100
          limit 10) d
    where c.id = d.id
    order by cb_price2_id + cb_premium_id * 100
    limit 10
    """)
    if rowcount == 10:
        print('insert double low strategy data is successful')
    # 低溢价
    rowcount = execute_sql_with_rowcount("""
        insert into changed_bond_top_history
        select c.*,
               date()  as create_date,
               strftime('%s', date()) as create_date_s,
               '低溢价率策略' as strategy_name,
               d.sort_num
        from changed_bond c,
             (select id,
                     (select count(*)
                      from (select cb_premium_id
                            from changed_bond_view
                            order by cb_premium_id
                            limit 10) b
                      where a.cb_premium_id >= b.cb_premium_id) as sort_num
              from (select id, cb_premium_id
                    from changed_bond_view
                    order by cb_premium_id
                    limit 10) a) d
        where c.id = d.id
        order by cb_premium_id
        limit 10
        """)
    if rowcount == 10:
        print('insert low premium strategy data is successful')
    # 高收益率
    rowcount = execute_sql_with_rowcount("""
    insert into changed_bond_top_history
    select c.*,
           date()   as create_date,
           strftime('%s', date()) as create_date_s,
           '高收益率策略' as strategy_name,
           d.sort_num
    from changed_bond c,
         (select id,
                 (select count(*)
                  from (select bt_yield
                        from changed_bond_view
                        order by bt_yield desc
                        limit 10) b
                  where a.bt_yield <= b.bt_yield) as sort_num
          from (select id, bt_yield
                from changed_bond_view
                order by bt_yield desc
                limit 10) a) d
    where c.id = d.id
    order by bt_yield desc
    limit 10
        """)
    if rowcount == 10:
        print('insert hight yield strategy data is successful')


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
    my_real_yield = calc_yield()
    # 获取可转债等权, 沪深300涨跌幅信息 from: https://www.ninwin.cn/index.php?m=cb&c=idx
    cb_day_yield, hs_day_yield = get_up_down_data()

    my_day_yield = round(my_real_yield - previous.my_real_yield, 2)

    invest_yield.my_real_yield = my_real_yield

    # 日收益率
    invest_yield.my_day_yield = my_day_yield
    invest_yield.cb_day_yield = cb_day_yield
    invest_yield.hs_day_yield = hs_day_yield
    # 累积收益率
    invest_yield.my_all_yield = round(previous.my_all_yield + my_day_yield, 2)
    invest_yield.cb_all_yield = round(previous.cb_all_yield + cb_day_yield, 2)
    invest_yield.hs_all_yield = round(previous.hs_all_yield + hs_day_yield, 2)

    double_low, high_yield, low_premium = get_strategy_yield_rate()
    # 日收益率
    invest_yield.strategy_double_low_day_yield = double_low
    invest_yield.strategy_high_yield_day_yield = high_yield
    invest_yield.strategy_low_premium_day_yield = low_premium
    #累积收益率
    invest_yield.strategy_double_low_all_yield = round(previous.strategy_double_low_all_yield + double_low, 2)
    invest_yield.strategy_high_yield_all_yield = round(previous.strategy_high_yield_all_yield + high_yield, 2)
    invest_yield.strategy_low_premium_all_yield = round(previous.strategy_low_premium_all_yield + low_premium, 2)


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
SELECT    
	--round(sum(c.cb_price2_id*hold_amount + today_sum_sell - today_sum_buy)/sum(c.cb_price2_id*hold_amount + today_sum_sell)*100,2) || '%' as '日收益率',
	round(sum(round(c.cb_price2_id*h.hold_amount+h.sum_sell -h.sum_buy, 3)) /sum(h.sum_buy - h.sum_sell) * 100, 2)  as 累积收益率
from (select hold_amount, sum_buy, hold_owner, bond_code, sum_sell, today_sum_sell, today_sum_buy from hold_bond union select hold_amount, sum_buy, hold_owner, bond_code, sum_sell, 0 as today_sum_sell, 0 as today_sum_buy from hold_bond_history) h , changed_bond c 
where h.bond_code = c.bond_code and hold_owner='me'
        """)

    row = cur.fetchone()
    # day_yield = row[0]
    # all_yield = row[1]
    all_yield = row[0]
    return all_yield


if __name__ == "__main__":
    sync_cb_data_job()

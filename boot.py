# -*- coding: utf-8 -*-
import os
import sqlite3
import threading
import time
from datetime import datetime

import schedule
from flask import render_template, request, url_for, redirect, flash, send_from_directory, session
from flask_login import login_user, login_required, logout_user

import trade_utils
import view_my_select
import view_my_yield
from config import app, db
from models import User, ChangedBond, HoldBond, ChangedBondSelect, InvestYield

from prettytable import from_db_cursor

from apscheduler.schedulers.background import BackgroundScheduler

import cb_jsl
import cb_ninwen
import cb_ninwen_detail
import common
import stock_10jqka
import stock_eastmoney
import stock_xueqiu
import view_market
import view_my_strategy
import view_my_account
import view_up_down

from flask_login import LoginManager

login_manager = LoginManager(app)  # 实例化扩展类

@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login.html', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        flash('Invalid input.')
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(name=username).first()
        if user.validate_password(password):
            login_user(user)
            flash('Login success.')

    return render_template('index.html')


@app.route('/logout.html')
def logout():
    logout_user()

    return render_template('index.html')


@app.route('/edit_hold_bond.html')
@app.route('/edit_hold_bond_by_id.html/<id>/')
@app.route('/edit_hold_bond.html/<bond_code>/')
@login_required
def edit_hold_bond(id='', bond_code=''):
    bond = None
    if id != '':
        bond = db.session.query(HoldBond).filter(HoldBond.id == id).first()
    elif bond_code != '':
        # 先查持有的
        bond = db.session.query(HoldBond).filter(HoldBond.bond_code == bond_code, HoldBond.hold_amount > -1).first()

        # 没有持有过, 转添加操作
        if bond is None:
            bond = db.session.query(ChangedBond).filter(ChangedBond.bond_code == bond_code).first()
            bond.id = ''

    return render_template("edit_hold_bond.html", bond=bond)


@app.route('/find_bond_by.html', methods=['GET'])
@login_required
def find_bond_by_code():
    bond_code = request.args.get("bond_code")
    bond_name = request.args.get("bond_name")
    account = request.args.get("account")
    # fixme 打新和其他策略可能同时存在
    # 先找hold_amount>-1的,没有再找hold_amount=-1的
    bond = None
    if bond_code != '':
        if account != '':
            bond = db.session.query(HoldBond).filter(HoldBond.bond_code == bond_code, HoldBond.account == account).first()
        else:
            bond = db.session.query(HoldBond).filter(HoldBond.bond_code == bond_code).first()
    elif bond_name != '':
        if account != '':
            bond = db.session.query(HoldBond).filter(HoldBond.cb_name_id.like('%' + bond_name + '%'), HoldBond.account == account).first()
        else:
            bond = db.session.query(HoldBond).filter(HoldBond.cb_name_id.like('%' + bond_name + '%')).first()

    if bond is None:
        if bond_code != '':
            bond = ChangedBond.query.filter_by(bond_code=bond_code).first()
        elif bond_name != '':
            bond = ChangedBond.query.filter(ChangedBond.cb_name_id.like('%' + bond_name + '%')).first()

        bond.id = None
        if bond is not None:
            return dict(bond)
        raise Exception('not find bond by code: ' + bond_code)
    else:
        return dict(bond)


@app.route('/view_my_select.html')
@login_required
def my_select_view():
    user_id = session.get('_user_id')
    title, navbar, content = view_my_select.draw_view(user_id is not None)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@app.route('/edit_changed_bond_select.html')
@app.route('/edit_changed_bond_select.html/<bond_code>/')
@login_required
def edit_changed_bond_select(bond_code=''):
    bond = None
    if bond_code != '':
        bond = db.session.query(ChangedBondSelect).filter(ChangedBondSelect.bond_code == bond_code).first()

    return render_template("edit_changed_bond_select.html", bond=bond)


@app.route('/find_changed_bond_select_by_code.html', methods=['GET'])
@login_required
def find_changed_bond_select_by_code():
    bond_code = request.args.get("bond_code")
    bond_name = request.args.get("bond_name")
    bond = None
    if bond_code != '':
        bond = db.session.query(ChangedBondSelect).filter(ChangedBondSelect.bond_code == bond_code).first()
        if bond is None:
            bond = db.session.query(ChangedBond).filter(ChangedBond.bond_code == bond_code).first()
            if bond is not None:
                bond.id = ''
    elif bond_name != '':
        bond = db.session.query(ChangedBondSelect).filter(ChangedBondSelect.cb_name_id.like('%' + bond_name + '%')).first()
        if bond is None:
            bond = db.session.query(ChangedBond).filter(ChangedBond.cb_name_id.like('%' + bond_name + '%')).first()
            if bond is not None:
                bond.id = ''

    if bond is None:
        raise Exception('not find bond by code/name: ' + bond_code + "," + bond_name)
    else:
        return dict(bond)

@app.route('/save_changed_bond_select.html', methods=['POST'])
@login_required
def save_changed_bond_select():
    id = request.form['id']
    changed_bond_select = None
    if id is None or id.strip(' ') == '':
        changed_bond_select = ChangedBondSelect()
    else:
        changed_bond_select = db.session.query(ChangedBondSelect).filter(ChangedBondSelect.id == id).first()

    bond_code = request.form['bond_code']
    if bond_code is None or bond_code.strip(' ') == '':
        raise Exception('转债代码不能为空')

    changed_bond_select.bond_code = bond_code

    cb_name_id = request.form['cb_name_id']
    if cb_name_id is None or cb_name_id.strip(' ') == '':
        raise Exception('转债名称不能为空')

    changed_bond_select.cb_name_id = cb_name_id

    strategy_type = request.form['strategy_type']
    if strategy_type is not None and strategy_type.strip(' ') != '':
        changed_bond_select.strategy_type = strategy_type

    memo = request.form['memo']
    # if memo is not None and memo.strip(' ') != '':
    changed_bond_select.memo = memo

    if id is None or id.strip(' ') == '':
        db.session.add(changed_bond_select)
    db.session.commit()

    return render_template("edit_changed_bond_select.html", result='save is successful')


@app.route('/save_hold_bond.html', methods=['POST'])
@login_required
def save_hold_bond():
    id = request.form['id']
    hold_bond = None
    is_new = id is None or id.strip(' ') == ''
    if is_new:
        #新增操作
        hold_bond = HoldBond()
    else:
        # 更新操作
        hold_bond = db.session.query(HoldBond).filter(HoldBond.id == id).first()

    bond_code = request.form['bond_code']
    if bond_code is None or bond_code.strip(' ') == '':
        raise Exception('转债代码不能为空')

    hold_bond.bond_code = bond_code

    if bond_code.startswith('11'):
        hold_bond.hold_unit = 10
    else:
        hold_bond.hold_unit = 1

    cb_name_id = request.form['bond_name']
    if cb_name_id is None or cb_name_id.strip(' ') == '':
        raise Exception('转债名称不能为空')

    hold_bond.cb_name_id = cb_name_id

    hold_amount = request.form['hold_amount']
    if hold_amount is None or hold_amount.strip(' ') == '':
        raise Exception('持有数量不能为空')

    hold_bond.hold_amount = int(hold_amount)

    hold_price = request.form['hold_price']
    if hold_price is None or hold_price.strip(' ') == '':
        raise Exception('持有价格不能为空')

    hold_bond.hold_price = float(hold_price)
    # 重置一下累积金额信息, 避免下次持仓价格计算错误
    if not is_new:
        # 增加数量
        delta = float(hold_price) - hold_bond.hold_price
        # 持仓金额同时增加
        hold_bond.sum_buy += delta * hold_bond.hold_amount

    account = request.form['account']
    if account is not None and account.strip(' ') != '':
        hold_bond.account = account

    strategy_type = request.form['strategy_type']
    if strategy_type is None or strategy_type.strip(' ') == '':
        raise Exception('必须指定策略类型')

    hold_bond.strategy_type = strategy_type

    memo = request.form['memo']
    if memo is not None and memo.strip(' ') != '':
        hold_bond.memo = memo

    if is_new:
        db.session.add(hold_bond)
    db.session.commit()

    return redirect(request.form['back_url'])

@app.route('/save_trade_data.html', methods=['POST'])
@login_required
def save_trade_data():
    id = request.form['id']
    hold_bond = None
    if id is None or id.strip(' ') == '':
        #新增操作
        hold_bond = HoldBond()
    else:
        # 更新操作
        hold_bond = db.session.query(HoldBond).filter(HoldBond.id == id).first()

    bond_code = request.form['bond_code']
    if bond_code is None or bond_code.strip(' ') == '':
        raise Exception('转债代码不能为空')

    hold_bond.bond_code = bond_code

    is_sh_market = bond_code.startswith('11')

    if is_sh_market:
        hold_bond.hold_unit = 10
    else:
        hold_bond.hold_unit = 1

    cb_name_id = request.form['bond_name']
    if cb_name_id is None or cb_name_id.strip(' ') == '':
        raise Exception('转债名称不能为空')

    hold_bond.cb_name_id = cb_name_id

    trade_amount = request.form['trade_amount']
    if trade_amount is None or trade_amount.strip(' ') == '':
        raise Exception('成交量不能为空')

    if int(trade_amount) < 0:
        raise Exception("成交量必须大于0")

    trade_price = request.form['trade_price']
    if trade_price is None or trade_price.strip(' ') == '':
        raise Exception('成交价不能为空')

    direction = request.form['direction']
    if direction is None or direction.strip(' ') == '':
        raise Exception('必须指定买卖方向')

    if direction == 'sell':
        if int(trade_amount) > hold_bond.hold_amount:
            raise Exception("成交量(" + trade_amount + ")不能超过持有量(" + str(hold_bond.hold_amount) + ")")

    account = request.form['account']
    if account is None or account.strip(' ') == '':
        raise Exception("必须指定交易账户")

    hold_bond.account = account

    # 计算持仓成本
    hold_bond.calc_hold_price(direction, trade_amount, trade_price)

    strategy_type = request.form['strategy_type']
    if strategy_type is None or strategy_type.strip(' ') == '':
        raise Exception('必须指定策略类型')

    hold_bond.strategy_type = strategy_type

    if id is None or id.strip(' ') == '':
        db.session.add(hold_bond)
    db.session.commit()

    return redirect(request.form['back_url'])


@app.route('/sync_jsl_bond_data.html')
@login_required
def sync_jsl_bond_data():
    return render_template("sync_jsl_bond_data.html")


@app.route('/sync_trade_data.html/<id>/')
@app.route('/new_sync_trade_data.html/<bond_code>/')
@app.route('/new_sync_trade_data.html')
@login_required
def sync_trade_data(id='', bond_code=''):
    bond = None
    if id != '':
        bond = db.session.query(HoldBond).filter(HoldBond.id == id).first()
    elif bond_code != '':
        bond = db.session.query(ChangedBond).filter(ChangedBond.bond_code == bond_code).first()

    return render_template("sync_trade_data.html", bond=bond)


@app.route('/view_up_down.html')
@login_required
def up_down_view():
    user_id = session.get('_user_id')
    title, navbar, content = view_up_down.draw_view(user_id is not None)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@app.route('/view_my_strategy.html')
@login_required
def my_strategy_view():
    user_id = session.get('_user_id')
    common.calc_middle_info()
    title, navbar, content = view_my_strategy.draw_my_view(user_id is not None)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@app.route('/view_my_yield.html')
@login_required
def my_yield_view():
    title, navbar, content = view_my_yield.draw_my_view()
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@app.route('/view_my_account.html')
@login_required
def my_account_view():
    user_id = session.get('_user_id')
    common.calc_middle_info()
    title, navbar, content = view_my_account.draw_my_view(user_id is not None)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@app.route('/view_market.html')
def market_view():
    # current_user = None
    user_id = session.get('_user_id')
    common.calc_middle_info()
    title, navbar, content = view_market.draw_market_view(user_id is not None)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@app.route('/jsl_update_data.html')
@login_required
def jsl_update_data():
    return cb_jsl.fetch_data()

@app.route('/cb_ninwen.html')
@login_required
def ninwen_update_data():
    return cb_ninwen.fetch_data()

@app.route('/cb_ninwen_detail.html')
@login_required
def ninwen_detail_update_data():
    return cb_ninwen_detail.fetch_data()

@app.route('/stock_10jqka.html')
@login_required
def stock_10jqka_update_data():
    return stock_10jqka.fetch_data()

@app.route('/stock_eastmoney.html')
@login_required
def stock_eastmoney_update_data():
    return stock_eastmoney.fetch_data()

@app.route('/stock_xueqiu.html')
@login_required
def stock_xueqiu_update_data():
    return stock_xueqiu.fetch_data()

@app.route('/download_db_data.html')
@login_required
def download_db_data():
    con = sqlite3.connect('db/cb.db3')
    file_name = 'dump/data.sql'
    with open(file_name, 'w') as f:
        for line in con.iterdump():
            f.write('%s\n' % line)

    # 需要知道2个参数, 第1个参数是本地目录的path, 第2个参数是文件名(带扩展名)
    directory = os.getcwd()  # 假设在当前目录
    return send_from_directory(directory, file_name, as_attachment=True)

@app.route('/upload_db_data.html')
@login_required
def upload_db_data():
    return render_template("upload_db_data.html")

@app.route('/save_db_data.html', methods=['POST'])
@login_required
def save_db_data():
    # 删除整个db
    os.unlink("db/cb.db3")
    # 获取文件(字符串?)
    file = request.files['file']
    s = file.read().decode('utf-8')
    # 灌入上传的数据
    con = sqlite3.connect('db/cb.db3')
    con.executescript(s)

    return 'OK'


@app.route('/query_database.html', methods=['POST', 'GET'])
@login_required
def query_database():
    table_html = ''
    sql_code = ''
    table_height_style = ''
    if len(request.form) > 0:
        sql_code = request.form['sql_code']
        if sql_code is None or sql_code.strip(' ') == '':
            raise Exception('SQL不能为空')

        if not sql_code.lower().strip().startswith('select'):
            raise Exception("仅允许select操作")

        conn = sqlite3.connect("db/cb.db3")
        cur = conn.cursor()
        cur.execute(sql_code)
        table = from_db_cursor(cur)

        if len(table._rows) > 10:
            table_height_style = """style="height:500px" """

        table_html = table.get_html_string()

    return render_template("query_database.html", table_html=table_html, sql_code=sql_code, table_height_style=table_height_style)


@app.route('/update_database.html')
@login_required
def update_database():
    return render_template("update_database.html")


@app.route('/execute_sql.html', methods=['POST'])
@login_required
def execute_sql():
    sql_code = request.form['sql_code']
    if sql_code is None or sql_code.strip(' ') == '':
        raise Exception('SQL不能为空')

    if not sql_code.lower().strip().startswith('update') and not sql_code.lower().strip().startswith('insert'):
        raise Exception("仅允许update/insert操作")

    con = sqlite3.connect('db/cb.db3')
    con.executescript(sql_code)

    return 'OK'


@app.route('/update_bond_yield.html')
@login_required
def update_bond_yield():
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
        update_bond_yield()
    except Exception as e:
        print('update_bond_yield_job is failure', e)


if __name__ == "__main__":

    scheduler = BackgroundScheduler()
    # 每天上午交易结束之后执行可转债数据同步
    scheduler.add_job(sync_cb_data_job, 'cron', hour='11', minute='35')
    # 每天下午交易结束之后执行可转债数据同步并更新收益率
    scheduler.add_job(update_bond_yield_job, 'cron', hour='15', minute='35')
    scheduler.start()

    # app.run(port=8080, host="127.0.0.1")  # 生产环境使用, 调用run方法，设定端口号，启动服务
    app.run(port=8080, host="127.0.0.1", debug=True, use_reloader=True)  #开发环境使用, 注意use_reloader=true会导致scheduler被调用两次

# -*- coding: utf-8 -*-

from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user

from config import app, db
from models import User, ChangedBond, HoldBond

import cb_jsl
import cb_ninwen
import cb_ninwen_detail
import common
import stock_10jqka
import stock_eastmoney
import stock_xueqiu
import view_market
import view_my
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


@app.route('/update_hold_bond.html')
@login_required
def update_hold_bond():
    return render_template("update_hold_bond.html")

@app.route('/find_bond_by/<string:bond_code>', methods=['GET'])
@login_required
def find_bond_by_code(bond_code):
    bond = ChangedBond.query.filter_by(bond_code=bond_code).first()
    if bond is not None:
        return bond.cb_name_id
    raise Exception('not find bond by code: ' + bond_code)

@app.route('/save_hold_bond.html', methods=['POST'])
@login_required
def save_hold_bond():
    hold_bond = HoldBond()

    bond_code = request.form['bond_code']
    if bond_code is None or bond_code.strip(' ') == '':
        raise Exception('转债代码不能为空')

    hold_bond.bond_code = bond_code

    cb_name_id = request.form['bond_name']
    if cb_name_id is None or cb_name_id.strip(' ') == '':
        raise Exception('转债名称不能为空')

    hold_bond.cb_name_id = cb_name_id

    hold_amount = request.form['hold_amount']
    if hold_amount is None or hold_amount.strip(' ') == '' or int(hold_amount.strip(' ')) <= 0:
        raise Exception('持有数量不能为空且大于零')

    hold_bond.hold_amount = int(hold_amount)

    hold_price = request.form['hold_price']
    if hold_price is None or hold_price.strip(' ') == '':
        raise Exception('持有价格不能为空')

    hold_bond.hold_price = float(hold_price)

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

    db.session.add(hold_bond)
    db.session.commit()

    return my_view()

@app.route('/save_jsl_bond_data.html', methods=['POST'])
@login_required
def save_jsl_bond_data():
    source_code = request.form['source_code']
    if source_code is None or source_code.strip(' ') == '':
        raise Exception('网页源码不能为空')

    return cb_jsl.fetch_data_from_source_code(source_code)

@app.route('/sync_jsl_bond_data.html')
@login_required
def sync_jsl_bond_data():
    return render_template("sync_jsl_bond_data.html")

@app.route('/view_up_down.html')
@login_required
def up_down_view():
    return view_up_down.draw_view(False, False)

@app.route('/view_my.html')
@login_required
def my_view():
    common.init_cb_sum_data()
    return view_my.draw_my_view(False)

@app.route('/view_market.html')
def market_view():
    common.init_cb_sum_data()
    return view_market.draw_market_view(False, False)

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


if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1", debug=True)  # 调用run方法，设定端口号，启动服务
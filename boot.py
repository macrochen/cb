# -*- coding: utf-8 -*-
import os
import sqlite3

from flask import render_template, request, url_for, redirect, flash, send_from_directory, session
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

@app.route('/logout.html')
def logout():
    logout_user()

    return render_template('index.html')


@app.route('/update_hold_bond.html')
@app.route('/update_hold_bond.html/<id>/')
@login_required
def update_hold_bond(id=''):
    bond = None
    if id != '':
        bond = db.session.query(HoldBond).filter(HoldBond.id == id).first()

    return render_template("update_hold_bond.html", bond=bond)

@app.route('/find_bond_by.html', methods=['GET'])
@login_required
def find_bond_by_code():
    bond_code = request.args.get("bond_code")
    bond_name = request.args.get("bond_name")
    # fixme 打新和其他策略可能同时存在
    # 先找hold_amount>-1的,没有再找hold_amount=-1的
    bond = None
    if bond_code != '':
        bond = db.session.query(HoldBond).filter(HoldBond.bond_code == bond_code, HoldBond.hold_amount > -1).first()
        if bond is None:
            bond = db.session.query(HoldBond).filter(HoldBond.bond_code == bond_code).first()
    elif bond_name != '':
        bond = db.session.query(HoldBond).filter(HoldBond.cb_name_id.like('%' + bond_name + '%'), HoldBond.hold_amount > -1).first()
        if bond is None:
            bond = db.session.query(HoldBond).filter(HoldBond.cb_name_id.like('%' + bond_name + '%')).first()

    if bond is None:
        if bond_code != '':
            bond = ChangedBond.query.filter_by(bond_code=bond_code).first()
        elif bond_name != '':
            bond = ChangedBond.query.filter(ChangedBond.cb_name_id.like('%' + bond_name + '%')).first()
        if bond is not None:
            return dict(bond)
        raise Exception('not find bond by code: ' + bond_code)
    else:
        return dict(bond)

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
    if hold_amount is None or hold_amount.strip(' ') == '':
        raise Exception('持有数量不能为空')

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

    id = request.form['id']
    if id is not None:
        hold_bond.id = id
        db.session.update(hold_bond)
    else:
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
    title, navbar, content = view_up_down.draw_view(False, False)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@app.route('/view_my.html')
@login_required
def my_view():
    common.init_cb_sum_data()
    title, navbar, content = view_my.draw_my_view(False)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@app.route('/view_market.html')
def market_view():
    # current_user = None
    user_id = session.get('_user_id')
    common.init_cb_sum_data()
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

    if sql_code.lower().strip().find('update') != 0:
        raise Exception("仅允许update操作")

    con = sqlite3.connect('db/cb.db3')
    con.executescript(sql_code)

    return 'OK'


if __name__ == "__main__":
    app.run(port=8080, host="127.0.0.1", debug=True)  # 调用run方法，设定端口号，启动服务
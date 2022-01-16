# -*- coding: utf-8 -*-
import json
import logging
import os
import sys
from datetime import datetime

from flask import Blueprint
from flask import render_template, request, url_for, redirect, flash, send_from_directory, session
from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user
from prettytable import from_db_cursor
from sqlalchemy import or_, and_, func

import backtest.jsl_test
import backtest.test_utils
import utils.table_html_utils
import utils.trade_utils
from backtest import jsl_test
from config import db_file_path, db_daily_file_path
from crawler import cb_ninwen, cb_jsl, cb_ninwen_detail, stock_10jqka, stock_xueqiu, stock_eastmoney, cb_eastmoney, \
    cb_jsl_daily
from jobs import do_update_data_after_trade_is_end, do_update_data_before_trade_is_start, \
    do_update_data_exclude_group_after_trade_is_end, do_update_back_test_data
from models import User, ChangedBond, HoldBond, ChangedBondSelect, db, TradeHistory, HoldBondHistory, Task
from utils import trade_utils
from utils.db_utils import get_connect, get_cursor, get_daily_connect
from utils.html_utils import get_strategy_options_html
from views import view_market, view_my_account, view_my_select, view_my_strategy, view_my_yield, view_up_down, \
    view_my_up_down, view_turnover, view_discount, view_stock, view_tree_map_industry, view_industry_premium, \
    view_tree_map_price, \
    view_tree_map_premium, view_my_price_list, view_my_trade_history, view_cb_trend, view_up_down_range, view_all_cb, \
    view_enforce_list, view_strategy_group, view_tree_map_remain, view_price_range, \
    view_industry_double_low, view_cb_wordcloud, view_hot_wordcloud
from views.nav_utils import build_select_nav_html, build_personal_nav_html_list, build_personal_nav_html, \
    build_back_test_nav_html
from views.view_strategy_group import update_groups

cb = Blueprint('cb', __name__)

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象


@cb.route('/')
@cb.route('/index.html')
def index():
    return render_template("index.html")


# @cb.before_request
# def check_need_login():
#     url = str(request.url_rule)
#     if url == '/login.html' or url == '/logout.html':
#         return
#
#     # 检查登录的逻辑
#     user_id = session.get('_user_id')
#     if user_id is None:
#         return render_template('index.html', sign=True)


@cb.route('/login.html', methods=['POST'])
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

@cb.route('/sign.html')
def sign():
    return render_template('index.html', sign=True)


@cb.route('/logout.html')
def logout():
    logout_user()

    return render_template('index.html')

#fixme 废弃掉, 用sync_trade_data代替
@cb.route('/edit_hold_bond.html')
@cb.route('/edit_hold_bond_by_id.html/<id>/')
@cb.route('/edit_hold_bond.html/<bond_code>/')
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
            # 先关闭session, 再修改model, 否则会触发update
            db.session.close()
            bond.id = ''

    return render_template("edit_hold_bond.html", bond=bond)


@cb.route('/find_bond_by.html', methods=['GET'])
@login_required
def find_bond_by_code():
    bond_code = request.args.get("bond_code")
    account = request.args.get("account")
    # fixme 打新和其他策略可能同时存在
    # 先找hold_amount>-1的,没有再找hold_amount=-1的
    bond = None
    if bond_code != '':
        if account != '':
            bond = db.session.query(HoldBond).filter(HoldBond.bond_code == bond_code, HoldBond.account == account).first()
        else:
            bond = db.session.query(HoldBond).filter(HoldBond.bond_code == bond_code).first()

    if bond is None:
        if bond_code != '':
            bond = ChangedBond.query.filter_by(bond_code=bond_code).first()

        if bond is not None:
            # 先关闭session, 再修改model, 否则会触发update
            db.session.close()
            bond.id = ''
            return dict(bond)
        raise Exception('not find bond by code: ' + bond_code)
    else:
        return dict(bond)


@cb.route('/find_bond_by_name.html/<bond_name>/', methods=['GET'])
@login_required
def find_bond_by_name(bond_name):

    if bond_name != '':
        bond1s = db.session.query(HoldBond).filter(or_(HoldBond.cb_name_id.like('%' + bond_name + '%'), HoldBond.pinyin.like('%' + bond_name + '%'))).all()

        bond2s = db.session.query(ChangedBond).filter(or_(ChangedBond.cb_name_id.like('%' + bond_name + '%'), ChangedBond.pinyin.like('%' + bond_name + '%'))).all()

        bonds = []
        bonds.extend(bond1s)
        bonds.extend(bond2s)

        # changedbond的id非holdbond的id, 故排除
        return json.dumps(bonds, default=lambda o: o.to_dict('id') if type(o) == ChangedBond else (
            o.to_dict() if type(o) != datetime else str(o)))

    return "{}"


@cb.route('/view_my_select.html')
@login_required
def my_select_view():
    user_id = session.get('_user_id')
    title, navbar, content = view_my_select.draw_view(user_id is not None)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/delete_selected_bond.html/<ids>/')
@login_required
def delete_selected_bond(ids):
    if ids is None or ids.strip(' ') == '':
        print("parameter ids is invalid.")

    ss = ids.split(',')
    db.session.query(ChangedBondSelect)\
        .filter(ChangedBondSelect.id.in_(ss))\
        .update({ChangedBondSelect.is_deleted: 1})
    db.session.commit()

    return 'OK'


@cb.route('/edit_changed_bond_select.html')
@cb.route('/edit_changed_bond_select.html/<bond_code>/')
@login_required
def edit_changed_bond_select(bond_code=''):
    bond = None
    if bond_code != '':
        bond = db.session.query(ChangedBondSelect).filter(ChangedBondSelect.bond_code == bond_code).first()

    type = None
    if bond is not None:
        type = bond.strategy_type
    options = get_strategy_options_html(type)

    navbar = build_select_nav_html('/edit_changed_bond_select.html')

    return render_template("edit_changed_bond_select.html", bond=bond, strategy_options=options, navbar=navbar)


@cb.route('/find_changed_bond_select_by_code.html', methods=['GET'])
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
                # 先关闭session, 再修改model, 否则会触发update
                db.session.close()
                bond.id = ''
    elif bond_name != '':
        bond = db.session.query(ChangedBondSelect).filter(ChangedBondSelect.cb_name_id.like('%' + bond_name + '%')).first()
        if bond is None:
            bond = db.session.query(ChangedBond).filter(ChangedBond.cb_name_id.like('%' + bond_name + '%')).first()
            if bond is not None:
                # 先关闭session, 在修改model, 否则会触发update
                db.session.close()
                bond.id = ''

    if bond is None:
        raise Exception('not find bond by code/name: ' + bond_code + "," + bond_name)
    else:
        return dict(bond)

@cb.route('/find_changed_bond_select_by_name.html/<bond_name>/', methods=['GET'])
@login_required
def find_changed_bond_select_by_name(bond_name):
    bonds = None
    if bond_name != '':
        bond1s = db.session.query(ChangedBondSelect).filter(or_(ChangedBondSelect.cb_name_id.like('%' + bond_name + '%'), ChangedBondSelect.pinyin.like('%' + bond_name + '%')), ChangedBondSelect.is_deleted != 1).all()
        bond2s = db.session.query(ChangedBond).filter(or_(ChangedBond.cb_name_id.like('%' + bond_name + '%'), ChangedBond.pinyin.like('%' + bond_name + '%'))).all()
        bonds = []
        bonds.extend(bond1s)
        bonds.extend(bond2s)

        # changedbond的id非select的id, 故排除
        return json.dumps(bonds, default=lambda o: o.to_dict('id') if type(o) == ChangedBond else (
            o.to_dict() if type(o) != datetime else str(o)))

    return "{}"

@cb.route('/save_changed_bond_select.html', methods=['POST'])
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
    changed_bond_select.pinyin = request.form['pinyin']

    strategy_type = request.form['strategy_type']
    if strategy_type is not None and strategy_type.strip(' ') != '':
        changed_bond_select.strategy_type = strategy_type

    memo = request.form['memo']
    # if memo is not None and memo.strip(' ') != '':
    changed_bond_select.memo = memo

    changed_bond_select.modify_date = datetime.now()
    if id is None or id.strip(' ') == '':
        changed_bond_select.create_date = datetime.now()
        db.session.add(changed_bond_select)
    db.session.commit()

    options = get_strategy_options_html(None)

    navbar = build_select_nav_html('/edit_changed_bond_select.html')

    return render_template("edit_changed_bond_select.html", result='save is successful', strategy_options=options, navbar=navbar)


#fixme 废弃掉, 用sync_trade_data代替
@cb.route('/save_hold_bond.html', methods=['POST'])
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
    hold_bond.cb_name_id = request.form['pinyin']

    hold_amount = request.form['hold_amount']
    if hold_amount is None or hold_amount.strip(' ') == '':
        raise Exception('持有数量不能为空')

    hold_bond.hold_amount = int(hold_amount)

    hold_price = request.form['hold_price']
    if hold_price is None or hold_price.strip(' ') == '':
        raise Exception('持有价格不能为空')

    hold_bond.hold_price = float(hold_price)
    # 重置一下累积金额信息, 避免下次持仓价格计算错误
    if is_new:
        # 持仓金额同时增加
        hold_bond.sum_buy += hold_bond.hold_price * hold_bond.hold_amount
    else:
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

    hold_bond.modify_date = datetime.now()
    if is_new:
        # 增加开始时间
        hold_bond.start_date = datetime.now()
        db.session.add(hold_bond)

    db.session.commit()

    return redirect(request.form['back_url'])


@cb.route('/save_trade_data.html', methods=['POST'])
@login_required
def save_trade_data():
    id = request.form['id']
    hold_bond = None
    is_new = id is None or id.strip(' ') == ''
    if is_new:
        # 新增操作
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

    is_sell = direction == 'sell'
    if is_sell:
        if int(trade_amount) > hold_bond.hold_amount:
            raise Exception("成交量(" + trade_amount + ")不能超过持有量(" + str(hold_bond.hold_amount) + ")")

    account = request.form['account']
    if account is None or account.strip(' ') == '':
        raise Exception("必须指定交易账户")

    hold_bond.account = account

    # 计算持仓成本
    fee = trade_utils.calc_hold_price(hold_bond, direction, trade_amount, trade_price)

    strategy_type = request.form['strategy_type']
    if strategy_type is None or strategy_type.strip(' ') == '':
        raise Exception('必须指定策略类型')

    hold_bond.strategy_type = strategy_type
    hold_bond.pinyin = request.form['pinyin']

    hold_bond.modify_date = datetime.now()
    if is_new:
        # 增加开始时间
        hold_bond.start_date = datetime.now()
        db.session.add(hold_bond)
        # 获取id, 强刷
        db.session.flush()

    # 保存成交记录
    trade_history = TradeHistory()
    trade_history.bond_code = bond_code
    trade_history.fee = fee
    user_id = session.get('_user_id')
    trade_history.owner_id = user_id
    trade_history.cb_name_id = cb_name_id
    trade_history.account = account
    trade_history.strategy_type = strategy_type
    trade_history.price = trade_price
    trade_history.amount = -int(trade_amount) if is_sell else trade_amount
    trade_history.hold_id = hold_bond.id
    db.session.add(trade_history)

    db.session.commit()

    options = get_strategy_options_html(None)


    return render_template("sync_trade_data.html", bond=None, navbar=build_personal_nav_html(request.url_rule), result='operation is successful', strategy_options=options)


@cb.route('/un_save_trade_data.html/<id>', methods=['GET'])
@login_required
def un_save_trade_data(id):
    trade_history = db.session.query(TradeHistory).filter(TradeHistory.id == id).first()
    if trade_history is None:
        raise Exception("not get trade_history by id:"+str(id))

    hold_id = trade_history.hold_id
    hold_bond = db.session.query(HoldBond).filter(HoldBond.id == hold_id).first()
    is_new_hold_bond = False
    if hold_bond is None:
        # 可能被归档了, 需要先从归档中恢复
        hold_bond_history = db.session.query(HoldBondHistory).filter(HoldBondHistory.id == hold_id).first()
        if hold_bond_history is None:
            raise Exception('not get hold_bond by id:' + str(hold_id))
        else:
            hold_bond = HoldBond()
            hold_bond.copy(hold_bond_history)
            is_new_hold_bond = True

    # 重新计算持仓成本
    trade_utils.re_calc_hold_price(hold_bond, trade_history)

    try:
        if is_new_hold_bond:
            db.session.add(hold_bond)
            db.session.query(HoldBondHistory).filter(HoldBondHistory.id == hold_id).delete()
        trade_history.is_delete = 1
        db.session.commit()
    except Exception as err:
        print('un_save_trade_data is failure. err:' + str(err))
        db.session.rollback()

    return 'OK'


@cb.route('/sync_jsl_bond_data.html')
@login_required
def sync_jsl_bond_data():
    return render_template("sync_jsl_bond_data.html")


@cb.route('/sync_trade_data.html/<id>/')
@cb.route('/new_sync_trade_data.html/<bond_code>/')
@cb.route('/new_sync_trade_data.html')
@cb.route('/new_grid_trade_data.html/<id>/')
@login_required
def sync_trade_data(id='', bond_code=''):
    bond = None
    if id != '':
        if 'new_grid_trade_data.html' in str(request.url_rule):
            bond = db.session.query(TradeHistory).filter(TradeHistory.id == id).first()
            # 先关闭session, 在修改model, 否则会触发update
            db.session.close()
            bond.id = ''
        else:
            bond = db.session.query(HoldBond).filter(HoldBond.id == id).first()
    elif bond_code != '':
        bond = db.session.query(ChangedBond).filter(ChangedBond.bond_code == bond_code).first()
        # 先关闭session, 在修改model, 否则会触发update
        db.session.close()
        bond.id = ''

    options = get_strategy_options_html(None
                                        if bond is None
                                        else (bond.strategy_type if hasattr(bond, 'strategy_type') else None))

    return render_template("sync_trade_data.html", bond=bond, navbar=build_personal_nav_html(request.url_rule), strategy_options=options)


@cb.route('/view_up_down.html')
def up_down_view():
    user_id = session.get('_user_id')
    title, navbar, content = view_up_down.draw_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_up_down_range.html')
def up_down_range_view():
    title, navbar, content = view_up_down_range.draw_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_price_range.html')
def price_range_view():
    title, navbar, content = view_price_range.draw_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_tree_map_industry.html')
def industry_tree_map_view():
    key = request.args.get("key")
    rise = request.args.get("rise")
    user_id = session.get('_user_id')
    title, navbar, content = view_tree_map_industry.draw_view(user_id is not None, key, rise, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_industry_premium.html')
def industry_premium_view():
    title, navbar, content = view_industry_premium.draw_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_industry_premium_detail.html')
def industry_premium_detail_view():
    key = request.args.get("key")
    user_id = session.get('_user_id')
    return view_industry_premium.generate_detail(key, user_id is not None)


@cb.route('/view_industry_double_low.html')
def industry_double_low_view():
    title, navbar, content = view_industry_double_low.draw_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_industry_double_low_detail.html')
def industry_double_low_detail_view():
    key = request.args.get("key")
    user_id = session.get('_user_id')
    return view_industry_double_low.generate_detail(key, user_id is not None)


@cb.route('/view_tree_map_price.html')
def price_tree_map_view():
    key = request.args.get("key")
    end, start = parse_range_value(key, '元')

    rise = request.args.get("rise")
    user_id = session.get('_user_id')
    title, navbar, content = view_tree_map_price.draw_view(user_id is not None, key, start, end, rise, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_tree_map_remain.html')
def remain_tree_map_view():
    key = request.args.get("key")
    end, start = parse_range_value(key, '亿')

    rise = request.args.get("rise")
    user_id = session.get('_user_id')
    title, navbar, content = view_tree_map_remain.draw_view(user_id is not None, key, start, end, rise, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_tree_map_premium.html')
def premium_tree_map_view():
    key = request.args.get("key")
    end, start = parse_range_value(key, '%')
    rise = request.args.get("rise")
    user_id = session.get('_user_id')
    title, navbar, content = view_tree_map_premium.draw_view(user_id is not None, key, start, end, rise, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


def parse_range_value(key, suffix):
    start = None
    end = None
    if key is not None and key.strip(' ') != '':
        key = key.replace(suffix, '')
        if key.find('~') >= 1:
            ss = key.split('~')
            start = int(ss[0])
            end = int(ss[1])
        elif key.find('<=') >= 0:
            start = -sys.maxsize
            end = int(key.replace('<=', ''))
        else:
            start = int(key.replace('>', ''))
            end = sys.maxsize
    return end, start


@cb.route('/view_discount.html')
def discount_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_discount.draw_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_all_cb.html')
def all_cb_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_all_cb.draw_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_cb_wordcloud.html')
def cb_wordcloud_view():
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_cb_wordcloud.draw_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_hot_wordcloud.html')
def hot_wordcloud_view():
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_hot_wordcloud.draw_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_cb_wordcloud_detail.html')
def cb_wordcloud_detail_view():
    key = request.args.get("key")
    user_id = session.get('_user_id')
    return view_cb_wordcloud.generate_detail(key, user_id is not None)


@cb.route('/view_stock.html')
def stock_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_stock.draw_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_turnover.html')
def turnover_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_turnover.draw_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_my_up_down.html')
@login_required
def my_up_down_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_my_up_down.draw_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_my_price_list.html')
@login_required
def my_price_list_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_my_price_list.draw_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@cb.route('/view_my_strategy.html')
@login_required
def my_strategy_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_my_strategy.draw_my_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_my_yield.html')
@login_required
def my_yield_view():
    title, navbar, content = view_my_yield.draw_my_view(request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_my_trade_history.html/<bond_code>/')
@cb.route('/view_my_trade_history.html')
@login_required
def my_trade_history_view(bond_code=''):
    user_id = session.get('_user_id')
    title, navbar, content = view_my_trade_history.draw_my_view(user_id, bond_code, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_my_account.html')
@login_required
def my_account_view():
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_my_account.draw_my_view(user_id is not None, request.url_rule)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@cb.route('/view_market.html')
def market_view():
    # current_user = None
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_market.draw_market_view(user_id)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/view_strategy_group.html')
def strategy_group_view():
    # current_user = None
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_strategy_group.draw_view(user_id)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)


@cb.route('/init_strategy_groups.html')
@login_required
def init_strategy_groups_view():
    view_strategy_group.init_strategy_groups()
    return "OK"


@cb.route('/update_strategy_groups.html')
@login_required
def update_strategy_groups_view():

    # 爬每日交易数据
    cb_jsl_daily.do_fetch_data()

    # 更新轮动组合数据
    update_groups()

    return "OK"


@cb.route('/view_good_year_back_test.html')
def good_year_back_test_view():
    return get_test_view("good_year_back_test")


@cb.route('/view_bad_year_back_test.html')
def bad_year_back_test_view():
    return get_test_view("bad_year_back_test")


@cb.route('/view_long_year_back_test.html')
def long_back_test_view():
    return get_test_view("long_year_back_test")


@cb.route('/view_back_test_1.html')
def back_test_1_view():
    return get_test_view("低溢价策略")


@cb.route('/view_back_test_2.html')
def back_test_2_view():
    return get_test_view("低余额+低溢价+双低策略")


@cb.route('/view_back_test_3.html')
def back_test_3_view():
    return get_test_view("低余额+双低策略")


@cb.route('/view_back_test_4.html')
def back_test_4_view():
    return get_test_view("低溢价+双低策略")


@cb.route('/view_back_test_5.html')
def back_test_5_view():
    return get_test_view("双低策略")


@cb.route('/view_back_test_8.html')
def back_test_8_view():
    return get_test_view("三低策略")


@cb.route('/view_back_test_6.html')
def back_test_6_view():
    return get_test_view("高收益率策略")


@cb.route('/view_back_test_7.html')
def back_test_7_view():
    return get_test_view("低价格策略")


def get_test_view(strategy_name):
    content = backtest.test_utils.get_back_test_data(strategy_name)
    return render_template("page_with_navbar.html",
                           title='轮动策略回测分析',
                           navbar=build_back_test_nav_html(request.url_rule),
                           content=content)


@cb.route('/view_custom_back_test.html')
# @login_required
def custom_back_test_view():
    content = render_template("custom_backtest.html")
    return render_template("page_with_navbar.html",
                           title='轮动策略回测分析',
                           navbar=build_back_test_nav_html(request.url_rule),
                           content=content)

@cb.route('/view_custom_back_test_result.html', methods=['POST'])
# @login_required
def custom_back_test_result_view():
    content = ''
    try:
        s_start = request.form.get("start")
        start = datetime.strptime(s_start, '%Y-%m-%d')

        end = None
        s_end = request.form.get("end")
        if s_end is not None and s_end.strip(' ') != '':
            end = datetime.strptime(s_end, '%Y-%m-%d')
        s_period = request.form.get("period")
        s_period = '' if s_period is None else s_period
        period = 10
        if s_period is not None and s_period.strip(' ') != '':
            period = int(s_period)

        s_count = request.form.get("count")
        s_count = '' if s_count is None else s_count
        count = 15
        if s_count is not None and s_count.strip(' ') != '':
            count = int(s_count)

        s_max_price = request.form.get("max_price")
        s_max_price = '' if s_max_price is None else s_max_price
        max_price = None  # 不同的策略值不一样, 所以只针对单个策略
        if s_max_price is not None and s_max_price.strip(' ') != '':
            max_price = int(s_max_price)

        s_max_double_low = request.form.get("max_double_low")
        s_max_double_low = '' if s_max_double_low is None else s_max_double_low
        max_double_low = None
        if s_max_double_low is not None and s_max_double_low.strip(' ') != '':
            max_double_low = int(s_max_double_low)

        s_pre_day = request.form.get("pre_day")
        s_pre_day = '' if s_pre_day is None else s_pre_day
        pre_day = 5
        if s_pre_day is not None and s_pre_day.strip(' ') != '':
            pre_day = int(s_pre_day)

        s_max_rise = request.form.get("max_rise")
        s_max_rise = '' if s_max_rise is None else s_max_rise
        max_rise = 30
        if s_max_rise is not None and s_max_rise.strip(' ') != '':
            max_rise = int(s_max_rise)

        strategy_types = request.form.getlist("strategy_type")
        if strategy_types is None or len(strategy_types) == 0:
            return 'strategy_type is required '

        is_multi_scenarios = request.form.get("is_multi_scenarios")
        if is_multi_scenarios is not None and is_multi_scenarios == '1':
            if len(strategy_types) != 1:
                return 'when is_multi_scenarios is selected. strategy_type only select one.'
            is_multi_scenarios = True
        else:
            is_multi_scenarios = False

        s_select_sql = request.form.get("select_sql")
        select_sql = None if len(strategy_types) != 1 else (None if s_select_sql is None or s_select_sql.strip(' ') == '' else s_select_sql)
        s_exchange_sql = request.form.get("exchange_sql")
        exchange_sql = None if len(strategy_types) != 1 else None if s_exchange_sql is None or s_exchange_sql.strip(' ') == '' else s_exchange_sql

        content += backtest.jsl_test.test_group(start,
                                                end=end,
                                                roll_period=period,
                                                bond_count=count,
                                                strategy_types=strategy_types,
                                                is_multi_scenarios=is_multi_scenarios,
                                                pre_day=pre_day,
                                                max_rise=max_rise,
                                                max_price=max_price,
                                                max_double_low=max_double_low,
                                                select_sql=select_sql,
                                                exchange_sql=exchange_sql,
                                                )
    except BaseException as e:
        logging.exception(e)
        content = 'occur error:' + str(e)
    return content


@cb.route('/view_enforce_list.html')
def enforce_list_view():
    # current_user = None
    user_id = session.get('_user_id')
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_enforce_list.draw_view(user_id)
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@cb.route('/view_trend.html')
def trend_view():
    # current_user = None
    utils.trade_utils.calc_mid_data()
    title, navbar, content = view_cb_trend.draw_view()
    return render_template("page_with_navbar.html", title=title, navbar=navbar, content=content)

@cb.route('/eastmoney_update_data.html')
@cb.route('/realtime_update_data.html')
# @login_required
def realtime_update_data():
    return cb_eastmoney.fetch_data()

@cb.route('/easy_update_data.html')
@login_required
def jsl_update_data():
    return cb_jsl.fetch_data()

@cb.route('/cb_ninwen.html')
@login_required
def ninwen_update_data():
    return cb_ninwen.fetch_data()

@cb.route('/cb_ninwen_detail.html/<task_name>/', methods=['GET'])
@login_required
def ninwen_detail_update_data(task_name):
    cb_ninwen_detail.fetch_data(task_name)
    return 'OK'

@cb.route('/stock_10jqka.html/<task_name>/', methods=['GET'])
@login_required
def stock_10jqka_update_data(task_name):
    stock_10jqka.fetch_data(task_name)
    return 'OK'


@cb.route('/update_stock_key_info_from_eastmoney.html/<task_name>/', methods=['GET'])
@login_required
def update_stock_key_info_from_eastmoney(task_name):
    stock_eastmoney.update_stock_sum()
    return 'OK'


@cb.route('/update_stock_theme_from_eastmoney.html/<task_name>/', methods=['GET'])
@login_required
def update_stock_theme_from_eastmoney(task_name):
    stock_eastmoney.update_stock_theme()
    return 'OK'

@cb.route('/stock_xueqiu.html/<task_name>/', methods=['GET'])
@login_required
def stock_xueqiu_update_data(task_name):
    stock_xueqiu.fetch_data(task_name)
    return 'OK'

@cb.route('/get_task_data.html/<task_name>/', methods=['GET'])
@login_required
def get_task_data(task_name):
    today = datetime.now()
    task = db.session.query(Task).filter(
        and_(
            Task.name == task_name,
            func.strftime("%Y-%m-%d", Task.modify_date) == today.strftime("%Y-%m-%d"),
        )).first()
    if task is None:
        task = Task()
    return dict(task)


@cb.route('/download_db_data.html')
@login_required
def download_cb_data():
    today = datetime.now()
    ymd = today.strftime('%Y-%m-%d')
    file_name = 'dump/data_' + ymd + '.sql'

    with open(file_name, 'w') as f:
        with get_connect() as con:
            for line in con.iterdump():
                f.write('%s\n' % line)

    # 需要知道2个参数, 第1个参数是本地目录的path, 第2个参数是文件名(带扩展名)
    directory = os.getcwd()  # 假设在当前目录
    return send_from_directory(directory, file_name, as_attachment=True)


@cb.route('/download_cb_daily_data.html')
@login_required
def download_cb_daily_data():
    today = datetime.now()
    ymd = today.strftime('%Y-%m-%d')
    file_name = 'dump/cb_daily_' + ymd + '.sql'

    with open(file_name, 'w') as f:
        with get_daily_connect() as con:
            for line in con.iterdump():
                f.write('%s\n' % line)

    # 需要知道2个参数, 第1个参数是本地目录的path, 第2个参数是文件名(带扩展名)
    directory = os.getcwd()  # 假设在当前目录
    return send_from_directory(directory, file_name, as_attachment=True)


@cb.route('/upload_db_data.html')
@login_required
def upload_db_data():
    return render_template("upload_db_data.html", save_data_url="/save_db_data.html")



@cb.route('/upload_cb_daily_data.html')
@login_required
def upload_cb_daily_data():
    return render_template("upload_db_data.html", save_data_url="/save_cb_daily_data.html")


@cb.route('/save_db_data.html', methods=['POST'])
@login_required
def save_db_data():
    # 删除整个db
    if os.path.exists(db_file_path):
        os.unlink(db_file_path)
    # 获取文件(字符串?)
    file = request.files['file']
    s = file.read().decode('utf-8')
    # 灌入上传的数据
    with get_connect() as con:
        con.executescript(s)

    return 'OK'


@cb.route('/save_cb_daily_data.html', methods=['POST'])
@login_required
def save_cb_daily_data():
    # 删除整个db
    if os.path.exists(db_daily_file_path):
        os.unlink(db_daily_file_path)

    # 获取文件(字符串?)
    file = request.files['file']
    s = file.read().decode('utf-8')
    # 灌入上传的数据
    with get_daily_connect() as con:
        con.executescript(s)

    return 'OK'


@cb.route('/query_database.html', methods=['POST', 'GET'])
@login_required
def query_database_view():
    table_html = ''
    sql_code = ''
    table_height_style = ''
    if len(request.form) > 0:
        sql_code = request.form['sql_code']
        if sql_code is None or sql_code.strip(' ') == '':
            raise Exception('SQL不能为空')

        if not sql_code.lower().strip().startswith('select'):
            raise Exception("仅允许select操作")

        db_type = request.form['db_type']
        cur = None
        if db_type == 'daily':
            with get_daily_connect() as con:
                cur = con.cursor()
                cur.execute(sql_code)
        else:
            with get_connect() as con:
                cur = con.cursor()
                cur.execute(sql_code)
        table = from_db_cursor(cur)

        if table.rowcount > 10:
            table_height_style = """style="height:500px" """

        table_html = utils.table_html_utils.build_table_html(table)

    return render_template("query_database.html", table_html=table_html, sql_code=sql_code, table_height_style=table_height_style)


@cb.route('/update_database.html')
@login_required
def update_database():
    return render_template("update_database.html")


@cb.route('/execute_sql.html', methods=['POST'])
@login_required
def execute_sql():
    sql_code = request.form['sql_code']
    db_type = request.form['db_type']
    if sql_code is None or sql_code.strip(' ') == '':
        raise Exception('SQL不能为空')

    if not sql_code.lower().strip().startswith('update') and not sql_code.lower().strip().startswith('insert'):
        raise Exception("仅允许update/insert操作")

    if db_type == 'daily':
        with get_daily_connect() as con:
            con.executescript(sql_code)
    else:
        with get_connect() as con:
            con.executescript(sql_code)


    return 'OK'


@cb.route('/update_data_after_trade_is_end.html')
@login_required
def update_data_after_trade_is_end():
    return do_update_data_exclude_group_after_trade_is_end(True)


@cb.route('/update_data_before_trade_is_start.html')
@login_required
def update_data_before_trade_is_start():
    return do_update_data_before_trade_is_start()


@cb.route('/update_back_test_data.html')
@login_required
def update_back_test_data():
    return do_update_back_test_data()


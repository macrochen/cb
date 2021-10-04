# -*- coding: utf-8 -*-
import os

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import trade_utils

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    return db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    password = db.Column(db.String(128))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password, password)

class ChangedBond(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bond_code = db.Column(db.String(20))
    cb_name_id = db.Column(db.String(20))

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id')

    def __getitem__(self, item):
        return getattr(self, item)


class TradeDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bond_code = db.Column(db.String(20))
    cb_name_id = db.Column(db.String(20))
    price = db.Column(db.Float)
    amount = db.Column(db.Integer)
    account = db.Column(db.String(20))
    fee = db.Column(db.Float)
    create_date = db.Column(db.Integer)

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'price', 'amount', 'account', 'fee', 'create_date')

    def __getitem__(self, item):
        return getattr(self, item)


class InvestYield(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Integer)
    date_string = db.Column(db.String(20))
    all_yield = db.Column(db.Float)

    day_yield = db.Column(db.Float)
    cb_day_yield = db.Column(db.Float)
    hs_day_yield = db.Column(db.Float)

    my_net_value = db.Column(db.Float)
    cb_net_value = db.Column(db.Float)
    hs_net_value = db.Column(db.Float)


class TradeSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bond_code = db.Column(db.String(20))
    cb_name_id = db.Column(db.String(20))
    # 资产(有交易就更新, 市值+落袋资金, 初始时等于市值)
    assets = db.Column(db.Float)
    # 市值(当前价格*数量)
    market_value = db.Column(db.Float)
    # 持有数量
    amount = db.Column(db.Integer)
    # 持有价格
    cost_price = db.Column(db.Float)
    # 收益(资产-持有数量*持有价格)
    yield_value = db.Column(db.Float)
    # 剩余资金(落袋资金, 初始值为0)
    money = db.Column(db.Float)
    account = db.Column(db.String(20))
    modified_date = db.Column(db.Integer)

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'money', 'amount', 'account', 'modified_date')

    def __getitem__(self, item):
        return getattr(self, item)


class ChangedBondSelect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bond_code = db.Column(db.String(20))
    cb_name_id = db.Column(db.String(20))
    strategy_type = db.Column(db.String(20))
    memo = db.Column(db.String(2048))

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'strategy_type', 'memo')

    def __getitem__(self, item):
        return getattr(self, item)


class HoldBond(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bond_code = db.Column(db.String(20))
    cb_name_id = db.Column(db.String(20))
    hold_price = db.Column(db.Float())
    hold_amount = db.Column(db.Integer)
    hold_unit = db.Column(db.Integer)
    account = db.Column(db.String(20))
    strategy_type = db.Column(db.String(20))
    sum_buy = db.Column(db.Float, default=0.0)
    sum_sell = db.Column(db.Float, default=0.0)
    memo = db.Column(db.String(1024), default='')

    def __init__(self):
        self.sum_sell = 0.0
        self.sum_buy = 0.0
        self.hold_amount = 0
        self.hold_price = 0.0
        self.memo = ''

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'hold_price', 'hold_amount', 'account', 'strategy_type', 'memo')

    def __getitem__(self, item):
        return getattr(self, item)

    def calc_hold_price(self, direction, trade_amount, trade_price):
        # 交易金额
        trade_num = round(float(trade_price) * int(trade_amount), 3)
        fee = trade_utils.calc_trade_fee(self.account, self.hold_unit == 10, trade_num)
        # 持仓成本
        cost_num = self.sum_buy - self.sum_sell + fee
        if direction == 'buy':
            self.hold_amount += int(trade_amount)
            self.sum_buy += trade_num + fee
            cost_num += trade_num
        elif direction == 'sell':
            self.hold_amount -= int(trade_amount)
            self.sum_sell += trade_num - fee
            cost_num -= trade_num
        # 重新计算持有价格: 持仓成本/持仓数量
        if self.hold_amount == 0:
            self.hold_price = 0
        else:
            self.hold_price = round(cost_num / self.hold_amount, 3)
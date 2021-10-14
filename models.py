# -*- coding: utf-8 -*-

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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

class BaseHoldBond(db.Model):
    __abstract__ = True

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
    memo = db.Column(db.String(1024))
    start_date = db.Column(db.String(20))

    def __init__(self):
        self.sum_sell = 0.0
        self.sum_buy = 0.0
        self.hold_amount = 0
        self.hold_price = 0.0
        self.memo = ''

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'hold_price', 'hold_amount', 'account', 'strategy_type', 'sum_buy', 'sum_sell', 'memo', 'start_date')


class HoldBond(BaseHoldBond):
    modify_date = db.Column(db.String(20))

    def keys(self):
        my_keys = list(super().keys())
        my_keys.append('modify_date')
        return tuple(my_keys)

    def __getitem__(self, item):
        return getattr(self, item)


class HoldBondHistory(BaseHoldBond):
    end_date = db.Column(db.String(20))

    def keys(self):
        my_keys = list(super().keys())
        my_keys.append('end_date')
        return tuple(my_keys)

    def copy(self, source):
        for key, value in source.__dict__.items():
            if key not in self.keys() or value is None:
                continue
            setattr(self, key, value)


class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String(20))
    key = db.Column(db.String(100))
    value = db.Column(db.String(2048))
    ext_value = db.Column(db.String(2048))
    desc = db.Column(db.String(2048))
    is_delete = db.Column(db.Integer)
    owner_id = db.Column(db.Integer)

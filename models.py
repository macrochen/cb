# -*- coding: utf-8 -*-
import math
from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
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

    def to_dict(self, expect_name=None):
        dict = {}
        for key in self.keys():
            if expect_name is not None and key == expect_name:
                continue

            dict[key] = self.__getitem__(key)
        return dict

    def __getitem__(self, item):
        return getattr(self, item)


class TradeHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bond_code = db.Column(db.String(20))
    cb_name_id = db.Column(db.String(20))
    price = db.Column(db.Float)
    amount = db.Column(db.Integer)
    hold_id = db.Column(db.Integer)
    owner_id = db.Column(db.Integer)
    account = db.Column(db.String(20))
    strategy_type = db.Column(db.String(20))
    fee = db.Column(db.Float)
    create_date = db.Column(db.DateTime, server_default=func.now())
    is_delete = db.Column(db.Integer, default=0)

    def __init__(self):
        self.is_delete = 0

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'price', 'amount', 'account', 'fee', 'create_date', 'owner_id', 'hold_id', 'strategy_type', 'is_delete')

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
    is_deleted = db.Column(db.Integer, default=0)

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'strategy_type', 'memo', 'is_deleted')

    def to_dict(self):
        dict = {}
        for key in self.keys():
            dict[key] = self.__getitem__(key)
        return dict

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

    def to_dict(self, expect_name=None):
        dict = {}
        for key in self.keys():
            if expect_name is not None and key == expect_name:
                continue

            dict[key] = self.__getitem__(key)
        return dict

    def copy(self, source):
        for key, value in source.__dict__.items():
            if key not in self.keys() or value is None:
                continue
            setattr(self, key, value)


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


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    current_num = db.Column(db.Integer)
    total_num = db.Column(db.Integer)
    process = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer)
    create_date = db.Column(db.DateTime)
    modify_date = db.Column(db.DateTime)
    is_delete = db.Column(db.DateTime)
    desc = db.Column(db.String(1024))

    def __init__(self):
        self.current_num = 0
        self.total_num = 0
        self.process = 0

    def keys(self):
        return ('id', 'name', 'current_num', 'total_num', 'process', 'status', 'modify_date', 'create_date', 'is_delete', 'desc')


    def __getitem__(self, item):
        return getattr(self, item)

    def update(self, num):
        self.current_num += num
        self.process = 0 if self.total_num == 0 else math.ceil(self.current_num/self.total_num*100)
        self.modify_date = datetime.now()

    def error(self, desc):
        self.status = -1
        self.desc = desc
        self.modify_date = datetime.now()

    def success(self, desc):
        self.current_num = self.total_num
        self.status = 1
        self.desc = desc
        self.modify_date = datetime.now()


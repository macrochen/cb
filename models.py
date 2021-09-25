# -*- coding: utf-8 -*-
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config import db


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
    memo = db.Column(db.String(1024))

    def keys(self):
        return ('id', 'bond_code', 'cb_name_id', 'hold_price', 'hold_amount', 'account', 'strategy_type', 'memo')

    def __getitem__(self, item):
        return getattr(self, item)


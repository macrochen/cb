# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.root_path, 'db/cb.db3')
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

db = SQLAlchemy(app)  # 初始化扩展，传入程序实例 app
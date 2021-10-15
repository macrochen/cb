# -*- coding: utf-8 -*-
from flask import Flask

import config
from jobs import init_job
from models import init_db
from routers import cb, login_manager


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config.config[config_name])
    config.config[config_name].init_app(app)

    init_job()
    init_db(app)
    init_router(app)

    return app


def init_router(app):
    login_manager.init_app(app)  # 实例化扩展类
    app.register_blueprint(cb)

app = create_app()

if __name__ == "__main__":
    # development 开发环境
    # production 生产环境
    app = create_app("development")

    # app.run()  # 生产环境使用, 调用run方法，设定端口号，启动服务
    app.run(port=8080, host="127.0.0.1", debug=True)  #开发环境使用, use_reloader=true, 方便频繁修改自动重启
    # app.run(port=8080, host="127.0.0.1", debug=True, use_reloader=False)  #开发环境使用, use_reloader=false, 默认为true会导致scheduler被调用两次

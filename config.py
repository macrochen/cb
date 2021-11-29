# -*- coding: utf-8 -*-

import os

basedir = os.path.abspath(os.path.dirname(__file__))

db_file_path = 'db/cb.db3'
db_daily_file_path = 'db/cb_daily.db3'

class Config:
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SECRET_KEY = 'super secret key'
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////' + os.path.join(basedir, db_file_path)
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True
    SQLALCHEMY_ECHO = True
    # SERVER_NAME = '127.0.0.1:8080'


class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
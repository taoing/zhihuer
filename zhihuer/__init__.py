from __future__ import absolute_import

import pymysql
# 引入celery实例对象
from .celery import app as celery_app

# 安装mysql数据库驱动
pymysql.install_as_MySQLdb()

__all__ = ('celery_app',)
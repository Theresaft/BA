# server/config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig(object):
    """Base configuration."""
    WTF_CSRF_ENABLED = True 
    REDIS_URL = "redis://redis:6379/0"
    QUEUES = ["my_queue"]


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    WTF_CSRF_ENABLED = False # Turn off Cross Site Orgin for development
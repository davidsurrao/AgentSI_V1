import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
    DEBUG = True

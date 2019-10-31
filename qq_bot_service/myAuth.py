from functools import wraps
import json
from flask import render_template
from flask import request


def cold_login_auth(redisdb,auth=2):
    def wrapper(func):
        @wraps(func)
        def __deco(*args, **kwargs):
            if "token" in request.cookies.keys():
                if redisdb.exists(request.cookies["token"]):
                    redisdb.expire(request.cookies["token"], 3600)
                    userdata = json.loads(redisdb.get(request.cookies["token"]))
                    if userdata["auth_class"] <= auth:
                        return func(*args, **kwargs)
                    else:
                        return "<h1>无权操作组件</h1>"
                else:
                    return render_template("redirect.html",target="/login",add_js="alert('登录超时，请重新登录');")
            else:
                return render_template("redirect.html", target="/login", add_js="alert('登录超时，请重新登录');")
        return __deco
    return wrapper



if __name__ == '__main__':
    import pymysql
    import redis
    import setupfile
    redisdb = redis.Redis(host=setupfile.redis_host,
                          port=setupfile.redis_port,
                          db=setupfile.redis_db)
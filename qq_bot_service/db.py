import traceback
import pymysql,redis
import setupfile

try:
    redisdb = redis.Redis(host=setupfile.redis_host,
                          port=setupfile.redis_port,
                          db=setupfile.redis_db)
    mysqlconn = pymysql.connect(host=setupfile.mysql_host,
                                port=setupfile.mysql_port,
                                user=setupfile.mysql_username,
                                passwd=setupfile.mysql_password,
                                db=setupfile.mysql_db)
    mysqldb = mysqlconn.cursor()
except Exception as e:
    traceback.print_exc()
    raise Exception("something wrong with set_up_file.py")
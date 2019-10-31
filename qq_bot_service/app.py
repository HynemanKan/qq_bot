import importlib
import logging
import json
import traceback
import pymysql
from flask import request
from cqhttp import CQHttp
import setupfile
from admin_service import admin
from db import mysqldb,mysqlconn,redisdb
from model import respond_private,respond_group
from plugin.special_plugin.empty_handle import handle as empty_handle
from plugin.special_plugin.tempstop_handle import handle as tempstop_handle
from plugin.special_plugin.take_message_handle import handle as take_message_handle
# logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='qq_connect_log.log',
                    filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
#int
bot = CQHttp(api_root=setupfile.cq_api_root,
             access_token=setupfile.cq_access_token,
             secret=setupfile.cq_secret)
app = bot.server_app


# plugin_private_add
sql = "SELECT * FROM private_message_plugin"
private_plugin_list = mysqldb.execute(sql)
privateMessageHandles=[]
data = mysqldb.fetchall()
for plugin in data:
    module = importlib.import_module(plugin[2])
    app.register_blueprint(module.blueprint,url_prefix=f"/admin/plugin/private/{plugin[0]}")
    #print(plugin)
    if plugin[3] ==0:
        privateMessageHandles.append([module.re_str,module.handle,module.sample_active_word])
    elif plugin[3]==1:
        privateMessageHandles.append([module.re_str,tempstop_handle,"null"])
    else:
        privateMessageHandles.append([module.re_str,empty_handle,"null"])


# plugin_group_add
sql= "SELECT * FROM group_message_plugin"
group_plugin_list = mysqldb.execute(sql)
data = mysqldb.fetchall()
for plugin in data:
    module = importlib.import_module(plugin[2])
    app.register_blueprint(module.blueprint,url_prefix=f"/admin/plugin/group/{plugin[0]}")
sql="SELECT a.g_id,b.package_name FROM group_message_plugin_activate as a LEFT JOIN group_message_plugin as b on a.plugin_name = b.plugin_name"
group_plugin_list = mysqldb.execute(sql)
data = mysqldb.fetchall()
groupMessageHandles = {}
groupMessageHandle_init_data = {}
for plugin in data:
    module = importlib.import_module(plugin[1])
    groupMessageHandle_init_data[module.plugin_name] = module.setup()
    if plugin[0] in groupMessageHandles.keys():
        groupMessageHandles[plugin[0]].append([module.plugin_name,module.handle])
    else:
        temp = [[module.plugin_name,module.handle]]
        groupMessageHandles[plugin[0]] = temp


#plugin_out_page
sql = "SELECT * FROM plugin_out_blueprint"
mysqldb.execute(sql)
plugin_out_page_list = mysqldb.fetchall()
for outpage in plugin_out_page_list:
    #print(outpage)
    exec(f"from {outpage[2]} import blueprint_out as blueprint_out")
    app.register_blueprint(blueprint_out,url_prefix=f"/out/{outpage[1]}")
# Control Panel
app.register_blueprint(admin, url_prefix="/admin")


#reflash
@app.route("/API/reflash.json")
def reflash_plugin():
    #plugin_private_reflash
    sql = "SELECT * FROM private_message_plugin"
    temp = mysqldb.execute(sql)
    new_privateMessageHandles = []
    data = mysqldb.fetchall()
    for plugin in data:
        module = importlib.import_module(plugin[2])
        if plugin[3] == 0:
            new_privateMessageHandles.append([module.re_str, module.handle, module.sample_active_word])
        elif plugin[3] == 1:
            new_privateMessageHandles.append([module.re_str, tempstop_handle, "null"])
        else:
            new_privateMessageHandles.append([module.re_str, empty_handle, "null"])
    global privateMessageHandles
    #print(privateMessageHandles)
    #print(new_privateMessageHandles)
    privateMessageHandles = new_privateMessageHandles
    #plugin_group_reflash
    sql = "SELECT a.g_id,b.package_name FROM group_message_plugin_activate as a LEFT JOIN group_message_plugin as b on a.plugin_name = b.plugin_name"
    mysqldb.execute(sql)
    data = mysqldb.fetchall()
    new_groupMessageHandles = {}
    new_groupMessageHandle_init_data = {}
    for plugin in data:
        module = importlib.import_module(plugin[1])
        new_groupMessageHandle_init_data[module.plugin_name] = module.setup()
        if plugin[0] in new_groupMessageHandles.keys():
            new_groupMessageHandles[plugin[0]].append([module.plugin_name,module.handle])
        else:
            temp = [[module.plugin_name,module.handle]]
            new_groupMessageHandles[plugin[0]] = temp
    global groupMessageHandles
    #print(groupMessageHandles)
    #print(new_groupMessageHandles)
    groupMessageHandles = new_groupMessageHandles
    global groupMessageHandle_init_data
    groupMessageHandle_init_data = new_groupMessageHandle_init_data
    return json.dumps({"state":True})


#handles
##私聊
@bot.on_message("private")
def private(context):
    mysqlconn.ping(reconnect=True)
    #logger
    sql = "INSERT INTO service_log (time, type, target) VALUES (NOW(),'privateMessage',%s)"
    mysqldb.execute(sql,(f"person:{context['sender']['user_id']}"))
    mysqlconn.commit()
    try:
        state = respond_private(privateMessageHandles,context,bot)
        if not state:
            take_message_handle(context,bot)
    except Exception as e:
        bot.send(context,"服务器发生内部错误，请稍后重试")
        traceback.print_exc()
        error_data = traceback.format_exc()
        sql = "INSERT INTO error_log (time, error_detail) VALUES (NOW(),%s)"
        mysqldb.execute(sql,(pymysql.escape_string(error_data)))
        mysqlconn.commit()
        redisdb.delete(context["sender"]["user_id"])


##群聊
@bot.on_message("group")
def group(context):
    mysqlconn.ping(reconnect=True)
    sql = "INSERT INTO service_log (time, type, target) VALUES (NOW(),'groupMessage',%s)"
    mysqldb.execute(sql, (f"group:{context['group_id']};person:{context['sender']['user_id']}"))
    mysqlconn.commit()
    try:
        respond_group(groupMessageHandles,groupMessageHandle_init_data,context,bot)
    except Exception as e:
        traceback.print_exc()
        error_data = traceback.format_exc()
        sql = "INSERT INTO error_log (time, error_detail) VALUES (NOW(),%s)"
        mysqldb.execute(sql, (pymysql.escape_string(error_data)))
        mysqlconn.commit()


##好友申请  待开发
@bot.on_request('friend')
def handle_request(context):
    mysqlconn.ping(reconnect=True)
    sql = 'INSERT INTO service_log (time, type, target) VALUES (NOW(),"friendAdd",%s)'
    mysqldb.execute(sql,(f'person:{context["user_id"]}'))
    mysqlconn.commit()
    return {"approve":True}


##群成员增加 待开发
@bot.on_notice('group_increase')
def handle_request(context):
    mysqlconn.ping(reconnect=True)
    sql = 'INSERT INTO service_log (time, type, target) VALUES (NOW(),"groupMumAdd",%s)'
    mysqldb.execute(sql,(f'group:{context["group_id"]}'))
    mysqlconn.commit()


##加群请求 待开发
@bot.on_request("group")
def handle_group_increase(context):
    mysqlconn.ping(reconnect=True)
    sql ='INSERT INTO service_log (time, type, target) VALUES (NOW(),"groupMumReq",%s)'
    mysqldb.execute(sql,(f'group:{context["user_id"]};person:{context["group_id"]}'))
    mysqlconn.commit()


if __name__ == '__main__':
    bot.run()

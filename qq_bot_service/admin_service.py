import hashlib
import json
import uuid
import traceback
import random,string
import urllib.parse
import re
import requests
import pyotp
from flask import Blueprint
from flask import redirect
from flask import request, Response, render_template
from db import mysqlconn,mysqldb,redisdb
import myAuth
#init

admin = Blueprint("admin",__name__,template_folder='templates', static_folder='static')


private_plugin = []
sql = "SELECT * FROM private_message_plugin"
private_plugin_list = mysqldb.execute(sql)
data = mysqldb.fetchall()
for plugin in data:
    plugin_label = {"bname":plugin[1],
                    "name":plugin[0],
                    "state":plugin[2]}
    private_plugin.append(plugin_label)

group_plugin = []
sql = "SELECT * FROM group_message_plugin"
private_plugin_list = mysqldb.execute(sql)
data = mysqldb.fetchall()
for plugin in data:
    plugin_label = {"bname":plugin[1],
                    "name":plugin[0]}
    group_plugin.append(plugin_label)



def replace_cq2html(message:str,nohtml=False):
    image = re.search("\[CQ:image.*]",message)
    if image is None:
        return message
    else:
        image=image.group()
        if nohtml:
            return message.replace(image,"[图片]")
        url = re.search("url=.*",image).group()[4:-1]
        new_img= f"<img src='{url}'>"
        new_message = message.replace(image, new_img)
        #print(new_img,new_message)
        return new_message

def check(user,password):
    md5 = hashlib.md5()
    md5.update(f"{password}{user[2]}".encode("utf-8"))
    return md5.hexdigest() == user[1]


def random_password():
    src = string.ascii_letters + string.digits
    list_passwd_all = random.sample(src, 5)  # 从字母和数字中随机取5位
    list_passwd_all.extend(random.sample(string.digits, 1))  # 让密码中一定包含数字
    list_passwd_all.extend(random.sample(string.ascii_lowercase, 1))  # 让密码中一定包含小写字母
    list_passwd_all.extend(random.sample(string.ascii_uppercase, 1))  # 让密码中一定包含大写字母
    random.shuffle(list_passwd_all)  # 打乱列表顺序
    str_passwd = ''.join(list_passwd_all)  # 将列表转化为字符串
    return str_passwd


def log_data(target="*"):
    data = []
    name = []
    if target == "*":
        mysqldb.execute(f"SELECT date_format(days,'%m月%d日'),num FROM `daily_event_num` LIMIT 5")
    else:
        mysqldb.execute(f"SELECT date_format(days,'%m月%d日'),num FROM `daily_friendadd_num` LIMIT 5")
    getdata = mysqldb.fetchall()
    for line in getdata:
        name.append(line[0])
        data.append(line[1])
    return name, data


@admin.route("/plugin/main/home")
@myAuth.cold_login_auth(redisdb)
def home():
    return render_template("homepage.html")


@admin.route("/")
@myAuth.cold_login_auth(redisdb)
def frame():
    data = json.loads(redisdb.get(request.cookies["token"]))
    return render_template("frame.html",
                           private_plugin=private_plugin,
                           group_plugin=group_plugin,
                           username=data["id"])


@admin.route("/plugin/main/index/state")
@myAuth.cold_login_auth(redisdb)
def now_state():
    friend_chat_name, friend_chat_data = log_data(target="friendAdd")
    message_chat_name, message_chat_data = log_data()
    sql = "SELECT * FROM message WHERE res='none'"
    message_num = mysqldb.execute(sql)
    return render_template("now_state.html",
                           friend_chat_name=friend_chat_name,
                           friend_chat_data=friend_chat_data,
                           message_chat_name=message_chat_name,
                           message_chat_data=message_chat_data,
                           message_num=message_num)


@admin.route("/plugin/main/index/message")
@myAuth.cold_login_auth(redisdb)
def message_list():
    sql = "SELECT * FROM message AS a WHERE a.send_time IN ( SELECT MAX( send_time ) FROM message GROUP BY sender ) ORDER BY send_time DESC"
    mysqldb.execute(sql)
    data = mysqldb.fetchall()
    messages =[]
    for line in data:
        message={"sender_id":line[1],
                 "detail":replace_cq2html(line[3],nohtml=True),
                 "time":line[2]}
        messages.append(message)
    return render_template("message_list.html",messages=messages)

@admin.route("/plugin/main/index/re_import")
@myAuth.cold_login_auth(redisdb, auth=0)
def re_import_page():
    return render_template("re_import.html")


@admin.route("/plugin/main/index/groupadd")
@myAuth.cold_login_auth(redisdb,auth=0)
def group_add_page():
    return render_template("group_add.html")


@admin.route("/plugin/main/index/group_plugin")
@myAuth.cold_login_auth(redisdb, auth=1)
def group_plugin_page():
    sql ="SELECT * FROM `group`"
    mysqldb.execute(sql)
    data = mysqldb.fetchall()
    groups=[]
    for line in data:
        group={"g_id":line[0],
               "g_name":line[1],
               "plugins":[]}
        if line[0] == "*":
            group["g_id"] = "all"
        groups.append(group)
    sql = """
    SELECT a.plugin_name,a.plugin_bname,a.package_name,c.g_id FROM group_message_plugin as a LEFT JOIN (
        SELECT * FROM group_message_plugin_activate as b WHERE b.g_id = %s
        ) as c on c.plugin_name = a.plugin_name
    """
    #print(groups)
    for i in range(len(groups)):
        now_group_id = groups[i]["g_id"]
        if now_group_id == "all":
            now_group_id = "*"
        mysqldb.execute(sql,(now_group_id))
        data = mysqldb.fetchall()
        for line in data:
            package = {
                "bname":line[1],
                "name":line[0],
                "package_name":line[2]
            }
            if isinstance(line[3],str):
                package["bstate"]="启用"
            else:
                package["bstate"]="停用"
            groups[i]["plugins"].append(package)
    #print(groups)
    return render_template("group_plugin_list.html",groups=groups)


@admin.route("/plugin/main/index/private_plugin")
@myAuth.cold_login_auth(redisdb, auth=1)
def private_plugin_page():
    sql="SELECT * FROM private_message_plugin"
    mysqldb.execute(sql)
    data = mysqldb.fetchall()
    plugins=[]
    for line in data:
        plugin={"name":line[0],
                "bname":line[1],
                "package_name":line[2],
                "state":line[3]}
        if line[3] ==0:
            plugin["bstate"]="启用"
        elif line[3]==1:
            plugin["bstate"]="临时停用"
        else:
            plugin["bstate"]="永久停用"
        plugins.append(plugin)
    return render_template("private_plugin_list.html",plugins=plugins)


@admin.route('/dialogue/<qid>')
@myAuth.cold_login_auth(redisdb)
def dialogue(qid):
    sql = "SELECT * FROM message WHERE sender=%s ORDER BY send_time ASC"
    state = mysqldb.execute(sql, (qid))
    if state > 0:
        data = mysqldb.fetchall()
        dialogues=[]
        for line in data:
            dialogue = {"detail":replace_cq2html(line[3]),
                        "send_time":line[2],
                        "res":line[4],
                        "res_time":line[6]}
            dialogues.append(dialogue)
        sql = "SELECT a.qid,b.* FROM qid2sid as a LEFT JOIN stdinfo  as b on a.sid=b.sid WHERE a.qid=%s"
        state = mysqldb.execute(sql, (qid))
        if state >0:
            have_info=True
            data = mysqldb.fetchall()
            sender = {"qid": qid,
                      "name":data[0][2],
                      "sid":data[0][1],
                      "major":data[0][5],
                      "school":data[0][4],
                      "sex":data[0][3]}
            if isinstance(data[0][6],str):
                sender["phone"] = data[0][6]
            else:
                sender["phone"] = "未绑定"
        else:
            have_info=False
            sender={"qid":qid}
        return render_template("dialogue.html", have_info=have_info, sender=sender, dialogues=dialogues)
    else:
        return "<h1>无该对话</h1>"

@admin.route('/user/<user_id>', methods=["GET"])
@myAuth.cold_login_auth(redisdb)
def user_home(user_id):
    userdata = json.loads(redisdb.get(request.cookies["token"]))
    operator_id = userdata["id"]
    operator_auth = userdata["auth_class"]
    if operator_id == user_id:
        operator_otpkey = userdata["OTP_key"]
        otp_url = pyotp.totp.TOTP(operator_otpkey).provisioning_uri(f"{operator_id}@sues.edu.cn", issuer_name="qq_bot_service")
        return render_template("user_personal.html",s_id=operator_id,usertype=operator_auth,otpuri=otp_url)
    else:
        if operator_auth > 0:
            return "<h1>无权访问</h1>"
        else:
            sql = "SELECT * FROM admin WHERE id=%s"
            mysqldb.execute(sql,(user_id))
            data = mysqldb.fetchall()[0]
            return render_template("user_root.html",s_id=data[0],usertype=data[-2])


@admin.route("/plugin/main/index/user")
@myAuth.cold_login_auth(redisdb,auth=0)
def user_list():
    sql = "SELECT admin.id,admin.auth_class FROM admin"
    mysqldb.execute(sql)
    users_list = mysqldb.fetchall()
    users = []
    for line in users_list:
        user = {"userid":line[0],
                "type":line[1]}
        users.append(user)
    #print(users)
    return render_template("user_list.html",users=users)


@admin.route("/plugin/main/index/useradd")
@myAuth.cold_login_auth(redisdb,auth=0)
def user_add():
        return render_template("user_add.html")

@admin.route("/plugin/main/API/v1/reset_by_admin.json",methods=["POST"])
@myAuth.cold_login_auth(redisdb,auth=0)
def reset_by_admin():
    target_id = request.form["s_id"]
    newpassword = request.form["newpassword"]
    otppassword = request.form["otppassword"]
    data = json.loads(redisdb.get(request.cookies["token"]))
    otp_key = data["OTP_key"]
    sql = "SELECT * FROM admin where id = %s"
    mysqldb.execute(sql, (target_id))
    user_data = mysqldb.fetchall()[0]
    otp_checker = pyotp.TOTP(otp_key)
    #print(otp_checker.now(),otppassword)
    if otp_checker.verify(otppassword):
        md5 = hashlib.md5()
        md5.update(f"{newpassword}{user_data[2]}".encode("utf-8"))
        md5_passwd = md5.hexdigest()
        try:
            sql = "UPDATE admin SET password=%s WHERE id=%s"
            mysqldb.execute(sql,(md5_passwd,target_id))
            mysqlconn.commit()
            return "success"
        except Exception as e:
            print(e)
            return "fail"
    else:
        return "fail"


@admin.route("/plugin/main/API/v1/group_add.js",methods=["POST"])
@myAuth.cold_login_auth(redisdb,auth=0)
def group_add():
    group_id=request.form["group_id"]
    bname = request.form["bname"]
    #print(group_id,bname)
    sql = "INSERT INTO `group` VALUES (%s,%s)"
    try:
        mysqldb.execute(sql,(group_id,bname))
        mysqlconn.commit()
    except Exception as e:
        return json.dumps({"state":"fail","message":"error"})
    return json.dumps({"state":"success","info":"成功"})


@admin.route("/plugin/main/API/v1/res_dialogue.json",methods=["POST"])
@myAuth.cold_login_auth(redisdb)
def send_private_message():
    operator = json.loads(redisdb.get(request.cookies["token"]))
    qid = request.form["qid"]
    message = request.form["message"]
    #print(qid,message)
    sql = "SELECT * FROM message WHERE sender=%s"
    data = mysqldb.execute(sql,(qid))
    if data > 0:
        sql = "SELECT * FROM message WHERE sender=%s and res='none'"
        state = mysqldb.execute(sql,(qid))
        #print(state)
        if state >0:
            sql = "UPDATE message SET res='ignore',res_time=NOW(),res_user_id=%s WHERE res='none' and sender=%s"
            mysqldb.execute(sql, (operator["id"],qid))
            sql = "UPDATE message SET res=%s WHERE sender=%s ORDER BY send_time DESC LIMIT 1"
            mysqldb.execute(sql,(message,qid))
        else:
            uid = str(uuid.uuid4())
            sql = "INSERT INTO message values(%s,%s,NOW(),'Dialogue_Detail_None',%s,%s,NOW())"
            mysqldb.execute(sql,(uid,qid,message,operator["id"]))
        data = {"qid":qid,
                "message":message}
        res = requests.post("http://127.0.0.1:5000/API/send_private_message.json", data).json()
        #print(res)
        if res["state"] == "success":
            mysqlconn.commit()
            return json.dumps({"state":"success","message":""})
        else:
            return json.dumps({"state":"fail","message":"系统出错"})
    else:
        return json.dumps({"state":"fail","message":"无留言可以回复"})


@admin.route("/plugin/main/API/v1/private_plugin.json",methods=["POST"])
@myAuth.cold_login_auth(redisdb,auth=1)
def private_plugin_state():
    plugin_name = request.form["plugin_name"]
    state = int(request.form["state"])
    if state == 0:
        bstate = "启用"
    elif state == 1:
        bstate = "临时停用"
    else:
        bstate = "永久停用"
    #print(plugin_name,state)
    sql = f"UPDATE private_message_plugin SET active={int(state)} WHERE plugin_name=%s"
    try:
        #print(sql)
        state = mysqldb.execute(sql,(plugin_name))
        if state == 1:
            mysqlconn.commit()
        else:
            return json.dumps({"state":"fail","message":"无内容修改"})
    except Exception as e:
        return json.dumps({"state":"fail","message":"服务器异常"})
    return json.dumps({"state":"success","bstate":bstate})


@admin.route("/plugin/main/API/v1/group_plugin.json",methods=["POST"])
@myAuth.cold_login_auth(redisdb,auth=1)
def private_group_state():
    gid = request.form["group_id"]
    if gid == "all":
        gid = "*"
    plugin_name = request.form["plugin_name"]
    state = int(request.form["state"])
    if state == 0:
        bstate = "启用"
    elif state == 1:
        bstate = "停用"
    #print(gid,plugin_name,state)
    if gid == "*" and state == 0:
        #print("a")
        sql = "DELETE FROM group_message_plugin_activate WHERE plugin_name = %s"
        mysqldb.execute(sql, (plugin_name))
        sql = "INSERT INTO group_message_plugin_activate values(%s,%s)"
        mysqldb.execute(sql, (gid, plugin_name))
        mysqlconn.commit()
        return json.dumps({"state":"success","bstate":bstate})
    elif gid == "*" and state ==1:
        #print("b")
        sql = "DELETE FROM group_message_plugin_activate WHERE plugin_name = %s"
        mysqldb.execute(sql, (plugin_name))
        mysqlconn.commit()
        return json.dumps({"state": "success", "bstate": bstate})
    elif state == 0:
        sql = 'SELECT * FROM group_message_plugin_activate WHERE (plugin_name = %s and g_id = "*")'
        exist = mysqldb.execute(sql, (plugin_name))
        if exist > 0:
            #print("c")
            return json.dumps({"state":"success","bstate":"已全局打开"})
        else:
            #print("d")
            sql = 'SELECT * FROM group_message_plugin_activate WHERE (plugin_name = %s and g_id = %s)'
            exist = mysqldb.execute(sql, (plugin_name,gid))
            if exist >0:
                return json.dumps({"state": "success", "bstate": bstate})
            sql = "INSERT INTO group_message_plugin_activate values(%s,%s)"
            mysqldb.execute(sql, (gid, plugin_name))
            mysqlconn.commit()
            return json.dumps({"state": "success", "bstate": bstate})
    else:
        sql = 'SELECT * FROM group_message_plugin_activate WHERE (plugin_name = %s and g_id = "*")'
        exist = mysqldb.execute(sql,(plugin_name))
        if exist >0:
            #print("e")
            return json.dumps({"state":"success","bstate":"已全局打开,请在全局中设置"})
        else:
            #print("f")
            sql = "DELETE FROM group_message_plugin_activate WHERE (plugin_name = %s and g_id = %s) "
            mysqldb.execute(sql, (plugin_name, gid))
            mysqlconn.commit()
            return json.dumps({"state": "success", "bstate": bstate})


@admin.route("/plugin/main/API/v1/re_import.json")
@myAuth.cold_login_auth(redisdb,auth=0)
def re_import_api():
    try:
        data = requests.get("http://127.0.0.1:5000/API/reflash.json").json()
    except Exception as e:
        return json.dumps({"state":"fail","message":"error"})
    if data["state"]:
        return json.dumps({"state":"success","info":"成功"})
@admin.route("/plugin/main/API/v1/reset_by_self.json",methods=["POST"])
@myAuth.cold_login_auth(redisdb)
def reset_by_user():
    oldpassword = request.form["oldpassword"]
    newpassword = request.form["newpassword"]
    data = json.loads(redisdb.get(request.cookies["token"]))
    user_id = data["id"]
    sql = "SELECT * FROM admin where id = %s"
    mysqldb.execute(sql, (user_id))
    user_data = mysqldb.fetchall()[0]
    if check(user_data,oldpassword):
        md5 = hashlib.md5()
        md5.update(f"{newpassword}{user_data[2]}".encode("utf-8"))
        md5_passwd = md5.hexdigest()
        try:
            sql = "UPDATE admin SET password=%s WHERE id=%s"
            mysqldb.execute(sql,(md5_passwd,user_id))
            mysqlconn.commit()
            return json.dumps({"state": "success","message":"修改成功"})
        except Exception as e:
            return json.dumps({"state": "fail","message":"服务器异常"})
    else:
        return json.dumps({"state": "fail","message":"密码有误"})


@admin.route("/plugin/main/API/v1/new_user.json",methods=["POST"])
@myAuth.cold_login_auth(redisdb,auth=0)
def new_user():
    data = json.loads(redisdb.get(request.cookies["token"]))
    otpkey = data["OTP_key"]
    user_id = request.form["s_id"]
    user_auth = request.form["auth"]
    otp_passwd = request.form["otppassword"]
    otp_checker = pyotp.TOTP(otpkey)
    if otp_checker.verify(otp_passwd):
        user_otp_key = pyotp.random_base32()
        user_salt = str(uuid.uuid4())
        md5 = hashlib.md5()
        new_random_password = random_password()
        md5.update(f"{new_random_password}{user_salt}".encode("utf-8"))
        md5_passwd = md5.hexdigest()
        try:
            sql = f"INSERT INTO admin values (%s,%s,%s,{int(user_auth)},%s)"
            mysqldb.execute(sql,(user_id,md5_passwd,user_salt,user_otp_key))
            mysqlconn.commit()
            return json.dumps({"state": "success", "password": new_random_password})
        except Exception as e:
            print(e)
            return json.dumps({"state": "fail","message":"该用户已存在"})
    return json.dumps({"state":"fail","message":"动态密码错误或超时"})

@admin.route("login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        resp = render_template("login_admin.html")
    else:
        mysqlconn.ping(reconnect=True)
        target = request.args.get("redirect")
        if target is None:
            target = "/"
        target = urllib.parse.unquote(target)
        #print(target)
        username = request.form["username"]
        passwd = request.form["password"]
        exist = mysqldb.execute("SELECT * from admin WHERE id=%s",username)
        state = False
        if exist:
            user = mysqldb.fetchall()[0]
            state = check(user, passwd)
        if state:
            cookies = str(uuid.uuid4())
            redisdb.set(cookies, json.dumps({"id": user[0],
                                             "auth_class": user[3],
                                             "OTP_key": user[4]}))
            resp = Response(render_template("redirect.html",target=target))
            resp.set_cookie("token",cookies)
        else:
            resp = render_template("login_admin.html",color='red',message='密码错误或用户不存在')
    return resp


@admin.route("logout")
@myAuth.cold_login_auth(redisdb)
def logout():
    redisdb.delete(request.cookies["token"])
    resp = Response(render_template("redirect.html", target="login"))
    resp.delete_cookie("token")
    return resp


if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    sql = "SELECT * FROM private_message_plugin"
    private_plugin_list = mysqldb.execute(sql)
    data = mysqldb.fetchall()
    for plugin in data:
        exec(f"from {plugin[2]} import blueprint as blueprint")
        app.register_blueprint(blueprint, url_prefix=f"/plugin/private/{plugin[0]}")
    app.register_blueprint(admin,url_prefix="/")
    app.run("localhost",8080)
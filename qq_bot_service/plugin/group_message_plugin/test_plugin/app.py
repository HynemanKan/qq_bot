from flask import Blueprint
from flask import render_template
from db import mysqldb,mysqlconn,redisdb
from flask import render_template
import myAuth
blueprint = Blueprint("group_test",__name__,template_folder='templates', static_folder='static')

plugin_name = "group_test"

@blueprint.route('/')
@myAuth.cold_login_auth(redisdb)
def hello_world():
    return render_template("group_test_main.html",plugin_bname="在线测试")

def handle(context, bot,init_data):
    #print(context)
    if "test" == context["message"]:
        bot.send(context,"success")

def setup():
    return {"global": {"useless":42}}

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(blueprint,url_prefix="/")
    app.run()

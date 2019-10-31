from flask import Blueprint
from flask import render_template,request
import myAuth
from db import mysqldb,mysqlconn,redisdb
blueprint = Blueprint("private_test",__name__,template_folder='templates', static_folder='static')
re_str="test"
sample_active_word = "test"


@blueprint.route('/')
@myAuth.cold_login_auth(redisdb)
def hello_world():
    return render_template("private_test_main.html",plugin_bname="在线测试")


def handle(context, bot):
    bot.send(context, "success")
    return "finish", None


if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(blueprint,url_prefix="/")
    app.run()

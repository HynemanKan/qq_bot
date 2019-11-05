# 插件编写

## 私聊插件
任意一个私聊插件必须包含一个blueprint、sample_active_word、re_str和一个handle函数，
其中blueprint用于后台，
handle用于接收事件， 
re_str 用以正则事件匹配，
sample_active_word 用于会话保持。

```py
@blueprint.route('/')
@myAuth.cold_login_auth(redisdb)
def hello_world():
    return render_template("private_test_main.html")

def handle(context, bot):
    bot.send(context, "success")
    return "finish", None
```
### 私聊插件激活

在  private_message_plugin 中添加 相应字段，其中 active， 0为激活， 1为停用但显示，2为停用但不显示 

### 会话概念
在本服务中用户可以进行多次对话，初步实现上下文功能。

### blueprint

其中 myAuth.cold_login_auth(redisdb) 装饰器用于权限管理。

### handle函数
在 group_message_plugin 中添加 相应字段。
在 group_message_plugin_active 中与需要启用的群绑定。

所有handle 函数需传入 context , bot 参数

| 参数 | 类型 |
| --- | --- |
| context | cqhttp事件 |
| bot | bot对象 |

其中context在cqhttp事件原有值时怎加以下内容

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| signal | str | 用于事件匹配，在会话建立时 signal值与message值相等 |
| inherited | dict | 用于保存事件需要变量，在会话建立时，不存在 |

返回值 包含state和data，其中state为会话状态，data为会话传递给下一此请求的数据。其中 state包含以下数个状态。

| state | 说明 |
| ----- | --- |
| finish | 当前事件处理结束，当处理过程中无插件跳转时，会话结束，有跳转时，结束目前插件 |
| break | 强制中断当前会话 |
| continue | 等待用户输入，不结束会话 |
| redirect | 会话插件跳转，不结束会话 |

当状态为 finish, break 时， data 为 None
当状态为 contiune 时 data如下表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| inherited | dict | 保存的会话数据 |

当状态为 redirect 时 data 如下表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| inherited | dict | 当前会话保存的会话数据 |
| target_sample | str | 用以激活对应插件 |
| redirect_init | dict | 跳转插件的会话初始化数据 |


##群聊插件

任意一个群聊插件必须包含一个blueprint，一个setup函数和一个handle函数，
其中blueprint用于后台，
handle用于接收事件， 
setup 用于服务初始化

```py

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

```
### 群聊插件激活


### blueprint

与私聊聊插件一致。

### setup函数

用于初始化插件，如从数据库取出常用数据以减少数据库负担，该函数的返回值将作为init_data传入handle函数。

### handle函数
所有handle 函数需传入 context , bot , init_data 参数

| 参数 | 类型 |
| --- | --- |
| context | cqhttp事件 |
| bot | bot对象 |
| init_data | dict |


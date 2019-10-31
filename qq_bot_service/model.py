import re,json
import logging
from db import redisdb
def respond_private(privateMessageHandles,context,bot):
    key = str(context["sender"]["user_id"]) + "pm"
    exc_state = False
    while True:
        #预加载
        if redisdb.exists(key):#尝试加载缓存，恢复会话
            event_data = json.loads(redisdb.get(key))
            context["signal"] = event_data[0]["signal"]
            context["inherited"] = event_data[0]["inherited"]
        else:#全新会话
            event_data=[]
            context["signal"] = context["message"]
        #开始遍历
        #print(event_data)
        state = "finish"
        for plugin in privateMessageHandles:#遍历插件
            if re.search(plugin[0],context["signal"]):
                exc_state = True
                logging.info("event take by {}".format(plugin[0]))
                state,data = plugin[1](context,bot)
                #print(plugin)
                sample_active_word = plugin[2]
                break
        #状态检测
        if state == "finish":
            if len(event_data) <= 1:
                redisdb.delete(key)
                break#会话正常结束，缓存清除
            else:
                event_data.pop(0)
                redisdb.set(key,json.dumps(event_data))
                redisdb.expire(key,300)
                # 跳回到原先插件，缓存覆盖
        elif state == "break":
            redisdb.delete(key)
            bot.send(context,"该会话被一个服务强制中断")
            break#强制中断，缓存清除
        elif state == 'continue':
            if len(event_data) == 0:
                new_data = {"signal": sample_active_word,
                            "inherited": data["inherited"]}
                event_data.insert(0,new_data)
                redisdb.set(key, json.dumps(event_data))
                redisdb.expire(key, 300)
                break#等待用户应答，缓存覆盖
            else:
                event_data[0]["inherited"] = data["inherited"]
                redisdb.set(key, json.dumps(event_data))
                redisdb.expire(key, 300)
                break#等待用户应答，缓存覆盖
        elif state == 'redirect':
            if len(event_data) == 0:
                new_data = {"signal": sample_active_word,
                            "inherited": data["inherited"]}
                event_data.insert(0,new_data)
            else:
                event_data[0]["inherited"] = data["inherited"]
            new_data={"signal":data["target_sample"],
                     "inherited":data["redirect_init"]}
            event_data.insert(0,new_data)
            redisdb.set(key, json.dumps(event_data))
            redisdb.expire(key, 300)
            # 跳转到新插件，缓存覆盖
        else:
            redisdb.delete(key)
            bot.send("服务器发生内部错误，请稍后重试")
            break
        #print(event_data)
    return exc_state

def respond_group(groupMessageHandles,groupMessageHandle_init_data,context,bot):
    global_handles = groupMessageHandles["*"]
    for global_handle in global_handles:
        global_handle[1](context,bot,groupMessageHandle_init_data[global_handle[0]])
    gid = context["group_id"]
    if str(gid) in groupMessageHandles.keys():
        for grouphandle in groupMessageHandles[str(gid)]:
            grouphandle[1](context,bot,groupMessageHandle_init_data[grouphandle[0]])


#def respond_group_mumber_add(groupNumAddHandles, rules, context):
#   if str(context["group_id"]) in rules.keys():
#        rule = groupNumAddHandles[str(context["group_id"])]
#        res = []
#        info_all = "系统自动拒绝了您的申请，可能是应为以下原因：\n"
#        for key in rule["handles"]:
#            state,info = groupNumAddHandles[key](context)
#            res.append(state)
#            info_all+=info
#            info_all+="\n"
#        try:
#            state = exec(rule["rule"])
#            if state:
#                return 1,""
#            else:
#                return -1,info_all
#        except Exception as e:
#            return 0,""
#    else:
#        return 0,""

import uuid
from db import mysqlconn,mysqldb
white_list=[2062433139,2909288299]


def handle(context, bot):
    message = context["message"]
    qid = context["sender"]["user_id"]
    if not(qid in white_list):
        message_id = str(uuid.uuid4())
        sql = "INSERT INTO message(message_id, sender, send_time, detail, res)values (%s,%s,NOW(),%s,'none')"
        mysqldb.execute(sql,(message_id,qid,message))
        mysqlconn.commit()

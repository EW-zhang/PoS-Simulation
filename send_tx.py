#  编一个程序，让随机内容每隔xxs秒就直接发送随机数据给所有节点
import requests
import time
import random

second = 1  # 设置发送交易的间隔时间

while True:
    random_data = "0x{}".format('%d' % (random.random() * pow(10, 17)))
    time.sleep(second)
    for i in range(12):  # 几个节点设置几次循环
        requests.post('http://127.0.0.1:{}/new_transaction'.format(8000+i), json={"hex_data": random_data})
        print('{} just received a txn'.format(8000+i))

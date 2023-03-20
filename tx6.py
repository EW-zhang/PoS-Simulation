import requests
import random
import time

random_validators = [8000, 8003, 8004, 8007, 8009, 8010]

while True:
    random_data = "0x{}".format('%d' % (random.random() * pow(10, 17)))
    time.sleep(1)
    for validator in random_validators:  # 几个节点设置几次循环
        requests.post('http://127.0.0.1:{}/new_transaction'.format(validator), json={"hex_data": random_data})
        print('{} just received a txn'.format(validator))


import requests
peers = set()
for i in range(12):   # 几个节点设置几次循环
    peers.add("http://127.0.0.1:{}".format(8000+i))
for j in peers:
    for k in peers:
        requests.post('{}/register_node'.format(j), json={"node_address": "{}".format(k)})

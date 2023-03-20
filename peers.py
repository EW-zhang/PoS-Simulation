import requests
peers = set()
peers.add("http://127.0.0.1:8000")
peers.add("http://127.0.0.1:8003")
peers.add("http://127.0.0.1:8004")
peers.add("http://127.0.0.1:8007")
peers.add("http://127.0.0.1:8009")
peers.add("http://127.0.0.1:8010")

for j in peers:
    for k in peers:
        requests.post('{}/register_node'.format(j), json={"node_address": "{}".format(k)})

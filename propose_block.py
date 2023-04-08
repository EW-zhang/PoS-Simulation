import requests
import random
import time

while True:
    # 先只运行区块提议者，不运行验证者委员会
    random_numbers = random.sample(range(12), 5) #为了模拟真实通信情况
    random_validators = [num + 8000 for num in random_numbers]

    proposer = random_validators[0]  # 区块提议者

    committee_ports = random_validators[1:]  # 验证者委员会

    print(proposer)
    print(committee_ports)
    requests.post('http://127.0.0.1:{}/get_ports'.format(proposer), json={"ports": (proposer, committee_ports)})
    for committee_port in committee_ports:
        requests.post('http://127.0.0.1:{}/get_ports'.format(committee_port), json={"ports": (proposer, committee_ports)})
    t1 = time.time()
    requests.get('http://127.0.0.1:{}/mine'.format(proposer))
    t2 = time.time()
    print(t2 - t1)
    time.sleep(1)

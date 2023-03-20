import requests
import time

proposer_index = 0
random_validators = [8000, 8003, 8004, 8007, 8009, 8010]

while True:
    proposer = random_validators[proposer_index]
    committee_ports = random_validators[:proposer_index] + random_validators[proposer_index+1:]

    print(proposer)
    print(committee_ports)

    requests.post('http://127.0.0.1:{}/get_ports'.format(proposer), json={"ports": (proposer, committee_ports)})

    for committee_port in committee_ports:
        requests.post('http://127.0.0.1:{}/get_ports'.format(committee_port),
                      json={"ports": (proposer, committee_ports)})

    requests.get('http://127.0.0.1:{}/mine'.format(proposer))

    time.sleep(1)

    proposer_index = (proposer_index + 1) % len(random_validators)

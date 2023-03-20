from hashlib import sha3_256
import json
import time

from flask import Flask, request
import requests
import numpy as np


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash,
                 nonce=0, mining_port="127.0.0.1:8000/", block_time=1):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.mining_port = mining_port
        self.block_time = block_time

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha3_256(block_string.encode()).hexdigest()


class Blockchain:

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.txs_packaged_in_this_block = []
        self.existing_hex_data = []
        self.committee_ports = []
        self.proposer_port = 0

    def create_genesis_block(self):  # 改：从创世区块开始算nonce，使之符合挖矿难度
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        print("add_block中的block", block.__dict__)
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            print("False1_in_add_block")
            return False

        if not Blockchain.is_valid_proof(block, proof):
            print("False2_in_add_block")
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        return block_hash == block.compute_hash()

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block_hash):
                print("check_chain_validity_False1")
                result = False
                break

            if previous_hash != block.previous_hash:
                print("check_chain_validity_False2")
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        block_storage = 4
        # 在这里更新一下unconfirmed_transactions，把其变为没被其他节点打包过的存在
        # 首先获取任意一节点的链上数据（因为数据已经同步完成，哪个节点都行）
        response = requests.get('http://127.0.0.1:8000/chain')
        chain1 = response.json()['chain']
        for i in range(len(chain1)):
            #  print("第", i, "个块的transactions数据", chain1[i]['transactions'])
            for j in range(len(chain1[i]['transactions'])):
                #  print("第", i, "个块的第", j, "个交易的hex_data数据", chain1[i]['transactions'][j]['hex_data'])
                self.existing_hex_data.append(chain1[i]['transactions'][j]['hex_data'])
        # print("hex_data集合", self.existing_hex_data)
        # 再获取unconfirmed_transactions的时间戳数据，如果有一样的，删除就行
        drop_list = []
        for k in range(len(self.unconfirmed_transactions)):
            #  print("未确认的交易的hex", self.unconfirmed_transactions[k]['hex_data'])
            if self.unconfirmed_transactions[k]['hex_data'] in self.existing_hex_data:
                drop_list.append(k)
        print("drop_list", drop_list)
        self.unconfirmed_transactions = np.delete(self.unconfirmed_transactions, drop_list).tolist()
        #  print("经过drop后的unconfirmed_transactions", self.unconfirmed_transactions)
        if len(self.unconfirmed_transactions) == 0:  # 空的就不要挖了
            print("no transactions to mine ")
            return False

        # 区块容量约束，得到这次能打包的交易，更新总共的未确认交易
        if len(self.unconfirmed_transactions) > block_storage:
            for i in range(block_storage):
                self.txs_packaged_in_this_block.append(self.unconfirmed_transactions[i])
            del self.unconfirmed_transactions[0: block_storage]
        else:  # 修
            self.txs_packaged_in_this_block = self.unconfirmed_transactions
            self.unconfirmed_transactions = []
        print("txs_packaged_in_this_block", self.txs_packaged_in_this_block)
        print("unconfirmed_transactions", self.unconfirmed_transactions)

        last_block = self.last_block

        # 出新块
        new_block = Block(index=last_block.index + 1,
                          transactions=self.txs_packaged_in_this_block,
                          timestamp=time.time(),
                          previous_hash=last_block.hash,
                          nonce=last_block.nonce + 1,
                          mining_port=request.host_url,
                          block_time=1)
        proof = new_block.compute_hash()
        added = self.add_block(new_block, proof)
        self.txs_packaged_in_this_block = []  # 修，清空数值
        if not added:
            return False

        return True


app = Flask(__name__)

blockchain = Blockchain()
blockchain.create_genesis_block()


peers = set()


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["hex_data"]  # 修，只需要得到交易的hex input data即可

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    if len(blockchain.unconfirmed_transactions) == 0:
        print("No transactions to mine")
        return "No transactions to mine"

    else:
        chain_length = len(blockchain.chain)
        print("chain_length", chain_length)
        consensus()
        print("共识后的chain_length", chain_length)
        print("共识后的len(blockchain.chain)", len(blockchain.chain))
        add_success = blockchain.mine()
        if add_success:
            # 先广播给验证者委员会
            # committee_ports会在mine之前发送数据进来
            validity = check_committee_ports(blockchain.committee_ports)
            print("validity", validity)
            if validity:
                announce_new_block(blockchain.last_block)
        return "Blockchain has been synchronized ".format(blockchain.last_block.index)


@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    peers.add(node_address)

    return get_chain()


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"],
                  block_data["mining_port"],
                  block_data["block_time"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


def consensus():
    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)
    print("共识中的current_len", current_len)

    for node in peers:
        response = requests.get('{}/chain'.format(node))  # 修，少个/
        length = response.json()['length']
        print("11--", length)
        chain0 = response.json()['chain']
        chain = []
        for block in chain0:   # 修，更改赋值方式，保证类型一致
            block0 = Block(block["index"],
                           block["transactions"],
                           block["timestamp"],
                           block["previous_hash"],
                           block["nonce"],
                           block["mining_port"],
                           block["block_time"])
            block0.hash = block["hash"]
            chain.append(block0)
        if length > current_len and blockchain.check_chain_validity(chain):
            print("length > current_len")  # 短链先挖出矿
            print("length=", length)
            print("current_len=", current_len)
            if True:
                current_len = length
                longest_chain = chain

    if longest_chain:
        blockchain.chain = longest_chain
        print("赋值成功")
        return True

    return False


def announce_new_block(block):
    print("广播交易", time.time())
    for peer in peers:
        url = "{}/add_block".format(peer)  # 修，少个/
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True),
                      headers=headers)


def check_committee_ports(ports):
    num_true_responses = 0
    threshold = len(ports) * 2 / 3  # 阈值为总端口数的2/3
    for port in ports:
        print("进入循环check", port)
        response = requests.get(f'http://127.0.0.1:{port}/committee_check')
        print(response.text.strip())
        if response.text.strip().lower() == 'true':
            num_true_responses += 1
            if num_true_responses >= threshold:
                return True
    print("check_chain_validity的返回值", False)
    return False


# 在propose_block中调用，事先发送验证ports
@app.route('/get_ports', methods=['POST'])
def get_committee_ports():
    data = request.get_json()
    blockchain.proposer_port = data['ports'][0]
    blockchain.committee_ports = data['ports'][1]
    print("proposer_port", blockchain.proposer_port)
    print("committee_ports", blockchain.committee_ports)
    return "Success", 201


# 验证委员会进行验证
@app.route('/committee_check', methods=['GET'])
def check_validity():
    print("blockchain.proposer_port", blockchain.proposer_port)
    response = requests.get('http://127.0.0.1:{}/chain'.format(blockchain.proposer_port))
    data = response.json()['chain']
    chain = []
    for block in data:
        block0 = Block(block["index"],
                       block["transactions"],
                       block["timestamp"],
                       block["previous_hash"],
                       block["nonce"],
                       block["mining_port"],
                       block["block_time"])
        block0.hash = block["hash"]
        chain.append(block0)
    print("获取新链", chain)
    return str(blockchain.check_chain_validity(chain))

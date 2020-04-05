#importing libs

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse 
 
# 1. building blockchain
# -- adding transactions and building concensus

class Blockchain:
     
    def __init__(self):
        self.chain = []
        self.transactions = [] # contains transactions before they are added to a block.
        self.create_block(proof = 1, previous_hash = '0')
        # contain all nodes in network (here it means all ports)
        self.nodes = set()
    
    def create_block(self, proof, previous_hash):
        block = {'index' : len(self.chain)+1,
                 'timestamp' : str(datetime.datetime.now()),
                 'proof' : proof,
                 'previous_hash' : previous_hash,
                 'transactions' : self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    # problem that miners need to solve
    # the more leading zeros , the more difficult is to solve the problem as target range decreases.
    # operation must be non symmetrical to avoid repeat eg.new-old because new-old!=old-new
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            # .encode( adds 'b' in front) .hexdigest() to get hexa digits
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    # fn to check 1.each block has correct proof_of_work 
                # 2. previous_hash of each block is equal to hash of previous block
    def hash(self, block):
        # dumps used to make our dictionary into string
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        block_index = 1
        previous_block = chain[0]
        
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index+=1
        
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
                'sender' : sender,
                'receiver' : receiver,
                'amount' : amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address) #gets the port and other data
        self.nodes.add(parsed_url.netloc)
    
    #concensus method || to make chain at all nodes same
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
                
# 2. Mining a web app
        
# creating a web app
app = Flask(__name__)
 
# creating address for node on port 5000
node_address = str(uuid4()).replace('-','')

# creating a blockchain
blockchain = Blockchain()  

# mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'Yashwant', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# getting the full blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods= {'GET'})
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'blockchain is valid'}
    else:
        response = {'message' : 'blockchain is invalid'}
    return jsonify(response), 200

# adding a new transaction to blockchain

@app.route('/add_tranction', methods= {'POST'})
def add_transaction():
    json = request.get_json()
    transaction_keys = {'sender', 'receiver', 'amount'}
    if not all (key in json for key in transaction_keys):
        return 'some elements of transaction are missing', 400
    index = blockchain.add_transactions(json['sender'], json['receiver'], json['amount'])
    response ={'message' : f'this transaction will be added to block {index}'}
    return jsonify(response), 201

# 3. Decentralizing blockchain

# connecting new nodes
@app.route('/connect_node', methods = {'POST'})
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : 'All nodes are now connected : Yashcoin contains following nodes now ',
                'total_nodes' : list(blockchain.nodes)}
    return jsonify(response), 201

# replacing chain by longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'different chains found, chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# running the app
app.run(host = '0.0.0.0', port = 5001)










    
    
    
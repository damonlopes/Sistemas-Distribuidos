from flask import Flask, request, jsonify
from flask_sse import sse
from datetime import datetime
import threading

app = Flask(__name__)
app.config['REDIS_URL'] = 'redis://localhost'
app.register_blueprint(sse, url_prefix = '/stream')

USERS = {}
AUCTIONS = {}

def message_response(status_request, message_request):
    return jsonify(
        status = status_request,
        message = message_request
    )

def notify_auction():
    with app.app_context():
        while(True):
            if list(AUCTIONS.keys()):
                for auction in list(AUCTIONS):
                    if AUCTIONS[auction]["state"] == "Em andamento":
                        users_auction = AUCTIONS[auction]["users_auction"]
                        names = []
                        for user in USERS:
                            names.append(USERS[user]["name"])
                        names.sort()
                        users_auction.sort()

                        if datetime.now() >= datetime.strptime(AUCTIONS[auction]["deadline"], "%Y-%m-%d %H:%M:%S"):
                            message = f"""
            Leilão encerrado!
        Código do Produto: {AUCTIONS[auction]["name"]}
        Vencedor: {AUCTIONS[auction]["ownerBid"]}
        Valor: R${AUCTIONS[auction]["actualBid"]}
            Parabéns!
                            """
                            for name in users_auction:
                                sse.publish(message, type = name)
                            AUCTIONS[auction]["state"] = "Encerrado"
                        else:
                            pass
                    else:
                        pass
            else:
                pass

@app.route('/users/new', methods = ['POST'])
def new_user():
    data_user = request.get_json()

    if not data_user["name"]:
        return message_response(False, 'Está faltando informação para cadastro')
    if data_user["name"] in USERS:
        return message_response(False, 'Usuário já cadastrado')
    
    USERS[data_user["name"]] = dict(
        name = data_user["name"]
    )

    return message_response(True, f'Usuário {data_user["name"]} cadastrado com sucesso!')

@app.route('/users/list', methods = ['GET'])
def get_users():
    return jsonify(list(USERS.keys()))

@app.route('/auctions/new', methods = ['POST'])
def new_auction():
    data_auction = request.get_json()
    productName = data_auction["name"]
    productOwner = data_auction["creator"]
    description = data_auction["description"]
    actualBid = data_auction["actualBid"]
    deadline = data_auction["deadline"]
    if not(productName and productOwner and description and actualBid and deadline):
        return message_response(False, 'Está faltando informação para cadastro!')
    
    if productName in AUCTIONS:
        return message_response(False, 'Produto com esse nome já cadastrado')
    
    users_auction = []
    users_auction.append(productOwner)
    AUCTIONS[productName] = dict(
        name = productName,
        creator = productOwner,
        description = description,
        actualBid = actualBid,
        ownerBid = None,
        deadline = deadline,
        users_auction = users_auction,
        state = "Em andamento"
    )

    sse.publish(
        f"""
            Novo produto cadastrado!
        Nome do Produto: {productName}
        Dono do Produto: {productOwner}
        Descrição: {description}
        Lance Inicial: {actualBid}
        Fim do leilão: {deadline}
        """,
        type = 'created'
    )

    return message_response(True, f'Produto {productName} com sucesso!')

@app.route('/auctions/list', methods = ['GET'])
def get_auctions():
    all = request.args.get('all')
    if all == 'True':
        return jsonify(list(AUCTIONS.keys()))
    
    list_auctions = []
    for auction in AUCTIONS:
        if AUCTIONS[auction]['state'] == "Em andamento":
            list_auctions.append(auction)
    return jsonify(list_auctions)

@app.route('/auctions/list/active', methods = ['GET'])
def get_active_auctions():
    # list_auctions = []
    message_auctions = ''
    for auction in AUCTIONS:
        if AUCTIONS[auction]["state"] == "Em andamento":
            # list_auctions.append(auction["name"])
            message_auctions += f"""
        Nome do Produto: {AUCTIONS[auction]["name"]}
        Descrição: {AUCTIONS[auction]["description"]}
        Lance atual: {AUCTIONS[auction]["actualBid"]}
        Dono do lance: {AUCTIONS[auction]["ownerBid"]}
        Fim do leilão: {AUCTIONS[auction]["deadline"]}
                """
    return message_response(True, message_auctions)

@app.route('/auctions/bid', methods = ['POST'])
def bid_auction():
    data_bid = request.get_json()
    if not (data_bid["name"] and data_bid["ownerBid"] and data_bid["bid"]):
        return message_response(False , 'Está faltando informação para computar o lance')
    
    if data_bid["ownerBid"] == AUCTIONS[data_bid["name"]]["creator"]:
        return message_response(False, 'Você é o dono deste produto')
    
    if AUCTIONS[data_bid["name"]]["state"] != 'Em andamento':
        return message_response(False, 'Já acabou o prazo')
    
    if data_bid["ownerBid"] == AUCTIONS[data_bid["name"]]["ownerBid"]:
        return message_response(False, 'Você está ganhando o leilão com o maior lance')
    
    if data_bid["bid"] <= AUCTIONS[data_bid["name"]]["actualBid"]:
        return message_response(False, 'O lance é menor ou equivalente ao atual')
    
    if data_bid["ownerBid"] not in AUCTIONS[data_bid["name"]]["users_auction"]:
        AUCTIONS[data_bid["name"]]["users_auction"].append(data_bid["ownerBid"])


    AUCTIONS[data_bid["name"]]["actualBid"] = data_bid["bid"]
    AUCTIONS[data_bid["name"]]["ownerBid"] = data_bid["ownerBid"]

    for user in AUCTIONS[data_bid["name"]]["users_auction"]:
        sse.publish(f'Valor do produto {AUCTIONS[data_bid["name"]]["name"]} atualizado!', type = user)

    return message_response(True, 'Lance computado com sucesso')

@app.route('/')
def hello_world():
    return 'Hello world!'

if __name__ == '__main__':
    thread_auctions = threading.Thread(target = notify_auction, daemon = True)
    thread_auctions.start()
    app.run()
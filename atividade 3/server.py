import Pyro4
import base64
import threading
from datetime import datetime

import cryptography.exceptions
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes

@Pyro4.behavior(instance_mode='single')

class Auction(object):

    def __init__(self):

        self.users = {}
        self.auctions = {}

        self.thread_auctions = threading.Thread(target = self.notifyAuction, daemon = True)
        self.thread_auctions.start()

    @Pyro4.expose
    def registerUser(self, userName, publicKey, callback):
        if not (userName and publicKey):
            raise ValueError('Erro: Tá faltando alguma informação ai!')
        
        if userName == '':
            raise ValueError('Erro: Faltou o nome do usuário!')

        if userName in self.users:
            raise ValueError('Erro: Usuário já cadastrado!')
        
        print(f'Registrando novo usuário {userName}')
        self.users[userName] = (userName, publicKey, callback)
        
        return userName

    @Pyro4.expose
    def registerAuction(self, userName, productCode, productName, description, actualBid, deadline):
        if not(userName and productCode and productName and description and actualBid and deadline):
            raise ValueError('Erro: Tá faltando informação')
        if productCode in self.auctions:
            raise ValueError(f'Erro: Produto com código {productCode} já cadastrado!')
        # if productCode not in self.auctions:
        print(f'Creating new auction {productCode}-{productName}')
        ownerBid = None
        users = []
        users.append(userName)
        self.auctions[productCode] = [productCode, productName, userName, description, actualBid, ownerBid, deadline, users, "Em andamento"]
        print(f'Produto {productCode} cadastrado. Enviando as notificações...')
        message = f"""
            Novo produto cadastrado!
        Código do Produto: {productCode}
        Nome do Produto: {productName}
        Dono do Produto: {userName}
        Descrição: {description}
        Lance Inicial: {actualBid}
        Fim do leilão: {deadline}
        """
        for user in self.users:
            self.publish(user, message)
        print('Notificações enviadas')
        return productCode
        
    def getAuctions(self, all):
        if all == True:
            return list(self.auctions.keys())
        else:
            listAuctions = []
            for product in self.auctions:
                pc, pn, u, d, ab, ob, dl, users, state = self.auctions[product]
                if state == 'Em andamento':
                    listAuctions.append(product)
            return listAuctions

    @Pyro4.expose
    def getActiveAuctions(self):
        list_products = []
        message_products = ''
        for product in self.auctions:
            pc, pn, u, d, ab, ob, dl, users, state = self.auctions[product]

            if state == 'Em andamento':
                list_products.append(pc)
                message_products += f"""
        Código do Produto: {pc}
        Nome do Produto: {pn}
        Descrição: {d}
        Lance atual: {ab}
        Dono do lance: {ob}
        Fim do leilão: {dl}
                """
        return list_products, message_products
        
    def notifyAuction(self):
        while True:
            list_auctions = self.getAuctions(True)
            if list_auctions:
                for auction in list_auctions:
                    pc, pn, u, d, ab, ob, dl, users, state = self.auctions[auction]
                    if state == "Em andamento":
                        names = []
                        for user in users:
                            n, pk, c = self.users[user]
                            names.append(n)
                        if(datetime.now() >= datetime.strptime(dl, "%Y-%m-%d %H:%M:%S")):
                            message = f"""
            Leilão encerrado!
        Código do Produto: {pc}
        Vencedor: {ob}
        Valor: R${ab}
            Parabéns!
                            """
                            for name in names:
                                self.publish(name, message)
                            self.auctions[auction][8] = 'Encerrado'
                    else:
                        pass
            else:
                pass

    @Pyro4.expose
    def bidAuction(self, productCode, userName, bid, signature):
        publicKeyStr = self.users[userName][1]
        pubk = serialization.load_pem_public_key(publicKeyStr.encode(), default_backend())
        if self.verifySignature(pubk, base64.b64decode(signature['data'])):
            if not(productCode and userName and bid):
                raise ValueError('Erro: Está faltando algum valor!')
            pc, pn, u, d, ab, ob, dl, users, state = self.auctions[productCode]
            if userName == u:
                raise PermissionError('Erro: Você é o dono do produto. Não pode fazer uma oferta!')
            if state != 'Em andamento':
                raise PermissionError('Erro: Já acabou o prazo!')
            if userName == ob:
                raise PermissionError('Erro: Você está ganhando o leilão com o maior lance!')
            if bid <= ab:
                raise ValueError('Erro: O lance é menor ou equivalente ao atual. Tente um valor maior')
            if userName not in users:
                users.append(userName)
            self.auctions[productCode][4] = bid
            self.auctions[productCode][5] = userName
            self.auctions[productCode][7] = users
            for user in users:
                self.publish(user, f'Valor do produto {productCode} atualizado!')
        else:
            return "Acesso negado!"

    def verifySignature(self, publicKey, signature):
        message = b"Eu sou este usuario"
        try:
            publicKey.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except cryptography.exceptions.InvalidSignature as e:
            return False
        
    def publish(self, userName, message):
        name, publicKey, callback = self.users[userName]
        try:
            callback.message(message)
        except:
            pass


Pyro4.Daemon.serveSimple({
    Auction: "auction.server"
})


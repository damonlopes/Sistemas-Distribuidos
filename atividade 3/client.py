import Pyro4
import sys
import threading
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

def menu(option):
    match option:
        case 0:
            print("""
        Obrigado por usar o sistema de leilão! Até mais...
            """)
        case 1:
            print("""
        Selecione uma opção:

        1 - Criar um usuário.
        2 - Sair
            """)
        case 2:
            print("""
        Bem vindo! Selecione uma opção:

        1 - Cadastrar um produto
        2 - Dar um lance em um produto
        3 - Obter informações dos produtos ativos
        4 - Sair
            """)
        case 3:
            print("""
        -> Cadastrar um produto

            Modelo de cadastro:
        - Código do produto: string
        - Nome do produto: string
        - Descrição: string
        - Valor inicial: float (10000.00)
        - Data de término: datetime (YYYY-mm-dd HH:MM:SS)
            """)
        case 4:
            print("""
        -> Dar um lance em um produto

        Lista de códigos de produtos ativos:
            """)
        case 5:
            print("""
        -> Obter informações dos produtos ativos

        Lista de todos os produtos ativos:
            """)

class Client(object):

    def __init__(self):

        self.auctionServer = Pyro4.Proxy('PYRONAME:auction.server')
        self.abort = 0

    @Pyro4.expose
    @Pyro4.oneway
    def message(self, message):
        print(message)

    def sign(self):
        message = b"Eu sou este usuario"
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def createPublicKey(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        self.pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.pem = self.pem.decode()

    def start(self):
        self.forbidden = ['', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.createPublicKey()
        while True:
            menu(1)
            match input('>: ').strip():
                case '1':
                    while True:
                        try:
                            print("Insira o nome do usuário")
                            userName = input(':> ').strip()
                            self.name = userName
                            self.auctionServer.registerUser(self.name, self.pem, self)
                            break
                        except ValueError as ve:
                            print(ve)
                    break
                case '2':
                    menu(0)
                    sys.exit()
            
        while True:
            menu(2)
            choice = input('>: ').strip()
            match choice:
                case '1':
                    while True:
                        try:
                            menu(3)
                            while True:
                                try:
                                    productCode = input('Código do produto: ').strip()
                                    forbidden = self.forbidden + ['0']
                                    if productCode in forbidden:
                                        raise ValueError('Código inválido')
                                    break
                                except ValueError as ve:
                                    print(ve)
                            productName = input('Nome do produto: ').strip()
                            description = input('Descrição: ').strip()
                            while True:
                                try:
                                    initialBid = float(input('Valor inicial: ').strip())
                                    break
                                except ValueError:
                                    print('Insira um valor válido!')
                            actualBid = round(initialBid, 2)
                            while True:
                                try:
                                    deadline = input('Data de término: ').strip()
                                    verify_deadline = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
                                    if datetime.now() >= verify_deadline:
                                        raise TypeError('Insira uma data maior do que a atual.')
                                    break
                                except ValueError:
                                    print('Insira uma data no formato válido (YYYY-mm-dd HH:MM:SS)!')
                                except TypeError as te:
                                    print(te)
                            product = self.auctionServer.registerAuction(self.name, productCode, productName, description, actualBid, deadline)
                            print(product)
                            break
                        except e:
                            print(e)

                case '2':
                    menu(4)
                    products, message = self.auctionServer.getActiveAuctions()
                    if products:
                        while True:
                            print(products)
                            product = input('Em qual dos produtos deseja ofertar (insira o Código do Produto, caso queira sair digite 0): ').strip()
                            if product in products or product == '0':
                                break
                            else:
                                print('Erro: Código inválido')
                            
                        while True:
                            if product == '0':
                                break
                            try:
                                bid = float(input('Digite o valor que deseja ofertar: ').strip())
                                self.auctionServer.bidAuction(product, self.name, bid, self.sign())
                                break
                            except TypeError:
                                print('Erro: Insira um valor válido!')
                            except ValueError as e:
                                print(e)
                            except PermissionError as e:
                                print(e)
                                break
                    else:
                        print('Não tem produtos ativos!')

                case '3':
                    menu(5)
                    products, message = self.auctionServer.getActiveAuctions()
                    if products:
                        print(message)
                    else:
                        print('Não tem produtos ativos!')

                case '4':
                    menu(0)
                    sys.exit()
                        
class DaemonThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        self.setDaemon(True)

    def run(self):
        with Pyro4.core.Daemon() as daemon:
            daemon.register(self.client)
            daemon.requestLoop(lambda: not self.client.abort)


client = Client()
daemonThread = DaemonThread(client)
daemonThread.start()
client.start()


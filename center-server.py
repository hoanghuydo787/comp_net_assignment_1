# sample code
from socket import *
import threading
import pickle
import json
import time



class Server:
    REQUEST_CONNECTION = 'REQUEST_CONNECTION'
    REJECT_CONNECTION = 'REJECT_CONNECTION'
    ACCEPT_CONNECTION = 'ACCEPT_CONNECTION'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    SIGNUP = 'SIGNUP'
    RETRIEVE_LIST_FRIEND =  'RETRIEVE LIST FRIEND'

    MAX_NUM_CLIENTS = 3

    """{<username>: {'password' :<password>,
                   'list_friends': [<username_friend1>,<username_friend2>,...]},
        ......
        }
    """
    """database = {'win':  {'password' :'123',
                   'list_friends': ['hana']},
                 'hana': {'password': '456',
                          'list_friends': ['win']}
        }
    """
    user_logins = {}
    clients_list = []
    last_received_message = ""

    def __init__(self):
        self.server_socket = None
        with open('database.json', 'r') as openfile:
            self.database = json.load(openfile)
        self.create_listening_server()
    #listen for incoming connection

    def create_listening_server(self):
        self.server_socket = socket(AF_INET, SOCK_STREAM) #create a socket using TCP port and ipv4
        server_host = '127.0.0.1'
        server_port = 12000
        # this will allow you to immediately restart a TCP server
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # this makes the server listen to requests coming from other computers on the network
        self.server_socket.bind((server_host, server_port))
        print("the server is ready to receive..")
        self.server_socket.listen(self.MAX_NUM_CLIENTS) #listen for incomming connections / max 5 clients
        self.receive_messages_in_a_new_thread()

    def isOnline(self,username):
        try:
            return self.user_status[username]['status'] == 'online'
        except:
            raise f"{username} chưa được lưu trữ"

    def processRequest(self,request):
        token = request.split('|')
        return token[0],token[1:]

    def username(self,ip,port):
        for name in self.user_logins:
            if self.user_logins[name][1] == (ip,int(port)):
                return name
        return None

    def lookup(self,ip,port):
        for client in self.clients_list:
            if client[1] == (ip,int(port)):
                return client
        return None

    def requestConnection(self,client,dest_ip,dest_port):
        so,_ = self.lookup(dest_ip,dest_port)
        msg = self.REQUEST_CONNECTION + f'|{client[1][0]},{client[1][1]}'
        self.sendMessage(so,msg)

    def rejectConnection(self,client,dest_ip,dest_port):
        so,_ = self.lookup(dest_ip, dest_port)
        msg = self.REJECT_CONNECTION + f'|{client[1][0]},{client[1][1]}'
        self.sendMessage(so,msg)

    def acceptConnection(self,client,dest_ip,dest_port):
        so,_ = self.lookup(dest_ip, dest_port)
        msg = self.ACCEPT_CONNECTION + f'|{client[1][0]},{client[1][1]}'
        self.sendMessage(so,msg)

    def sendListFriend(self,username):
        list_friends = []
        for name in self.database[username]['list_friends']:
            ip = port = None
            status = 'offline'
            if name in self.user_logins:
                ip,port = self.user_logins[name][1]
                status = 'online'
            list_friends.append([name,ip,port,status])
        so = self.user_logins[username][0]
        frlist = pickle.dumps(list_friends)
        so.sendall(frlist)

    def signup(self,conn):
        username = conn.recv(1024).decode()
        password = conn.recv(1024).decode()
        if username not in self.database:
            self.database[username] = {'password':password,'list_friends':[]}
            self.sendMessage(conn,'Success')
            with open("database.json", "w") as outfile:
                json.dump(self.database, outfile)
            return True
        else:
            self.sendMessage(conn,'Fail')
            return False


    def login(self, client):
        conn, _ = client
        username = conn.recv(1024).decode()
        password = conn.recv(1024).decode()
        if  self.authenticate(username,password):
            self.user_logins[username] = client
            self.sendMessage(conn,'Success')
            time.sleep(0.1)
            self.sendListFriend(username)
            return True
        else:
            self.sendMessage(conn,'Fail')
            return False

    def authenticate(self, username, password):
        return username in self.database and self.database[username]['password'] == password

    def sendMessage(self,conn,msg):
        conn.sendall(msg.encode())

    def disconnectClient(self,client):
        self.clients_list.remove(client)
        ip, port = client[1]
        username = self.username(ip,port)
        if username:
            self.user_logins.pop(username)

        print(f'Disconnect to ', ip, ':', str(port))
        client[0].close()

    def clientThread(self,client):
        so, _ = client
        # login/signup
        while True:
            """try:
                rqst = so.recv(256) #initialize the buffer
            except:
                self.disconnectClient(client)
                return"""
            rqst = so.recv(256)
            rqst = rqst.decode()
            if  rqst == self.LOGIN:
                if self.login(client): break
            elif rqst == self.SIGNUP:
                self.signup(so)

        #username = self.username(*client[1])
        """while True:
            try:
                incoming_buffer = so.recv(256) #initialize the buffer
            except:
                self.disconnectClient(client)
                return
            request = incoming_buffer.decode('utf-8')
            rqst, args = self.processRequest(request)
            if rqst == self.REQUEST_CONNECTION:
                dest_ip,des_port = args
                self.requestConnection(client,dest_ip,des_port)
            elif rqst == self.REJECT_CONNECTION:
                est_ip, des_port = args
                self.rejectConnection(client,dest_ip,des_port)
            elif rqst == self.ACCEPT_CONNECTION:
                est_ip, des_port = args
                self.acceptConnection(client,dest_ip,des_port)
            elif rqst == self.RETRIEVE_LIST_FRIEND:
                self.sendListFriend(username)
            else:
                pass
            """

    #broadcast the message to all clients
    def broadcast_to_all_clients(self, senders_socket):
        for client in self.clients_list:
            socket, (ip, port) = client
            if socket is not senders_socket:
                socket.sendall(self.last_received_message.encode('utf-8'))

    def receive_messages_in_a_new_thread(self):
        while True:
            if len(self.clients_list) == self.MAX_NUM_CLIENTS:
                continue
            client = so, (ip, port) = self.server_socket.accept()
            self.add_to_clients_list(client)
            print('Connected to ', ip, ':', str(port))
            t = threading.Thread(target=self.clientThread, args=(client,))
            t.start()

    #add a new client
    def add_to_clients_list(self, client):
        if client not in self.clients_list:
            self.clients_list.append(client)

        for client in self.clients_list:
            print(client[1][1],' ')
        print()


if __name__ == "__main__":
    Server()



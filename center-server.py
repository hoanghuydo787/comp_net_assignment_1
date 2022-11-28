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
    FRIENDS_LIST = 'FRIENDS_LIST'

    MAX_NUM_CLIENTS = 10

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
        # server_host = gethostbyname(gethostname())
        server_host = "127.0.0.1"
        server_port = 12000
        # this will allow you to immediately restart a TCP server
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # this makes the server listen to requests coming from other computers on the network
        self.server_socket.bind((server_host, server_port))
        print("the server is ready to receive..")
        self.server_socket.listen(self.MAX_NUM_CLIENTS) #listen for incomming connections / max 5 clients
        self.receive_messages_in_a_new_thread()

    def processRequest(self,request):
        token = request.split('|')
        return token[0],token[1:]

    def username(self,ip,port):
        for name in self.user_logins:
            if self.user_logins[name][1] == (ip,int(port)):
                return name
        return None

    def lookup(self, ip, port):
        for name in self.user_logins:
            if self.user_logins[name][1] == (ip, int(port)):
                return name
        return None

    def requestConnection(self,src_username,des_username,src_ip,src_port):
        conn = self.user_logins[des_username][0]
        msg = (self.REQUEST_CONNECTION, (src_username,src_ip,src_port))
        self.sendMessage(conn, msg)

    # def rejectConnection(self, ):
    #     conn = self.user_logins[des][0]
    #     msg = (self.REJECT_CONNECTION, (src,))
    #     self.sendMessage(conn, msg)
    #
    # def acceptConnection(self, src, des):
    #     conn = self.user_logins[des][0]
    #     msg = (self.ACCEPT_CONNECTION, (src,))
    #     self.sendMessage(conn, msg)

    def updateStatus(self,username):
        friends_list = self.database[username]['list_friends']
        for friend in friends_list:
            if self.isOnline(friend):
                self.sendListFriend(friend)

    def isOnline(self,username):
        return username in self.user_logins

    def sendListFriend(self,username):
        list_friends = {}
        for name in self.database[username]['list_friends']:
            ip = port = None
            status = 'OFFLINE'
            if self.isOnline(name):
                ip,port = self.user_logins[name][1]
                status = 'ONLINE'
            list_friends[name]=[ip,port,status]
        conn = self.user_logins[username][0]
        self.sendMessage(conn,(self.FRIENDS_LIST,(list_friends,)))

    def signup(self,conn,username,password):
        if username not in self.database:
            self.database[username] = {'password':password,'list_friends':[]}
            self.sendMessage(conn,('SUCCESS',))
            with open("database.json", "w") as outfile:
                json.dump(self.database, outfile)
            return True
        else:
            msg = (self.SIGNUP, ('FAIL',))
            self.sendMessage(conn, msg)
            return False


    def login(self, client, username,password):
        conn, _ = client
        time.sleep(0.1)
        msg = conn.recv(1024)
        ip, port = pickle.loads(msg)
        if  self.authenticate(username,password):
            self.user_logins[username] = (conn, (ip, int(port)))
            msg = (self.LOGIN, ('SUCCESS',))
            self.sendMessage(conn, msg)
            time.sleep(0.1)
            self.sendListFriend(username)
            self.updateStatus(username)
            return True
        else:
            msg = (self.LOGIN, ('FAIL',))
            self.sendMessage(conn, msg)
            return False

    def authenticate(self, username, password):
        return username in self.database and self.database[username]['password'] == password

    def logout(self,username):
        if username in self.user_logins:
            self.user_logins.pop(username)
            self.updateStatus(username)

    def disconnectClient(self,client):
        if client in self.clients_list:
            self.clients_list.remove(client)
        ip,port = client[1]
        print(f'Disconnect to ', ip, ':', str(port))
        client[0].close()

    def sendMessage(self,conn,msg):
        conn.sendall(pickle.dumps(msg))


    def clientThread(self,client):
        so, _ = client
        # login/signup
        while True:
            try:
                msg = so.recv(256) #initialize the buffer
            except:
                self.disconnectClient(client)
                return
            rqst, args = pickle.loads(msg)
            if  rqst == self.LOGIN:
                if self.login(client, *args):
                    username = args[0]
                    break
            elif rqst == self.SIGNUP:
                self.signup(so, *args)

        while True:
            try:
                msg = so.recv(512)
            except:
                self.logout(username)
                self.disconnectClient(client)
                return
            rqst, args = pickle.loads(msg)
            if rqst == self.REQUEST_CONNECTION:
                self.requestConnection(username,*args)
            elif rqst == self.LOGOUT:
                self.logout(username)
                self.clientThread(client)
            else:
                raise "request error"


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


if __name__ == "__main__":
    Server()

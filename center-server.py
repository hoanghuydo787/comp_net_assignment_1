#imports
import socket 
import threading


class Server:
    REQUEST_CONNECTION = 'REQUEST_CONNECTION'
    REJECT_CONNECTION = 'REJECT_CONNECTION'
    ACCEPT_CONNECTION = 'ACCEPT_CONNECTION'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    REGISTER = 'REGISTER'
    RETRIEVE_LIST_FRIEND =  'RETRIEVE LIST FRIEND'

    MAX_NUM_CLIENTS = 3

    """{<username>: {'password' :<password>,
                   'list_friends': [<username_friend1>,<username_friend2>,...]},
        ......
        }
    """
    user_info = {'win':  {'password' :'123',
                   'list_friends': ['hana']},
                 'hana': {'password': '456',
                          'list_friends': ['win']}
        }
    user_logins = {}

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
        list_friends = ''
        for name in self.user_info[username]['list_friends']:
            ip = port = None
            status = 'offline'
            if name in self.user_logins:
                ip,port = self.user_logins[name][1]
                status = 'online'
            list_friends += f"({name},{ip},{port},{status})"
        if list_friends == '':
            list_friends = '|'
        msg = self.RETRIEVE_LIST_FRIEND + list_friends
        so = self.user_logins[username][0]
        self.sendMessage(so,msg)

    def register(self,client,username,password):
        if username not in self.user_info:
            self.user_info[username] = {'password':password,'list_friends':[]}
            self.sendMessage(client[0],self.REGISTER+'|successful')
            return True
        else:
            self.sendMessage(client[0],self.REGISTER+'|fail')
            return False


    def login(self,client,username,password):
        if  self.authenticate(username,password):
            self.user_logins[username] = client
            self.sendMessage(client[0],self.LOGIN + f'|successful')
            return True
        else:
            self.sendMessage(client[0], self.LOGIN + f'|fail')
            return False

    def authenticate(self, username, password):
        return username in self.user_info and self.user_info[username]['password'] == password

    clients_list = []

    last_received_message = ""

    def __init__(self):
        self.server_socket = None
        self.create_listening_server()
    #listen for incoming connection

    def sendMessage(self,so,msg):
        so.sendall(msg.encode('utf-8'))

    def create_listening_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket using TCP port and ipv4
        local_ip = '127.0.0.1'
        local_port = 10319
        # this will allow you to immediately restart a TCP server
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # this makes the server listen to requests coming from other computers on the network
        self.server_socket.bind((local_ip, local_port))
        print("Listening for incoming messages..")
        self.server_socket.listen(self.MAX_NUM_CLIENTS) #listen for incomming connections / max 5 clients
        self.receive_messages_in_a_new_thread()

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
        username = None
        # login/register
        while True:
            try:
                incoming_buffer = so.recv(256) #initialize the buffer
            except:
                self.disconnectClient(client)
                return
            request = incoming_buffer.decode('utf-8')
            rqst, args = self.processRequest(request)
            print(rqst,len(rqst),args)
            if  rqst == self.LOGIN:
                if self.login(client,*args):
                   break
            elif rqst == self.REGISTER:
                self.register(client,*args)

        username = self.username(*client[1])
        while True:
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

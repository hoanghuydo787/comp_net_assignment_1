# sample code
from socket import *
import pickle
import time
import threading
import random
from os import listdir
from tkinter import *
from tkinter import messagebox

HOST = '127.0.0.1'
PORT = random.randint(1024, 49151)

class Server:
    serverSocket = None
    def __init__(self):
        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.bind((HOST, PORT))
        self.serverSocket.listen(10)
        print("Connecting...")
        self.peerASocket, addrA = self.serverSocket.accept()
        while True:
            conn, addr = self.serverSocket.accept()
            print('Connected ' + str(addr))
            t = threading.Thread(target=self.receive_messages_in_a_new_thread, args = (conn,), daemon = True)
            t.start()
    def receive_messages_in_a_new_thread(self, conn):
        while True:
            try:
                message = conn.recv(1023)
                self.peerASocket.send(message)
            except:
                conn.close()
                break

class GUI:
    serverSocket = None
    targetSocket = None
    selfSocket = None
    last_received_message = None

    REQUEST_CONNECTION = 'REQUEST_CONNECTION'
    REJECT_CONNECTION = 'REJECT_CONNECTION'
    ACCEPT_CONNECTION = 'ACCEPT_CONNECTION'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    SIGNUP = 'SIGNUP'
    FRIENDS_LIST = 'FRIENDS_LIST'
    FILE_TRANSFER = 'FILE_TRANSFER'
    MESSAGE = 'MESSAGE'
    path = 'D:\\assignment2\\comp_net_assignment_1-master\\recv_file'

    def __init__(self, master):
        self.root = master
        self.chat_transcript_area = None
        self.enter_text_widget = None
        self.frframe = None
        self.chatframe = None
        self.entryframe = None
        self.logout_but = None
        self.chat_history = {}
        self.username = None
        self.password = None
        self.repassword = None
        self.friend_list = {} #{username: [ip, port, status]}
        self.target = '' #username of opponent
        self.targets = None
        self.reset_frame()
        self.init_socket()
        self.init_gui()
        self.peers = {}

    def createSocket(self):
        try:
            so = socket(AF_INET, SOCK_STREAM)
            ip = HOST
            port = random.randint(10000, 49151)
            so.bind((ip,port))
            return so, (ip, port)
        except:
            return self.createSocket()

    def init_socket(self):
        serverName = "127.0.0.1"
        serverPort = 12000

        self.serverSocket = socket(AF_INET, SOCK_STREAM)
        self.serverSocket.connect((serverName, serverPort))

    def sendMessage(self, conn, msg):
        conn.sendall(pickle.dumps(msg))

    def init_gui(self):  # GUI initializer
        self.root.title("Chat App")
        self.root.resizable(0, 0)
        self.login_ui()

    def login_ui(self):
        self.hide_frame()
        self.reset_frame()

        Label(self.userframe, text='Username:', font=("Helvetica", 13)).pack(side='left',padx=10)
        self.username = Entry(self.userframe, width=40, borderwidth=2)
        self.username.pack(side='left',anchor='e')
        Label(self.passframe, text='Password:', font=("Helvetica", 13)).pack(side='left',padx=10)
        self.password = Entry(self.passframe, show = '*', width=40, borderwidth=2)
        self.password.pack(side='left',anchor='e')
        Button(self.login_but, text="Log in", width=10, command=self.log_in).pack(side='bottom')
        Label(self.signup_but, text='If you don\'t have an account,', font=("Helvetica", 10)).pack(side='left', padx=10)
        Button(self.signup_but, text='Sign up', bd=0, fg='blue', command=self.signup_ui).pack(side='left')

        self.userframe.pack(anchor='nw')
        self.passframe.pack(anchor='nw')
        self.login_but.pack(anchor='center')
        self.signup_but.pack(anchor='nw')

    def log_in(self):
        if len(self.username.get()) == 0:
            messagebox.showerror('Message', "Please enter username")
            return
        if len(self.password.get()) == 0:
            messagebox.showerror('Message', "Please enter password")
            return
        self.username.config(state='disabled')
        self.password.config(state='disabled')
        time.sleep(0.1)
        msg = (self.LOGIN, (self.username.get(), self.password.get()))
        self.sendMessage(self.serverSocket, msg)
        time.sleep(0.1)
        msg = (HOST, PORT)
        self.sendMessage(self.serverSocket, msg)

        header = None
        while header != self.LOGIN:
            header, (reply,) = pickle.loads(self.serverSocket.recv(1024))

        if reply == 'SUCCESS':
            frlist_dumps = b''
            while True:
                income = self.serverSocket.recv(1024)
                frlist_dumps += income
                if len(income) < 1024:
                    break
            header, args = pickle.loads(frlist_dumps)
            self.friend_list = args[0]
            self.hide_frame()
            self.display_logout_but()
            self.display_friend_box()
            self.display_chat_box()
            self.display_chat_entry_box()
            thread = threading.Thread(target=self.receive_message_from_server, daemon=True)
            thread.start()

        elif reply == 'FAIL':
            messagebox.showinfo('Message', 'Username or password is invalid')
            self.username.config(state='normal')
            self.password.config(state='normal')

    def signup_ui(self):
        self.hide_frame()
        self.reset_frame()

        Label(self.userframe, text='Username:', font=("Helvetica", 13)).pack(side='left', padx=10)
        self.username = Entry(self.userframe, width=40, borderwidth=2)
        self.username.pack(side='left', anchor='e')
        Label(self.passframe, text='Password:', font=("Helvetica", 13)).pack(side='left', padx=10)
        self.password = Entry(self.passframe, show='*', width=40, borderwidth=2)
        self.password.pack(side='left', anchor='e')
        Label(self.repassframe, text='Re-Password:', font=("Helvetica", 13)).pack(side='left', padx=10)
        self.repassword = Entry(self.repassframe, show='*', width=40, borderwidth=2)
        self.repassword.pack(side='left', anchor='e')
        Button(self.signup_but, text="Sign up", width=10, command=self.sign_up).pack(side='bottom')
        Label(self.login_but, text='If you already have an account,', font=("Helvetica", 10)).pack(side='left', padx=10)
        Button(self.login_but, text='Log in', bd=0, fg='blue', command=self.login_ui).pack(side='left')

        self.userframe.pack(anchor='nw')
        self.passframe.pack(anchor='nw')
        self.repassframe.pack(anchor='nw')
        self.signup_but.pack(anchor='center')
        self.login_but.pack(anchor='nw')

    def sign_up(self):
        if len(self.username.get()) == 0:
            messagebox.showerror('Message', "Please enter username")
            return
        if len(self.password.get()) == 0:
            messagebox.showerror('Message', "Please enter password")
            return
        if len(self.repassword.get()) == 0:
            messagebox.showerror('Message', "Please enter re-password")
            return
        if self.password.get() != self.repassword.get():
            messagebox.showerror('Message', 'Password don\'t match')
            return
        self.username.config(state='disabled')
        self.password.config(state='disabled')
        self.repassword.config(state='disabled')
        time.sleep(0.1)

        msg = (self.SIGNUP, (self.username.get(), self.password.get()))
        self.sendMessage(self.serverSocket, msg)

        header = None
        while header != self.SIGNUP:
            header, (reply, _) = pickle.loads(self.serverSocket.recv(1024))
        if reply == 'SUCCESS':
            messagebox.showinfo('Message', 'Sign up successful!')
        elif reply == 'FAIL':
            messagebox.showinfo('Message', 'Username has in used')
        self.username.config(state='normal')
        self.password.config(state='normal')
        self.repassword.config(state='normal')

    def log_out(self):
        msg = (self.LOGOUT, (self.username.get(),))
        self.sendMessage(self.serverSocket, msg)
        self.login_ui()

    def request_session(self):
        username = self.targets.get()
        if username in self.peers:
            return
        if self.friend_list[username][2] == 'OFFLINE':
            messagebox.showinfo('Message', 'The user if offline!')
            return
        self.target = username
        so,(ip,port) = self.createSocket()
        msg = ('REQUEST_CONNECTION', (username,ip,port))
        self.sendMessage(self.serverSocket,msg)
        self.reset_chatbox()
        print(ip,port)
        t=threading.Thread(target=self.wait_connect,args = (so,username), daemon = True)
        t.start()

    def wait_connect(self,so,username):
        so.listen(5)
        so.settimeout(120)
        try:
            conn, addr = so.accept()
            self.peers[username] = conn
            if username not in self.chat_history:
                self.chat_history[username] = []
            t = threading.Thread(target=self.receive_message_from_peer,args =(username,), daemon = True)
            t.start()
        except:
            return

    def accept_session(self,username,ip,port):
        print(username,ip,port)
        so = socket(AF_INET, SOCK_STREAM)
        # try:
        so.connect((ip,port))
        self.peers[username]=so
        if username not in self.chat_history:
            self.chat_history[username]=[]

        t = threading.Thread(target=self.receive_message_from_peer,args =(username,),daemon = True)
        t.start()
        # except:
        #     print('Không thể connect tới',username)

    def recv(self,conn):
        msg = b''
        while True:
            try:
                buffer = conn.recv(1024)
            except:
                return None
            msg += buffer
            if len(buffer) < 1024:
                break
        return msg

    def receive_message_from_peer(self,username):
        while True:
            conn = self.peers[username]
            # msg = self.recv(conn)
            # if msg is None:
            #     print('Disconnected to ',username)
            #     return
            msg = conn.recv(512)
            header, args = pickle.loads(msg)
            if header == self.MESSAGE:
                message = args[1]
                self.chat_history[username] += [message]
                print(self.target)
                if self.target == message.split(':')[0]: self.insertchatbox(message)

            elif header == self.FILE_TRANSFER:
                filename = args[0]
                if filename in listdir(self.path):
                    file = filename.split('.')
                    i = 1
                    filename_i = file[0] + '(' + str(i) + ')' + file[1]
                    while filename_i in listdir(self.path):
                        i = i + 1
                        filename_i = file[0] + '(' + str(i) + ')' + file[1]
                    filename = filename_i
                file = open(self.path + '\\' + filename, 'wb')
                file.write(args[1])
                file.close()
                msg = username + ' da gui cho ban ' + filename
                self.insertchatbox(msg)
                self.chat_history[username] += [msg]


    # def listen_for_incoming_messages_in_a_thread(self):
    #     thread = threading.Thread(target=self.receive_message_from_self)  # Create a thread for the send and receive in same time
    #     thread.start()

    # function to recieve msg
    def receive_message_from_server(self):
        while True:
            msg =self.recv(self.serverSocket)
            if msg is None:
                print('Mát kết nối với server')
                break
            header, args = pickle.loads(msg)
            if header == self.FRIENDS_LIST:
                self.friend_list = args[0]
                self.update_friend_box()
            elif header == self.REQUEST_CONNECTION:
                op = args[0]
                if messagebox.askokcancel("Connect request", "Request connection from "+op):
                    self.target = op
                    self.accept_session(*args)
                else: print('reject kết nối từ', op)
        self.serverSocket.close()


    # def getAddr(self, username):
    #     if username in self.friend_list:
    #         return self.friend_list[username][0], self.friend_list[username][1]
    #     return None

    # def receive_message_from_self(self):
    #     while True:
    #         msg = b''
    #         while True:
    #             try:
    #                 buffer = self.selfSocket.recv(1024)
    #             except:
    #                 return
    #
    #             msg += buffer
    #             if len(buffer) <1024:
    #                 break
    #         header, args = pickle.loads(msg)
    #         if header == self.MESSAGE:
    #             user = args[0]
    #             message = args[1]
    #             if self.target not in self.chat_history: self.chat_history[self.target] = []
    #             self.chat_history[self.target] += [message]
    #             if self.target == user: self.insertchatbox(message)
    #         elif header == self.FILE_TRANSFER:
    #             filename = args[0]
    #             if filename in listdir(self.path):
    #                 file = filename.split('.')
    #                 i = 1
    #                 filename_i = file[0]+'('+str(i)+')'+file[1]
    #                 while filename_i in listdir(self.path):
    #                     i = i+1
    #                     filename_i = file[0]+'('+str(i)+')'+file[1]
    #                 filename = filename_i
    #             file = open(self.path + '\\' + filename, 'wb')
    #             file.write(args[1])
    #             file.close()
    #             msg = self.target + ' da gui cho ban ' + filename
    #             self.insertchatbox(msg)
    #             self.chat_history[self.target] += [msg]

    def file_transfer(self,conn,file_path):
        file = open(file_path, 'rb')
        n = file_path.split('\\')
        filename = n[len(n)-1]
        data = b''
        while True:
            line = file.read(1024)
            data += line
            if len(line)<1024:
                break
        file.close()
        msg = (self.FILE_TRANSFER,(filename,data))
        self.sendMessage(conn,msg)

    def display_logout_but(self):
        self.logout_but = Frame()
        Label(self.logout_but, text=self.username.get()).pack(side='left', padx=10)
        Button(self.logout_but, text="Log out", width=10, command=self.log_out).pack(side='left')
        self.logout_but.pack(anchor='nw')

    def display_name_section(self):
        frame = Frame()
        Label(frame, text='Enter your name:', font=("Helvetica", 16)).pack(side='left', padx=10)
        self.name_widget = Entry(frame, width=50, borderwidth=2)
        self.name_widget.pack(side='left', anchor='e')
        self.join_button = Button(frame, text="Join", width=10, command=self.on_join).pack(side='left')
        frame.pack(side='top', anchor='nw')

    def display_friend_box(self):
        self.frframe = Frame()
        Label(self.frframe, text='Friend List:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.friend_area = Frame(self.frframe, width=30, height=15)
        scrollbar = Scrollbar(self.frframe, orient=VERTICAL)
        self.friend_area.pack(side='left', padx=10)
        scrollbar.pack(side='right', fill='y')
        self.frframe.pack(side='left')
        self.targets = StringVar(self.friend_area, '')
        for name in self.friend_list:
            Radiobutton(self.friend_area, text=str((name, self.friend_list[name][2])), variable=self.targets, value=name, indicator = 0, width=30, background = "light blue", command=self.request_session).pack(side='top', fill=X, ipady=5)
        """for fr in frlist:
            self.friend_area.insert('end', fr[0] + '\n')
            self.friend_area.yview(END)"""
    def update_friend_box(self):
        self.friend_area.pack_forget()
        self.friend_area = Frame(self.frframe, width=30, height=15)
        self.friend_area.pack(side='left', padx=10)
        for name in self.friend_list:
            Radiobutton(self.friend_area, text=str((name, self.friend_list[name][2])), variable=self.targets, value=name, indicator = 0, width=30, background = "light blue", command=self.request_session).pack(side='top', fill=X, ipady=5)
    def display_chat_box(self):
        self.chatframe = Frame()
        Label(self.chatframe, text='Chat Box:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.chat_transcript_area = Text(self.chatframe, width=60, height=10, font=("Serif", 12))
        scrollbar = Scrollbar(self.chatframe, command=self.chat_transcript_area.yview, orient=VERTICAL)
        self.chat_transcript_area.config(yscrollcommand=scrollbar.set)
        self.chat_transcript_area.bind('<KeyPress>', lambda e: 'break')
        self.chat_transcript_area.pack(side='left', padx=10)
        scrollbar.pack(side='right', fill='y')
        self.chatframe.pack(side='top')
        if self.target in self.chat_history:
            for msg in self.chat_history[self.target]:
                self.insertchatbox(msg)

    def display_chat_entry_box(self):
        self.entryframe = Frame()
        Label(self.entryframe, text='Enter message:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.enter_text_widget = Text(self.entryframe, width=60, height=3, font=("Serif", 12))
        self.enter_text_widget.pack(side='left', pady=15)
        self.enter_text_widget.bind('<Return>', self.on_enter_key_pressed)
        self.entryframe.pack(side='top')

    def on_enter_key_pressed(self, event):
        self.send_chat()
        self.clear_text()

    def clear_text(self):
        self.enter_text_widget.delete(1.0, 'end')

    def insertchatbox(self, msg):
        self.chat_transcript_area.insert('end', msg + '\n')
        self.chat_transcript_area.yview(END)

    def send_chat(self):
        senders_name = self.username.get().strip() + ": "
        conn = self.peers[self.target]
        data = self.enter_text_widget.get(1.0, 'end').strip()
        if data.split(' ')[0] == '\\file_transfer':
            path = data.split(' ')[1]
            self.file_transfer(conn, path)
            msg = 'Ban da gui file cho ' + self.target + ' '
            self.insertchatbox(msg)
            self.chat_history[self.target] += [msg]
            return 'break'
        msg = (senders_name + data)
        self.insertchatbox(msg)
        if self.target not in self.chat_history: self.chat_history[self.target] = []
        self.chat_history[self.target] += [msg]

        message = (self.MESSAGE, (self.username.get(), msg))
        self.sendMessage(conn, message)
        self.enter_text_widget.delete(1.0, 'end')
        # print(self.chat_history)
        return 'break'

    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
            self.serverSocket.close()
            exit(0)

    def hide_frame(self):
        self.userframe.pack_forget()
        self.passframe.pack_forget()
        self.repassframe.pack_forget()
        self.login_but.pack_forget()
        self.signup_but.pack_forget()
        if self.logout_but: self.logout_but.pack_forget()
        if self.frframe: self.frframe.pack_forget()
        if self.chatframe: self.chatframe.pack_forget()
        if self.entryframe: self.entryframe.pack_forget()

    def reset_frame(self):
        self.userframe = Frame()
        self.passframe = Frame()
        self.repassframe = Frame()
        self.login_but = Frame()
        self.signup_but = Frame()

    def reset_chatbox(self):
        if self.entryframe:self.entryframe.pack_forget()
        if self.chatframe: self.chatframe.pack_forget()
        self.display_chat_box()
        self.display_chat_entry_box()

    def clear_buffer(self, conn):
        try:
            while conn.recv(1024): pass
        except:
            pass
def run_server():
    Server()


if __name__ == '__main__':
    thread = threading.Thread(target=run_server, daemon = True)
    thread.start()
    time.sleep(0.1)
    root = Tk()
    gui = GUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
    root.mainloop()

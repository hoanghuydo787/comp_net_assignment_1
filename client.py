# sample code
from socket import *
import pickle
import time
import threading
from tkinter import *
from tkinter import messagebox


class GUI:
    peerSocket = None
    last_received_message = None

    def __init__(self, master):
        self.root = master
        self.chat_transcript_area = None
        self.enter_text_widget = None
        self.username = None
        self.password = None
        self.repassword = None
        self.friend_list = [] #[[username, ip, port, status]]
        self.target = None #username of opponent
        self.reset_frame()
        self.init_socket()
        self.init_gui()

    def init_socket(self):
        serverName = "127.0.0.1"
        serverPort = 12000
        self.peerSocket = socket(AF_INET, SOCK_STREAM)
        self.peerSocket.connect((serverName, serverPort))

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
        self.peerSocket.send('LOGIN'.encode())
        self.username.config(state='disabled')
        self.peerSocket.send(self.username.get().encode())
        self.password.config(state='disabled')
        time.sleep(0.1)
        self.peerSocket.send(self.password.get().encode())
        reply = self.peerSocket.recv(1024).decode()
        if reply == 'Success':
            frlist_dumps = b''
            while True:
                income = self.peerSocket.recv(1024)
                frlist_dumps += income
                if len(income) < 1024:
                    break
            self.friend_list = pickle.loads(frlist_dumps)
            self.hide_frame()

            self.display_friend_box()
            self.display_chat_box()
            self.display_chat_entry_box()
            self.listen_for_incoming_messages_in_a_thread()
        elif reply == 'Fail':
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
        self.peerSocket.send('SIGNUP'.encode())
        self.username.config(state='disabled')
        self.peerSocket.send(self.username.get().encode())
        self.password.config(state='disabled')
        self.repassword.config(state='disabled')
        time.sleep(0.1)
        self.peerSocket.send(self.password.get().encode())
        reply = self.peerSocket.recv(1024).decode()
        if reply == 'Success':
            messagebox.showinfo('Message', 'Sign up successful!')
            self.username.config(state='normal')
            self.password.config(state='normal')
            self.repassword.config(state='normal')
        elif reply == 'Fail':
            messagebox.showinfo('Message', 'Username has in used')
            self.username.config(state='normal')
            self.password.config(state='normal')
            self.repassword.config(state='normal')

    def listen_for_incoming_messages_in_a_thread(self):
        thread = threading.Thread(target=self.receive_message_from_server,
                                  args=(self.peerSocket,))  # Create a thread for the send and receive in same time 
        thread.start()

    # function to recieve msg
    def receive_message_from_server(self, so):
        while True:
            buffer = so.recv(256)
            if not buffer:
                break
            message = buffer.decode('utf-8')
            self.chat_transcript_area.insert('end', message + '\n')
            self.chat_transcript_area.yview(END)
        so.close()

    def display_name_section(self):
        frame = Frame()
        Label(frame, text='Enter your name:', font=("Helvetica", 16)).pack(side='left', padx=10)
        self.name_widget = Entry(frame, width=50, borderwidth=2)
        self.name_widget.pack(side='left', anchor='e')
        self.join_button = Button(frame, text="Join", width=10, command=self.on_join).pack(side='left')
        frame.pack(side='top', anchor='nw')

    def display_friend_box(self):
        frame = Frame()
        Label(frame, text='Friend List:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.friend_area = Frame(frame, width=30, height=15)
        scrollbar = Scrollbar(frame, orient=VERTICAL)
        self.friend_area.pack(side='left', padx=10)
        scrollbar.pack(side='right', fill='y')
        frame.pack(side='left')
        self.target = StringVar(self.friend_area, '')
        for [name, ip, port, status] in self.friend_list:
            Radiobutton(self.friend_area, text=str((name, status)), variable=self.target, value=name, indicator = 0, width=30, background = "light blue").pack(side='top', fill=X, ipady=5)
        """for fr in frlist:
            self.friend_area.insert('end', fr[0] + '\n')
            self.friend_area.yview(END)"""

    def display_chat_box(self):
        frame = Frame()
        Label(frame, text='Chat Box:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.chat_transcript_area = Text(frame, width=60, height=10, font=("Serif", 12))
        scrollbar = Scrollbar(frame, command=self.chat_transcript_area.yview, orient=VERTICAL)
        self.chat_transcript_area.config(yscrollcommand=scrollbar.set)
        self.chat_transcript_area.bind('<KeyPress>', lambda e: 'break')
        self.chat_transcript_area.pack(side='left', padx=10)
        scrollbar.pack(side='right', fill='y')
        frame.pack(side='top')

    def display_chat_entry_box(self):
        frame = Frame()
        Label(frame, text='Enter message:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.enter_text_widget = Text(frame, width=60, height=3, font=("Serif", 12))
        self.enter_text_widget.pack(side='left', pady=15)
        self.enter_text_widget.bind('<Return>', self.on_enter_key_pressed)
        frame.pack(side='top')

    def on_enter_key_pressed(self, event):
        self.send_chat()
        self.clear_text()

    def clear_text(self):
        self.enter_text_widget.delete(1.0, 'end')

    def send_chat(self):
        senders_name = self.name_widget.get().strip() + ": "
        data = self.enter_text_widget.get(1.0, 'end').strip()
        message = (senders_name + data).encode('utf-8')
        self.chat_transcript_area.insert('end', message.decode('utf-8') + '\n')
        self.chat_transcript_area.yview(END)
        self.peerSocket.send(message)
        self.enter_text_widget.delete(1.0, 'end')
        return 'break'

    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
            self.peerSocket.close()
            exit(0)

    def hide_frame(self):
        self.userframe.pack_forget()
        self.passframe.pack_forget()
        self.repassframe.pack_forget()
        self.login_but.pack_forget()
        self.signup_but.pack_forget()

    def reset_frame(self):
        self.userframe = Frame()
        self.passframe = Frame()
        self.repassframe = Frame()
        self.login_but = Frame()
        self.signup_but = Frame()

    def clear_buffer(self, conn):
        try:
            while sock.recv(1024): pass
        except:
            pass

if __name__ == '__main__':
    root = Tk()
    gui = GUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
    root.mainloop()

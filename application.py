# -*- coding: utf-8 -*-
import json
import socket
import threading
import messages
import model
import view

BUFFER_SIZE = 2 ** 10


class Application(object):
    instance = None

    def __init__(self, args):
        self.args = args
        self.closing = False
        self.host = None
        self.port = None
        self.receive_worker = None
        self.sock = None
        self.username = None
        self.ui = view.UI(self)
        Application.instance = self

    def execute(self):
        """
        Метод, вызываемый в самом начале запуска клиента
        """
        if not self.ui.show():
            return  # если не отрисовалось что-то, то он сюда зайдет
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except (socket.error, OverflowError):
            self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
            return
        self.first_hello_message()
        self.receive_worker = threading.Thread(target=self.receive)
        self.receive_worker.start()
        self.ui.loop()

    def first_hello_message(self):
        """
        Клиент пишет серверу пустое сообщение, только лишь с именем данного клиента,
        Чтобы сервер оповеслил всех остальных о новом игроке.
        Сервер делает рассылку с новым score, с учетом нового игрока
        """
        message = model.Message(username_last_player=self.username)
        try:
            self.sock.sendall(message.marshal())  # шлем сообщение через сокет серверу
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def receive(self):
        """
        Метод, в котором с помощью receive_all мы получаем объект класса message, внутри которого лежат нужные
        нам данные. В конце метода вызывается метод show_message(message), определенный внутри класса UI
        """
        while True:
            try:
                message = model.Message(**json.loads(self.receive_all()))
            except (ConnectionAbortedError, ConnectionResetError):
                if not self.closing:
                    self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
                return
            self.ui.show_message(message)

    def receive_all(self):
        """
        Метод, который пытается считывать из сокета кусочки размером с BUFFER_SIZE,
        пока не получит символ, означающий конец передачи
        """
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += self.sock.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def add_number(self):
        """
        Метод, который вызывается при нажатии кнопки add у клиента
        """
        message = model.Message(username_last_player=self.username, quit=False)

        self.ui.add_number_button['state'] = 'disabled'
        self.ui.end_game_button['state'] = 'disabled'
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def end_game_for_this_client(self):
        """
        Метод, который вызывается при нажатии кнопки end у клиента
        """
        message = model.Message(username_last_player=self.username, quit=True)
        self.ui.add_number_button['state'] = 'disabled'
        self.ui.end_game_button['state'] = 'disabled'
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def exit(self):
        """
        Метод, который вызывался изначально, чтобы отключить текущего клиента от чата
        """
        self.closing = True
        try:
            self.sock.sendall(model.Message(username=self.username, message="", quit=True).marshal())
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print(messages.CONNECTION_ERROR)
        finally:
            self.sock.close()

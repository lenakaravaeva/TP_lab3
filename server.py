# -*- coding: utf-8 -*-
import json
import socket
import sys
import threading
import model
import random

BUFFER_SIZE = 2 ** 10
CLOSING = "Application closing..."
CONNECTION_ABORTED = "Connection aborted"
CONNECTED_PATTERN = "Client connected: {}:{}"
ERROR_ARGUMENTS = "Provide port number as the first command line argument"
ERROR_OCCURRED = "Error Occurred"
EXIT = "exit"
JOIN_PATTERN = "{username} has joined"
RUNNING = "Server is running..."
SERVER = "SERVER"
SHUTDOWN_MESSAGE = "shutdown"
TYPE_EXIT = "Type 'exit' to exit>"


class Server(object):
    def __init__(self, argv):
        self.clients = set()
        self.players_score = {}  # Словарь с счётами игроков
        self.rnd_number = None
        self.listen_thread = None
        self.port = None
        self.sock = None
        self.parse_args(argv)
        self.name_current_player = None  # имя текущего игрока
        self.names_of_active_players = []  # актуальнй список имен играющих клиентов
        self.index_of_current_player = None

    def listen(self):
        self.sock.listen(1)
        while True:
            try:
                client, address = self.sock.accept()
            except OSError:
                print(CONNECTION_ABORTED)
                return
            print(CONNECTED_PATTERN.format(*address))
            self.clients.add(client)
            threading.Thread(target=self.handle, args=(client,)).start()

    def handle(self, client):
        while True:
            try:
                message = model.Message(**json.loads(self.receive(client)))
            except (ConnectionAbortedError, ConnectionResetError):
                print(CONNECTION_ABORTED)
                return
            if message.quit:
                client.close()
                self.clients.remove(client)
                return
            print(str(message))
            # if SHUTDOWN_MESSAGE.lower() == message.message.lower(): #Тут гайделевский обработчик выхода из приложения
            #     self.exit()
            #    return

            message = self.next_action(message)

            print(self.names_of_active_players)  # выводим в консоль очередь
            self.broadcast(message)

    def broadcast(self, message):
        print(message)
        for client in self.clients:
            client.sendall(message.marshal())

    def is_end_game(self, message):
        print('\t !Сейчас мы будем проверять для удаления игроков!')
        print('до:'+str(self.names_of_active_players))
        if message.quit:
            print('Мы сейчас удаляем: ', message.username_last_player)
            self.names_of_active_players.remove(message.username_last_player)
            self.index_of_current_player -= 1  # мы удалили элемент, на котором стоит индекс.
            # Чтобы скомпенсировать сдвиг очереди, уменьшаем на 1 индекс
        for key, val in self.players_score.items():
            if val >= 21 and key in self.names_of_active_players:
                print('Мы сейчас удаляем: ', key)
                self.names_of_active_players.remove(key)
                self.index_of_current_player -= 1  # мы удалили элемент, на котором стоит индекс.
                # Чтобы скомпенсировать сдвиг очереди, уменьшаем на 1 индекс
        print('после:' + str(self.names_of_active_players))

    def get_name_next_player(self):
        if len(self.names_of_active_players) != 0:  # если не самый последний ход, когда актуальных игроков не осталось
            self.index_of_current_player = (self.index_of_current_player + 1) % len(
                self.names_of_active_players)  # следующий индекс (по кругу)
            self.name_current_player = self.names_of_active_players[self.index_of_current_player]
            print('индекс текущего игрока: ' + str(self.index_of_current_player))
            print("\tСейчас писать будет" + str(self.name_current_player))
            return self.name_current_player
        else:
            return None

    def next_action(self, message):
        if message.username_last_player not in self.players_score:  # Если написал чувак,
                                                                    # который ещё не разу не обращался к серверу
            self.players_score[message.username_last_player] = 0  # добавляем в скоры этого чувака и счет:=ноль
            self.names_of_active_players.append(message.username_last_player)  # Добавляем пользователя в список
                                                                                # активный юзеров (нк закончивших игру)
            if self.rnd_number is None:  # Если это самое первое подключение к серверу
                self.index_of_current_player = 0
                self.rnd_number = random.randint(1, 11)
                message.rnd_number = self.rnd_number
                message.username_current_player = self.get_name_next_player()  # говорим кому можно ходить
        else:
            self.players_score[message.username_last_player] += self.rnd_number
            self.rnd_number = random.randint(1, 11)  # храним это чиселко у себя
            self.is_end_game(message)
            self.name_current_player = self.get_name_next_player()  # говорим кому можно ходить

        # в любом случае пишем в сообщение от имени сервера актуальные результаты
        message.username_last_player = 'Server'
        message.username_current_player = self.name_current_player
        message.players_score = self.players_score
        message.rnd_number = self.rnd_number
        message.quit = False

        if self.name_current_player is None:  # Самый последний ход закончился, и нам надо вывести результат
            message.quit = True  # сервер сообщает всем о конце игры поднятой переменной

        return message

    def receive(self, client):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += client.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
            return buffer[:-1]

    def run(self):
        print(RUNNING)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("", self.port))
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def parse_args(self, argv):
        if len(argv) != 2:
            raise RuntimeError(ERROR_ARGUMENTS)
        try:
            self.port = int(argv[1])
        except ValueError:
            raise RuntimeError(ERROR_ARGUMENTS)

    def exit(self):
        self.sock.close()
        for client in self.clients:
            client.close()
        print(CLOSING)


if __name__ == "__main__":
    try:
        Server(sys.argv).run()
    except RuntimeError as error:
        print(ERROR_OCCURRED)
        print(str(error))

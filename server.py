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
        self.clients = set()  # множество клиентов, которые эксплуатируют сокет
        self.players_score = {}  # словарь с счётами игроков
        self.rnd_number = None
        self.listen_thread = None
        self.port = None
        self.sock = None
        self.parse_args(argv)
        self.name_current_player = None  # имя текущего игрока
        self.names_of_active_players = []  # актуальнй список имен играющих клиентов
        self.index_of_current_player = None  # числовой указатель на игрока, который сейчас должен ходить

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
        """
        Метод-слушатель конкретного клиента
        :param client: - клиент, с от которого он ждет сообщения
        """
        while True:  # бесконечный цикл
            try:
                message = model.Message(**json.loads(self.receive(client)))  # ожидание получения сообщения целиком
            except (ConnectionAbortedError, ConnectionResetError):
                print(CONNECTION_ABORTED)
                return
            print(str(message))

            message = self.next_action(message)

            print(self.names_of_active_players)  # вывод очереди в консоль
            self.broadcast(message)

    def broadcast(self, message):
        """
        Метод рассылает сообщение message всем клиентам, которые подключены к серверу
        (даже неактивным, чтобы получать актуальный счёт игроков)
        """
        print(message)
        for client in self.clients:
            client.sendall(message.marshal())

    def is_end_game(self, message):
        """
        В данном методе проверям, надо ли кого-нибудь убрать из списка актуальных игроков.
        Например, если счет игрока >=21 или если он пожелал закончить игру.
        :param message: сообщение, которое получили от клиента и передали в эту функцию
        """
        if message.quit:  # если клиент поставил этот флаг, то он желает прекратить игру
            print('Мы сейчас удаляем: ', message.username_last_player)
            self.names_of_active_players.remove(message.username_last_player)  # удаление игрока из списка актуальных
            self.index_of_current_player -= 1  # удалили элемент, на котором стоит индекс
            # чтобы скомпенсировать сдвиг очереди, уменьшаем индекс на 1
        for key, val in self.players_score.items():  # проверяем словарь результатов игоков
            if val >= 21 and key in self.names_of_active_players:
                print('Мы сейчас удаляем: ', key)
                self.names_of_active_players.remove(key)  # удаляем игрока из списка актуальных
                self.index_of_current_player -= 1  # мы удалили элемент, на котором стоит индекс
                # чтобы скомпенсирковать сдвиг очереди, уменьшаем на 1 индекс
        print('после:' + str(self.names_of_active_players))

    def get_name_next_player(self):
        """
        Метод дает имя игрока, котороый должен ходить следующим
        Использует актуальный список игроков self.names_of_active_players
        и индекс-указатель на того, кто ходит: self.index_of_current_player
        """
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
        """
        Совершает ряд подготовеительных действий с полями класса сервера и c сообщением, которое будем рассылать всем
        :return: обновленный message, которое будем рассылать дальше всем игрокам
        """
        if message.username_last_player not in self.players_score:
            # если написал игрок, который ещё ни разу не обращался к серверу
            self.players_score[message.username_last_player] = 0  # добавляем в скоры этого игрока и счет:=ноль
            self.names_of_active_players.append(message.username_last_player)
            # добавляем пользователя в список активных игроков (которые не закончили игру)
            if self.rnd_number is None:  # если это самое первое подключение к серверу
                self.index_of_current_player = 0
                self.rnd_number = random.randint(1, 11)
                message.rnd_number = self.rnd_number
                message.username_current_player = self.get_name_next_player()  # говорим кому можно ходить
        else:
            # если написал игрок, который уже обращался к серверу
            if not message.quit:
                # если последний игрок пожелал закончить игру, действия в этом if не будут выполняться
                self.players_score[message.username_last_player] += self.rnd_number
                self.rnd_number = random.randint(1, 11)  # храним это число у себя
            self.is_end_game(message)
            self.name_current_player = self.get_name_next_player()  # говорим кому можно ходить

        # в любом случае пишем в сообщение от имени сервера актуальные результаты
        message.username_last_player = 'Server'
        message.username_current_player = self.name_current_player
        message.players_score = self.players_score
        message.rnd_number = self.rnd_number
        message.quit = False

        if self.name_current_player is None:
            # тут, если самый последний возможный ход закончился и надо вывести результат
            message.quit = True  # сервер сообщает всем о конце игры поднятой переменной

        return message

    def receive(self, client):
        """
        Метод, который пытается считывать из сокета кусочки размером с BUFFER_SIZE,
        пока не получит символ, означающий конец передачи
        Метод аналогичен receiveAll у клиента.
        """
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += client.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
            return buffer[:-1]

    def run(self):
        """
        Самый первый метод, который будет запущен
        """
        print(RUNNING)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # создаём сокеты
        self.sock.bind(("", self.port))
        self.listen_thread = threading.Thread(target=self.listen)  # запускаем метод listen в отдельном потоке
        self.listen_thread.start()

    def parse_args(self, argv):
        """
        В данном методе (изначальном) парсятся параметры, которые передаются при запуске server.py
        У нас параметром передается 5678
        """
        if len(argv) != 2:  # если число аргументов отличается от 2 (нулевой аргумент - имя проги)
            raise RuntimeError(ERROR_ARGUMENTS)
        try:
            self.port = int(argv[1])  # достаем из массива аргументов наш номер порта у сервера
        except ValueError:
            raise RuntimeError(ERROR_ARGUMENTS)


if __name__ == "__main__":
    try:
        Server(sys.argv).run()
    except RuntimeError as error:
        print(ERROR_OCCURRED)
        print(str(error))

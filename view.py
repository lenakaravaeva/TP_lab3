# -*- coding: utf-8 -*-
import tkinter
import messages
from random import randint
from tkinter import messagebox, simpledialog

CLOSING_PROTOCOL = "WM_DELETE_WINDOW"
END_OF_LINE = "\n"
TEXT_STATE_DISABLED = "disabled"
TEXT_STATE_NORMAL = "normal"


class UI(object):

    def __init__(self, application):
        self.application = application
        self.gui = None
        self.frame = None
        self.add_number_button = None
        self.end_game_button = None
        self.text_field = None

    def show(self):
        """
        Метод, в котором отрисовываем окошко и что-то внутри
        """
        self.gui = tkinter.Tk()
        self.gui.title(messages.TITLE)
        self.fill_frame()
        self.gui.protocol(CLOSING_PROTOCOL, self.on_closing)
        return self.input_dialogs()

    def loop(self):
        self.gui.mainloop()

    def fill_frame(self):
        """
        Метод отрисовывает начальное значание внутри клиента до того момента,
        пока клиент не получит информацию от сервера (с актуальным счетом, случайным числом)
        """
        self.frame = tkinter.Frame(self.gui)
        self.text_field1 = tkinter.Text(width=32, height=10)  # поле, в котором отрисовывается счёт игроков
        self.text_field1.pack()
        self.text_field1.insert(tkinter.END, " ")
        self.frame.pack()
        self.text_field2 = tkinter.Text(width=10, height=1)  # поле, в котором отрисовывается случайное число
        self.text_field2.insert(1.0, "Ваше число: ")
        self.text_field2.pack()

        self.add_number_button = tkinter.Button(self.gui, text=messages.ADD_NUMBER, command=self.application.add_number)
        self.add_number_button.pack()
        self.add_number_button['state'] = 'disabled'
        self.end_game_button = tkinter.Button(self.gui, text=messages.END_GAME,
                                              command=self.application.end_game_for_this_client)
        self.end_game_button.pack()
        self.end_game_button['state'] = 'disabled'

    def input_dialogs(self):
        """
        Метод, в котором изначально показывались окошки simpledialog с целью заполнения полей: username, host, port
        """
        # self.gui.lower()
        # self.application.username = simpledialog.askstring(messages.USERNAME, messages.INPUT_USERNAME, parent=self.gui)
        # if self.application.username is None:
        #     return False
        # self.application.host = simpledialog.askstring(messages.SERVER_HOST, messages.INPUT_SERVER_HOST,parent=self.gui)
        # if self.application.host is None:
        #     return False
        # self.application.port = simpledialog.askinteger(messages.SERVER_PORT, messages.INPUT_SERVER_PORT, parent=self.gui)
        # if self.application.port is None:
        #     return False
        self.application.username = "player"+str(randint(1, 1000))
        self.gui.title(self.application.username)  # обновили название окошка, подписали именем юзера
        # тут надо запретить одинаковые имена по идее
        self.application.host = "localhost"
        self.application.port = 5678
        return True  # если сюда дошли, то всё отрисовалось в этом методе нормально

    def alert(self, title, message):
        """
        Метод, который вызываем при возникновении ошибок.
        В нем мы ругаемся для пользователя.
        """
        messagebox.showerror(title, message)

    def show_message(self, message):
        """
        В этом методе перерисовываем окошко клиента, как только у нас появилось собщение
        Вызывается в конце метода application.receive()
        """
        if not message.quit:  # если игра ещё продолжается
            self.text_field1.delete(1.0, tkinter.END)
            for key, value in message.players_score.items():  # бежим по строкам мапы
                self.text_field1.insert(tkinter.END, "Счёт " + str(key) + " = " + str(value)+'\n')

            self.text_field2.delete(1.0, tkinter.END)
            self.text_field2.insert(tkinter.END, message.rnd_number)

            print("message.username_last_player = " + str(message.username_last_player))
            print('self.application.username = ' + str(self.application.username))
            if message.username_current_player == self.application.username:  # Если в сообщении сказано,
                # что текущий клиент должен ходить
                self.add_number_button['state'] = 'normal'
                self.end_game_button['state'] = 'normal'
        else:  # если сервер объявил о конце игры
            self.text_field1.delete(1.0, tkinter.END)
            self.text_field1.insert(tkinter.END, 'Отсортированные результаты игры\n')
            sorted_players_score = sorted(message.players_score.items(), key=lambda kv: kv[1])  # получаем список
            # кортежей отсортированных по значению по возрастанию
            sorted_players_score.reverse()  # разворачиваем по убыванию
            for key, value in sorted_players_score:
                self.text_field1.insert(tkinter.END, "Счёт " + str(key) + " = " + str(value) + '\n')

    def on_closing(self):
        self.application.exit()
        self.gui.destroy()

# -*- coding: utf-8 -*-

import json

END_CHARACTER = "\0"
MESSAGE_PATTERN = "{username_last_player}>{username_current_player}>{players_score}>{rnd_number}"
TARGET_ENCODING = "utf-8"


class Message(object):

    def __init__(self, **kwargs):
        self.username_last_player = None  # имя игрока, который послал сообщение
        self.username_current_player = None  # имя игрока, который должен сделать ход
        self.players_score = dict()
        self.rnd_number = None
        self.quit = False
        self.__dict__.update(kwargs)

    def __str__(self):
        return MESSAGE_PATTERN.format(**self.__dict__)

    def marshal(self):
        return (json.dumps(self.__dict__) + END_CHARACTER).encode(TARGET_ENCODING)

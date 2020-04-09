import json
import os
from typing import Dict, Set

import src.settings as var
from src.messages.message import Message

MESSAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "messages")
ROOT_DIR = os.path.join(os.path.dirname(__file__), "..", "..")


class Messages:
    def __init__(self):
        self.lang = var.LANGUAGE
        self.cache = {}
        self._load_messages()

    def get(self, key, index=None):
        if key not in self.messages:
            raise KeyError("Key {0!r} does not exist! Add it to messages.json".format(key))
        return Message(key, self.messages[key], index)

    __getitem__ = get

    def raw(self, *args):
        m = self.messages
        for key in args:
            m = m[key]

        return m

    def get_role_mapping(self,
                         reverse: bool = False,
                         remove_spaces: bool = False) -> Dict[str, str]:
        """ Retrieve a mapping between internal role names and localized role names.

        :param reverse: If True, maps localized role names and aliases to internal role names.
            If False, maps internal role names to the singular localized version of that name.
        :param remove_spaces: Whether the lookup keys (not values) should have spaces removed
        :return:
        """
        cache_key = "role_map_" + str(reverse) + str(remove_spaces)
        if cache_key in self.cache:
            return self.cache[cache_key]

        plural_rules = self.messages["_metadata"]["plural"]
        plural_index = 0
        for rule in plural_rules:
            if rule["number"] == 1 or rule["number"] is None:
                plural_index = rule["index"]
                break

        def maybe_remove_spaces(x: str) -> str:
            return x.replace(" ", "") if remove_spaces else x

        roles = {}  # type: Dict[str, str]
        for key, role in self.messages["_roles"].items():
            if key.startswith("*"):
                continue
            internal = key
            local = role[plural_index]
            if reverse:
                roles[maybe_remove_spaces(local)] = internal
            else:
                roles[maybe_remove_spaces(internal)] = local

        if reverse:
            for key, aliases in self.messages["_role_aliases"].items():
                if key.startswith("*"):
                    continue
                for alias in aliases:
                    roles[maybe_remove_spaces(alias)] = key

        self.cache[cache_key] = roles
        return roles

    def _load_messages(self):
        with open(os.path.join(MESSAGES_DIR, self.lang + ".json"), encoding="utf-8") as f:
            self.messages = json.load(f)

        fallback = self.messages["_metadata"]["fallback"]
        seen = {self.lang}
        while fallback is not None:
            if fallback in seen:
                raise TypeError("Fallback loop detected")
            seen.add(fallback)
            with open(os.path.join(MESSAGES_DIR, fallback + ".json"), encoding="utf-8") as f:
                fallback_msgs = json.load(f)
                fallback = fallback_msgs["_metadata"]["fallback"]
                for key, message in fallback_msgs.items():
                    if key not in self.messages:
                        self.messages[key] = message

        if not os.path.isfile(os.path.join(ROOT_DIR, "messages.json")):
            return
        with open(os.path.join(ROOT_DIR, "messages.json"), encoding="utf-8") as f:
            custom_msgs = json.load(f)

        if not custom_msgs:
            return

        for key, message in custom_msgs.items():
            if key in self.messages:
                if isinstance(self.messages[key], dict):
                    if not isinstance(message, dict):
                        raise TypeError("messages.json: Key {0!r} must be of type dict".format(key))
                    self.messages[key].update(message)
                elif isinstance(self.messages[key], list):
                    if not isinstance(message, (list, dict)):
                        raise TypeError("messages.json: Key {0!r} must be of type list or dict (with merge_strategy and value keys)".format(key))

                    if isinstance(message, list):
                        self.messages[key] = message
                    elif message["merge_strategy"] == "extend":
                        self.messages[key].extend(message["value"])
                    elif message["merge_strategy"] == "replace":
                        self.messages[key] = message["value"]
                else:
                    if not isinstance(message, type(self.messages[key])):
                        raise TypeError("messages.json: Key {0!r} must be of type {1!r}".format(key, type(
                            self.messages[key]).__name__))
                    self.messages[key] = message
            else:
                self.messages[key] = message

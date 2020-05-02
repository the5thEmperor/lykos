import traceback
import threading
import string
import random
import json
import re
import os.path
import functools
from typing import Optional, Iterable

import urllib.request, urllib.parse

from collections import defaultdict

import botconfig
import src.settings as var
import src
from src.functions import get_players
from src.messages import messages
from src import channels, users, logger, errlog, events
from src.users import User
from src.dispatcher import MessageDispatcher

adminlog = logger.logger("audit.log")

COMMANDS = defaultdict(list)
HOOKS = defaultdict(list)

# Error handler decorators and context managers

class _local(threading.local):
    handler = None
    level = 0

_local = _local()

# This is a mapping of stringified tracebacks to (link, uuid) tuples
# That way, we don't have to call in to the website everytime we have
# another error.

_tracebacks = {}

class chain_exceptions:

    def __init__(self, exc, *, suppress_context=False):
        self.exc = exc
        self.suppress_context = suppress_context

    def __enter__(self):
        return self

    def __exit__(self, exc, value, tb):
        if exc is value is tb is None:
            return False

        value.__context__ = self.exc
        value.__suppress_context__ = self.suppress_context
        self.exc = value
        return True

    @property
    def traceback(self):
        return "".join(traceback.format_exception(type(self.exc), self.exc, self.exc.__traceback__))

class print_traceback:

    def __enter__(self):
        _local.level += 1
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is exc_value is tb is None:
            _local.level -= 1
            return False

        if not issubclass(exc_type, Exception):
            _local.level -= 1
            return False

        if _local.level > 1:
            _local.level -= 1
            return False # the outermost caller should handle this

        variables = ["", None]

        if _local.handler is None:
            _local.handler = chain_exceptions(exc_value)

        if var.TRACEBACK_VERBOSITY > 0:
            word = "\nLocal variables from frame #{0} (in {1}):\n"
            variables.append(None)
            frames = []

            while tb is not None:
                ignore_locals = not tb.tb_frame.f_locals or tb.tb_frame.f_locals.get("_ignore_locals_")
                # also ignore locals for library code
                if "/lib/" in tb.tb_frame.f_code.co_filename.replace("\\", "/"):
                    ignore_locals = True
                if tb.tb_next is not None and ignore_locals:
                    frames.append(None)
                else:
                    frames.append(tb.tb_frame)
                tb = tb.tb_next

            if var.TRACEBACK_VERBOSITY < 2:
                word = "Local variables from innermost frame (in {1}):\n"
                frames = [frames[-1]]

            with _local.handler:
                for i, frame in enumerate(frames, start=1):
                    if frame is None:
                        continue
                    variables.append(word.format(i, frame.f_code.co_name))
                    for name, value in frame.f_locals.items():
                        try:
                            if isinstance(value, dict):
                                try:
                                    log_value = "{{{0}}}".format(", ".join("{0:for_tb}: {1:for_tb}".format(k, v) for k, v in value.items()))
                                except:
                                    try:
                                        log_value = "{{{0}}}".format(", ".join("{0!r}: {1:for_tb}".format(k, v) for k, v in value.items()))
                                    except:
                                        log_value = "{{{0}}}".format(", ".join("{0:for_tb}: {1!r}".format(k, v) for k, v in value.items()))
                            elif isinstance(value, list):
                                log_value = "[{0}]".format(", ".join(format(v, "for_tb") for v in value))
                            elif isinstance(value, set):
                                log_value = "{{{0}}}".format(", ".join(format(v, "for_tb") for v in value))
                            else:
                                log_value = format(value, "for_tb")
                        except:
                            log_value = repr(value)
                        variables.append("{0} = {1}".format(name, log_value))

            if len(variables) > 3:
                variables.append("\n")
                if var.TRACEBACK_VERBOSITY > 1:
                    variables[2] = "Local variables in all frames (most recent call last):"
                else:
                    variables[2] = ""
            else:
                variables[2] = "No local variables found in all frames."

        variables[1] = _local.handler.traceback
        errlog("\n".join(variables))

        # sanitize paths in tb: convert backslash to forward slash and remove prefixes from src and library paths
        variables[1] = variables[1].replace("\\", "/")
        variables[1] = re.sub(r'File "[^"]*/(src|gamemodes|oyoyo|roles|lib|wolfbot)', r'File "/\1', variables[1])

        # sanitize values within local frames
        if len(variables) > 3:
            for i in range(3, len(variables)):
                # strip filenames out of module printouts
                variables[i] = re.sub(r"<(module .*?) from .*?>", r"<\1>", variables[i])

        if channels.Main is not channels.Dev:
            channels.Main.send(messages["error_log"])
        message = [str(messages["error_log"])]

        link = _tracebacks.get("\n".join(variables))
        if link is None:
            api_url = "https://ww.chat/submit"
            data = None
            with _local.handler:
                req = urllib.request.Request(api_url, json.dumps({
                        "c": "\n".join(variables),  # contents
                    }).encode("utf-8", "replace"))

                req.add_header("Accept", "application/json")
                req.add_header("Content-Type", "application/json; charset=utf-8")
                resp = urllib.request.urlopen(req)
                data = json.loads(resp.read().decode("utf-8"))

            if data is None:  # couldn't fetch the link
                message.append(messages["error_pastebin"])
                errlog(_local.handler.traceback)
            else:
                link = _tracebacks["\n".join(variables)] = data["url"]
                message.append(link)

        else:
            message.append(link)

        if channels.Dev is not None:
            channels.Dev.send(" ".join(message), prefix=botconfig.DEV_PREFIX)

        _local.level -= 1
        if not _local.level: # outermost caller; we're done here
            _local.handler = None

        return True # a true return value tells the interpreter to swallow the exception

class handle_error:

    def __new__(cls, func=None, *, instance=None):
        if isinstance(func, cls) and instance is func.instance: # already decorated
            return func

        if isinstance(func, cls):
            func = func.func

        self = super().__new__(cls)
        self.instance = instance
        self.func = func
        return self

    def __get__(self, instance, owner):
        if instance is not self.instance:
            return type(self)(self.func, instance=instance)
        return self

    def __call__(*args, **kwargs):
        _ignore_locals_ = True
        self, *args = args
        if self.instance is not None:
            args = [self.instance] + args
        with print_traceback():
            return self.func(*args, **kwargs)
            return self.func(*args, **kwargs)

class command:
    def __init__(self, command: str, *, flag: Optional[str] = None, owner_only: bool = False,
                 chan: bool = True, pm: bool = False, playing: bool = False, silenced: bool = False,
                 phases: Iterable[str] = (), roles: Iterable[str] = (), users: Iterable[User] = None):

        # the "d" flag indicates it should only be enabled in debug mode
        if flag == "d" and not botconfig.DEBUG_MODE:
            return

        # handle command localizations
        commands = messages.raw("_commands")[command]

        self.commands = frozenset(commands)
        self.flag = flag
        self.owner_only = owner_only
        self.chan = chan
        self.pm = pm
        self.playing = playing
        self.silenced = silenced
        self.phases = phases
        self.roles = roles
        self.users = users # iterable of users that can use the command at any time (should be a mutable object)
        self.func = None
        self.aftergame = False
        self.name = commands[0]
        self.key = command
        self.alt_allowed = bool(flag or owner_only)

        alias = False
        self.aliases = []

        if var.DISABLED_COMMANDS.intersection(commands):
            return # command is disabled, do not add to COMMANDS

        for name in commands:
            for func in COMMANDS[name]:
                if func.owner_only != owner_only or func.flag != flag:
                    raise ValueError("unmatching access levels for {0}".format(func.name))

            COMMANDS[name].append(self)
            if name in botconfig.ALLOWED_ALT_CHANNELS_COMMANDS:
                self.alt_allowed = True
            if name in getattr(botconfig, "OWNERS_ONLY_COMMANDS", ()):
                self.owner_only = True
            if alias:
                self.aliases.append(name)
            alias = True

        if playing: # Don't restrict to owners or allow in alt channels
            self.owner_only = False
            self.alt_allowed = False

    def __call__(self, func):
        if isinstance(func, command):
            func = func.func
        self.func = func
        self.__doc__ = func.__doc__
        return self

    @handle_error
    def caller(self, var, wrapper: MessageDispatcher, message: str):
        _ignore_locals_ = True
        if (not self.pm and wrapper.private) or (not self.chan and wrapper.public):
            return # channel or PM command that we don't allow

        if wrapper.public and wrapper.target is not channels.Main and not (self.flag or self.owner_only):
            if "" in self.commands or not self.alt_allowed:
                return # commands not allowed in alt channels

        if "" in self.commands:
            self.func(var, wrapper, message)
            return

        if self.phases and var.PHASE not in self.phases:
            return

        wrapper.source.update_account_data(self.key, functools.partial(self._thunk, var, wrapper, message))

    @handle_error
    def _thunk(self, var, wrapper: MessageDispatcher, message: str, user: User):
        _ignore_locals_ = True
        wrapper.source = user
        self._caller(var, wrapper, message)

    @handle_error
    def _caller(self, var, wrapper: MessageDispatcher, message: str):
        _ignore_locals_ = True
        if self.playing and (wrapper.source not in get_players() or wrapper.source in var.DISCONNECTED):
            return

        for role in self.roles:
            if wrapper.source in var.ROLES[role]:
                break
        else:
            if (self.users is not None and wrapper.source not in self.users) or self.roles:
                return

        if self.silenced and src.status.is_silent(var, wrapper.source):
            wrapper.pm(messages["silenced"])
            return

        if self.playing or self.roles or self.users:
            self.func(var, wrapper, message) # don't check restrictions for game commands
            # Role commands might end the night if it's nighttime
            if var.PHASE == "night":
                from src.wolfgame import chk_nightdone
                chk_nightdone()
            return

        if self.owner_only:
            if wrapper.source.is_owner():
                adminlog(wrapper.target.name, wrapper.source.rawnick, self.name, message)
                self.func(var, wrapper, message)
                return

            wrapper.pm(messages["not_owner"])
            return

        temp = wrapper.source.lower()

        flags = var.FLAGS_ACCS[temp.account] # TODO: add flags handling to User

        if self.flag and (wrapper.source.is_admin() or wrapper.source.is_owner()):
            adminlog(wrapper.target.name, wrapper.source.rawnick, self.name, message)
            return self.func(var, wrapper, message)

        denied_commands = var.DENY_ACCS[temp.account] # TODO: add denied commands handling to User

        if self.commands & denied_commands:
            wrapper.pm(messages["invalid_permissions"])
            return

        if self.flag:
            if self.flag in flags:
                adminlog(wrapper.target.name, wrapper.source.rawnick, self.name, message)
                self.func(var, wrapper, message)
                return

            wrapper.pm(messages["not_an_admin"])
            return

        self.func(var, wrapper, message)

class hook:
    def __init__(self, name, hookid=-1):
        self.name = name
        self.hookid = hookid
        self.func = None

        HOOKS[name].append(self)

    def __call__(self, func):
        if isinstance(func, hook):
            self.func = func.func
        else:
            self.func = func
        self.__doc__ = self.func.__doc__
        return self

    @handle_error
    def caller(self, *args, **kwargs):
        _ignore_locals_ = True
        return self.func(*args, **kwargs)

    @staticmethod
    def unhook(hookid):
        for each in list(HOOKS):
            for inner in list(HOOKS[each]):
                if inner.hookid == hookid:
                    HOOKS[each].remove(inner)
            if not HOOKS[each]:
                del HOOKS[each]

class event_listener:
    def __init__(self, event, priority=5, listener_id=None):
        self.event = event
        self.priority = priority
        self.func = None
        self.listener_id = listener_id
        self.listener = None # type: Optional[events.EventListener]

    def __call__(self, *args, **kwargs):
        if self.func is None:
            func = args[0]
            if isinstance(func, event_listener):
                func = func.func
            if self.listener_id is None:
                self.listener_id = func.__qualname__
            # always prefix with module for disambiguation if possible
            if func.__module__ is not None:
                self.listener_id = func.__module__ + "." + self.listener_id
            self.func = handle_error(func)
            self.listener = events.EventListener(self.func, priority=self.priority, listener_id=self.listener_id)
            self.listener.install(self.event)
            self.__doc__ = self.func.__doc__
            return self
        else:
            return self.func(*args, **kwargs)

    def remove(self):
        self.listener.remove(self.event)


# /usr/bin/python
# encoding: utf-8
from __future__ import unicode_literals

from os import getenv
from os.path import curdir, join
from workflow.util import set_config

try:
    from typing import Any, Dict, List
    from types import FunctionType
except ImportError:
    pass

from workflow import Workflow3
from workflow.background import run_in_background, is_running

from workflow import ICON_ERROR, ICON_WEB, ICON_INFO

Str = str or unicode

SEARCH_DOT = "⬜️"
SEARCH_DOT_SELECTED = "️⬛️"
SEARCH_LENGTH = 5

LOADING_BRAILLE = [
    '⠧',
    '⠏',
    '⠛',
    '⠹',
    '⠼',
    '⠶'
]

EMOJI_DIR = join(curdir, "icons")


class Icon(object):
    GAME = join(EMOJI_DIR, "game.svg")
    PRODUCT = join(EMOJI_DIR, "product.svg")
    PROGRAM = join(EMOJI_DIR, "program.svg")
    STATE = join(EMOJI_DIR, "state.svg")

    GEAR = join(EMOJI_DIR, "gear.png")
    LINK = join(EMOJI_DIR, "link.png")
    VIDEO_GAME = join(EMOJI_DIR, "video-game.png")
    TECHNOLOGIST = join(EMOJI_DIR, "technologist.png")
    PAGE_FACING_UP = join(EMOJI_DIR, "page-facing-up.png")
    DESKTOP_COMPUTER = join(EMOJI_DIR, "desktop-computer.png")
    BUSTS_IN_SILHOUETTE = join(EMOJI_DIR, "busts-in-silhouette.png")
    MAGNIFYING_GLASS_TILTED_LEFT = join(EMOJI_DIR, "magnifying-glass-tilted-left.png")

    ERROR = ICON_ERROR
    WEB = ICON_WEB
    INFO = ICON_INFO

    DIR = join(curdir, "image")


# MAX_AGE at the bottom of the file

PROGRAMS = "programs"
GAMES = "games"
UPDATES = "CHECK_UPDATE"

PREFIXES = {
    "id": "id",
    'p': PROGRAMS,
    'g': GAMES,
    's': "FORCE_SEARCH",
    "u": UPDATES
}
PREFIX_SYMBOL_END = ':'

LIBRARIES = [
    "./lib",
    "./venv/lib/site-packages"
]

LOADINGS = []


def add_to_loading(func):
    # type: (FunctionType) -> FunctionType
    LOADINGS.append(func)
    return func


def get_var_boolean(key, default=False):
    # type: (Str, bool or Str) -> bool
    a = get_var(key, default)
    if not a:
        return default
    return a in ("yes", "on", '1', "true", True)


def get_var_numeric(key, default=None):
    # type: (Str, int or float) -> int or float
    a = get_var(key, default)
    try:
        return int(a)
    except ValueError:
        try:
            return float(a)
        except ValueError:
            return default


def get_var(key, default=None):
    # type: (Str, Str) -> Str
    f = getenv(key)
    return f.strip().lower() if f else default


def set_var(key, value):
    # type: (Str, Str) -> None
    return set_config(key, value)


def set_var_boolean(key, value):
    # type: (Str, bool or Str) -> None
    return set_var(key, value in ("yes", "on", '1', "true", True))


def word_with_number(number):
    # type: (int) -> Str
    if number % 10 == 1:
        return 'а'
    if number % 10 in range(2, 5):
        return 'ы'
    return ''


class Workflow(Workflow3):
    def __init__(self, **kwargs):
        Workflow3.__init__(self, **kwargs)
        self.magic_prefix = 'S' + PREFIX_SYMBOL_END

    def get_background_data(self, name, data_func=None, max_age=0, task=None, args=None,
                            rerun_item=None, rerun=0.1):
        # type: (Workflow, Str, FunctionType or None, int, Str, List, Dict, float or int) -> Any
        if args is None:
            args = []
        if not isinstance(args, list):
            args = list(args) if isinstance(args, tuple) else [args]
        if rerun_item is None:
            rerun_item = {}
        if task is None:
            task = name

        data = self.cached_data(name, data_func, 0)
        self.logger.debug("Is `%s` running: %s", name, is_running(name))

        if max_age and not self.cached_data_fresh(name, max_age):
            if get_var_boolean("SUPER_DEBUG"):
                Task.wf = self
                self.logger.info("Start task: %s; %s", task, args)
                return Task.run(task, *args)

            else:
                self.logger.info("Start task: %s; %s", task, args)
                cmd = ['/usr/bin/python', self.workflowfile("update.py"), task] + args
                d = run_in_background(name, cmd)
                self.logger.info("Start task: %s; %s (%s)", task, args, d)

        if is_running(name):
            if rerun_item and "title" in rerun_item:
                lt = get_var("LOADING_TYPE", '0')
                lt = int(lt) if lt.isdigit() else 0
                lt = lt if lt in range(len(LOADINGS)) else 0
                rerun_item["subtitle"] = LOADINGS[lt](self)
                self.add_item(**rerun_item)
            self.rerun = rerun
            return None
        return data


class Task(object):
    _tasks = {}  # type: Dict[Str, FunctionType]
    wf = None  # type: Workflow

    def __init__(self, name_of_task):
        # type: (Task, Str) -> None
        self.task = name_of_task

    def __call__(self, func):
        # type: (Task, FunctionType) -> FunctionType
        self._tasks[self.task] = func
        return func

    @classmethod
    def run(cls, task, *args):
        # type: (Task, Str, Str) -> Any
        if not isinstance(cls.wf, Workflow):
            raise TypeError('Type of "wf" is "%s". "%s" required' % (
                type(cls.wf).__name__, type(Workflow).__name__
            ))
        if task in cls._tasks:
            cls.wf.logger.warning("Start TASK: %s %s", task, args)
            return cls._tasks.get(task)(cls.wf, *args)


MAX_AGE = get_var_numeric("MAX_AGE", 60 * 60 * 24)
# MAX_AGE = 0

"""키 설정, 키보드 입력, 입력 버퍼(콤보 명령 판정).

게임 로직은 실제 키 대신 'up', 'punch' 같은 추상 동작만 본다.
P1/P2와 컴퓨터(AI)는 모두 같은 InputFrame을 만들어 캐릭터에 넘긴다.
"""
import json
import sys
from collections import deque

import pygame

from settings import CONFIG_PATH, MOTION_WINDOW, SUPER_WINDOW

ACTIONS = ["up", "down", "left", "right", "punch", "kick"]
ACTION_NAMES = {"up": "위", "down": "아래", "left": "왼쪽", "right": "오른쪽",
                "punch": "팔 공격", "kick": "발 공격"}
BUTTONS = ("punch", "kick")

DEFAULT_KEYS = {
    1: {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d,
        "punch": pygame.K_f, "kick": pygame.K_g},
    2: {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
        "punch": pygame.K_k, "kick": pygame.K_l},
}

ARROW_NAMES = {"up": "↑", "down": "↓", "left": "←", "right": "→"}


DEFAULT_OPTIONS = {"show_commands": True}
STORAGE_KEY = "kwon-jok-cham-config"


def _read_saved():
    """저장된 설정 글(JSON). 브라우저(pygbag)에서는 파일 대신 localStorage를 쓴다.
    브라우저 안의 파일은 새로고침하면 사라지기 때문이다."""
    if sys.platform == "emscripten":
        import platform
        return platform.window.localStorage.getItem(STORAGE_KEY)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return f.read()


def _write_saved(text):
    if sys.platform == "emscripten":
        import platform
        platform.window.localStorage.setItem(STORAGE_KEY, text)
        return
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(text)


class KeyConfig:
    """P1/P2 키 배치와 게임 설정. config.json에 저장하고 다음 실행 때 불러온다."""

    def __init__(self):
        self.keys = {p: dict(k) for p, k in DEFAULT_KEYS.items()}
        self.options = dict(DEFAULT_OPTIONS)
        self.load()

    def load(self):
        try:
            data = json.loads(_read_saved())
            for name, value in data.get("options", {}).items():
                if name in DEFAULT_OPTIONS and isinstance(value, type(DEFAULT_OPTIONS[name])):
                    self.options[name] = value
            for p in (1, 2):
                for action in ACTIONS:
                    key = data["keys"][str(p)][action]
                    if isinstance(key, int):
                        self.keys[p][action] = key
        except Exception:
            pass  # 저장된 설정이 없거나 깨졌으면 기본값 사용

    def save(self):
        data = {"keys": {str(p): self.keys[p] for p in (1, 2)}, "options": self.options}
        try:
            _write_saved(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            pass   # 저장하지 못해도 게임은 계속한다

    def reset(self):
        self.keys = {p: dict(k) for p, k in DEFAULT_KEYS.items()}
        self.save()

    def assign(self, player, action, key):
        """키를 배정한다. 이미 다른 동작에 쓰이던 키라면 두 동작의 키를 서로 바꾼다."""
        old = self.keys[player][action]
        for p in (1, 2):
            for a in ACTIONS:
                if self.keys[p][a] == key and (p, a) != (player, action):
                    self.keys[p][a] = old
        self.keys[player][action] = key
        self.save()

    def key_name(self, player, action):
        return key_label(self.keys[player][action])


def key_label(key):
    name = pygame.key.name(key)
    if name in ARROW_NAMES:
        return ARROW_NAMES[name]
    return name.upper() if len(name) <= 2 else name.title()


class InputFrame:
    """한 틱 동안의 입력: 누르고 있는 방향 + 이번 틱에 새로 누른 버튼."""
    __slots__ = ("up", "down", "left", "right", "pressed")

    def __init__(self, up=False, down=False, left=False, right=False, pressed=()):
        self.up, self.down, self.left, self.right = up, down, left, right
        self.pressed = set(pressed)

    @property
    def x(self):
        # 왼쪽·오른쪽을 같이 누르면 중립으로 본다
        return (1 if self.right else 0) - (1 if self.left else 0)


EMPTY_INPUT = InputFrame()


class KeyboardController:
    def __init__(self, player, config):
        self.player = player
        self.config = config

    def read(self, held, pressed_keys):
        k = self.config.keys[self.player]
        return InputFrame(held[k["up"]], held[k["down"]], held[k["left"]], held[k["right"]],
                          [b for b in BUTTONS if k[b] in pressed_keys])


def numpad(x_rel, up, down):
    """방향을 숫자패드 표기로 바꾼다. 6 = 앞, 4 = 뒤, 2 = 아래, 3 = 앞아래."""
    return 5 + x_rel + (3 if up and not down else 0) - (3 if down and not up else 0)


# 명령 이름 → 순서대로 거쳐야 하는 방향(앞 기준)
MOTIONS = {
    "236236": [{2}, {3}, {6}, {2}, {3}, {6}],
    "623": [{6}, {2}, {3}],
    "236": [{2}, {3}, {6}],
    "214": [{2}, {1}, {4}],
}


class InputBuffer:
    """최근 입력 기록. 방향은 캐릭터가 보는 쪽 기준 숫자로 저장해 좌우가 바뀌어도 같은 명령이 된다."""

    def __init__(self):
        self.hist = deque(maxlen=48)

    def push(self, num, pressed):
        self.hist.append((num, frozenset(pressed)))

    def motion(self, name):
        """명령이 입력됐으면 완성된 위치(클수록 최근)를, 아니면 -1을 돌려준다.
        →↓↘(623)와 ↓↘→(236)가 겹칠 때 더 최근에 완성된 쪽을 고르는 데 쓴다."""
        seq = MOTIONS[name]
        window = SUPER_WINDOW if len(seq) > 3 else MOTION_WINDOW
        i = 0
        for pos, (num, _) in enumerate(list(self.hist)[-window:]):
            if num in seq[i]:
                i += 1
                if i == len(seq):
                    return pos
        return -1

    def clear(self):
        """필살기가 나간 뒤 같은 방향 입력으로 또 나가지 않게 기록을 비운다."""
        self.hist.clear()

    def recent(self, n):
        return list(self.hist)[-n:]

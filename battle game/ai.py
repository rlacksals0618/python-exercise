"""컴퓨터 상대(PVE). 사람과 똑같이 가상 키 입력(InputFrame)을 만들어 캐릭터를 조작한다."""
import random
from collections import deque

from controls import InputFrame
from fighter import AIR, ATTACK, BLOCKSTUN, CROUCH, IDLE, JUGGLE, WALK
from settings import SUPER_MAX

LEVELS = {
    # react: 상대 행동을 알아차리기까지의 지연(틱), think: 다시 판단하는 간격
    "쉬움": dict(react=22, think=20, block=0.15, combo=0.25, special=0.15, anti_air=0.1, aggro=0.35),
    "보통": dict(react=13, think=11, block=0.45, combo=0.6, special=0.3, anti_air=0.35, aggro=0.55),
    "어려움": dict(react=7, think=5, block=0.8, combo=0.9, special=0.45, anti_air=0.7, aggro=0.7),
}

# 숫자패드 방향 → (앞뒤, 아래, 위)
DIRS = {1: (-1, True, False), 2: (0, True, False), 3: (1, True, False), 4: (-1, False, False),
        5: (0, False, False), 6: (1, False, False), 7: (-1, False, True), 8: (0, False, True),
        9: (1, False, True)}


class AIController:
    def __init__(self, me, opp, level="보통"):
        self.me, self.opp = me, opp
        self.p = LEVELS[level]
        self.queue = deque()
        self.hold = 5           # 계획이 없을 때 계속 누르고 있을 방향
        self.hold_ticks = 0
        self.think_cd = 0
        self.seen = deque(maxlen=40)
        self.continued = None   # 이미 콤보를 이어 준 기술(같은 기술에서 두 번 잇지 않게)

    # ── 계획 만들기 ──
    def _push(self, num, press=(), ticks=1):
        for i in range(ticks):
            self.queue.append((num, press if i == 0 else ()))

    def _motion(self, seq, btn):
        for n in seq[:-1]:
            self._push(n, ticks=2)
        self._push(seq[-1], (btn,), 1)
        self._push(seq[-1], ticks=2)

    def _hold(self, num, ticks):
        self.hold, self.hold_ticks = num, ticks

    def _observe(self):
        o, m = self.opp, self.me
        self.seen.append(dict(dist=abs(o.pos.x - m.pos.x), threat=o.threatening,
                              low=o.threatening and o.move.level == "low",
                              overhead=o.threatening and o.move.level == "overhead",
                              air=not o.on_ground and o.state in (AIR, ATTACK), rising=o.vel.y < 0))
        delay = self.p["react"]
        return self.seen[-delay] if len(self.seen) >= delay else self.seen[0]

    def _decide(self, view):
        me, p = self.me, self.p
        r = random.random
        dist = view["dist"]

        if not me.on_ground:
            if dist < 170 and me.vel.y > 0:
                self._push(5, (random.choice(["punch", "kick"]),))
            return
        # 상대 공격이 보이면 막는다
        if view["threat"] and dist < 260 and r() < p["block"]:
            self._hold(1 if view["low"] else 4, 14)
            return
        # 상대가 뛰어들면 대공기
        if view["air"] and dist < 170 and r() < p["anti_air"]:
            self._motion([6, 2, 3], "punch")
            return
        if me.super >= SUPER_MAX and dist < 230 and r() < p["special"]:
            self._motion([2, 3, 6, 2, 3, 6], "punch")
            return

        if dist > 300:
            choice = r()
            if choice < 0.12 * p["aggro"] * 2:
                self._push(9, ticks=1)          # 앞으로 점프
                self._hold(9, 7)
            elif choice < 0.12 + p["special"] * 0.4 and me.style == "sword":
                self._motion([2, 3, 6], "punch")  # 돌진 베기
            else:
                self._hold(6, random.randint(12, 26))
        elif dist > 150:
            choice = r()
            if choice < p["special"] * 0.6:
                self._motion([2, 3, 6], random.choice(["punch", "kick"]))
            elif choice < p["special"] * 0.6 + 0.2:
                self._push(6, ("punch",) if r() < 0.5 else ("kick",))
            elif choice < 0.55 + p["aggro"] * 0.3:
                self._hold(6, random.randint(8, 18))
            elif choice < 0.85:
                self._hold(4, random.randint(6, 14))
            else:
                self._push(9, ticks=1)
                self._hold(9, 7)
        else:
            choice = r()
            if choice < p["aggro"] * 0.45:
                self._push(5, ("punch",))       # 콤보 시작 (맞으면 아래에서 이어 준다)
            elif choice < p["aggro"] * 0.65:
                self._push(5, ("kick",))
            elif choice < p["aggro"] * 0.8:
                self._push(2, ("kick",))        # 하단 쓸기
            elif choice < p["aggro"] * 0.8 + p["special"] * 0.4:
                self._motion(random.choice([[2, 1, 4], [2, 3, 6]]), random.choice(["punch", "kick"]))
            elif choice < 0.85:
                self._hold(1 if r() < 0.5 else 4, random.randint(8, 16))
            else:
                self._hold(4, random.randint(10, 20))

    def _continue_combo(self):
        """내 공격이 맞았으면 연결기나 필살기로 잇는다."""
        me = self.me
        if not (me.state == ATTACK and me.cancel_ok) or self.continued is me.move or self.queue:
            return
        self.continued = me.move
        if random.random() > self.p["combo"]:
            return
        mv = me.move
        if mv.chain:
            btn = next(iter(mv.chain))
            self._push(5, (btn,))
        elif mv.kind in ("normal", "chain") and random.random() < 0.7:
            if me.super >= SUPER_MAX and random.random() < 0.5:
                self._motion([2, 3, 6, 2, 3, 6], "punch")
            else:
                self._motion(random.choice([[2, 3, 6], [6, 2, 3]]), "punch")

    # ── 매 틱 입력 ──
    def get_frame(self):
        me = self.me
        view = self._observe()
        self._continue_combo()
        if not self.queue:
            self.think_cd -= 1
            if self.hold_ticks > 0:
                self.hold_ticks -= 1
            elif self.think_cd <= 0 and me.state in (IDLE, WALK, CROUCH, BLOCKSTUN, AIR):
                self.think_cd = self.p["think"] + random.randint(0, 4)
                self.hold = 5
                self._decide(view)
            elif me.state not in (BLOCKSTUN,):
                self.hold = 5
            # 이미 막는 중이면 경직이 끝날 때까지 계속 막는다
            if me.state == BLOCKSTUN and self.hold not in (1, 4):
                self.hold = 1 if view["low"] else 4
        if self.queue:
            num, press = self.queue.popleft()
        else:
            num, press = self.hold, ()
        if me.state == JUGGLE:
            num, press = 5, ()
        fx, down, up = DIRS[num]
        x = fx * me.facing
        return InputFrame(up=up, down=down, left=x < 0, right=x > 0, pressed=press)

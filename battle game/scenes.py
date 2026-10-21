"""화면(씬) 모음: 타이틀 → 모드 선택 → 캐릭터 선택 → 스테이지 선택 → 전투 → 결과.
일시정지·기술표·설정·키 설정은 다른 화면 위에 덮어서 연다(씬 스택).
"""
import math
import random

import pygame

import ui
from ai import LEVELS, AIController
from camera import Camera, View
from characters import CHARACTERS
from controls import ACTION_NAMES, ACTIONS, EMPTY_INPUT, KeyboardController, key_label
from effects import Effects, ease_out_back
from fighter import ATTACK, BLOCKSTUN, HITSTUN, JUGGLE, KO, NEUTRAL, Fighter
from hud import HUD
from moves import COMBOS
from settings import (BODY_HALF_W, EFFECT_COLORS, GOLD, GROUND_Y, HITSTOP, INK, MAX_SEPARATION, P_COLORS,
                      ROUND_TIME, ROUNDS_TO_WIN, SCREEN_H, SCREEN_W, SHAKE, STAGE_LEFT, STAGE_RIGHT, WHITE)
from stages import STAGES

FLAT_VIEW = View()   # 확대 없이 그대로 그리는 보기(캐릭터 선택 카드용)

CONFIRM = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)
CANCEL = (pygame.K_ESCAPE, pygame.K_BACKSPACE)


def nav(app, e, players=(1, 2), arrows=True):
    """메뉴 조작 키를 'up'/'down'/'left'/'right'/'ok'/'back'으로 바꾼다."""
    if e.type != pygame.KEYDOWN:
        return None
    k = e.key
    if arrows:
        arrow = {pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_LEFT: "left", pygame.K_RIGHT: "right"}
        if k in arrow:
            return arrow[k]
        if k in CONFIRM:
            return "ok"
        if k in CANCEL:
            return "back"
    for p in players:
        keys = app.config.keys[p]
        for action in ("up", "down", "left", "right"):
            if k == keys[action]:
                return action
        if k == keys["punch"]:
            return "ok"
        if k == keys["kick"]:
            return "back"
    return None


class Scene:
    overlay = False

    def __init__(self, app):
        self.app = app
        self.t = 0

    def handle_event(self, e):
        pass

    def update(self):
        self.t += 1

    def draw(self, surf, alpha):
        pass


class SceneManager:
    def __init__(self):
        self.stack = []

    def push(self, scene):
        self.stack.append(scene)

    def pop(self):
        if len(self.stack) > 1:
            self.stack.pop()

    def replace(self, scene):
        self.stack = [scene]

    @property
    def top(self):
        return self.stack[-1]

    def handle_event(self, e):
        self.top.handle_event(e)

    def update(self):
        self.top.update()

    def draw(self, surf, alpha):
        start = len(self.stack) - 1
        while start > 0 and self.stack[start].overlay:
            start -= 1
        for scene in self.stack[start:]:
            scene.draw(surf, alpha if scene is self.top else 1.0)


def hint(surf, text):
    ui.draw_text(surf, text, 20, (90, 80, 70), (SCREEN_W / 2, SCREEN_H - 28), outline=0)


# ── 타이틀 ──
class TitleScene(Scene):
    def handle_event(self, e):
        if nav(self.app, e) in ("ok",) or (e.type == pygame.KEYDOWN and e.key not in CANCEL and self.t > 30):
            self.app.manager.replace(ModeSelectScene(self.app))
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.running = False

    def draw(self, surf, alpha):
        surf.blit(self.app.paper, (0, 0))
        for i, kind in enumerate(("fist", "foot", "slash")):
            t = max(0.0, min(1.0, (self.t - i * 10) / 26))
            if t <= 0:
                continue
            size = int(300 * (0.5 + 0.5 * ease_out_back(t)))
            img = self.app.images.get(kind, size)
            bob = math.sin(self.t * 0.04 + i * 2.1) * 6
            surf.blit(img, img.get_rect(center=(340 + i * 300, 290 + bob)))
        if self.t > 30:
            a = min(255, (self.t - 30) * 10)
            ui.draw_text(surf, "권 · 족 · 참", 92, (250, 244, 230), (SCREEN_W / 2, 520), kind="heavy",
                         outline=5, alpha=a)
            ui.draw_text(surf, "拳 · 足 · 斬   붓으로 겨루는 격투", 26, (120, 40, 36), (SCREEN_W / 2, 588),
                         outline=0, alpha=a)
        if self.t > 50 and (self.t // 30) % 2 == 0:
            ui.draw_text(surf, "아무 키나 눌러 시작", 28, INK, (SCREEN_W / 2, 650), outline=0)


# ── 모드 선택 ──
class ModeSelectScene(Scene):
    MAIN = ["PVP 대전 (2인)", "PVE 대전 (컴퓨터)", "기술표", "설정", "종료"]
    DESC = {"PVP 대전 (2인)": "한 키보드로 두 사람이 대전합니다.",
            "PVE 대전 (컴퓨터)": "컴퓨터와 대전합니다. 난이도를 고릅니다.",
            "기술표": "캐릭터별 기술과 콤보, 선딜·후딜을 확인합니다.",
            "설정": "전투 중 커맨드 표시를 켜고 끄거나, 키 배치를 바꿉니다.",
            "종료": "게임을 끝냅니다."}

    def __init__(self, app):
        super().__init__(app)
        self.menu = ui.Menu(self.MAIN, (SCREEN_W / 2, 380))
        self.picking_level = False

    def handle_event(self, e):
        n = nav(self.app, e, players=(1,))
        if n == "up":
            self.menu.move(-1)
        elif n == "down":
            self.menu.move(1)
        elif n == "back":
            if self.picking_level:
                self._main()
            else:
                self.app.manager.replace(TitleScene(self.app))
        elif n == "ok":
            item = self.menu.selected
            if self.picking_level:
                if item == "뒤로":
                    self._main()
                else:
                    self.app.manager.replace(CharSelectScene(self.app, "pve", item))
            elif item == "PVP 대전 (2인)":
                self.app.manager.replace(CharSelectScene(self.app, "pvp"))
            elif item == "PVE 대전 (컴퓨터)":
                self.picking_level = True
                self.menu = ui.Menu(list(LEVELS) + ["뒤로"], (SCREEN_W / 2, 380))
                self.menu.index = 1
            elif item == "기술표":
                self.app.manager.push(MoveListScene(self.app, 0))
            elif item == "설정":
                self.app.manager.push(SettingsScene(self.app))
            elif item == "종료":
                self.app.running = False

    def _main(self):
        self.picking_level = False
        self.menu = ui.Menu(self.MAIN, (SCREEN_W / 2, 380))
        self.menu.index = 1

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf, alpha):
        surf.blit(self.app.paper, (0, 0))
        for i, kind in enumerate(("fist", "foot", "slash")):
            img = self.app.images.get(kind, 150)
            img = img.copy()
            img.set_alpha(70)
            surf.blit(img, img.get_rect(center=(160 + i * 480, 120)))
        title = "난이도 선택" if self.picking_level else "모드 선택"
        ui.ink_stroke(surf, 470, 810, 130, 70, (150, 30, 30), seed=2)
        ui.draw_text(surf, title, 48, (255, 246, 228), (SCREEN_W / 2, 130), kind="heavy", outline=3)
        self.menu.draw(surf)
        if self.picking_level:
            desc = {"쉬움": "반응이 느리고 콤보를 잘 쓰지 않습니다.", "보통": "적당히 막고 콤보를 섞어 씁니다.",
                    "어려움": "빠르게 반응하고 콤보와 필살기를 자주 씁니다.", "뒤로": "모드 선택으로 돌아갑니다."}
            text = desc[self.menu.selected]
        else:
            text = self.DESC[self.menu.selected]
        ui.draw_text(surf, text, 24, INK, (SCREEN_W / 2, 600), outline=0)
        hint(surf, "↑↓ 또는 W/S 선택   ·   Enter 또는 F 확인   ·   Esc 또는 G 뒤로")


# ── 캐릭터 선택 ──
class Cursor:
    def __init__(self, pid, index):
        self.pid, self.index, self.done = pid, index, False
        self.x = self.target_x(index)

    @staticmethod
    def target_x(i):
        return SCREEN_W / 2 + (i - 1.5) * 240

    def update(self):
        self.x += (self.target_x(self.index) - self.x) * 0.3


class CharSelectScene(Scene):
    def __init__(self, app, mode, level=None, picks=None, stage=0):
        super().__init__(app)
        self.mode, self.level, self.stage = mode, level, stage
        a, b = picks if picks else (0, 2)
        self.cursors = [Cursor(1, a), Cursor(2, b)]
        self.previews = []
        for i, ch in enumerate(CHARACTERS):
            f = Fighter(1, ch)
            f.pos.update(Cursor.target_x(i), 430)
            f.prev_pos = f.pos.copy()
            f.update_pose()
            self.previews.append(f)

    def _active_cursor_for_cpu(self):
        # PVE에서는 P1이 자기 캐릭터를 고른 뒤 같은 키로 컴퓨터 캐릭터를 고른다
        return self.cursors[1] if self.cursors[0].done else self.cursors[0]

    def handle_event(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key == pygame.K_ESCAPE:
            self.app.manager.replace(ModeSelectScene(self.app))
            return
        if self.mode == "pvp":
            for cur in self.cursors:
                self._control(cur, nav(self.app, e, players=(cur.pid,), arrows=False))
        else:
            self._control(self._active_cursor_for_cpu(), nav(self.app, e, players=(1,)), pve=True)

    def _control(self, cur, n, pve=False):
        if n is None:
            return
        if n == "back":
            if pve and cur.pid == 2 and not cur.done:
                self.cursors[0].done = False
            cur.done = False
            return
        if cur.done:
            return
        if n == "left":
            cur.index = (cur.index - 1) % len(CHARACTERS)
        elif n == "right":
            cur.index = (cur.index + 1) % len(CHARACTERS)
        elif n == "ok":
            cur.done = True
            self.previews[cur.index].win()
        if all(c.done for c in self.cursors):
            chars = [CHARACTERS[c.index] for c in self.cursors]
            self.app.manager.replace(StageSelectScene(self.app, chars, self.mode, self.level,
                                                      [c.index for c in self.cursors], self.stage))

    def update(self):
        super().update()
        for c in self.cursors:
            c.update()
        for i, f in enumerate(self.previews):
            if f.state == "WIN" and not any(c.done and c.index == i for c in self.cursors):
                f.reset_round()
                f.pos.update(Cursor.target_x(i), 430)
                f.prev_pos = f.pos.copy()
            f.inp = EMPTY_INPUT
            f.step()
            f.pos.update(Cursor.target_x(i), 430)
            f.update_pose()

    def draw(self, surf, alpha):
        surf.blit(self.app.paper, (0, 0))
        ui.ink_stroke(surf, 420, 860, 70, 64, (150, 30, 30), seed=5)
        ui.draw_text(surf, "캐릭터 선택", 44, (255, 246, 228), (SCREEN_W / 2, 70), kind="heavy", outline=3)
        for i, ch in enumerate(CHARACTERS):
            x = Cursor.target_x(i)
            card = pygame.Rect(0, 0, 200, 290)
            card.midbottom = (x, 470)
            ui.panel(surf, card, color=(60, 50, 44), alpha=60, radius=12)
            icon = self.app.images.get(ch.effect, 180)
            icon = icon.copy()
            icon.set_alpha(90)
            surf.blit(icon, icon.get_rect(center=(x, 330)))
            self.previews[i].draw(surf, alpha, FLAT_VIEW)
            ui.draw_text(surf, ch.name, 30, WHITE, (x, 205), kind="heavy", outline=3)
            ui.draw_text(surf, f"{ch.style_name} · {'남' if ch.gender == 'male' else '여'}", 20, INK,
                         (x, 492), outline=0)
        labels = {1: "1P", 2: "2P" if self.mode == "pvp" else "CPU"}
        same = self.cursors[0].index == self.cursors[1].index
        for k, c in enumerate(self.cursors):
            if self.mode == "pve" and c.pid == 2 and not self.cursors[0].done:
                continue
            col = P_COLORS[c.pid]
            off = (-6 if k == 0 else 6) if same else 0
            card = pygame.Rect(0, 0, 208 + abs(off) * 2, 298 + abs(off) * 2)
            card.midbottom = (c.x, 474 + abs(off))
            pygame.draw.rect(surf, col, card, 6 if c.done else 4, border_radius=14)
            tag = pygame.Rect(0, 0, 96 if c.done else 70, 34)
            tag.midbottom = (c.x + (-52 if k == 0 else 52) * (1 if same else 0), card.top + 2)
            pygame.draw.rect(surf, col, tag, border_radius=8)
            ui.draw_text(surf, labels[c.pid] + (" 확정" if c.done else ""), 20, WHITE, tag.center, kind="heavy")
        for k, c in enumerate(self.cursors):
            if self.mode == "pve" and c.pid == 2 and not self.cursors[0].done:
                continue
            self._info(surf, CHARACTERS[c.index], -1 if k == 0 else 1, P_COLORS[c.pid], labels[c.pid])
        if self.mode == "pvp":
            hint(surf, "P1: A/D 이동 · F 확정 · G 취소      P2: ←/→ 이동 · K 확정 · L 취소      Esc 뒤로")
        else:
            who = "컴퓨터 캐릭터를 고르세요" if self.cursors[0].done else "내 캐릭터를 고르세요"
            hint(surf, f"{who}   ·   ←/→ 이동 · Enter 확정 · G 취소 · Esc 뒤로")

    def _info(self, surf, ch, side, col, label):
        rect = pygame.Rect(0, 0, 420, 150)
        rect.center = (SCREEN_W / 2 + side * 330, 590)
        ui.panel(surf, rect, alpha=200, border=col)
        x = rect.left + 22
        ui.draw_text(surf, f"{label}  {ch.name}", 28, WHITE, (x, rect.top + 26), "midleft", "heavy")
        ui.draw_text(surf, ch.blurb, 20, (220, 210, 190), (x, rect.top + 58), "midleft")
        stats = [("체력", (ch.hp - 850) / 300), ("속도", (ch.speed - 0.85) / 0.35), ("공격력", (ch.power - 0.85) / 0.3)]
        for i, (name, k) in enumerate(stats):
            y = rect.top + 90 + i * 20
            ui.draw_text(surf, name, 16, (220, 210, 190), (x, y), "midleft", outline=0)
            pygame.draw.rect(surf, (70, 60, 60), (x + 70, y - 5, 300, 10))
            pygame.draw.rect(surf, col, (x + 70, y - 5, int(300 * max(0.1, min(1, k))), 10))



# ── 스테이지 선택 ──
class StageSelectScene(Scene):
    """전투 무대 고르기. 마지막 칸은 무작위. 고르면 VS 화면을 거쳐 전투로 들어간다."""

    def __init__(self, app, chars, mode, level, picks, index=0):
        super().__init__(app)
        self.chars, self.mode, self.level, self.picks = chars, mode, level, picks
        self.index = index
        self.cursor_x = self._x(index)
        self.vs_t = -1
        self.stage = None

    @staticmethod
    def _x(i):
        return SCREEN_W / 2 + (i - len(STAGES) / 2) * 196

    def handle_event(self, e):
        if self.vs_t >= 0 or e.type != pygame.KEYDOWN:
            return
        n = nav(self.app, e, players=(1, 2) if self.mode == "pvp" else (1,))
        count = len(STAGES) + 1
        if n == "left":
            self.index = (self.index - 1) % count
        elif n == "right":
            self.index = (self.index + 1) % count
        elif n == "back":
            self.app.manager.replace(CharSelectScene(self.app, self.mode, self.level, self.picks, self.index))
        elif n == "ok":
            self.stage = STAGES[self.index] if self.index < len(STAGES) else random.choice(STAGES)
            self.vs_t = 0

    def update(self):
        super().update()
        self.cursor_x += (self._x(self.index) - self.cursor_x) * 0.3
        if self.vs_t >= 0:
            self.vs_t += 1
            if self.vs_t > 80:
                self.app.manager.replace(BattleScene(self.app, self.chars, self.mode, self.level, self.stage))

    def draw(self, surf, alpha):
        surf.blit(self.app.paper, (0, 0))
        ui.ink_stroke(surf, 420, 860, 56, 60, (150, 30, 30), seed=9)
        ui.draw_text(surf, "스테이지 선택", 42, (255, 246, 228), (SCREEN_W / 2, 56), kind="heavy", outline=3)
        # 큰 미리보기
        big = pygame.Rect(0, 0, 704, 396)
        big.midtop = (SCREEN_W / 2, 100)
        pygame.draw.rect(surf, INK, big.inflate(10, 10), border_radius=10)
        if self.index < len(STAGES):
            st = STAGES[self.index]
            surf.blit(st.thumbnail(big.size), big)
            name, desc = st.name, st.desc
        else:
            pygame.draw.rect(surf, (60, 54, 50), big)
            ui.draw_text(surf, "?", 160, WHITE, big.center, kind="heavy", outline=4)
            name, desc = "무작위", "다섯 무대 중 하나를 무작위로 고릅니다"
        ui.draw_text(surf, name, 34, WHITE, (big.left + 24, big.bottom - 34), "midleft", "heavy", outline=3)
        ui.draw_text(surf, desc, 22, INK, (SCREEN_W / 2, big.bottom + 30), outline=0)
        # 아래쪽 작은 그림 줄
        for i in range(len(STAGES) + 1):
            r = pygame.Rect(0, 0, 176, 99)
            r.center = (self._x(i), 610)
            pygame.draw.rect(surf, INK, r.inflate(6, 6), border_radius=6)
            if i < len(STAGES):
                surf.blit(STAGES[i].thumbnail(r.size), r)
                label = STAGES[i].name
            else:
                pygame.draw.rect(surf, (60, 54, 50), r)
                ui.draw_text(surf, "?", 54, WHITE, r.center, kind="heavy")
                label = "무작위"
            ui.draw_text(surf, label, 18, WHITE, (r.centerx, r.bottom - 14), kind="heavy", outline=2)
        sel = pygame.Rect(0, 0, 190, 113)
        sel.center = (self.cursor_x, 610)
        pygame.draw.rect(surf, GOLD, sel, 5, border_radius=8)
        hint(surf, "←/→ 고르기   ·   Enter 또는 팔 공격 키로 확정   ·   발 공격 키로 캐릭터 선택으로")
        if self.vs_t >= 0:
            self._vs(surf)

    def _vs(self, surf):
        t = min(1.0, self.vs_t / 18)
        ui.dim(surf, int(170 * t))
        a, b = self.chars
        k = ease_out_back(t)
        ui.draw_text(surf, self.stage.name, 30, (230, 220, 200), (SCREEN_W / 2, 470), kind="heavy", outline=3,
                     alpha=int(255 * t))
        ui.draw_text(surf, a.name, 70, P_COLORS[1], (SCREEN_W / 2 - 300 * k, 360), kind="heavy", outline=4)
        ui.draw_text(surf, b.name, 70, P_COLORS[2], (SCREEN_W / 2 + 300 * k, 360), kind="heavy", outline=4)
        ui.draw_text(surf, "VS", 110, GOLD, (SCREEN_W / 2, 360), kind="heavy", outline=5, scale=0.6 + 0.4 * k)


# ── 전투 ──
class BattleScene(Scene):
    def __init__(self, app, chars, mode, level=None, stage=None):
        super().__init__(app)
        self.chars, self.mode, self.level = chars, mode, level
        self.stage = stage or STAGES[0]
        self.cam = Camera()
        # 같은 캐릭터끼리 붙으면 P2는 다른 색 옷을 입는다
        self.fighters = [Fighter(1, chars[0]), Fighter(2, chars[1], alt=chars[0] is chars[1])]
        f1, f2 = self.fighters
        self.controllers = [KeyboardController(1, app.config),
                            KeyboardController(2, app.config) if mode == "pvp" else AIController(f2, f1, level)]
        self.effects = Effects(app.images)
        self.hud = HUD(self.fighters, app.images, command_pids=(1, 2) if mode == "pvp" else (1,))
        self.pending = set()
        self.round = 1
        self.debug = False
        self.banner = None
        self.start_round()

    def start_round(self):
        for f in self.fighters:
            f.reset_round()
        self.cam.snap(self.fighters)
        self.effects.clear()
        self.hud.reset()
        self.timer = ROUND_TIME
        self.frames = 0
        self.hitstop = 0
        self.slowmo = 0
        self.phase, self.phase_t = "intro", 0
        self.winner = None
        final = any(f.wins == ROUNDS_TO_WIN - 1 for f in self.fighters) and all(
            f.wins == ROUNDS_TO_WIN - 1 for f in self.fighters)
        self.banner = ("FINAL ROUND" if final else f"ROUND {self.round}", 0)

    # 입력
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.app.manager.push(PauseScene(self.app, self))
                return
            if e.key == pygame.K_F1:
                self.debug = not self.debug
            elif e.key == pygame.K_F2:
                self.hud.show_inputs = not self.hud.show_inputs
            self.pending.add(e.key)

    def _inputs(self):
        held = pygame.key.get_pressed()
        frames = []
        for ctrl in self.controllers:
            if self.phase != "fight":
                frames.append(EMPTY_INPUT)
            elif isinstance(ctrl, AIController):
                frames.append(ctrl.get_frame())
            else:
                frames.append(ctrl.read(held, self.pending))
        self.pending.clear()
        return frames

    # 진행
    def update(self):
        super().update()
        self.phase_t += 1
        self.effects.update()
        self.hud.update()
        self.cam.update(self.fighters)
        frames = self._inputs()
        self._phase_logic()
        if self.slowmo > 0:
            self.slowmo -= 1
            if self.slowmo % 3:  # KO 순간은 세 틱에 한 번만 움직여 느리게 보인다
                for f in self.fighters:
                    f.hold()
                return
        if self.hitstop > 0:
            self.hitstop -= 1
            for f, fr in zip(self.fighters, frames):
                f.record_input(fr)
                f.hold()
            return
        for f, fr in zip(self.fighters, frames):
            f.record_input(fr)
            f.step()
        self._separate()
        self._limit_distance()
        self._update_facing()
        for f in self.fighters:
            f.update_pose()
        self._check_hits()
        self._handle_events()

    def _phase_logic(self):
        f1, f2 = self.fighters
        if self.phase == "intro":
            if self.phase_t == 70:
                self.banner = ("FIGHT!", self.t)
            if self.phase_t >= 100:
                self.phase, self.phase_t = "fight", 0
        elif self.phase == "fight":
            self.frames += 1
            if self.frames % 60 == 0 and self.timer > 0:
                self.timer -= 1
            if f1.hp <= 0 or f2.hp <= 0:
                self.phase, self.phase_t = "ko", 0
                self.slowmo = 60
                self.effects.flash(WHITE, 14, 170)
                self.banner = ("K.O.", self.t)
            elif self.timer <= 0:
                self.phase, self.phase_t = "ko", 40
                self.banner = ("TIME UP", self.t)
        elif self.phase == "ko":
            if self.phase_t == 110:
                r1, r2 = f1.hp / f1.max_hp, f2.hp / f2.max_hp
                if r1 > r2:
                    self.winner = f1
                elif r2 > r1:
                    self.winner = f2
                if self.winner:
                    self.winner.wins += 1
                    if self.winner.state != KO:
                        self.winner.win()
                    self.banner = (f"P{self.winner.pid} {self.winner.char.name} 승리", self.t)
                else:
                    for f in self.fighters:
                        f.wins += 1
                    self.banner = ("무승부", self.t)
            if self.phase_t >= 230:
                if any(f.wins >= ROUNDS_TO_WIN for f in self.fighters):
                    w = [f for f in self.fighters if f.wins >= ROUNDS_TO_WIN]
                    winner = w[0] if len(w) == 1 else None
                    self.app.manager.replace(ResultScene(self.app, winner, self.chars, self.mode, self.level, self.stage))
                else:
                    self.round += 1
                    self.start_round()

    def _separate(self):
        a, b = self.fighters
        for f in self.fighters:
            if f.state == ATTACK and f.move.no_push and f.advancing:
                return
        if abs(a.pos.y - b.pos.y) > 110:
            return
        dx = b.pos.x - a.pos.x
        min_d = BODY_HALF_W * 2
        if abs(dx) >= min_d:
            return
        s = (1 if dx > 0 else -1) if dx else a.facing
        overlap = min_d - abs(dx)
        lo, hi = STAGE_LEFT + BODY_HALF_W, STAGE_RIGHT - BODY_HALF_W
        a.pos.x -= s * overlap / 2
        b.pos.x += s * overlap / 2
        # 한쪽이 벽에 막히면 나머지가 전부 밀린다
        for f, other, d in ((a, b, -s), (b, a, s)):
            if f.pos.x < lo:
                other.pos.x += lo - f.pos.x
                f.pos.x = lo
            elif f.pos.x > hi:
                other.pos.x -= f.pos.x - hi
                f.pos.x = hi

    def _limit_distance(self):
        """화면이 확대되어 있으므로 두 캐릭터가 화면 밖으로 벌어지지 않게 막는다.
        멀어지려는 쪽이 멈추고, 둘 다 멀어지면 반씩 끌어당긴다."""
        a, b = self.fighters
        dx = b.pos.x - a.pos.x
        excess = abs(dx) - MAX_SEPARATION
        if excess <= 0:
            return
        s = 1 if dx > 0 else -1
        a_away, b_away = a.vel.x * -s > 0, b.vel.x * s > 0
        if a_away and not b_away:
            a.pos.x += s * excess
        elif b_away and not a_away:
            b.pos.x -= s * excess
        else:
            a.pos.x += s * excess / 2
            b.pos.x -= s * excess / 2
        for f, away in ((a, a_away), (b, b_away)):
            if away:
                f.vel.x = 0
        lo, hi = STAGE_LEFT + BODY_HALF_W, STAGE_RIGHT - BODY_HALF_W
        for f in self.fighters:
            f.pos.x = max(lo, min(hi, f.pos.x))

    def _update_facing(self):
        a, b = self.fighters
        for f, o in ((a, b), (b, a)):
            if f.state in NEUTRAL and f.on_ground and abs(o.pos.x - f.pos.x) > 2:
                want = 1 if o.pos.x > f.pos.x else -1
                if want != f.facing:
                    f.facing = want
                    f.update_pose()

    def _check_hits(self):
        a, b = self.fighters
        found = []
        for att, dfd in ((a, b), (b, a)):
            if att.hit is None or dfd.invulnerable:
                continue
            slot = att.hit_slot()
            i = dfd.hurt.collidelist(att.hit) if slot is not None else -1
            if i >= 0:
                found.append((att, dfd, slot, att.hit[i].clip(dfd.hurt).center))
        for att, dfd, slot, point in found:
            mv = att.move
            att.hit_slots.add(slot)
            result = dfd.take_hit(att, mv)
            att.cancel_ok = True
            blocked = result == "block"
            self.effects.hit(mv.effect, point, mv.tier, att.facing, blocked)
            self.hitstop = max(self.hitstop, 4 + mv.tier if blocked else HITSTOP[mv.tier])
            if not blocked:
                self.effects.shake(SHAKE[mv.tier])
                if mv.kind == "super":
                    self.effects.flash(WHITE, 10, 150)
            # 상대가 벽에 붙어 있으면 대신 때린 쪽이 뒤로 밀린다
            if dfd.at_wall and att.on_ground and not att.advancing:
                att.vel.x = -att.facing * mv.push * 0.7

    def _handle_events(self):
        for f, o in ((self.fighters[0], self.fighters[1]), (self.fighters[1], self.fighters[0])):
            for kind, mv in f.events:
                if kind == "special":
                    self.effects.aura(mv.effect, (f.pos.x - f.facing * 10, f.pos.y - 120), 300, alpha=110, life=36)
                elif kind == "super":
                    self.effects.aura(mv.effect, (SCREEN_W / 2, 320), 640, alpha=200, life=56, screen=True)
                    self.effects.darken = 50
                    self.effects.flash(EFFECT_COLORS[mv.effect], 6, 90)
                    o.freeze = mv.startup
                    self.banner = (mv.name, self.t)
                elif kind in ("land", "jump"):
                    self.effects.dust((f.pos.x, GROUND_Y - 2), 5 if kind == "jump" else 7)
            f.events.clear()

    # 그리기
    def draw(self, surf, alpha):
        cam = self.cam
        cam.shake = self.effects.offset
        surf.fill(INK)
        self.stage.draw(surf, cam)
        if self.effects.darken > 0:
            ui.dim(surf, int(min(1, self.effects.darken / 15) * 160))
        self.effects.draw_back(surf, cam)
        for f in self.fighters:
            p = f.prev_pos.lerp(f.pos, alpha)
            sx, sy = cam.to_screen((p.x, GROUND_Y))
            ui.draw_shadow(surf, sx, sy, GROUND_Y - p.y, cam.zoom)
        self._trails(surf)
        order = sorted(self.fighters, key=lambda f: f.state == ATTACK)
        for f in order:
            vib = 0
            if self.hitstop > 0 and f.state in (HITSTUN, JUGGLE, BLOCKSTUN):
                vib = 5 if self.t % 2 else -5
            j = f.draw(surf, alpha, cam, vib, 0)
            if self.debug:
                self._debug(surf, f, j)
        self.effects.draw_front(surf, cam)
        self.hud.draw(surf, self.timer, self.app.config)
        self._banner(surf)
        self.effects.draw_flash(surf)

    def _trails(self, surf):
        layer = None
        for f in self.fighters:
            tr = list(f.trail)
            if len(tr) < 2:
                continue
            if layer is None:
                layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            color = EFFECT_COLORS[f.move.effect] if f.move else WHITE
            n = len(tr)
            for i in range(n - 1):
                (a0, b0), (a1, b1) = tr[i], tr[i + 1]
                k = (i + 1) / n
                pts = [self.cam.to_screen(p) for p in (a0, b0, b1, a1)]
                pygame.draw.polygon(layer, (*color, int(150 * k)), pts)
        if layer is not None:
            surf.blit(layer, (0, 0))

    def _banner(self, surf):
        if not self.banner:
            return
        text, start = self.banner
        t = self.t - start
        life = 90
        if t > life:
            return
        k = ease_out_back(min(1.0, t / 14))
        alpha = 255 if t < life - 20 else int(255 * (life - t) / 20)
        size = 96 if len(text) < 12 else 64
        color = GOLD if text in ("FIGHT!", "K.O.") else WHITE
        ui.draw_text(surf, text, size, color, (SCREEN_W / 2, 300), kind="heavy", outline=5, alpha=alpha,
                     scale=1.5 - 0.5 * k)

    def _debug(self, surf, f, j):
        pygame.draw.rect(surf, (60, 120, 255), self.cam.rect(f.hurt), 2)
        for box in f.hit or ():
            pygame.draw.rect(surf, (255, 40, 40), self.cam.rect(box), 2)
        info = f.state + (f" {f.move.name} {f.move_frame}/{f.move.total}" if f.state == ATTACK else "")
        ui.draw_text(surf, info, 16, WHITE, self.cam.to_screen((f.pos.x, f.hurt.top - 16)))
        ui.draw_text(surf, f"FPS {self.app.clock.get_fps():.0f}", 16, WHITE, (SCREEN_W / 2, 110))


# ── 일시정지 ──
class PauseScene(Scene):
    overlay = True
    ITEMS = ["계속하기", "기술표", "설정", "캐릭터 선택으로", "타이틀로"]

    def __init__(self, app, battle):
        super().__init__(app)
        self.battle = battle
        self.menu = ui.Menu(self.ITEMS, (SCREEN_W / 2, 380), spacing=60, on_paper=False)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.manager.pop()
            return
        n = nav(self.app, e, players=(1,))
        if n == "up":
            self.menu.move(-1)
        elif n == "down":
            self.menu.move(1)
        elif n == "back":
            self.app.manager.pop()
        elif n == "ok":
            item = self.menu.selected
            if item == "계속하기":
                self.app.manager.pop()
            elif item == "기술표":
                idx = CHARACTERS.index(self.battle.chars[0])
                self.app.manager.push(MoveListScene(self.app, idx))
            elif item == "설정":
                self.app.manager.push(SettingsScene(self.app))
            elif item == "캐릭터 선택으로":
                b = self.battle
                picks = [CHARACTERS.index(c) for c in b.chars]
                self.app.manager.replace(CharSelectScene(self.app, b.mode, b.level, picks, STAGES.index(b.stage)))
            elif item == "타이틀로":
                self.app.manager.replace(TitleScene(self.app))

    def update(self):
        super().update()
        self.menu.update()
        self.battle.pending.clear()

    def draw(self, surf, alpha):
        ui.dim(surf, 160)
        ui.draw_text(surf, "일시정지", 56, WHITE, (SCREEN_W / 2, 170), kind="heavy", outline=4)
        self.menu.draw(surf)


# ── 기술표 ──
def command_text(app, cmd):
    """'236P' 같은 표기를 현재 키 설정에 맞춰 '↓↘→ + 팔(F)'로 바꾼다."""
    arrows = {"1": "↙", "2": "↓", "3": "↘", "4": "←", "6": "→", "7": "↖", "8": "↑", "9": "↗"}
    p = f"팔({app.config.key_name(1, 'punch')})"
    k = f"발({app.config.key_name(1, 'kick')})"
    out = []
    dirs = ""
    for ch in cmd:
        if ch in arrows:
            dirs += arrows[ch]
        elif ch == "P":
            out.append((dirs + " + " if dirs else "") + p)
            dirs = ""
        elif ch == "K":
            out.append((dirs + " + " if dirs else "") + k)
            dirs = ""
        else:
            out.append(dirs + ch)
            dirs = ""
    return "".join(out)


class MoveListScene(Scene):
    overlay = True

    def __init__(self, app, index):
        super().__init__(app)
        self.index = index

    def handle_event(self, e):
        n = nav(self.app, e, players=(1,))
        if n in ("back", "ok"):
            self.app.manager.pop()
        elif n == "left":
            self.index = (self.index - 1) % len(CHARACTERS)
        elif n == "right":
            self.index = (self.index + 1) % len(CHARACTERS)

    def draw(self, surf, alpha):
        if len(self.app.manager.stack) == 1 or self.app.manager.stack[0] is self:
            surf.blit(self.app.paper, (0, 0))
        surf.fill((22, 20, 26))
        ch = CHARACTERS[self.index]
        m = ch.moves
        ui.draw_text(surf, f"◀  {ch.name} · {ch.style_name}  ▶", 36, WHITE, (SCREEN_W / 2, 44), kind="heavy", outline=3)
        cols = [56, 240, 590, 690, 770, 850, 940]
        heads = ["기술", "입력 (P1 키 기준)", "데미지", "선딜", "지속", "후딜", "판정"]
        y = 100
        for x, h in zip(cols, heads):
            ui.draw_text(surf, h, 20, GOLD, (x, y), "midleft", "heavy")
        level = {"high": "상단 · 앉으면 피함", "mid": "중단 · 서서/앉아 막기", "low": "하단 · 앉아서 막기",
                 "overhead": "중단 · 서서 막기"}
        rows = [("기본기", None)]
        rows += [(m[k].name, m[k]) for k in ("5P", "5K", "2P", "2K", "6P", "6K", "jP", "jK")]
        rows += [("필살기", None)]
        rows += [(m[k].name, m[k]) for k in ("236P", "623P", "214P", "236K", "214K", "super")]
        y = 134
        for name, mv in rows:
            if mv is None:
                ui.draw_text(surf, name, 20, (240, 120, 100), (cols[0], y), "midleft", "heavy")
                y += 28
                continue
            color = GOLD if mv.kind == "super" else WHITE
            ui.draw_text(surf, name, 20, color, (cols[0], y), "midleft")
            cmd = mv.command.replace("점프 중 ", "")
            prefix = "점프 중 " if mv.base == "air" else ""
            ui.draw_text(surf, prefix + command_text(self.app, cmd), 20, color, (cols[1], y), "midleft")
            dmg = f"{mv.dmg}×{mv.hits}" if mv.hits > 1 else str(mv.dmg)
            for x, v in zip(cols[2:], (dmg, mv.startup, mv.active, mv.recovery, level[mv.level])):
                ui.draw_text(surf, str(v), 20, color, (x, y), "midleft")
            y += 28
        # 콤보
        y += 6
        ui.draw_text(surf, "콤보 (맞힌 뒤 이어서 입력)", 20, (240, 120, 100), (cols[0], y), "midleft", "heavy")
        y += 28
        for name, cmd, start in COMBOS[ch.style]:
            parts, mv = [], m[start]
            seq = [b.strip() for b in cmd.split("→")]
            for i, b in enumerate(seq):
                parts.append(mv.name)
                if i + 1 < len(seq):
                    mv = m[mv.chain["punch" if seq[i + 1] == "P" else "kick"]]
            ui.draw_text(surf, name, 20, WHITE, (cols[0], y), "midleft")
            text = " → ".join(command_text(self.app, b) for b in seq)
            ui.draw_text(surf, f"{text}    ({' → '.join(parts)})", 20, WHITE, (cols[1], y), "midleft")
            y += 28
        ui.draw_text(surf, "기본기·연결기를 맞힌 직후 필살기 입력으로 끊고 이을 수 있습니다. 선딜·후딜 단위: 프레임(1/60초)",
                     18, (200, 190, 175), (SCREEN_W / 2, 672), outline=0)
        ui.draw_text(surf, "←/→ 캐릭터 바꾸기   ·   Esc 닫기", 18, (200, 190, 175), (SCREEN_W / 2, 700), outline=0)


# ── 설정 ──
class SettingsScene(Scene):
    """게임 설정: 전투 중 커맨드 표시 켜기/끄기, 키 설정으로 들어가기."""
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.menu = ui.Menu(self._items(), (SCREEN_W / 2, 360), spacing=66, on_paper=False)

    def _items(self):
        on = self.app.config.options["show_commands"]
        return [f"커맨드 표시: {'켜짐' if on else '꺼짐'}", "키 설정", "돌아가기"]

    def _toggle(self):
        opts = self.app.config.options
        opts["show_commands"] = not opts["show_commands"]
        self.app.config.save()
        self.menu.items = self._items()

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.manager.pop()
            return
        n = nav(self.app, e, players=(1,))
        if n == "up":
            self.menu.move(-1)
        elif n == "down":
            self.menu.move(1)
        elif n in ("left", "right") and self.menu.index == 0:
            self._toggle()
        elif n == "back":
            self.app.manager.pop()
        elif n == "ok":
            if self.menu.index == 0:
                self._toggle()
            elif self.menu.index == 1:
                self.app.manager.push(KeyConfigScene(self.app))
            else:
                self.app.manager.pop()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf, alpha):
        surf.fill((22, 20, 26))
        ui.draw_text(surf, "설정", 52, WHITE, (SCREEN_W / 2, 150), kind="heavy", outline=3)
        self.menu.draw(surf)
        desc = {0: "켜 두면 전투 화면 왼쪽에 콤보·필살기 입력법이 표시됩니다. (←/→ 또는 Enter로 바꾸기)",
                1: "P1/P2의 방향키, 팔 공격, 발 공격 키를 바꿉니다.", 2: "이전 화면으로 돌아갑니다."}
        ui.draw_text(surf, desc[self.menu.index], 22, (220, 210, 190), (SCREEN_W / 2, 520), outline=0)


# ── 키 설정 ──
class KeyConfigScene(Scene):
    overlay = True

    def __init__(self, app):
        super().__init__(app)
        self.row, self.col = 0, 0
        self.waiting = False
        self.rows = ACTIONS + ["reset", "back"]
        self.message = ""

    def handle_event(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if self.waiting:
            if e.key == pygame.K_ESCAPE:
                self.waiting = False
                self.message = "취소했습니다."
            elif e.key in (pygame.K_F1, pygame.K_F2, pygame.K_F11):
                self.message = "F1·F2·F11은 쓸 수 없는 키입니다."
            else:
                pid, action = self.col + 1, self.rows[self.row]
                before = {(p, a): self.app.config.keys[p][a] for p in (1, 2) for a in ACTIONS}
                self.app.config.assign(pid, action, e.key)
                swapped = [f"P{p} {ACTION_NAMES[a]}" for (p, a), k in before.items()
                           if self.app.config.keys[p][a] != k and (p, a) != (pid, action)]
                self.message = (f"이미 쓰이던 키라서 {swapped[0]}와(과) 바꿨습니다." if swapped
                                else f"P{pid} {ACTION_NAMES[action]} = {key_label(e.key)}")
                self.waiting = False
            return
        k = e.key
        if k in (pygame.K_UP, pygame.K_w):
            self.row = (self.row - 1) % len(self.rows)
        elif k in (pygame.K_DOWN, pygame.K_s):
            self.row = (self.row + 1) % len(self.rows)
        elif k in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            self.col = 1 - self.col
        elif k in CONFIRM:
            item = self.rows[self.row]
            if item == "reset":
                self.app.config.reset()
                self.message = "기본값으로 되돌렸습니다."
            elif item == "back":
                self.app.manager.pop()
            else:
                self.waiting = True
                self.message = ""
        elif k in CANCEL:
            self.app.manager.pop()

    def draw(self, surf, alpha):
        if self.app.manager.stack[0] is self or len(self.app.manager.stack) == 1:
            surf.blit(self.app.paper, (0, 0))
        surf.fill((22, 20, 26))
        ui.draw_text(surf, "키 설정", 48, WHITE, (SCREEN_W / 2, 70), kind="heavy", outline=3)
        xs = (SCREEN_W / 2 - 40, SCREEN_W / 2 + 200)
        for c, x in enumerate(xs):
            ui.draw_text(surf, f"P{c + 1}", 28, P_COLORS[c + 1], (x, 140), kind="heavy")
        for r, item in enumerate(self.rows):
            y = 196 + r * 52
            if item in ACTIONS:
                ui.draw_text(surf, ACTION_NAMES[item], 26, WHITE, (SCREEN_W / 2 - 220, y), "midright")
                for c, x in enumerate(xs):
                    sel = r == self.row and c == self.col
                    box = pygame.Rect(0, 0, 150, 42)
                    box.center = (x, y)
                    if sel:
                        color = (200, 60, 50) if self.waiting else (150, 30, 30)
                        ui.panel(surf, box, color=color, alpha=230, border=GOLD, radius=8)
                    else:
                        ui.panel(surf, box, alpha=120, radius=8)
                    label = "키를 누르세요" if sel and self.waiting else self.app.config.key_name(c + 1, item)
                    ui.draw_text(surf, label, 20 if sel and self.waiting else 24, WHITE, (x, y), kind="heavy")
            else:
                text = "기본값으로" if item == "reset" else "돌아가기"
                sel = r == self.row
                box = pygame.Rect(0, 0, 260, 42)
                box.center = (SCREEN_W / 2 + 80, y + 8)
                ui.panel(surf, box, color=(150, 30, 30) if sel else (16, 14, 20), alpha=220, radius=8,
                         border=GOLD if sel else None)
                ui.draw_text(surf, text, 24, WHITE, box.center, kind="heavy")
        if self.message:
            ui.draw_text(surf, self.message, 22, GOLD, (SCREEN_W / 2, 640))
        ui.draw_text(surf, "↑↓ 항목 · ←→ P1/P2 · Enter 바꾸기 · Esc 닫기   (이미 쓰이던 키를 누르면 두 키가 서로 바뀝니다)",
                     18, (200, 190, 175), (SCREEN_W / 2, 690), outline=0)


# ── 결과 ──
class ResultScene(Scene):
    def __init__(self, app, winner, chars, mode, level, stage=None):
        super().__init__(app)
        self.winner, self.chars, self.mode, self.level, self.stage = winner, chars, mode, level, stage
        self.view = View(zoom=1.8, cx=380, ground=640, screen_x=380)
        self.menu = ui.Menu(["재대결", "캐릭터 선택", "타이틀로"], (SCREEN_W / 2 + 300, 470), spacing=62)
        self.figure = None
        if winner:
            self.figure = Fighter(1, winner.char)
            self.figure.pos.update(380, GROUND_Y)
            self.figure.prev_pos = self.figure.pos.copy()
            self.figure.win()

    def handle_event(self, e):
        n = nav(self.app, e, players=(1,))
        if n == "up":
            self.menu.move(-1)
        elif n == "down":
            self.menu.move(1)
        elif n == "ok":
            item = self.menu.selected
            if item == "재대결":
                self.app.manager.replace(BattleScene(self.app, self.chars, self.mode, self.level, self.stage))
            elif item == "캐릭터 선택":
                picks = [CHARACTERS.index(c) for c in self.chars]
                stage = STAGES.index(self.stage) if self.stage in STAGES else 0
                self.app.manager.replace(CharSelectScene(self.app, self.mode, self.level, picks, stage))
            else:
                self.app.manager.replace(TitleScene(self.app))

    def update(self):
        super().update()
        self.menu.update()
        if self.figure:
            self.figure.inp = EMPTY_INPUT
            self.figure.step()
            self.figure.pos.update(380, GROUND_Y)
            self.figure.update_pose()

    def draw(self, surf, alpha):
        surf.blit(self.app.paper, (0, 0))
        if self.figure:
            k = ease_out_back(min(1.0, self.t / 24))
            img = self.app.images.get(self.winner.char.effect, int(600 * (0.6 + 0.4 * k)))
            surf.blit(img, img.get_rect(center=(380, 470)))
            self.figure.draw(surf, alpha, self.view)
            who = "컴퓨터" if self.mode == "pve" and self.winner.pid == 2 else f"P{self.winner.pid}"
            ui.draw_text(surf, f"{who} 승리!", 72, P_COLORS[self.winner.pid], (SCREEN_W / 2 + 300, 200),
                         kind="heavy", outline=5)
            ui.draw_text(surf, self.winner.char.name, 36, INK, (SCREEN_W / 2 + 300, 280), kind="heavy", outline=0)
        else:
            ui.draw_text(surf, "무승부", 80, INK, (SCREEN_W / 2, 220), kind="heavy", outline=0)
        self.menu.draw(surf)
        hint(surf, "↑↓ 선택   ·   Enter 확인")

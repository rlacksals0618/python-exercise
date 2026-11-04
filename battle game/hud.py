"""전투 화면 HUD. 캐릭터·라운드 값을 읽어서 그리기만 하고 값을 바꾸지 않는다."""
import math

import pygame

import ui
from moves import COMBOS
from settings import GOLD, INK, P_COLORS, ROUNDS_TO_WIN, SCREEN_W, SUPER_MAX, WHITE

BAR_W, BAR_H, BAR_Y = 500, 26, 34
CENTER_GAP = 62

ARROWS = {1: "↙", 2: "↓", 3: "↘", 4: "←", 5: "·", 6: "→", 7: "↖", 8: "↑", 9: "↗"}
MIRROR = {1: 3, 3: 1, 4: 6, 6: 4, 7: 9, 9: 7}
SPECIAL_ORDER = ("236P", "623P", "214P", "236K", "214K", "super")


def command_label(cmd, facing, punch, kick):
    """'236P'를 화면 방향에 맞춘 화살표와 실제 키 이름으로: 오른쪽을 볼 때 '↓↘→ + F'.
    왼쪽을 보고 있으면 앞이 ←이므로 화살표를 좌우로 뒤집는다."""
    dirs, out = "", []
    for ch in cmd.replace(" ", "").replace("→", ">"):
        if ch.isdigit():
            n = int(ch)
            dirs += ARROWS[MIRROR.get(n, n) if facing < 0 else n]
        elif ch in "PK":
            out.append((dirs + " + " if dirs else "") + (punch if ch == "P" else kick))
            dirs = ""
    return " → ".join(out)


def side_x(side, offset):
    """P1(side=-1)은 화면 왼쪽, P2(side=+1)는 오른쪽으로 대칭 배치한다."""
    return SCREEN_W / 2 + side * offset


class HealthBar:
    def __init__(self, max_hp):
        self.max_hp, self.shown, self.delay = max_hp, max_hp, 0

    def reset(self, hp):
        self.shown, self.delay = hp, 0

    def update(self, hp, in_combo):
        if hp < self.shown:
            if in_combo:
                self.delay = 30
            elif self.delay > 0:
                self.delay -= 1
            else:
                self.shown = max(hp, self.shown - self.max_hp * 0.01)
        else:
            self.shown = hp


class ComboCounter:
    def __init__(self):
        self.hits = 0
        self.dmg = 0
        self.pop = 0
        self.fade = 0

    def update(self, defender):
        if defender.in_combo and defender.combo_hits >= 2:
            if defender.combo_hits != self.hits:
                self.pop = 8
            self.hits, self.dmg, self.fade = defender.combo_hits, defender.combo_dmg, 60
        elif self.fade > 0:
            self.fade -= 1
        if self.pop > 0:
            self.pop -= 1


class HUD:
    def __init__(self, fighters, effect_images, command_pids=(1,)):
        self.fighters = fighters
        self.command_pids = command_pids   # 커맨드 표를 보여줄 플레이어
        self.bars = [HealthBar(f.max_hp) for f in fighters]
        self.combos = [ComboCounter(), ComboCounter()]
        self.icons = {f.pid: effect_images.get(f.char.effect, 58) for f in fighters}
        self.t = 0
        self.show_inputs = False

    def reset(self):
        for bar, f in zip(self.bars, self.fighters):
            bar.reset(f.hp)

    def update(self):
        self.t += 1
        for bar, f in zip(self.bars, self.fighters):
            bar.update(f.hp, f.in_combo)
        # 콤보 숫자는 때리는 쪽 화면에 표시한다
        self.combos[0].update(self.fighters[1])
        self.combos[1].update(self.fighters[0])

    def draw(self, surf, timer, config, touch=False):
        for i, f in enumerate(self.fighters):
            side = -1 if i == 0 else 1
            if config.options.get("show_commands") and f.pid in self.command_pids:
                self._commands(surf, f, side, config, touch)
            self._health(surf, f, self.bars[i], side)
            self._super(surf, f, side)
            self._combo(surf, self.combos[i], side)
            if self.show_inputs:
                self._inputs(surf, f, side)
        self._timer(surf, timer)

    def _health(self, surf, f, bar, side):
        inner = side_x(side, CENTER_GAP)
        outer = side_x(side, CENTER_GAP + BAR_W)
        left = min(inner, outer)
        frame = pygame.Rect(left - 4, BAR_Y - 4, BAR_W + 8, BAR_H + 8)
        pygame.draw.rect(surf, INK, frame, border_radius=6)
        pygame.draw.rect(surf, (60, 20, 24), (left, BAR_Y, BAR_W, BAR_H))
        ratio = f.hp / f.max_hp
        shown = bar.shown / f.max_hp

        def fill(k, color):
            w = int(BAR_W * k)
            x = left if side < 0 else left + BAR_W - w   # 바깥쪽에 붙여서 가운데부터 줄어든다
            pygame.draw.rect(surf, color, (x, BAR_Y, w, BAR_H))

        fill(shown, (250, 240, 220))
        color = (236, 196, 60)
        if ratio <= 0.3 and (self.t // 8) % 2 == 0:
            color = (235, 70, 50)
        elif ratio <= 0.3:
            color = (250, 120, 60)
        fill(ratio, color)
        pygame.draw.rect(surf, (255, 255, 255), (left, BAR_Y, BAR_W, 5))
        # 초상(이펙트 아이콘)과 이름은 체력바 바깥쪽 끝
        icon = self.icons[f.pid]
        icon_x = outer + side * 40
        pygame.draw.circle(surf, (238, 230, 212), (icon_x, BAR_Y + 14), 34)
        pygame.draw.circle(surf, P_COLORS[f.pid], (icon_x, BAR_Y + 14), 34, 4)
        surf.blit(icon, icon.get_rect(center=(icon_x, BAR_Y + 14)))
        anchor = "midleft" if side < 0 else "midright"
        ui.draw_text(surf, f"P{f.pid}  {f.char.name}", 24, WHITE, (outer, BAR_Y + BAR_H + 22), anchor, "heavy")
        # 라운드 승리 표시: 체력바 안쪽 끝에서 바깥쪽으로 늘어선다(가운데 타이머와 겹치지 않게)
        for k in range(ROUNDS_TO_WIN):
            cx = inner + side * (22 + k * 26)
            cy = BAR_Y + BAR_H + 22
            pygame.draw.circle(surf, INK, (cx, cy), 10)
            pygame.draw.circle(surf, GOLD if k < f.wins else (90, 80, 70), (cx, cy), 7)

    def _super(self, surf, f, side):
        w, h, y = 300, 16, 688
        outer = side_x(side, 600)
        left = outer if side < 0 else outer - w
        pygame.draw.rect(surf, INK, (left - 3, y - 3, w + 6, h + 6), border_radius=5)
        pygame.draw.rect(surf, (40, 30, 50), (left, y, w, h))
        k = f.super / SUPER_MAX
        fw = int(w * k)
        x = left if side < 0 else left + w - fw
        full = f.super >= SUPER_MAX
        color = P_COLORS[f.pid]
        if full:
            glow = 0.5 + 0.5 * math.sin(self.t * 0.25)
            color = tuple(int(c + (255 - c) * glow) for c in GOLD)
        pygame.draw.rect(surf, color, (x, y, fw, h))
        label = "필살 MAX!" if full else "필살"
        anchor = "bottomleft" if side < 0 else "bottomright"
        ui.draw_text(surf, label, 20, GOLD if full else WHITE, (outer, y - 4), anchor, "heavy")

    def _combo(self, surf, c, side):
        if c.fade <= 0 or c.hits < 2:
            return
        alpha = 255 if c.fade > 30 else int(255 * c.fade / 30)
        scale = 1.0 + 0.3 * (c.pop / 8)
        x = side_x(side, 470)
        ui.draw_text(surf, f"{c.hits} HITS", 54, (255, 214, 90), (x, 210), "center", "heavy", 3, alpha, scale)
        ui.draw_text(surf, f"{c.dmg} 데미지", 24, WHITE, (x, 254), "center", "bold", 2, alpha)

    def _timer(self, surf, timer):
        box = pygame.Rect(0, 0, 96, 70)
        box.midtop = (SCREEN_W / 2, 18)
        pygame.draw.rect(surf, INK, box, border_radius=10)
        pygame.draw.rect(surf, (120, 30, 30), box.inflate(-8, -8), border_radius=8)
        warn = timer <= 10
        scale = 1.0 + (0.12 * abs(math.sin(self.t * 0.15)) if warn else 0)
        ui.draw_text(surf, str(timer), 44, (255, 90, 70) if warn else WHITE, box.center, "center", "heavy", 2,
                     scale=scale)

    def _commands(self, surf, f, side, config, touch=False):
        """전투 중 커맨드 표: 콤보와 필살기 입력법. 지금 쓰는 기술은 금색으로 빛난다.
        캐릭터 머리 위 빈 공간에 들어가도록 두 칸으로 나눠 낮게 그린다."""
        if touch:
            punch, kick = "팔", "발"
            legend = "조이스틱 방향 + 팔·발 버튼"
        else:
            punch, kick = config.key_name(f.pid, "punch"), config.key_name(f.pid, "kick")
            legend = f"팔 공격 = {punch}    발 공격 = {kick}"
        left = [("콤보", None, None)]
        left += [(name, command_label(cmd.replace("→", ""), f.facing, punch, kick), None)
                 for name, cmd, _ in COMBOS[f.style]]
        left += [(f.moves["super"].name, command_label(f.moves["super"].command, f.facing, punch, kick), "super")]
        right = [(f.moves[k].name, command_label(f.moves[k].command, f.facing, punch, kick), k)
                 for k in SPECIAL_ORDER if k != "super"]
        col_w, row_h, head = 236, 21, 28
        w = col_w * 2 + 8
        h = head + max(len(left), len(right)) * row_h + 6
        x0 = 12 if side < 0 else SCREEN_W - 12 - w
        y0 = 100
        ui.panel(surf, (x0, y0, w, h), alpha=190, border=P_COLORS[f.pid], radius=8)
        ui.draw_text(surf, legend, 16, GOLD, (x0 + 12, y0 + 15), "midleft", "heavy", outline=0)
        ui.draw_text(surf, "필살기", 15, (240, 130, 110), (x0 + col_w + 14, y0 + 15), "midleft", "heavy", outline=0)
        using = f.move.key if f.state == "ATTACK" and f.move else None
        for col, rows in ((0, left), (1, right)):
            x, y = x0 + 6 + col * (col_w + 2), y0 + head
            for name, label, key in rows:
                cy = y + row_h / 2
                if label is None:
                    ui.draw_text(surf, name, 15, (240, 130, 110), (x + 6, cy), "midleft", "heavy", outline=0)
                else:
                    color = WHITE
                    if key == "super" and f.super < SUPER_MAX:
                        color = (130, 124, 118)           # 게이지가 모자라면 흐리게
                    if key is not None and key == using:
                        color = GOLD
                        pygame.draw.rect(surf, (150, 30, 30), (x, y + 1, col_w - 4, row_h - 2), border_radius=4)
                    ui.draw_text(surf, name, 16, color, (x + 8, cy), "midleft", outline=0)
                    ui.draw_text(surf, label, 16, color, (x + 82, cy), "midleft", outline=0)
                y += row_h

    def _inputs(self, surf, f, side):
        x = side_x(side, 600)
        y = 420
        last = None
        rows = []
        for num, pressed in f.buffer.recent(60):
            key = (num, pressed)
            if key != last or pressed:
                rows.append(key)
            last = key
        for num, pressed in rows[-9:][::-1]:
            label = ARROWS[num] + (" " + "+".join("P" if b == "punch" else "K" for b in sorted(pressed)) if pressed else "")
            ui.draw_text(surf, label, 22, WHITE, (x, y), "midleft" if side < 0 else "midright", "bold")
            y += 26

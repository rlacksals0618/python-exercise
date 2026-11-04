"""터치스크린 조작: 화면 속 조이스틱·버튼과 손가락 좌표 변환.

손가락 이벤트(FINGERDOWN 등)가 한 번이라도 들어오면 터치 모드가 켜져서
전투 화면에 가상 조이스틱과 팔·발 버튼이 나타나고, 메뉴에는 '뒤로' 버튼이 생긴다.
"""
import math

import pygame

import ui
from controls import InputFrame
from settings import GOLD, SCREEN_H, SCREEN_W, WHITE

FINGER_EVENTS = (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP)
BACK_RECT = pygame.Rect(14, 14, 132, 52)          # 메뉴 화면의 '뒤로' 버튼
PAUSE_RECT = pygame.Rect(SCREEN_W // 2 - 34, 96, 68, 46)   # 전투 화면의 일시정지 버튼


def to_logical(e):
    """손가락 좌표(0~1 비율)를 게임 화면 좌표(1280×720)로 바꾼다."""
    return (max(0.0, min(1.0, e.x)) * SCREEN_W, max(0.0, min(1.0, e.y)) * SCREEN_H)


def draw_button(surf, rect, text, size=24):
    ui.panel(surf, rect, alpha=170, border=WHITE, radius=12)
    ui.draw_text(surf, text, size, WHITE, rect.center, kind="heavy")


# 화면 배치: 혼자 할 때는 조이스틱 왼쪽·버튼 오른쪽, 둘이 할 때는 양쪽 끝에 하나씩 마주 보게
LAYOUTS = {
    "single": dict(stick=(190, 560), stick_r=100, zone=pygame.Rect(0, 280, 600, 440),
                   punch=(1010, 612), kick=(1160, 498), btn_r=74, btn_zone=pygame.Rect(760, 280, 520, 440)),
    "left": dict(stick=(150, 580), stick_r=82, zone=pygame.Rect(0, 330, 290, 390),
                 punch=(380, 640), kick=(482, 548), btn_r=56, btn_zone=pygame.Rect(290, 420, 270, 300)),
    "right": dict(stick=(1130, 580), stick_r=82, zone=pygame.Rect(990, 330, 290, 390),
                  punch=(900, 640), kick=(798, 548), btn_r=56, btn_zone=pygame.Rect(720, 420, 270, 300)),
}


class VirtualPad:
    """한 플레이어의 가상 조이스틱 + 팔·발 버튼. 여러 손가락을 동시에 받는다."""

    def __init__(self, layout, images, punch_icon):
        L = LAYOUTS[layout]
        self.stick, self.stick_r, self.zone = pygame.Vector2(L["stick"]), L["stick_r"], L["zone"]
        self.buttons = {"punch": pygame.Vector2(L["punch"]), "kick": pygame.Vector2(L["kick"])}
        self.btn_r, self.btn_zone = L["btn_r"], L["btn_zone"]
        size = int(self.btn_r * 1.5)
        self.icons = {"punch": images.get(punch_icon, size), "kick": images.get("foot", size)}
        self.reset()

    def reset(self):
        self.fingers = {}                  # 손가락 번호 → "stick" / "punch" / "kick"
        self.vec = pygame.Vector2()
        self.pressed = set()
        self.flash = {"punch": 0, "kick": 0}

    def owns(self, fid):
        return fid in self.fingers

    def _button_at(self, pos):
        best = None
        for name, c in self.buttons.items():
            d = c.distance_to(pos)
            if d <= self.btn_r * 1.3 and (best is None or d < best[0]):
                best = (d, name)
        return best[1] if best else None

    def finger_down(self, fid, pos):
        """이 패드가 맡은 손가락이면 True."""
        if self.zone.collidepoint(pos):
            self.fingers[fid] = "stick"
            self._aim(pos)
            return True
        if self.btn_zone.collidepoint(pos):
            name = self._button_at(pos)
            if name:
                self.fingers[fid] = name
                self.pressed.add(name)
                self.flash[name] = 8
                return True
        return False

    def finger_move(self, fid, pos):
        role = self.fingers.get(fid)
        if role == "stick":
            self._aim(pos)
        elif role in self.buttons:
            # 손가락을 다른 버튼 위로 미끄러뜨리면 그 버튼이 눌린다
            name = self._button_at(pos)
            if name and name != role:
                self.fingers[fid] = name
                self.pressed.add(name)
                self.flash[name] = 8

    def finger_up(self, fid):
        if self.fingers.pop(fid, None) == "stick":
            self.vec.update(0, 0)

    def _aim(self, pos):
        v = pygame.Vector2(pos) - self.stick
        if v.length() > self.stick_r:
            v.scale_to_length(self.stick_r)
        self.vec = v

    def frame(self):
        """이번 틱의 입력. 조이스틱은 8방향으로 나누고, 가운데 근처는 중립."""
        up = down = left = right = False
        if self.vec.length() > self.stick_r * 0.3:
            ang = math.degrees(math.atan2(self.vec.y, self.vec.x))   # 0 = 오른쪽, 90 = 아래
            sector = round(ang / 45) % 8                               # 0:→ 1:↘ 2:↓ 3:↙ 4:← 5:↖ 6:↑ 7:↗
            right = sector in (7, 0, 1)
            down = sector in (1, 2, 3)
            left = sector in (3, 4, 5)
            up = sector in (5, 6, 7)
        f = InputFrame(up, down, left, right, self.pressed)
        self.pressed = set()
        for k in self.flash:
            self.flash[k] = max(0, self.flash[k] - 1)
        return f

    def draw(self, surf):
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(layer, (20, 18, 26, 110), self.stick, self.stick_r)
        pygame.draw.circle(layer, (250, 248, 240, 150), self.stick, self.stick_r, 3)
        knob = self.stick + self.vec * 0.8
        pygame.draw.circle(layer, (250, 248, 240, 170), knob, self.stick_r * 0.42)
        for name, c in self.buttons.items():
            held = name in self.fingers.values() or self.flash[name] > 0
            pygame.draw.circle(layer, (180, 40, 40, 190) if held else (20, 18, 26, 120), c, self.btn_r)
            pygame.draw.circle(layer, (250, 248, 240, 160), c, self.btn_r, 3)
        surf.blit(layer, (0, 0))
        for name, c in self.buttons.items():
            icon = self.icons[name]
            surf.blit(icon, icon.get_rect(center=c))
            ui.draw_text(surf, "팔" if name == "punch" else "발", 18, GOLD, (c.x, c.y + self.btn_r * 0.72), kind="heavy")

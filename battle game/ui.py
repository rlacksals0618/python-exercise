"""화면 그리기 도구: 한글 글꼴, 외곽선 글자, 메뉴, 패널, 무대 배경."""
import math
import os
import random

import pygame

from settings import FONT_DIR, INK, PAPER

FONT_FILES = {"bold": "NanumGothicBold.ttf", "heavy": "NanumGothicExtraBold.ttf", "brush": "YujiBoku-Regular.ttf"}
_fonts = {}
_texts = {}


def font(size, kind="bold"):
    key = (size, kind)
    if key not in _fonts:
        path = os.path.join(FONT_DIR, FONT_FILES[kind])
        try:
            _fonts[key] = pygame.font.Font(path, size)
        except (OSError, pygame.error):
            # 글꼴 파일이 없으면 Windows 기본 한글 글꼴로 대신한다
            _fonts[key] = pygame.font.SysFont("malgungothic", size, bold=kind != "bold")
    return _fonts[key]


def text_surface(text, size, color, kind="bold", outline=2, outline_color=INK):
    key = (text, size, color, kind, outline, outline_color)
    surf = _texts.get(key)
    if surf is None:
        f = font(size, kind)
        body = f.render(text, True, color)
        if outline:
            edge = f.render(text, True, outline_color)
            w, h = body.get_width() + outline * 2, body.get_height() + outline * 2
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            for dx in range(-outline, outline + 1):
                for dy in range(-outline, outline + 1):
                    if dx * dx + dy * dy <= outline * outline + 1:
                        surf.blit(edge, (outline + dx, outline + dy))
            surf.blit(body, (outline, outline))
        else:
            surf = body
        if len(_texts) > 600:
            _texts.clear()
        _texts[key] = surf
    return surf


def draw_text(surf, text, size, color, pos, anchor="center", kind="bold", outline=2, alpha=255, scale=1.0,
              outline_color=INK):
    img = text_surface(text, size, color, kind, outline, outline_color)
    if scale != 1.0:
        img = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * scale)),
                                                 max(1, int(img.get_height() * scale))))
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    return rect


def panel(surf, rect, color=(16, 14, 20), alpha=190, border=None, radius=10):
    rect = pygame.Rect(rect)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    surf.blit(s, rect)
    if border:
        pygame.draw.rect(surf, border, rect, 2, border_radius=radius)


def dim(surf, alpha=150):
    s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    surf.blit(s, (0, 0))


class Menu:
    """방향키로 고르는 세로 메뉴. 선택 표시는 부드럽게 미끄러진다."""

    def __init__(self, items, center, spacing=58, size=34, on_paper=True):
        self.items = items
        self.on_paper = on_paper    # 밝은 한지 배경이면 먹색 글자, 어두운 배경이면 밝은 글자
        self.index = 0
        self.center = center
        self.spacing = spacing
        self.size = size
        self.cursor_y = self._y(0)

    def _y(self, i):
        return self.center[1] + (i - (len(self.items) - 1) / 2) * self.spacing

    def move(self, d):
        self.index = (self.index + d) % len(self.items)

    def item_rect(self, i):
        """i번째 항목을 누를 수 있는 영역(터치·마우스용)."""
        r = pygame.Rect(0, 0, 400, self.spacing - 4)
        r.center = (self.center[0], round(self._y(i)))
        return r

    @property
    def selected(self):
        return self.items[self.index]

    def update(self):
        self.cursor_y += (self._y(self.index) - self.cursor_y) * 0.3

    def draw(self, surf, accent=(236, 196, 92)):
        cx = self.center[0]
        w = 380
        bar = pygame.Rect(0, 0, w, self.size + 18)
        bar.center = (cx, round(self.cursor_y))
        panel(surf, bar, color=(150, 30, 30), alpha=200, radius=8)
        pygame.draw.polygon(surf, accent, [(bar.left - 22, bar.centery - 10), (bar.left - 8, bar.centery),
                                           (bar.left - 22, bar.centery + 10)])
        for i, item in enumerate(self.items):
            if i == self.index:
                draw_text(surf, item, self.size, (255, 246, 220), (cx, self._y(i)), kind="heavy")
            elif self.on_paper:
                draw_text(surf, item, self.size - 4, (70, 60, 52), (cx, self._y(i)), outline=0)
            else:
                draw_text(surf, item, self.size - 4, (205, 196, 180), (cx, self._y(i)))


# ── 배경 ──
def paper_texture(size, seed=3, base=PAPER):
    rng = random.Random(seed)
    surf = pygame.Surface(size)
    w, h = size
    for y in range(h):
        k = y / h
        c = tuple(int(base[i] * (1 - 0.1 * k)) for i in range(3))
        pygame.draw.line(surf, c, (0, y), (w, y))
    blot = pygame.Surface(size, pygame.SRCALPHA)
    for _ in range(140):
        r = rng.randint(30, 120)
        x, y = rng.randint(-50, w + 50), rng.randint(-50, h + 50)
        pygame.draw.circle(blot, (120, 100, 70, rng.randint(3, 8)), (x, y), r)
    surf.blit(blot, (0, 0))
    return surf


def draw_shadow(surf, x, ground_y, height_above, zoom=1.0):
    """발밑 그림자. 높이 뜰수록 작고 옅어진다. x, ground_y는 화면 좌표."""
    k = max(0.3, 1 - height_above / 260)
    w, h = max(2, int(90 * k * zoom)), max(2, int(16 * k * zoom))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, int(90 * k)), s.get_rect())
    surf.blit(s, (x - w / 2, ground_y - h / 2 + 2 * zoom))


def ink_stroke(surf, x0, x1, y, thick, color=INK, seed=0):
    """붓으로 그은 듯한 가로 띠(메뉴·제목 장식)."""
    rng = random.Random(seed)
    steps = 40
    for i in range(steps):
        t = i / (steps - 1)
        x = x0 + (x1 - x0) * t
        w = thick * (0.6 + 0.4 * math.sin(t * math.pi)) * rng.uniform(0.85, 1.0)
        pygame.draw.circle(surf, color, (x, y + rng.uniform(-1.5, 1.5)), w / 2)

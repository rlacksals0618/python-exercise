"""전투 무대 5종: 황야, 초원, 뒷골목, 격투기 링, 흰 방.

무대는 여러 겹의 그림(층)으로 되어 있고, 먼 층일수록 카메라를 따라 덜 움직여서 깊이감이 난다.
층마다 factor가 있다: 0이면 고정된 하늘, 1이면 바닥과 함께 움직이는 가장 가까운 층.
"""
import math
import os
import random

import pygame

from settings import CAM_MAX_X, CAM_MIN_X, FONT_DIR, GROUND_SCREEN, SCREEN_H, SCREEN_W, ZOOM

SCROLL = int((CAM_MAX_X - CAM_MIN_X) * ZOOM)   # 카메라가 끝에서 끝까지 움직이는 화면 거리
TOP = 260                                       # 카메라가 위로 올라갈 때 보일 여분의 위쪽
GY = TOP + GROUND_SCREEN                        # 층 그림 안에서 바닥선의 높이


def layer(factor):
    w = SCREEN_W + int(SCROLL * factor) + 4
    return pygame.Surface((w, SCREEN_H + TOP), pygame.SRCALPHA), factor


def vgrad(surf, top, bottom, y0=0, y1=None):
    y1 = surf.get_height() if y1 is None else y1
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        pygame.draw.line(surf, [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)], (0, y), (surf.get_width(), y))


def ridge(rng, width, base, amp, rough=0.55, n=7):
    pts = [base + rng.uniform(-amp, amp) for _ in range(2)]
    for _ in range(n):
        new = []
        for a, b in zip(pts, pts[1:]):
            new += [a, (a + b) / 2 + rng.uniform(-amp, amp)]
        pts = new + [pts[-1]]
        amp *= rough
    step = width / (len(pts) - 1)
    return [(i * step, y) for i, y in enumerate(pts)]


def font(size, kind="NanumGothicExtraBold.ttf"):
    try:
        return pygame.font.Font(os.path.join(FONT_DIR, kind), size)
    except (OSError, pygame.error):
        return pygame.font.SysFont("malgungothic", size)


# ── 황야 ──
def build_wasteland():
    rng = random.Random(21)
    sky, f0 = layer(0)
    vgrad(sky, (226, 132, 78), (252, 214, 150), 0, GY - 60)
    vgrad(sky, (252, 214, 150), (240, 190, 130), GY - 60)
    glow = pygame.Surface((420, 420), pygame.SRCALPHA)
    for r, a in ((200, 30), (150, 50), (96, 255)):
        pygame.draw.circle(glow, (255, 238, 190, a), (210, 210), r)
    sky.blit(glow, (760, TOP + 160))

    far, f1 = layer(0.15)
    w = far.get_width()
    x = -40
    while x < w:
        mw, mh = rng.randint(160, 340), rng.randint(90, 200)
        base = GY - 70
        top_w = mw * rng.uniform(0.45, 0.7)
        pygame.draw.polygon(far, (176, 104, 90), [(x, base), (x + (mw - top_w) / 2, base - mh),
                                                   (x + (mw + top_w) / 2, base - mh), (x + mw, base)])
        pygame.draw.line(far, (196, 126, 104), (x + (mw - top_w) / 2, base - mh), (x + (mw + top_w) / 2, base - mh), 3)
        x += mw + rng.randint(40, 220)
    pygame.draw.rect(far, (190, 120, 96), (0, GY - 72, w, far.get_height()))

    mid, f2 = layer(0.45)
    w = mid.get_width()
    pts = ridge(rng, w, GY - 70, 30, 0.6)
    pygame.draw.polygon(mid, (152, 84, 62), pts + [(w, mid.get_height()), (0, mid.get_height())])
    for _ in range(9):
        x = rng.randint(0, w)
        h = rng.randint(60, 150)
        pygame.draw.polygon(mid, (132, 70, 54), [(x - 26, GY - 40), (x - 10, GY - 40 - h), (x + 8, GY - 40 - h * 0.8),
                                                  (x + 24, GY - 40)])
    haze = pygame.Surface((w, 120), pygame.SRCALPHA)
    for i in range(120):
        pygame.draw.line(haze, (246, 200, 150, int(140 * (1 - i / 120))), (0, i), (w, i))
    mid.blit(haze, (0, GY - 120))

    near, f3 = layer(1.0)
    w = near.get_width()
    vgrad(near, (200, 146, 96), (166, 112, 70), GY - 26, near.get_height())
    pygame.draw.line(near, (120, 76, 46), (0, GY - 26), (w, GY - 26), 3)
    for _ in range(26):   # 갈라진 땅
        x, y = rng.randint(0, w), rng.randint(GY - 10, near.get_height() - 10)
        p = [(x, y)]
        for _ in range(4):
            x += rng.randint(-26, 26)
            y += rng.randint(2, 10)
            p.append((x, y))
        pygame.draw.lines(near, (126, 82, 50), False, p, 2)
    for _ in range(40):
        x, y = rng.randint(0, w), rng.randint(GY - 20, near.get_height() - 6)
        pygame.draw.ellipse(near, (140, 96, 62), (x, y, rng.randint(6, 14), rng.randint(4, 7)))
    for x in (90, 860, 1620, 2240):   # 선인장
        cactus(near, x + rng.randint(-30, 30), GY - 24, rng.uniform(0.8, 1.2))
    for x in (480, 1300, 1980):       # 마른 풀
        for k in range(7):
            a = math.radians(-150 + k * 20)
            pygame.draw.line(near, (150, 120, 70), (x, GY - 20), (x + math.cos(a) * 26, GY - 20 + math.sin(a) * 26), 2)
    return [(sky, f0), (far, f1), (mid, f2), (near, f3)]


def cactus(surf, x, y, k):
    c, dark = (84, 122, 70), (40, 60, 36)
    def arm(points, w):
        pygame.draw.lines(surf, dark, False, points, int(w + 6))
        pygame.draw.lines(surf, c, False, points, int(w))
        for p in (points[0], points[-1]):
            pygame.draw.circle(surf, dark, p, (w + 6) / 2)
            pygame.draw.circle(surf, c, p, w / 2)
    arm([(x, y), (x, y - 150 * k)], 26 * k)
    arm([(x - 2, y - 70 * k), (x - 40 * k, y - 70 * k), (x - 40 * k, y - 112 * k)], 16 * k)
    arm([(x + 2, y - 92 * k), (x + 34 * k, y - 92 * k), (x + 34 * k, y - 126 * k)], 14 * k)


# ── 초원 ──
def build_grassland():
    rng = random.Random(7)
    sky, f0 = layer(0)
    vgrad(sky, (96, 162, 232), (214, 236, 250), 0, GY - 80)
    vgrad(sky, (214, 236, 250), (200, 230, 240), GY - 80)
    clouds, fc = layer(0.08)
    for _ in range(9):
        cx, cy = rng.randint(0, clouds.get_width()), rng.randint(TOP + 40, TOP + 300)
        for k in range(6):
            r = rng.randint(26, 52)
            pygame.draw.circle(clouds, (255, 255, 255, 230), (cx + rng.randint(-70, 70), cy + rng.randint(-14, 14)), r)
        pygame.draw.ellipse(clouds, (255, 255, 255, 230), (cx - 90, cy, 180, 34))
    far, f1 = layer(0.2)
    w = far.get_width()
    pts = ridge(rng, w, GY - 150, 50, 0.55)
    pygame.draw.polygon(far, (124, 172, 160), pts + [(w, far.get_height()), (0, far.get_height())])
    mid, f2 = layer(0.5)
    w = mid.get_width()
    pts = ridge(rng, w, GY - 90, 36, 0.5)
    pygame.draw.polygon(mid, (96, 160, 82), pts + [(w, mid.get_height()), (0, mid.get_height())])
    for _ in range(14):   # 나무
        x = rng.randint(0, w)
        y = min(p[1] for p in pts if abs(p[0] - x) < 30) + 10
        h = rng.randint(50, 90)
        pygame.draw.rect(mid, (96, 70, 46), (x - 4, y - h * 0.5, 8, h * 0.5))
        for dx, dy, r in ((0, -h * 0.75, h * 0.36), (-h * 0.22, -h * 0.55, h * 0.28), (h * 0.22, -h * 0.55, h * 0.28)):
            pygame.draw.circle(mid, (50, 112, 58), (x + dx, y + dy), r)
    near, f3 = layer(1.0)
    w = near.get_width()
    vgrad(near, (120, 182, 74), (80, 140, 54), GY - 36, near.get_height())
    for _ in range(4):    # 울타리
        x0 = rng.randint(0, w - 300)
        for k in range(5):
            pygame.draw.rect(near, (130, 96, 60), (x0 + k * 70, GY - 100, 10, 66))
        pygame.draw.rect(near, (150, 112, 70), (x0 - 6, GY - 88, 300, 8))
        pygame.draw.rect(near, (150, 112, 70), (x0 - 6, GY - 62, 300, 8))
    for _ in range(320):  # 풀잎
        x, y = rng.randint(0, w), rng.randint(GY - 34, near.get_height())
        h = rng.randint(6, 16)
        pygame.draw.line(near, (66, 120, 44), (x, y), (x + rng.randint(-4, 4), y - h), 2)
    for _ in range(60):   # 들꽃
        x, y = rng.randint(0, w), rng.randint(GY - 30, near.get_height() - 4)
        pygame.draw.circle(near, rng.choice([(250, 250, 250), (250, 220, 90), (240, 150, 170)]), (x, y), 3)
    return [(sky, f0), (clouds, fc), (far, f1), (mid, f2), (near, f3)]


# ── 뒷골목 ──
def build_alley():
    rng = random.Random(3)
    sky, f0 = layer(0)
    vgrad(sky, (16, 16, 34), (54, 40, 76))
    pygame.draw.circle(sky, (236, 232, 210), (1040, TOP + 110), 40)
    pygame.draw.circle(sky, (30, 28, 52), (1056, TOP + 100), 36)
    far, f1 = layer(0.25)
    w = far.get_width()
    x = -20
    while x < w:
        bw, bh = rng.randint(90, 180), rng.randint(260, 520)
        top = GY - 120 - bh
        pygame.draw.rect(far, (34, 32, 52), (x, top, bw, far.get_height()))
        for wy in range(top + 20, GY - 120, 34):
            for wx in range(x + 12, x + bw - 16, 26):
                if rng.random() < 0.35:
                    pygame.draw.rect(far, (238, 206, 120), (wx, wy, 12, 16))
        x += bw + rng.randint(4, 30)
    wall, f2 = layer(0.65)
    w = wall.get_width()
    pygame.draw.rect(wall, (84, 50, 46), (0, TOP + 130, w, wall.get_height()))
    for y in range(TOP + 130, wall.get_height(), 22):   # 벽돌
        off = 0 if (y // 22) % 2 else 24
        pygame.draw.line(wall, (64, 36, 34), (0, y), (w, y), 2)
        for x in range(off, w, 48):
            pygame.draw.line(wall, (64, 36, 34), (x, y), (x, y + 22), 2)
    for x in range(160, w, 520):   # 문, 배관, 환풍기
        pygame.draw.rect(wall, (40, 36, 44), (x, GY - 230, 110, 200))
        pygame.draw.rect(wall, (24, 22, 28), (x, GY - 230, 110, 200), 4)
        pygame.draw.circle(wall, (200, 180, 110), (x + 90, GY - 130), 5)
        pygame.draw.rect(wall, (90, 94, 104), (x + 200, TOP + 130, 14, GY - TOP - 160))
        pygame.draw.rect(wall, (120, 124, 132), (x + 300, GY - 360, 90, 60))
        for k in range(5):
            pygame.draw.line(wall, (70, 74, 84), (x + 306, GY - 352 + k * 12), (x + 384, GY - 352 + k * 12), 3)
    neon = font(64, "YujiBoku-Regular.ttf")
    for x, text, color in ((520, "拳", (255, 70, 90)), (1500, "酒", (90, 220, 255))):
        glow = pygame.Surface((200, 200), pygame.SRCALPHA)
        for r, a in ((90, 30), (64, 50)):
            pygame.draw.circle(glow, (*color, a), (100, 100), r)
        wall.blit(glow, (x - 100, GY - 520))
        pygame.draw.rect(wall, (30, 26, 34), (x - 50, GY - 470, 100, 100), border_radius=8)
        img = neon.render(text, True, color)
        wall.blit(img, img.get_rect(center=(x, GY - 420)))
    near, f3 = layer(1.0)
    w = near.get_width()
    vgrad(near, (54, 54, 64), (30, 30, 38), GY - 40, near.get_height())
    pygame.draw.rect(near, (80, 80, 90), (0, GY - 44, w, 10))
    for _ in range(10):   # 젖은 바닥에 비친 불빛
        x = rng.randint(0, w)
        pygame.draw.ellipse(near, (90, 96, 130), (x, GY + rng.randint(0, 40), rng.randint(60, 160), 8))
    for x in (60, 1240, 2200):   # 쓰레기통
        pygame.draw.rect(near, (50, 84, 70), (x, GY - 120, 130, 90), border_radius=6)
        pygame.draw.rect(near, (30, 54, 44), (x - 6, GY - 128, 142, 16), border_radius=4)
    pygame.draw.ellipse(near, (24, 24, 30), (1500, GY + 4, 120, 26))
    return [(sky, f0), (far, f1), (wall, f2), (near, f3)]


# ── 격투기 링 ──
def build_ring():
    rng = random.Random(5)
    back, f0 = layer(0)
    vgrad(back, (12, 10, 20), (40, 34, 52))
    beams = pygame.Surface(back.get_size(), pygame.SRCALPHA)
    for x in (240, 640, 1040):
        pygame.draw.polygon(beams, (255, 246, 200, 26), [(x - 30, 0), (x + 30, 0), (x + 230, GY), (x - 230, GY)])
    back.blit(beams, (0, 0))
    crowd, f1 = layer(0.35)
    w = crowd.get_width()
    for row, (y, col) in enumerate(((GY - 330, (34, 30, 44)), (GY - 280, (44, 38, 56)), (GY - 230, (54, 46, 66)))):
        for x in range(-20, w, 34):
            xx = x + rng.randint(-6, 6) + row * 12
            pygame.draw.circle(crowd, col, (xx, y), 14)
            pygame.draw.ellipse(crowd, col, (xx - 20, y + 10, 40, 60))
    for _ in range(30):
        pygame.draw.circle(crowd, (255, 255, 240), (rng.randint(0, w), rng.randint(GY - 350, GY - 220)), 3)
    pygame.draw.rect(crowd, (24, 20, 32), (0, GY - 190, w, crowd.get_height()))
    boards, f2 = layer(0.6)
    w = boards.get_width()
    f = font(40)
    for i, x in enumerate(range(0, w, 300)):
        color = (170, 34, 40) if i % 2 == 0 else (34, 70, 160)
        pygame.draw.rect(boards, color, (x, GY - 180, 296, 70))
        img = f.render("拳 · 足 · 斬" if i % 2 == 0 else "FIGHT", True, (250, 240, 220))
        boards.blit(img, img.get_rect(center=(x + 148, GY - 145)))
    pygame.draw.rect(boards, (20, 18, 26), (0, GY - 110, w, boards.get_height()))
    ring, f3 = layer(1.0)
    w = ring.get_width()
    vgrad(ring, (206, 210, 220), (170, 174, 186), GY - 60, ring.get_height())
    pygame.draw.ellipse(ring, (176, 40, 44), (w / 2 - 260, GY - 20, 520, 90), 8)
    for x in (24, w - 24):   # 코너 기둥
        pygame.draw.rect(ring, (60, 60, 70), (x - 12, GY - 300, 24, 270))
        pygame.draw.rect(ring, (200, 200, 210), (x - 16, GY - 306, 32, 14))
    for h, color in ((250, (200, 40, 44)), (200, (240, 240, 240)), (150, (40, 80, 180))):   # 로프
        pygame.draw.line(ring, (20, 20, 26), (24, GY - h), (w - 24, GY - h), 9)
        pygame.draw.line(ring, color, (24, GY - h), (w - 24, GY - h), 6)
    pygame.draw.rect(ring, (40, 40, 52), (0, GY - 66, w, 8))
    return [(back, f0), (crowd, f1), (boards, f2), (ring, f3)]


# ── 흰 방 ──
def build_white_room():
    wall, f0 = layer(0.6)
    w = wall.get_width()
    wall.fill((246, 246, 248))
    for x in range(0, w, 160):
        pygame.draw.line(wall, (232, 232, 238), (x, 0), (x, wall.get_height()), 2)
    floor, f1 = layer(1.0)
    w = floor.get_width()
    vgrad(floor, (232, 234, 238), (212, 214, 220), GY - 50, floor.get_height())
    pygame.draw.line(floor, (200, 202, 210), (0, GY - 50), (w, GY - 50), 2)
    vx = w / 2
    for x in range(-2000, w + 2000, 120):   # 바닥 원근 격자
        pygame.draw.line(floor, (220, 222, 228), (vx + (x - vx) * 0.35, GY - 50), (x, floor.get_height()), 1)
    for y in (GY - 30, GY, GY + 40, GY + 100):
        pygame.draw.line(floor, (220, 222, 228), (0, y), (w, y), 1)
    return [(wall, f0), (floor, f1)]


class Stage:
    def __init__(self, key, name, desc, builder):
        self.key, self.name, self.desc, self.builder = key, name, desc, builder
        self._layers = None
        self._thumb = {}

    @property
    def layers(self):
        if self._layers is None:
            self._layers = [(s.convert_alpha(), f) for s, f in self.builder()]
        return self._layers

    def draw(self, surf, cam):
        sx, sy = cam.shake
        for img, f in self.layers:
            surf.blit(img, (-(cam.x - CAM_MIN_X) * ZOOM * f + sx * f, -TOP + cam.rise * f + sy * f))

    def thumbnail(self, size):
        if size not in self._thumb:
            from camera import Camera
            full = pygame.Surface((SCREEN_W, SCREEN_H))
            self.draw(full, Camera())
            self._thumb[size] = pygame.transform.smoothscale(full, size)
        return self._thumb[size]


STAGES = [
    Stage("wasteland", "황야", "붉은 노을 아래 메마른 땅", build_wasteland),
    Stage("grassland", "초원", "바람이 지나가는 푸른 들판", build_grassland),
    Stage("alley", "뒷골목", "네온이 깜박이는 밤의 골목", build_alley),
    Stage("ring", "격투기 링", "함성이 쏟아지는 경기장", build_ring),
    Stage("white", "흰 방", "아무것도 없는 흰 방", build_white_room),
]

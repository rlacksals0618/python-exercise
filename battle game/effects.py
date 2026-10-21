"""타격 연출: 拳·足·斬 붓 원 이펙트, 불꽃 파편, 먼지, 화면 흔들림, 번쩍임.

이펙트 위치는 게임 세계 좌표로 저장하고, 그릴 때 카메라(view)로 화면 좌표로 바꾼다.
"""
import math
import os
import random

import pygame

from settings import BASE_DIR, EFFECT_COLORS, EFFECT_FILES, EFFECT_SIZE, ZOOM

EFFECT_ZOOM = ZOOM * 0.8   # 캐릭터가 커진 만큼 이펙트도 키우되, 화면을 덮지 않게 조금 덜 키운다
MAX_EFFECT = 760


def ease_out_back(t, s=1.70158):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


class EffectImages:
    """이펙트 원본(1024px)을 불러와 크기별로 한 번만 줄여 둔다."""

    def __init__(self):
        self.base = {}
        for kind, name in EFFECT_FILES.items():
            path = os.path.join(BASE_DIR, name)
            try:
                self.base[kind] = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self.base[kind] = self._fallback(kind)
        self._cache = {}

    @staticmethod
    def _fallback(kind):
        surf = pygame.Surface((256, 256), pygame.SRCALPHA)
        pygame.draw.circle(surf, EFFECT_COLORS[kind], (128, 128), 110, 18)
        return surf

    def get(self, kind, size):
        size = max(8, int(size))
        key = (kind, size)
        if key not in self._cache:
            self._cache[key] = pygame.transform.smoothscale(self.base[kind], (size, size))
        return self._cache[key]


class Enso:
    """붓 원 이펙트 하나: 튀어나오듯 커졌다가 살짝 퍼지며 사라진다."""

    def __init__(self, images, kind, pos, size, life=34, alpha=255, screen=False):
        """screen=True면 pos를 화면 좌표로 보고 확대하지 않는다(필살기 연출용)."""
        self.kind, self.pos, self.life = kind, pygame.Vector2(pos), life
        self.size = size if screen else min(MAX_EFFECT, size * EFFECT_ZOOM)
        self.alpha = alpha
        self.t = 0
        self.screen = screen
        angle = random.uniform(-18, 18)
        self.img = pygame.transform.rotozoom(images.get(kind, self.size * 1.15), angle, 1.0)

    def update(self):
        self.t += 1
        return self.t < self.life

    def draw(self, surf, view):
        t = self.t
        pop = 8
        if t < pop:
            k = 0.55 + 0.6 * ease_out_back(t / pop)
        else:
            k = 1.15 + 0.12 * (t - pop) / (self.life - pop)
        fade = 1.0 if t < self.life - 14 else max(0.0, (self.life - t) / 14)
        a = int(self.alpha * fade)
        if a <= 3:
            return
        w = max(4, int(self.size * k))
        img = pygame.transform.smoothscale(self.img, (w, w)) if w != self.img.get_width() else self.img.copy()
        img.set_alpha(a)
        if self.screen:
            center = (self.pos.x + view.shake[0], self.pos.y + view.shake[1])
        else:
            center = view.to_screen(self.pos)
        surf.blit(img, img.get_rect(center=center))


class Spark:
    def __init__(self, pos, vel, color, life, width):
        self.pos, self.vel = pygame.Vector2(pos), pygame.Vector2(vel)
        self.color, self.life, self.max_life, self.width = color, life, life, width

    def update(self):
        self.pos += self.vel
        self.vel *= 0.86
        self.vel.y += 0.15
        self.life -= 1
        return self.life > 0

    def draw(self, surf, view):
        k = self.life / self.max_life
        p = view.to_screen(self.pos)
        q = view.to_screen(self.pos - self.vel * 2.2)
        pygame.draw.line(surf, self.color, q, p, max(1, int((self.width * k + 1) * view.zoom * 0.7)))


class Effects:
    def __init__(self, images):
        self.images = images
        self.back = []      # 캐릭터 뒤에 그릴 이펙트(필살기 시작 등)
        self.front = []     # 캐릭터 앞에 그릴 이펙트(타격)
        self.sparks = []
        self.shake_amp = 0.0
        self.offset = (0, 0)
        self.flash_color, self.flash_t, self.flash_len, self.flash_alpha = (255, 255, 255), 0, 1, 150
        self.darken = 0

    def clear(self):
        self.back.clear()
        self.front.clear()
        self.sparks.clear()
        self.shake_amp = 0
        self.flash_t = 0
        self.darken = 0

    def hit(self, kind, pos, tier, direction, blocked=False):
        size = EFFECT_SIZE[tier] * (0.55 if blocked else 1.0)
        self.front.append(Enso(self.images, kind, pos, size, life=26 if blocked else 34,
                               alpha=150 if blocked else 255))
        color = (235, 235, 255) if blocked else EFFECT_COLORS[kind]
        for _ in range(6 + tier * 3 if not blocked else 5):
            ang = math.radians(random.uniform(-70, 70)) if direction > 0 else math.radians(random.uniform(110, 250))
            speed = random.uniform(5, 9 + tier * 2)
            self.sparks.append(Spark(pos, (math.cos(ang) * speed, math.sin(ang) * speed - 1.5),
                                     color, random.randint(10, 18), random.uniform(2, 3 + tier)))
        for _ in range(4):
            ang = random.uniform(0, math.tau)
            speed = random.uniform(2, 5)
            self.sparks.append(Spark(pos, (math.cos(ang) * speed, math.sin(ang) * speed),
                                     (255, 250, 235), random.randint(6, 10), 2))

    def aura(self, kind, pos, size, alpha=170, life=40, screen=False):
        self.back.append(Enso(self.images, kind, pos, size, life=life, alpha=alpha, screen=screen))

    def dust(self, pos, amount=6):
        for _ in range(amount):
            ang = math.radians(random.uniform(190, 350))
            speed = random.uniform(1, 3.5)
            self.sparks.append(Spark(pos, (math.cos(ang) * speed * 1.6, math.sin(ang) * speed * 0.5),
                                     (150, 135, 115), random.randint(10, 18), 3))

    def shake(self, amount):
        self.shake_amp = max(self.shake_amp, amount)

    def flash(self, color, ticks, alpha=150):
        self.flash_color, self.flash_t, self.flash_len, self.flash_alpha = color, ticks, ticks, alpha

    def update(self):
        self.back = [e for e in self.back if e.update()]
        self.front = [e for e in self.front if e.update()]
        self.sparks = [s for s in self.sparks if s.update()]
        if self.shake_amp > 0.3:
            a = self.shake_amp
            self.offset = (random.uniform(-a, a), random.uniform(-a, a) * 0.6)
            self.shake_amp *= 0.85
        else:
            self.shake_amp, self.offset = 0, (0, 0)
        if self.flash_t > 0:
            self.flash_t -= 1
        if self.darken > 0:
            self.darken -= 1

    def draw_back(self, surf, view):
        for e in self.back:
            e.draw(surf, view)

    def draw_front(self, surf, view):
        for e in self.front:
            e.draw(surf, view)
        for s in self.sparks:
            s.draw(surf, view)

    def draw_flash(self, surf):
        if self.flash_t > 0:
            overlay = pygame.Surface(surf.get_size())
            overlay.fill(self.flash_color)
            overlay.set_alpha(int(self.flash_alpha * self.flash_t / self.flash_len))
            surf.blit(overlay, (0, 0))

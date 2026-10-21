"""카메라: 게임 세계 좌표를 화면 좌표로 바꾼다.

게임 로직(이동·판정·AI)은 그대로 두고, 그릴 때만 ZOOM배로 확대한다.
두 캐릭터의 가운데를 부드럽게 따라가고, 높이 뛰면 화면도 따라 올라간다.
"""
import pygame

from settings import CAM_MAX_X, CAM_MIN_X, GROUND_SCREEN, GROUND_Y, SCREEN_W, ZOOM


class View:
    """확대 비율과 기준점만 가진 단순한 보기(캐릭터 선택·결과 화면용)."""

    def __init__(self, zoom=1.0, cx=SCREEN_W / 2, ground=GROUND_Y, screen_x=SCREEN_W / 2):
        self.zoom, self.x, self.ground, self.screen_x = zoom, cx, ground, screen_x
        self.shake = (0, 0)

    def to_screen(self, p):
        return ((p[0] - self.x) * self.zoom + self.screen_x + self.shake[0],
                (p[1] - GROUND_Y) * self.zoom + self.ground + self.shake[1])

    def rect(self, r):
        x, y = self.to_screen(r.topleft)
        return pygame.Rect(round(x), round(y), round(r.w * self.zoom), round(r.h * self.zoom))

    @property
    def rise(self):
        return self.ground - GROUND_SCREEN


class Camera(View):
    def __init__(self):
        super().__init__(ZOOM, (CAM_MIN_X + CAM_MAX_X) / 2, GROUND_SCREEN)

    def snap(self, fighters):
        self.x, self.ground = self._target(fighters)

    def _target(self, fighters):
        mid = sum(f.pos.x for f in fighters) / len(fighters)
        x = max(CAM_MIN_X, min(CAM_MAX_X, mid))
        # 높이 뛴 캐릭터가 화면 위로 잘리지 않게 바닥선을 아래로 내린다
        height = max(GROUND_Y - f.pos.y for f in fighters)
        ground = GROUND_SCREEN + max(0.0, height - 30) * self.zoom * 0.6
        return x, ground

    def update(self, fighters):
        x, ground = self._target(fighters)
        self.x += (x - self.x) * 0.15
        self.ground += (ground - self.ground) * 0.18

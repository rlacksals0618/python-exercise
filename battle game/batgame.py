"""권 · 족 · 참 - 팔·발 공격과 방향키 콤보로 겨루는 2D 격투 게임.

실행: python batgame.py   (웹 버전은 build_web.py로 만든다)
조작(기본값): P1 = W/A/S/D 이동, F 팔 공격, G 발 공격
              P2 = 방향키 이동, K 팔 공격, L 발 공격
Esc 일시정지, F1 판정 상자 보기, F2 입력 기록 보기, F11 전체 화면
"""
import asyncio
import sys

import pygame

import ui
from controls import KeyConfig
from effects import EffectImages
from scenes import SceneManager, TitleScene
from settings import CAPTION, FPS, SCREEN_H, SCREEN_W

WEB = sys.platform == "emscripten"   # pygbag으로 브라우저에서 돌고 있는가


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(CAPTION)
        flags = pygame.SCALED | pygame.RESIZABLE
        try:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags, vsync=0 if WEB else 1)
        except pygame.error:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        self.clock = pygame.time.Clock()
        self.config = KeyConfig()
        self.images = EffectImages()
        pygame.display.set_icon(self.images.get("fist", 64))
        self.paper = ui.paper_texture((SCREEN_W, SCREEN_H))
        self.manager = SceneManager()
        self.manager.push(TitleScene(self))
        self.running = True

    async def run(self):
        dt = 1 / FPS
        acc = 0.0
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11 and not WEB:
                    pygame.display.toggle_fullscreen()
                else:
                    self.manager.handle_event(e)
            # 고정 타임스텝: 로직은 항상 1/60초 단위로, 그리기는 남은 시간만큼 보간
            acc += min(self.clock.tick(60 if WEB else 144) / 1000, 0.25)
            while acc >= dt and self.running:
                self.manager.update()
                acc -= dt
            self.manager.draw(self.screen, min(1.0, acc / dt))
            pygame.display.flip()
            await asyncio.sleep(0)   # 브라우저에 차례를 넘긴다(데스크톱에서는 영향 없음)
        pygame.quit()


async def main():
    await App().run()


if __name__ == "__main__":
    asyncio.run(main())

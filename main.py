#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WARHAMMER FORGED IN THE DARK - Gestor de Personajes y Partidas para el juego de rol de mesa warhammer fantasy en versión Forged in the Dark
Carga dungeons creados con el Editor de Dungeons.
"""

from screens.screen_main import ScreenMain
from constants import SCREEN_W, SCREEN_H, TITLE, FPS
import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class WarhammerGame:
    def __init__(self):
        pygame.init()
        pygame.freetype.init()

        self.screen = pygame.display.set_mode(
            (SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE + " - Juego")

        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = ScreenMain(self)
        self._party_state = None

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h), pygame.RESIZABLE)
                else:
                    self.current_screen.handle_event(event)

            self.current_screen.update(dt)
            self.current_screen.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = WarhammerGame()
    game.run()

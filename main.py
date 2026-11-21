#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORGED IN THE DARK FANTASY - Juego de rol de ordenador al estilo de los dungeon crawlers
en primera persona de finales de los 80 (The Bard's Tale, Might and Magic, Eye of the
Beholder), con el reglamento FORGED IN THE DARK FANTASY.
Carga dungeons creados con el Editor de Dungeons (carpeta data/dungeons).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from constants import SCREEN_W, SCREEN_H, TITLE, FPS
from screens.screen_main import ScreenMain


class FantasyGame:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass

        self.screen = pygame.display.set_mode(
            (SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        pygame.key.start_text_input()

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
                    self.screen = pygame.display.get_surface()
                else:
                    self.current_screen.handle_event(event)

            self.screen = pygame.display.get_surface()
            self.current_screen.update(dt)
            self.current_screen.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = FantasyGame()
    game.run()

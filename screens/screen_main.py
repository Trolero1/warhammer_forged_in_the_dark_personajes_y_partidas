# screens/screen_main.py - Pantalla principal

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button
from screens.screen_personajes import ScreenPersonajesManager
from screens.screen_partidas import ScreenPartidasManager


class ScreenMain:
    def __init__(self, app):
        self.app = app
        W = app.screen.get_width()
        
        btn_w, btn_h, gap = 220, 60, 24
        total_w = 3 * btn_w + 2 * gap
        start_x = W // 2 - total_w // 2
        
        self.btn_personajes = Button((start_x, 380, btn_w, btn_h),
                                     "👥  PERSONAJES", font_size=18, bold=True)
        self.btn_partidas = Button((start_x + btn_w + gap, 380, btn_w, btn_h),
                                   "🎲  PARTIDAS", font_size=18, bold=True)
        self.btn_salir = Button((start_x + 2 * (btn_w + gap), 380, btn_w, btn_h),
                                "🚪  SALIR", font_size=18, bold=True,
                                color=C_ERROR)
        
        self.buttons = [self.btn_personajes, self.btn_partidas, self.btn_salir]
        self.active_screen = None
    
    def handle_event(self, event):
        if self.active_screen:
            self.active_screen.handle_event(event)
            if hasattr(self.active_screen, 'closed') and self.active_screen.closed:
                self.active_screen = None
            return
        
        if self.btn_personajes.handle_event(event):
            self.active_screen = ScreenPersonajesManager(self.app)
        elif self.btn_partidas.handle_event(event):
            self.active_screen = ScreenPartidasManager(self.app)
        elif self.btn_salir.handle_event(event):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def update(self, dt):
        if self.active_screen:
            self.active_screen.update(dt)
            return
        mp = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update_hover(mp)
    
    def draw(self, surf):
        if self.active_screen:
            self.active_screen.draw(surf)
            return
        
        surf.fill(C_FONDO)
        self._draw_header(surf)
        
        W = surf.get_width()
        draw_text(surf, "Sistema de juego Warhammer Forged in the Dark", W // 2 - 180, 190, 18, C_SUBTITULO, bold=True)
        draw_text(surf, "Crea personajes y juega partidas usando dungeons personalizados",
                  W // 2 - 280, 230, 14, C_TEXTO_DIM, max_width=560)
        
        for btn in self.buttons:
            btn.draw(surf)
    
    def _draw_header(self, surf):
        W = surf.get_width()
        draw_text(surf, "WARHAMMER", W // 2 - 180, 40, 60, C_TITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)
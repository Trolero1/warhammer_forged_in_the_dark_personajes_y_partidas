# screens/screen_main.py - Pantalla principal

import pygame
from constants import *
from ui_utils import draw_text
from formularios import boton


class ScreenMain:
    def __init__(self, app):
        self.app = app
        self.botones = [("PERSONAJES", self._personajes), ("AVENTURAS", self._partidas), ("SALIR", self._salir)]

    def _rects(self):
        W, H = self.app.screen.get_size()
        bw, bh, gap = 240, 60, 24
        x0 = W // 2 - (len(self.botones) * bw + (len(self.botones) - 1) * gap) // 2
        return [pygame.Rect(x0 + i * (bw + gap), 380, bw, bh) for i in range(len(self.botones))]

    def _personajes(self):
        from screens.screen_personajes import ScreenPersonajesManager
        self.app.current_screen = ScreenPersonajesManager(self.app)

    def _partidas(self):
        from screens.screen_partidas import ScreenPartidasManager
        self.app.current_screen = ScreenPartidasManager(self.app)

    def _salir(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for r, (t, f) in zip(self._rects(), self.botones):
                if r.collidepoint(event.pos):
                    f()
                    return

    def update(self, dt):
        pass

    def draw(self, surf):
        from screens.screen_partidas import dibujar_cabecera
        W, H = surf.get_size()
        surf.fill(C_FONDO)
        dibujar_cabecera(surf)
        for i, t in enumerate(["Un juego de rol de fantasía con el sistema Forged in the Dark",
                               "Crea personajes y explora dungeons en primera persona, casilla a casilla"]):
            draw_text(surf, t, W // 2 - len(t) * 4 - (len(t) // 2 if i == 0 else 0), 190 + i * 36,
                      18 if i == 0 else 14, C_SUBTITULO if i == 0 else C_TEXTO_DIM, bold=(i == 0))
        for r, (t, f) in zip(self._rects(), self.botones):
            boton(surf, r, t, 18, color=C_ERROR if t == "SALIR" else None)
        draw_text(surf, "Basado en Blades in the Dark (John Harper / One Seven Design)", 20, H - 28, 11, C_TEXTO_DIM)

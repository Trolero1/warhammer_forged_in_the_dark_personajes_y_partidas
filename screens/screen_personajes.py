# screens/screen_personajes.py - Gestión de personajes: crear, ver (cargar) y eliminar

import pygame
from constants import *
from ui_utils import draw_text
from formularios import boton, mensaje, confirmar, elegir
import persistence


class ScreenPersonajesManager:
    def __init__(self, app):
        self.app = app
        self.botones = [("CREAR", self._crear), ("VER FICHA", self._cargar),
                        ("ELIMINAR", self._eliminar), ("VOLVER", self._volver)]

    def _rects(self):
        W, H = self.app.screen.get_size()
        bw, bh, gap = 220, 56, 20
        x0 = W // 2 - (len(self.botones) * bw + (len(self.botones) - 1) * gap) // 2
        return [pygame.Rect(x0 + i * (bw + gap), 380, bw, bh) for i in range(len(self.botones))]

    def _crear(self):
        from screens.screen_personaje_creador import ScreenPersonajeCreador
        self.app.current_screen = ScreenPersonajeCreador(self.app)

    def _volver(self):
        from screens.screen_main import ScreenMain
        self.app.current_screen = ScreenMain(self.app)

    def _elegir(self, titulo):
        personajes = persistence.listar_personajes()
        if not personajes:
            mensaje(self.app.screen, "PERSONAJES", "No hay personajes guardados.")
            return None
        idx = elegir(self.app.screen, titulo,
                     [f"#{p['numero']} {p['nombre']} — {p['raza']} {p['profesion']}" for p in personajes])
        return personajes[idx] if idx is not None else None

    def _cargar(self):
        p = self._elegir("ELIGE PERSONAJE")
        if not p:
            return
        try:
            personaje = persistence.cargar_personaje(p["id"])
        except Exception as e:
            mensaje(self.app.screen, "ERROR", f"No se pudo cargar: {e}")
            return
        from screens.screen_ficha_personaje import ScreenFichaPersonaje
        self.app.current_screen = ScreenFichaPersonaje(self.app, personaje)

    def _eliminar(self):
        p = self._elegir("ELIGE PERSONAJE A ELIMINAR")
        if p and confirmar(self.app.screen, f"¿Eliminar el personaje «{p['nombre']}»? No se puede deshacer."):
            persistence.eliminar_personaje(p["id"])
            mensaje(self.app.screen, "ELIMINAR", f"Personaje «{p['nombre']}» eliminado.")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for r, (t, f) in zip(self._rects(), self.botones):
                if r.collidepoint(event.pos):
                    f()
                    return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._volver()

    def update(self, dt):
        pass

    def draw(self, surf):
        from screens.screen_partidas import dibujar_cabecera
        W, H = surf.get_size()
        surf.fill(C_FONDO)
        dibujar_cabecera(surf)
        t = "PERSONAJES"
        draw_text(surf, t, W // 2 - len(t) * 9, 190, 30, C_SUBTITULO, bold=True)
        s = "Crea nuevos aventureros, consulta su ficha o elimínalos"
        draw_text(surf, s, W // 2 - len(s) * 4, 240, 14, C_TEXTO_DIM)
        n = len(persistence.listar_personajes())
        draw_text(surf, f"Personajes guardados: {n}", W // 2 - 110, 290, 14, C_TEXTO)
        for r, (t, f) in zip(self._rects(), self.botones):
            boton(surf, r, t, 16, color=C_ERROR if t == "ELIMINAR" else None)

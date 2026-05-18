# screens/screen_ficha_personaje.py
# Pantalla para ver la ficha de un personaje ya guardado

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button, ScrollArea
from models import Personaje, TODAS_LAS_HABILIDADES
from screens.screen_personaje_creador import CARACTERISTICAS


def text_size(text, size, bold=False):
    font = get_font(size, bold=bold)
    return font.size(text)


class ScreenFichaPersonaje:
    def __init__(self, app, personaje: Personaje):
        self.app = app
        self.personaje = personaje
        self.scroll = ScrollArea()
        W = app.screen.get_width()
        self.btn_volver = Button((W - 180, 20, 160, 40), "VOLVER", font_size=14, bold=True)
        self._build_content_height()

    def _build_content_height(self):
        n_habs = len([h for h in self.personaje.habilidades.values() if h > 0])
        h = 500 + n_habs * 18 + 200
        self.scroll.set_content_height(h, self.app.screen.get_height() - 120)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        if self.btn_volver.handle_event(event, self.scroll.offset):
            from screens.screen_personajes import ScreenPersonajesManager
            self.app.current_screen = ScreenPersonajesManager(self.app)

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.btn_volver.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        surf.fill(C_FONDO)
        self._draw_header(surf)
        W = surf.get_width()
        p = self.personaje
        off = self.scroll.offset

        draw_text(surf, "FICHA DE PERSONAJE", W // 2 - 150, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)

        y = 210
        nombre_txt = f"#{p.numero} {p.nombre} '{p.apodo}'"
        draw_text(surf, nombre_txt, 80, y - off, 22, C_TITULO, bold=True)
        y += 30
        draw_text(surf, f"{p.raza}  ·  {p.profesion}  ·  {p.edad}", 80, y - off, 15, C_SUBTITULO)
        y += 22
        if p.fecha_creacion:
            draw_text(surf, f"Creado: {p.fecha_creacion}", 80, y - off, 11, C_TEXTO_DIM)
            y += 16

        pygame.draw.line(surf, C_SEPARADOR, (80, y - off), (W - 80, y - off), 1)
        y += 12

        a = p.atributos
        draw_text(surf, f"ATRIBUTOS:  CUE {a['CUE']}  INT {a['INT']}  VOL {a['VOL']}", 80, y - off, 14, C_TITULO, bold=True)
        y += 22
        draw_text(surf, f"Estrés: {p.estres}/10  |  Corrupción: {p.corrupcion}/10  |  Nivel: {p.nivel}", 80, y - off, 13, C_TEXTO)
        y += 18
        draw_text(surf, f"Heridas:  Leves {p.heridas_leves}/3  |  Graves {p.heridas_graves}/2  |  Muy Graves {p.heridas_muy_graves}/1", 80, y - off, 13, C_TEXTO)
        y += 22

        pygame.draw.line(surf, C_SEPARADOR, (80, y - off), (W - 80, y - off), 1)
        y += 10
        draw_text(surf, "HABILIDADES", 80, y - off, 14, C_TITULO, bold=True)
        y += 20

        habs_con_valor = {h: v for h, v in sorted(p.habilidades.items()) if v > 0}
        mitad = (len(habs_con_valor) + 1) // 2
        col_x = [80, W // 2 + 20]
        for ci in range(2):
            items = list(habs_con_valor.items())[ci * mitad:(ci + 1) * mitad]
            for hi, (hab, val) in enumerate(items):
                hy = y + hi * 18 - off
                if -18 < hy < surf.get_height():
                    draw_text(surf, f"{hab}: {val}", col_x[ci], hy, 12, C_TEXTO)
        y += mitad * 18 + 10

        pygame.draw.line(surf, C_SEPARADOR, (80, y - off), (W - 80, y - off), 1)
        y += 8
        if p.raza in CARACTERISTICAS:
            draw_text(surf, "CARACTERÍSTICA RACIAL", 80, y - off, 13, C_TITULO, bold=True)
            y += 18
            draw_text(surf, CARACTERISTICAS[p.raza], 80, y - off, 12, C_TEXTO, max_width=W - 160)
            y += 30

        for etiqueta, valor in [
            ("DEBILIDAD", p.debilidad),
            ("MOTIVACIÓN", p.motivacion),
            ("VICIO", p.vicio),
            ("EQUIPO", p.equipo),
        ]:
            if valor:
                pygame.draw.line(surf, C_SEPARADOR, (80, y - off), (W - 80, y - off), 1)
                y += 8
                draw_text(surf, etiqueta, 80, y - off, 13, C_TITULO, bold=True)
                y += 18
                draw_text(surf, str(valor), 80, y - off, 12, C_TEXTO, max_width=W - 160)
                y += 30

        if p.recuerdos:
            pygame.draw.line(surf, C_SEPARADOR, (80, y - off), (W - 80, y - off), 1)
            y += 8
            draw_text(surf, "RECUERDOS", 80, y - off, 13, C_TITULO, bold=True)
            y += 18
            for rec in p.recuerdos:
                draw_text(surf, f"  ·  {rec}", 80, y - off, 12, C_TEXTO)
                y += 16

        if p.aspecto:
            pygame.draw.line(surf, C_SEPARADOR, (80, y - off), (W - 80, y - off), 1)
            y += 8
            draw_text(surf, "ASPECTO", 80, y - off, 13, C_TITULO, bold=True)
            y += 18
            draw_text(surf, "  ·  ".join(p.aspecto), 80, y - off, 12, C_TEXTO, max_width=W - 160)
            y += 30

        for label, val in [("ORIGEN", p.trasfondo_origen), ("NIÑEZ", p.trasfondo_ninez),
                           ("ADOLESCENCIA", p.trasfondo_adolescencia), ("JUVENTUD", p.trasfondo_juventud)]:
            if val:
                pygame.draw.line(surf, C_SEPARADOR, (80, y - off), (W - 80, y - off), 1)
                y += 8
                draw_text(surf, f"TRASFONDO - {label}", 80, y - off, 13, C_TITULO, bold=True)
                y += 18
                draw_text(surf, val, 80, y - off, 12, C_TEXTO, max_width=W - 160)
                y += 30

        self.btn_volver.draw(surf, off)
        self.scroll.set_content_height(y + 60, self.app.screen.get_height() - 120)
        self.scroll.draw_scrollbar(surf, pygame.Rect(0, 120, W, surf.get_height() - 120))

    def _draw_header(self, surf):
        W = surf.get_width()
        draw_text(surf, "WARHAMMER", W // 2 - 180, 40, 60, C_TITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)

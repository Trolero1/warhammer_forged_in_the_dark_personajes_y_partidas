# screens/screen_partidas.py - Gestión de partidas

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button, MessageDialog, ConfirmDialog, ScrollList, TextInput
import persistence
from screens import screen_game
from models import Partida


class ScreenPartidasManager:
    def __init__(self, app):
        self.app = app
        W = app.screen.get_width()

        btn_w, btn_h, gap = 180, 56, 24
        total_w = 4 * btn_w + 3 * gap
        start_x = W // 2 - total_w // 2

        self.btn_nueva = Button((start_x, 390, btn_w, btn_h),
                                "NUEVA", font_size=16, bold=True,
                                color=(106, 48, 16))
        self.btn_cargar = Button((start_x + btn_w + gap, 390, btn_w, btn_h),
                                 "CARGAR", font_size=16, bold=True)
        self.btn_eliminar = Button((start_x + 2 * (btn_w + gap), 390, btn_w, btn_h),
                                   "ELIMINAR", font_size=16, bold=True,
                                   color=C_ERROR)
        self.btn_inicio = Button((start_x + 3 * (btn_w + gap), 390, btn_w, btn_h),
                                 "INICIO", font_size=16, bold=True,
                                 color=(40, 40, 80))

        self.buttons = [self.btn_nueva, self.btn_cargar, self.btn_eliminar, self.btn_inicio]
        self.closed = False
        self._pending_continue = hasattr(app, '_party_state') and app._party_state is not None

    def handle_event(self, event):
        if self.btn_inicio.handle_event(event):
            self.app._party_state = None
            if self.app.current_screen is self:
                from screens.screen_main import ScreenMain
                self.app.current_screen = ScreenMain(self.app)
            else:
                self.closed = True
            return
        if self.btn_nueva.handle_event(event):
            self._nueva_partida()
        elif self.btn_cargar.handle_event(event):
            self._cargar_partida()
        elif self.btn_eliminar.handle_event(event):
            self._eliminar_partida()

    def _nueva_partida(self):
        nombre = self._ask_name("Nombre de la nueva partida:")
        if not nombre:
            return

        dungeons = persistence.listar_dungeons()
        if not dungeons:
            MessageDialog(self.app.screen, "No hay dungeons disponibles. Crea uno primero con el Editor de Dungeons.").run()
            return

        idx = self._pick_dungeon(dungeons, "SELECCIONA DUNGEON")
        if idx is None:
            return

        dungeon = persistence.cargar_dungeon(dungeons[idx]["id"])

        self.app._party_state = {
            "nombre": nombre,
            "dungeon": dungeon,
            "seleccionados_ids": [],
        }
        self._seleccionar_siguiente_personaje()

    def _seleccionar_siguiente_personaje(self):
        state = self.app._party_state
        i = len(state["seleccionados_ids"]) + 1
        if i > 4:
            self._iniciar_partida()
            return

        # Refresh desde disco: siempre carga los templates (personajes creados)
        todos = persistence.listar_personajes()
        disponibles = [p for p in todos if p["id"] not in state["seleccionados_ids"]]

        opciones = list(disponibles)
        crear_opcion = {"id": "__crear__", "numero": 0, "nombre": "[CREAR NUEVO PERSONAJE]", "raza": "", "profesion": ""}
        opciones.insert(0, crear_opcion)

        idx = self._pick_personaje_con_crear(opciones, f"ELIGE PERSONAJE {i} PARA EL GRUPO (o crea uno nuevo)")
        if idx is None:
            self.app._party_state = None
            return

        seleccionado = opciones[idx]
        if seleccionado["id"] == "__crear__":
            from screens.screen_personaje_creador import ScreenPersonajeCreador
            self.app.current_screen = ScreenPersonajeCreador(self.app)
        else:
            # Carga el template desde disco (siempre fresco, copia para la partida)
            state["seleccionados_ids"].append(seleccionado["id"])
            self._seleccionar_siguiente_personaje()

    def _iniciar_partida(self):
        state = self.app._party_state
        if not state:
            return

        # Carga cada template desde disco y lo COPIA para la partida
        personajes_partida = []
        for pid in state["seleccionados_ids"]:
            p = persistence.cargar_personaje(pid)
            personajes_partida.append(p)

        partida = Partida()
        partida.nombre = state["nombre"]
        partida.dungeon_id = state["dungeon"].id
        partida.personajes = personajes_partida
        partida.room_actual_id = state["dungeon"].rooms[0].id if state["dungeon"].rooms else ""
        self.app._party_state = None
        partida, dungeon = screen_game.run_game(self.app.screen, partida, state["dungeon"])

    def _cargar_partida(self):
        nombres = persistence.listar_nombres_partidas()
        if not nombres:
            MessageDialog(self.app.screen, "No hay partidas guardadas.").run()
            return

        idx_n = self._pick_from_list(nombres, "ELIGE PARTIDA")
        if idx_n is None:
            return

        guardados = persistence.listar_guardados_partida(nombres[idx_n])
        if not guardados:
            MessageDialog(self.app.screen, "No hay guardados para esta partida.").run()
            return

        labels = [f"{g['nombre']} - {g['fecha_guardado']} - {g['dungeon_nombre']}" for g in guardados]
        idx_g = self._pick_from_list(labels, "ELIGE GUARDADO")
        if idx_g is None:
            return

        partida, dungeon = persistence.cargar_guardado(guardados[idx_g]["path"])
        partida, dungeon = screen_game.run_game(self.app.screen, partida, dungeon)

    def _eliminar_partida(self):
        nombres = persistence.listar_nombres_partidas()
        if not nombres:
            MessageDialog(self.app.screen, "No hay partidas guardadas.").run()
            return

        idx = self._pick_from_list(nombres, "ELIGE PARTIDA A ELIMINAR")
        if idx is None:
            return

        if ConfirmDialog(self.app.screen, f"Eliminar TODOS los guardados de '{nombres[idx]}'?").run():
            persistence.eliminar_partida(nombres[idx])
            MessageDialog(self.app.screen, f"Partida '{nombres[idx]}' eliminada.").run()

    def _pick_dungeon(self, dungeons, title):
        labels = [f"{d['nombre']} ({d['num_rooms']} rooms) - {d['fecha_creacion']}" for d in dungeons]
        return self._pick_from_list(labels, title)

    def _pick_personaje_con_crear(self, opciones, title):
        labels = []
        for p in opciones:
            if p["id"] == "__crear__":
                labels.append("+  CREAR NUEVO PERSONAJE")
            else:
                labels.append(f"#{p['numero']} {p['nombre']} - {p['raza']} {p['profesion']}")
        return self._pick_from_list(labels, title)

    def _pick_from_list(self, items, title):
        W, H = self.app.screen.get_width(), self.app.screen.get_height()
        rect = pygame.Rect(W // 2 - 350, H // 2 - 200, 700, 400)
        sl = ScrollList(rect, items, font_size=14, title=title)
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                idx = sl.handle_event(event)
                if idx is not None:
                    return idx

            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.app.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.app.screen, DARK_GRAY, rect, border_radius=6)
            pygame.draw.rect(self.app.screen, GOLD, rect, 2, border_radius=6)
            sl.draw(self.app.screen)
            hint = get_font(12).render("ESC para cancelar", True, MID_GRAY)
            self.app.screen.blit(hint, (rect.x + 10, rect.bottom - 18))
            pygame.display.flip()
            clock.tick(30)

    def _ask_name(self, prompt):
        W, H = self.app.screen.get_width(), self.app.screen.get_height()
        rect = pygame.Rect(W // 2 - 300, H // 2 - 40, 600, 80)
        inp = TextInput((rect.x + 10, rect.y + 40, rect.width - 20, 30), prompt="", font_size=17)
        clock = pygame.time.Clock()

        while not inp.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                inp.handle_event(event)

            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.app.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.app.screen, DARK_GRAY, rect, border_radius=6)
            pygame.draw.rect(self.app.screen, GOLD, rect, 2, border_radius=6)
            draw_text(self.app.screen, prompt, rect.x + 10, rect.y + 10, 16, YELLOW, bold=True)
            inp.draw(self.app.screen)
            pygame.display.flip()
            clock.tick(30)

        return inp.text.strip() or None

    def update(self, dt):
        if self._pending_continue:
            self._pending_continue = False
            self._seleccionar_siguiente_personaje()
            return
        mp = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update_hover(mp)

    def draw(self, surf):
        surf.fill(C_FONDO)
        self._draw_header(surf)

        W = surf.get_width()
        draw_text(surf, "GESTIÓN DE PARTIDAS", W // 2 - 150, 190, 28, C_SUBTITULO, bold=True)
        draw_text(surf, "Inicia nuevas aventuras, carga partidas guardadas o elimínalas",
                  W // 2 - 280, 240, 14, C_TEXTO_DIM, max_width=560)

        for btn in self.buttons:
            btn.draw(surf)

    def _draw_header(self, surf):
        W = surf.get_width()
        draw_text(surf, "WARHAMMER", W // 2 - 180, 40, 60, C_TITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)

# screens/screen_partidas.py - Gestión de aventuras (partidas)
#
# NUEVA: elige un dungeon y forma un grupo (de 1 a 6 personajes; puedes crear
# personajes nuevos sin salir). Los personajes se COPIAN a la partida: su progreso
# se guarda en la partida (y opcionalmente en sus fichas al salir del juego).
# CARGAR: elige una aventura y uno de sus guardados.
# ELIMINAR: borra una aventura con todos sus guardados.

import pygame
from constants import *
from ui_utils import draw_text
from formularios import mensaje, confirmar, elegir, pedir_texto, boton
import persistence
from screens import screen_game
from models import Partida

MAX_GRUPO = 6


def _nombre_valido(nombre):
    limpio = "".join(c for c in nombre if c not in '\\/:*?"<>|').strip().rstrip(".")
    return limpio


class ScreenPartidasManager:
    def __init__(self, app):
        self.app = app
        self.closed = False
        self._pending_continue = getattr(app, "_party_state", None) is not None
        self.botones = [("NUEVA AVENTURA", self._nueva_partida), ("CARGAR", self._cargar_partida),
                        ("ELIMINAR", self._eliminar_partida), ("VOLVER", self._volver)]

    def _rects(self):
        W, H = self.app.screen.get_size()
        bw, bh, gap = 230, 56, 20
        x0 = W // 2 - (len(self.botones) * bw + (len(self.botones) - 1) * gap) // 2
        return [pygame.Rect(x0 + i * (bw + gap), 380, bw, bh) for i in range(len(self.botones))]

    def _volver(self):
        self.app._party_state = None
        from screens.screen_main import ScreenMain
        self.app.current_screen = ScreenMain(self.app)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for r, (t, f) in zip(self._rects(), self.botones):
                if r.collidepoint(event.pos):
                    f()
                    return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._volver()

    # ── Nueva aventura ────────────────────────────────────────────────────
    def _nueva_partida(self):
        dungeons = persistence.listar_dungeons()
        if not dungeons:
            mensaje(self.app.screen, "SIN DUNGEONS", "No hay dungeons en data/dungeons. Crea uno con el Editor de Dungeons.")
            return
        nombre = pedir_texto(self.app.screen, "NUEVA AVENTURA", "Nombre de la aventura", placeholder="Ej.: El templo del desierto")
        if not nombre:
            return
        nombre = _nombre_valido(nombre)
        if not nombre:
            return
        if nombre in persistence.listar_nombres_partidas():
            if not confirmar(self.app.screen, f"Ya existe una aventura llamada «{nombre}». ¿Añadir los guardados a ella?"):
                return
        idx = elegir(self.app.screen, "ELIGE DUNGEON",
                     [f"{d['nombre']}  ({d['num_rooms']} rooms)  {d['fecha_creacion']}" for d in dungeons])
        if idx is None:
            return
        dungeon = persistence.cargar_dungeon(dungeons[idx]["id"])
        if not dungeon.rooms:
            mensaje(self.app.screen, "DUNGEON VACÍO", "Ese dungeon no tiene rooms.")
            return
        self.app._party_state = {"nombre": nombre, "dungeon": dungeon, "seleccionados_ids": []}
        self._seleccionar_siguiente_personaje()

    def _seleccionar_siguiente_personaje(self):
        state = self.app._party_state
        while True:
            sel = state["seleccionados_ids"]
            if len(sel) >= MAX_GRUPO:
                self._iniciar_partida()
                return
            todos = persistence.listar_personajes()
            nombres = {p["id"]: p["nombre"] for p in todos}
            disponibles = [p for p in todos if p["id"] not in sel]
            opciones = []
            if sel:
                opciones.append(("__empezar__", f">> EMPEZAR LA AVENTURA CON {len(sel)} PERSONAJE(S)"))
            opciones.append(("__crear__", "+  CREAR UN PERSONAJE NUEVO"))
            opciones += [(p["id"], f"#{p['numero']} {p['nombre']} — {p['raza']} {p['profesion']}") for p in disponibles]
            grupo = ", ".join(nombres.get(i, "?") for i in sel) or "nadie todavía"
            idx = elegir(self.app.screen, f"FORMA EL GRUPO ({len(sel)}/{MAX_GRUPO})", [t for _, t in opciones],
                         texto=f"Grupo: {grupo}", ancho=820)
            if idx is None:
                self.app._party_state = None
                return
            clave = opciones[idx][0]
            if clave == "__empezar__":
                self._iniciar_partida()
                return
            if clave == "__crear__":
                from screens.screen_personaje_creador import ScreenPersonajeCreador
                self.app.current_screen = ScreenPersonajeCreador(self.app)
                return
            sel.append(clave)

    def _iniciar_partida(self):
        state = self.app._party_state
        self.app._party_state = None
        if not state or not state["seleccionados_ids"]:
            return
        partida = Partida()
        partida.nombre = state["nombre"]
        partida.dungeon_id = state["dungeon"].id
        partida.personajes = [persistence.cargar_personaje(pid) for pid in state["seleccionados_ids"]]
        partida.room_actual_id = min(state["dungeon"].rooms, key=lambda r: r.numero or 0).id
        screen_game.run_game(self.app.screen, partida, state["dungeon"])

    # ── Cargar / eliminar ─────────────────────────────────────────────────
    def _cargar_partida(self):
        nombres = persistence.listar_nombres_partidas()
        if not nombres:
            mensaje(self.app.screen, "CARGAR", "No hay aventuras guardadas.")
            return
        idx = elegir(self.app.screen, "ELIGE AVENTURA", nombres)
        if idx is None:
            return
        guardados = persistence.listar_guardados_partida(nombres[idx])
        if not guardados:
            mensaje(self.app.screen, "CARGAR", "Esa aventura no tiene guardados.")
            return
        ig = elegir(self.app.screen, "ELIGE GUARDADO (el más reciente arriba)",
                    [f"{g['fecha_guardado']}  —  {g['dungeon_nombre']}" for g in guardados])
        if ig is None:
            return
        try:
            partida, dungeon = persistence.cargar_guardado(guardados[ig]["path"])
        except Exception as e:
            mensaje(self.app.screen, "ERROR", f"No se pudo cargar el guardado: {e}")
            return
        screen_game.run_game(self.app.screen, partida, dungeon)

    def _eliminar_partida(self):
        nombres = persistence.listar_nombres_partidas()
        if not nombres:
            mensaje(self.app.screen, "ELIMINAR", "No hay aventuras guardadas.")
            return
        idx = elegir(self.app.screen, "ELIGE AVENTURA A ELIMINAR", nombres)
        if idx is None:
            return
        if confirmar(self.app.screen, f"¿Eliminar TODOS los guardados de «{nombres[idx]}»? No se puede deshacer."):
            persistence.eliminar_partida(nombres[idx])
            mensaje(self.app.screen, "ELIMINAR", f"Aventura «{nombres[idx]}» eliminada.")

    # ── Bucle ─────────────────────────────────────────────────────────────
    def update(self, dt):
        if self._pending_continue:
            self._pending_continue = False
            self._seleccionar_siguiente_personaje()

    def draw(self, surf):
        W, H = surf.get_size()
        surf.fill(C_FONDO)
        dibujar_cabecera(surf)
        t = "AVENTURAS"
        draw_text(surf, t, W // 2 - len(t) * 9, 190, 30, C_SUBTITULO, bold=True)
        s = "Empieza una nueva aventura en un dungeon, carga una partida guardada o elimínala"
        draw_text(surf, s, W // 2 - len(s) * 4, 240, 14, C_TEXTO_DIM)
        for r, (t, f) in zip(self._rects(), self.botones):
            boton(surf, r, t, 16, color=C_ERROR if t == "ELIMINAR" else None)


def dibujar_cabecera(surf):
    W = surf.get_width()
    from ui_utils import get_font
    f = get_font(54, True)
    s = f.render(TITLE, True, C_TITULO)
    if s.get_width() > W - 120:
        f = get_font(40, True)
        s = f.render(TITLE, True, C_TITULO)
    surf.blit(s, (W // 2 - s.get_width() // 2, 40))
    pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)

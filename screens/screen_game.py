# screens/screen_game.py - Pantalla de juego estilo "dungeon crawler" en primera persona
#
# Inspirado en The Bard's Tale, Might and Magic o Eye of the Beholder: el grupo ve el
# mundo con sus propios ojos, avanza casilla a casilla (room a room), gira a izquierda
# y derecha, y los aventureros aparecen como retratos en la parte inferior con su
# salud, estrés y corrupción. Las acciones usan el reglamento de reglas.py.
#
# Controles:
#   ↑ / W  avanzar        ↓ / S  retroceder       ← / A  girar izq.   → / D  girar der.
#   Q / E  paso lateral    RePág / AvPág  subir / bajar    X  salida especial
#   1-6 elegir personaje   T tirada   R resistir   F ficha   G guardar   ESC salir

import os
import random
import pygame
from constants import *
from ui_utils import get_font, draw_text
import reglas
from reglas import (TODAS_LAS_HABILIDADES, NOMBRE_ATRIBUTO, NOMBRE_RESULTADO, NOMBRE_DANO,
                    TIPOS_RESISTENCIA)
from models import Dungeon, Partida, DIR_DELTA, OPPOSITE
from formularios import (dialogo, mensaje, confirmar, Titulo, Info, Opciones, Multi, Check, Texto,
                         Dados, Separador, Fila, boton, texto_ajustado, envolver)
from screens.screen_ficha_personaje import dibujar_retrato, builder_ficha
import persistence


HORIZONTALES = ["norte", "este", "sur", "oeste"]          # en sentido horario
NOMBRE_DIR = {"norte": "norte", "sur": "sur", "este": "este", "oeste": "oeste",
              "arriba": "arriba", "abajo": "abajo", "especial": "especial"}
LETRA_DIR = {"norte": "N", "sur": "S", "este": "E", "oeste": "O"}
OPC_DANO = [(0, "Ninguna"), (1, "Leve (1)"), (2, "Grave (2)"), (3, "Muy grave (3)"), (4, "Enorme (4)")]
COLOR_RESULTADO = {"critico": (250, 215, 90), "exito": C_VERDE, "parcial": ORANGE, "fallo": C_ERROR}


def girar(orientacion, pasos):
    i = HORIZONTALES.index(orientacion) if orientacion in HORIZONTALES else 0
    return HORIZONTALES[(i + pasos) % 4]


class Juego:
    def __init__(self, screen, partida: Partida, dungeon: Dungeon):
        self.screen = screen
        self.partida = partida
        self.dungeon = dungeon
        self.grupo = partida.personajes
        self.sel = 0
        self.salir = False
        self.guardar_al_salir = False
        self.log_offset = 0
        self._imagenes = {}
        self._sonido_actual = None
        try:
            self.canal = pygame.mixer.Channel(0)
        except Exception:
            self.canal = None
        if partida.orientacion not in HORIZONTALES:
            partida.orientacion = "norte"
        self.room = dungeon.room_por_id(partida.room_actual_id) if partida.room_actual_id else None
        if self.room is None and dungeon.rooms:
            self.room = dungeon.rooms[0]
        if self.room:
            partida.room_actual_id = self.room.id
            if self.room.id not in partida.visitadas:
                partida.visitadas.append(self.room.id)
        if not partida.registro:
            self.log(f"Comienza la aventura «{partida.nombre}» en {dungeon.nombre}.")
            self.log("Usa las flechas para moverte. T: tirada de habilidad. ESC: salir.")
            self._describir_room()
        else:
            self.log(f"— Se reanuda la partida ({partida.fecha_guardado}) —")
        self._sonido_room()

    # ══════════════════════════════════════════════════════════════════════
    # REGISTRO
    # ══════════════════════════════════════════════════════════════════════
    def log(self, *lineas):
        for l in lineas:
            if isinstance(l, (list, tuple)):
                self.log(*l)
            elif l:
                self.partida.registro.append(str(l))
        self.partida.registro = self.partida.registro[-300:]
        self.log_offset = 0

    # ══════════════════════════════════════════════════════════════════════
    # MOVIMIENTO
    # ══════════════════════════════════════════════════════════════════════
    def mover(self, direccion):
        if not self.room:
            return
        if not any(p.puede_actuar for p in self.grupo):
            self.log("Nadie en el grupo está en condiciones de moverse.")
            return
        dest, estado = self.dungeon.paso(self.room, direccion)
        if estado == "sin_salida":
            self.log("No hay salida hacia " + ("ese lugar." if direccion == "especial" else f"el {direccion}."))
            return
        if estado == "cerrada":
            self.log(f"La salida hacia {direccion} está cerrada o no permite pasar en este sentido.")
            return
        self.room = dest
        self.partida.room_actual_id = dest.id
        if dest.id not in self.partida.visitadas:
            self.partida.visitadas.append(dest.id)
        self.log(f"Avanzáis hacia {direccion}...")
        self._describir_room()
        self._sonido_room()

    def _describir_room(self):
        r = self.room
        if not r:
            return
        self.log(f"» {r.nombre or 'Lugar sin nombre'}", r.descripcion)
        monstruos = [m.nombre for m in r.monstruos if m.presente]
        if monstruos:
            self.log("¡Peligro! Aquí hay: " + ", ".join(monstruos) + ".")
        pnjs = [p.nombre for p in r.pnjs if p.presente]
        if pnjs:
            self.log("Hay alguien aquí: " + ", ".join(pnjs) + ".")
        items = [i.nombre for i in r.items if i.estado == "en_room"]
        if items:
            self.log("Veis: " + ", ".join(items) + ".")

    def _sonido_room(self):
        if not self.canal:
            return
        nombre = (self.room.sonido or "").strip() if self.room else ""
        if nombre in ("", "None"):
            self.canal.stop()
            self._sonido_actual = None
            return
        if nombre == self._sonido_actual:
            return
        ruta = os.path.join(AUDIO_DIR, nombre)
        if not os.path.isfile(ruta):
            self.canal.stop()
            self._sonido_actual = None
            return
        try:
            self.canal.play(pygame.mixer.Sound(ruta), loops=-1)
            self._sonido_actual = nombre
        except Exception:
            self._sonido_actual = None

    def _imagen(self, nombre):
        nombre = (nombre or "").strip()
        if nombre in ("", "None"):
            return None
        if nombre not in self._imagenes:
            ruta = os.path.join(IMAGES_DIR, nombre)
            img = None
            if os.path.isfile(ruta):
                try:
                    img = pygame.image.load(ruta).convert()
                except Exception:
                    img = None
            self._imagenes[nombre] = img
        return self._imagenes[nombre]

    # ══════════════════════════════════════════════════════════════════════
    # BUCLE PRINCIPAL
    # ══════════════════════════════════════════════════════════════════════
    def acciones(self):
        o = self.partida.orientacion
        return [
            ("◄ Girar", lambda: self._girar(-1)), ("▲ Avanzar", lambda: self.mover(o)),
            ("Girar ►", lambda: self._girar(1)), ("▼ Retroceder", lambda: self.mover(OPPOSITE[o])),
            ("Subir", lambda: self.mover("arriba")), ("Bajar", lambda: self.mover("abajo")),
            ("Especial", lambda: self.mover("especial")), ("Ficha", self.accion_ficha),
            ("TIRADA", self.accion_tirada), ("Resistir", self.accion_resistir),
            ("En equipo", self.accion_equipo), ("Curar", self.accion_curar),
            ("Examinar", self.accion_examinar), ("Objetos", self.accion_objetos),
            ("Mecanismo", self.accion_mecanismo), ("Fortuna", self.accion_fortuna),
            ("Corrupción", self.accion_corrupcion), ("Experiencia", self.accion_experiencia),
            ("Descanso", self.accion_descanso), ("Guardar", self.accion_guardar),
            ("Salir", self.accion_salir),
        ]

    def _girar(self, pasos):
        self.partida.orientacion = girar(self.partida.orientacion, pasos)

    def layout(self):
        W, H = self.screen.get_size()
        m = 8
        party_h = 172
        top_h = H - party_h - 3 * m
        view_w = int(W * 0.6)
        view_h = int(top_h * 0.70)
        L = {}
        L["view"] = pygame.Rect(m, m, view_w, view_h)
        L["log"] = pygame.Rect(m, L["view"].bottom + m, view_w, top_h - view_h - m)
        x = L["view"].right + m
        w = W - x - m
        L["mapa"] = pygame.Rect(x, m, w, int(top_h * 0.40))
        L["info"] = pygame.Rect(x, L["mapa"].bottom + m, w, int(top_h * 0.25))
        L["botones"] = pygame.Rect(x, L["info"].bottom + m, w, top_h - L["mapa"].h - L["info"].h - 2 * m)
        L["grupo"] = pygame.Rect(m, H - party_h - m, W - 2 * m, party_h)
        return L

    def rects_botones(self, r):
        acc = self.acciones()
        cols = 4
        filas = (len(acc) + cols - 1) // cols
        bw = (r.w - (cols - 1) * 6) // cols
        bh = min(38, (r.h - (filas - 1) * 6) // filas)
        return [(pygame.Rect(r.x + (i % cols) * (bw + 6), r.y + (i // cols) * (bh + 6), bw, bh), t, f)
                for i, (t, f) in enumerate(acc)]

    def rects_grupo(self, r):
        n = 6
        cw = (r.w - (n - 1) * 8) // n
        return [pygame.Rect(r.x + i * (cw + 8), r.y, cw, r.h) for i in range(len(self.grupo))]

    def run(self):
        import formularios
        clock = pygame.time.Clock()
        formularios.fondo_base = lambda: self.dibujar(self.screen, self.layout())
        try:
            return self._bucle(clock)
        finally:
            formularios.fondo_base = None

    def _bucle(self, clock):
        while not self.salir:
            L = self.layout()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.guardar_al_salir = confirmar(self.screen, "¿Guardar la partida antes de cerrar?")
                    self.salir = True
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                    break
                self.evento(ev, L)
            self.dibujar(self.screen, self.layout())
            pygame.display.flip()
            clock.tick(30)
        if self.canal:
            self.canal.stop()
        if self.guardar_al_salir:
            persistence.guardar_partida(self.partida, self.dungeon)
        return self.partida, self.dungeon

    def evento(self, ev, L):
        o = self.partida.orientacion
        if ev.type == pygame.KEYDOWN:
            k = ev.key
            teclas = {
                pygame.K_UP: lambda: self.mover(o), pygame.K_w: lambda: self.mover(o),
                pygame.K_DOWN: lambda: self.mover(OPPOSITE[o]), pygame.K_s: lambda: self.mover(OPPOSITE[o]),
                pygame.K_LEFT: lambda: self._girar(-1), pygame.K_a: lambda: self._girar(-1),
                pygame.K_RIGHT: lambda: self._girar(1), pygame.K_d: lambda: self._girar(1),
                pygame.K_q: lambda: self.mover(girar(o, -1)), pygame.K_e: lambda: self.mover(girar(o, 1)),
                pygame.K_PAGEUP: lambda: self.mover("arriba"), pygame.K_PAGEDOWN: lambda: self.mover("abajo"),
                pygame.K_x: lambda: self.mover("especial"),
                pygame.K_t: self.accion_tirada, pygame.K_r: self.accion_resistir,
                pygame.K_f: self.accion_ficha, pygame.K_g: self.accion_guardar,
                pygame.K_ESCAPE: self.accion_salir,
            }
            if k in teclas:
                teclas[k]()
                self.resolver_pendientes()
            elif pygame.K_1 <= k <= pygame.K_6 and k - pygame.K_1 < len(self.grupo):
                self.sel = k - pygame.K_1
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for r, t, f in self.rects_botones(L["botones"]):
                if r.collidepoint(ev.pos):
                    f()
                    self.resolver_pendientes()
                    return
            for i, r in enumerate(self.rects_grupo(L["grupo"])):
                if r.collidepoint(ev.pos):
                    if self.sel == i:
                        self.accion_ficha()
                    self.sel = i
                    return
        elif ev.type == pygame.MOUSEWHEEL and L["log"].collidepoint(pygame.mouse.get_pos()):
            self.log_offset = max(0, min(len(self.partida.registro) - 1, self.log_offset + ev.y * 2))

    # ══════════════════════════════════════════════════════════════════════
    # DIBUJO
    # ══════════════════════════════════════════════════════════════════════
    def dibujar(self, surf, L):
        surf.fill((12, 8, 4))
        self.dibujar_vista(surf, L["view"])
        self.dibujar_log(surf, L["log"])
        self.dibujar_mapa(surf, L["mapa"])
        self.dibujar_info(surf, L["info"])
        for r, t, f in self.rects_botones(L["botones"]):
            boton(surf, r, t, 12, color=(110, 60, 20) if t == "TIRADA" else None)
        self.dibujar_grupo(surf, L["grupo"])

    def _marco(self, surf, r, titulo=None):
        pygame.draw.rect(surf, C_PANEL, r, border_radius=6)
        pygame.draw.rect(surf, C_BORDE, r, 2, border_radius=6)
        if titulo:
            draw_text(surf, titulo, r.x + 10, r.y + 6, 13, C_TITULO, bold=True)

    def dibujar_vista(self, surf, r):
        pygame.draw.rect(surf, BLACK, r)
        img = self._imagen(self.room.imagen) if self.room else None
        if img:
            iw, ih = img.get_size()
            esc = max(r.w / iw, r.h / ih)
            esc_img = pygame.transform.smoothscale(img, (int(iw * esc), int(ih * esc)))
            clip = surf.get_clip()
            surf.set_clip(r)
            surf.blit(esc_img, (r.centerx - esc_img.get_width() // 2, r.centery - esc_img.get_height() // 2))
            surf.set_clip(clip)
        else:
            self.dibujar_pasillo(surf, r)
        self.dibujar_indicadores(surf, r)
        if self.room:
            banda = pygame.Surface((r.w, 34), pygame.SRCALPHA)
            banda.fill((0, 0, 0, 170))
            surf.blit(banda, (r.x, r.y))
            draw_text(surf, self.room.nombre or "???", r.x + 12, r.y + 7, 18, GOLD, bold=True)
            o = self.partida.orientacion
            t = f"Mirando al {o.upper()}"
            draw_text(surf, t, r.right - 12 - get_font(14, True).size(t)[0], r.y + 9, 14, C_SUBTITULO, bold=True)
            monstruos = [m.nombre for m in self.room.monstruos if m.presente]
            if monstruos:
                t = "¡" + ", ".join(monstruos) + "!"
                s = get_font(22, True).render(t, True, (255, 90, 60))
                fondo = pygame.Surface((s.get_width() + 20, s.get_height() + 8), pygame.SRCALPHA)
                fondo.fill((0, 0, 0, 160))
                surf.blit(fondo, (r.centerx - fondo.get_width() // 2, r.y + 48))
                surf.blit(s, (r.centerx - s.get_width() // 2, r.y + 52))
        pygame.draw.rect(surf, C_BORDE, r, 3)

    def dibujar_pasillo(self, surf, r):
        """Vista en primera persona dibujada con polígonos cuando la room no tiene imagen."""
        o = self.partida.orientacion
        frente, izq, der = o, girar(o, -1), girar(o, 1)
        est = {d: self.dungeon.paso(self.room, d)[1] if self.room else "sin_salida"
               for d in HORIZONTALES + ["arriba", "abajo"]}
        cx, cy = r.center
        iw, ih = int(r.w * 0.42), int(r.h * 0.46)
        inner = pygame.Rect(cx - iw // 2, cy - ih // 2, iw, ih)
        techo, suelo = (28, 24, 22), (48, 38, 26)
        muro, muro_osc = (92, 80, 64), (66, 56, 44)
        pygame.draw.polygon(surf, techo, [r.topleft, r.topright, inner.topright, inner.topleft])
        pygame.draw.polygon(surf, suelo, [r.bottomleft, r.bottomright, inner.bottomright, inner.bottomleft])
        # baldosas del suelo
        for k in range(1, 4):
            t = k / 4
            y = int(inner.bottom + (r.bottom - inner.bottom) * t * t)
            xl = int(inner.left + (r.left - inner.left) * t * t)
            xr = int(inner.right + (r.right - inner.right) * t * t)
            pygame.draw.line(surf, (60, 48, 34), (xl, y), (xr, y), 1)
        # paredes laterales
        for lado, d in (("izq", izq), ("der", der)):
            if lado == "izq":
                pts = [r.topleft, inner.topleft, inner.bottomleft, r.bottomleft]
            else:
                pts = [r.topright, inner.topright, inner.bottomright, r.bottomright]
            if est[d] == "abierta":
                # abertura: pasillo lateral oscuro
                pygame.draw.polygon(surf, (10, 8, 6), pts)
                x0 = r.left if lado == "izq" else r.right
                x1 = inner.left if lado == "izq" else inner.right
                xm = (x0 + x1) // 2
                pygame.draw.line(surf, muro_osc, (xm, r.top + (inner.top - r.top) // 2),
                                 (xm, r.bottom - (r.bottom - inner.bottom) // 2), 3)
            else:
                pygame.draw.polygon(surf, muro_osc, pts)
                for k in range(1, 6):
                    t = k / 6
                    yt = r.top + (inner.top - r.top) * 0.0
                    y = int(r.top + (r.bottom - r.top) * t)
                    x1 = inner.left if lado == "izq" else inner.right
                    yi = int(inner.top + (inner.bottom - inner.top) * t)
                    x0 = r.left if lado == "izq" else r.right
                    pygame.draw.line(surf, (54, 46, 36), (x0, y), (x1, yi), 1)
                if est[d] == "cerrada":
                    self._puerta_lateral(surf, r, inner, lado)
        # pared del fondo
        if est[frente] == "abierta":
            pygame.draw.rect(surf, muro, inner)
            hueco = inner.inflate(-int(iw * 0.36), -int(ih * 0.2)).move(0, int(ih * 0.1))
            pygame.draw.rect(surf, (6, 5, 4), hueco)
            deep = hueco.inflate(-hueco.w // 2, -hueco.h // 2)
            pygame.draw.rect(surf, (20, 16, 12), deep, 1)
        else:
            pygame.draw.rect(surf, muro, inner)
            for k in range(1, 5):
                y = inner.y + k * inner.h // 5
                pygame.draw.line(surf, muro_osc, (inner.x, y), (inner.right, y), 1)
                for j in range(4):
                    x = inner.x + (j + (0.5 if k % 2 else 0)) * inner.w // 4
                    pygame.draw.line(surf, muro_osc, (x, y - inner.h // 5), (x, y), 1)
            if est[frente] == "cerrada":
                puerta = inner.inflate(-int(iw * 0.4), -int(ih * 0.2)).move(0, int(ih * 0.1))
                pygame.draw.rect(surf, (90, 52, 24), puerta)
                pygame.draw.rect(surf, (40, 22, 10), puerta, 3)
                for j in range(1, 3):
                    x = puerta.x + j * puerta.w // 3
                    pygame.draw.line(surf, (60, 34, 14), (x, puerta.y), (x, puerta.bottom), 2)
                pygame.draw.circle(surf, (200, 170, 60), (puerta.right - 10, puerta.centery), 4)
        pygame.draw.rect(surf, (30, 26, 20), inner, 2)
        # arriba / abajo
        if est["arriba"] != "sin_salida":
            tr = pygame.Rect(cx - 40, r.y + 40, 80, 26)
            pygame.draw.ellipse(surf, (8, 6, 4) if est["arriba"] == "abierta" else (90, 52, 24), tr)
            pygame.draw.ellipse(surf, (60, 50, 40), tr, 2)
        if est["abajo"] != "sin_salida":
            tr = pygame.Rect(cx - 60, r.bottom - 60, 120, 34)
            pygame.draw.ellipse(surf, (4, 3, 2) if est["abajo"] == "abierta" else (90, 52, 24), tr)
            pygame.draw.ellipse(surf, (70, 58, 44), tr, 2)

    def _puerta_lateral(self, surf, r, inner, lado):
        t0, t1 = 0.35, 0.75
        if lado == "izq":
            x0 = r.left + (inner.left - r.left) * t0
            x1 = r.left + (inner.left - r.left) * t1
        else:
            x0 = r.right - (r.right - inner.right) * t0
            x1 = r.right - (r.right - inner.right) * t1

        def ytop(x):
            if lado == "izq":
                t = (x - r.left) / max(1, inner.left - r.left)
            else:
                t = (r.right - x) / max(1, r.right - inner.right)
            return r.top + (inner.top - r.top) * t, r.bottom - (r.bottom - inner.bottom) * t
        a0, b0 = ytop(x0)
        a1, b1 = ytop(x1)
        h0, h1 = (b0 - a0), (b1 - a1)
        pts = [(x0, a0 + h0 * 0.25), (x1, a1 + h1 * 0.25), (x1, b1), (x0, b0)]
        pygame.draw.polygon(surf, (80, 46, 20), pts)
        pygame.draw.polygon(surf, (40, 22, 10), pts, 3)

    def dibujar_indicadores(self, surf, r):
        """Flechas en los bordes de la vista indicando salidas relativas a la orientación."""
        if not self.room:
            return
        o = self.partida.orientacion
        rel = [("frente", o), ("izq", girar(o, -1)), ("der", girar(o, 1)), ("atras", OPPOSITE[o])]
        for pos, d in rel:
            _, est = self.dungeon.paso(self.room, d)
            if est == "sin_salida":
                continue
            col = C_VERDE if est == "abierta" else C_ERROR
            if pos == "frente":
                c = (r.centerx, r.y + 44 + 30)
                pts = [(c[0], c[1] - 14), (c[0] - 14, c[1] + 8), (c[0] + 14, c[1] + 8)]
            elif pos == "atras":
                c = (r.centerx, r.bottom - 20)
                pts = [(c[0], c[1] + 12), (c[0] - 14, c[1] - 8), (c[0] + 14, c[1] - 8)]
            elif pos == "izq":
                c = (r.x + 20, r.centery)
                pts = [(c[0] - 12, c[1]), (c[0] + 8, c[1] - 14), (c[0] + 8, c[1] + 14)]
            else:
                c = (r.right - 20, r.centery)
                pts = [(c[0] + 12, c[1]), (c[0] - 8, c[1] - 14), (c[0] - 8, c[1] + 14)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, BLACK, pts, 2)
        chips = []
        for d, t in (("arriba", "↑ SUBIR"), ("abajo", "↓ BAJAR"), ("especial", "ESPECIAL")):
            _, est = self.dungeon.paso(self.room, d)
            if est != "sin_salida":
                chips.append((t, C_VERDE if est == "abierta" else C_ERROR))
        x = r.x + 12
        for t, col in chips:
            s = get_font(13, True).render(t, True, BLACK)
            rr = pygame.Rect(x, r.bottom - 34, s.get_width() + 14, 24)
            pygame.draw.rect(surf, col, rr, border_radius=5)
            surf.blit(s, (rr.x + 7, rr.y + 4))
            x = rr.right + 8

    def dibujar_log(self, surf, r):
        self._marco(surf, r)
        ancho = r.w - 24
        lineas = []
        for entrada in self.partida.registro[-80:]:
            for l in envolver(entrada, 13, ancho):
                lineas.append((l, entrada.startswith("»"), entrada.startswith("¡")))
        alto_l = 16
        cab = (r.h - 16) // alto_l
        fin = len(lineas) - self.log_offset
        vis = lineas[max(0, fin - cab):fin]
        y = r.y + 8
        for l, es_room, alerta in vis:
            col = GOLD if es_room else ((255, 120, 80) if alerta else C_TEXTO)
            draw_text(surf, l, r.x + 12, y, 13, col, bold=es_room)
            y += alto_l
        if self.log_offset:
            draw_text(surf, "▼ (rueda para volver)", r.right - 200, r.bottom - 18, 11, C_TEXTO_DIM)

    def dibujar_mapa(self, surf, r):
        z = self.room.z if self.room else 0
        self._marco(surf, r, f"MAPA — nivel {z}")
        if not self.room:
            return
        celda = 34
        cx, cy = r.centerx, r.y + 16 + (r.h - 16) // 2
        visitadas = [self.dungeon.room_por_id(i) for i in self.partida.visitadas]
        visitadas = [v for v in visitadas if v and v.z == z]
        clip = surf.get_clip()
        surf.set_clip(r.inflate(-6, -6))

        def pos(room):
            return (cx + (room.x - self.room.x) * celda, cy - (room.y - self.room.y) * celda)
        for v in visitadas:
            px, py = pos(v)
            for d in HORIZONTALES:
                dest, est = self.dungeon.paso(v, d)
                if est == "sin_salida":
                    continue
                dx, dy, _ = DIR_DELTA[d]
                fin = (px + dx * celda // 2, py - dy * celda // 2)
                if est == "abierta":
                    vuelta = self.dungeon.paso(dest, OPPOSITE[d])[1] if dest else "sin_salida"
                    col = (90, 160, 80) if vuelta == "abierta" else YELLOW
                    pygame.draw.line(surf, col, (px, py), fin, 4)
                else:
                    pygame.draw.line(surf, (140, 50, 40), (px, py), fin, 4)
                    perp = (dy * 6, dx * 6)
                    pygame.draw.line(surf, C_ERROR, (fin[0] - perp[0], fin[1] - perp[1]),
                                     (fin[0] + perp[0], fin[1] + perp[1]), 3)
        for v in visitadas:
            px, py = pos(v)
            cr = pygame.Rect(px - 11, py - 11, 22, 22)
            actual = v.id == self.room.id
            pygame.draw.rect(surf, (120, 90, 40) if actual else (70, 54, 30), cr, border_radius=3)
            pygame.draw.rect(surf, C_TITULO if actual else C_BORDE, cr, 2, border_radius=3)
            marcas = ""
            if self.dungeon.paso(v, "arriba")[1] != "sin_salida":
                marcas += "↑"
            if self.dungeon.paso(v, "abajo")[1] != "sin_salida":
                marcas += "↓"
            if marcas and not actual:
                draw_text(surf, marcas, cr.x + 3, cr.y + 3, 12, C_TEXTO)
            if any(m.presente for m in v.monstruos) and not actual:
                pygame.draw.circle(surf, C_ERROR, (cr.right - 4, cr.y + 4), 4)
        # el grupo (triángulo orientado)
        px, py = cx, cy
        dx, dy, _ = DIR_DELTA[self.partida.orientacion]
        punta = (px + dx * 9, py - dy * 9)
        base1 = (px - dx * 6 + dy * 7, py + dy * 6 + dx * 7)
        base2 = (px - dx * 6 - dy * 7, py + dy * 6 - dx * 7)
        pygame.draw.polygon(surf, (255, 230, 120), [punta, base1, base2])
        surf.set_clip(clip)
        # rosa de los vientos
        rx, ry = r.right - 30, r.y + 40
        for d in HORIZONTALES:
            dx, dy, _ = DIR_DELTA[d]
            col = GOLD if d == self.partida.orientacion else C_TEXTO_DIM
            draw_text(surf, LETRA_DIR[d], rx + dx * 16 - 4, ry - dy * 16 - 7, 13, col, bold=True)

    def dibujar_info(self, surf, r):
        self._marco(surf, r, "LUGAR")
        if not self.room:
            return
        rm = self.room
        x, y, w = r.x + 10, r.y + 26, r.w - 20
        draw_text(surf, f"#{rm.numero} {rm.nombre}  ({rm.x},{rm.y},{rm.z})", x, y, 13, C_SUBTITULO, bold=True)
        y += 20
        salidas = []
        for d in HORIZONTALES + ["arriba", "abajo", "especial"]:
            _, est = self.dungeon.paso(rm, d)
            if est != "sin_salida":
                salidas.append(f"{d}{'' if est == 'abierta' else ' (cerrada)'}")
        y += texto_ajustado(surf, "Salidas: " + (", ".join(salidas) or "ninguna"), x, y, 12, C_TEXTO, w)
        for etq, lista in (("Objetos", [i.nombre for i in rm.items if i.estado == "en_room"]),
                           ("Criaturas", [m.nombre for m in rm.monstruos if m.presente]),
                           ("PNJ", [p.nombre for p in rm.pnjs if p.presente]),
                           ("Mecanismos", [f"{m.nombre} [{m.estado}]" for m in rm.mecanismos])):
            if lista and y < r.bottom - 16:
                y += texto_ajustado(surf, f"{etq}: " + ", ".join(lista), x, y, 12,
                                    (255, 120, 80) if etq == "Criaturas" else C_TEXTO, w)
        draw_text(surf, f"Monedas: {self.partida.monedas}   Inventario: {len(self.partida.inventario)}",
                  x, r.bottom - 20, 12, YELLOW)

    def dibujar_grupo(self, surf, r):
        for i, (p, cr) in enumerate(zip(self.grupo, self.rects_grupo(r))):
            sel = i == self.sel
            pygame.draw.rect(surf, (52, 36, 18) if sel else C_PANEL, cr, border_radius=6)
            pygame.draw.rect(surf, C_TITULO if sel else C_BORDE, cr, 3 if sel else 2, border_radius=6)
            tam = min(100, cr.h - 50)
            dibujar_retrato(surf, (cr.x + 8, cr.y + 8, tam, tam), p, apagado=not p.puede_actuar)
            tx = cr.x + tam + 16
            tw = cr.right - tx - 8
            nombre = p.nombre
            while get_font(14, True).size(nombre)[0] > tw and len(nombre) > 3:
                nombre = nombre[:-1]
            draw_text(surf, f"{nombre}", tx, cr.y + 8, 14, GOLD if sel else C_TEXTO, bold=True)
            draw_text(surf, f"{i + 1}", cr.right - 16, cr.y + 6, 11, C_TEXTO_DIM)
            draw_text(surf, p.raza[:8], tx, cr.y + 27, 11, C_TEXTO_DIM)
            draw_text(surf, (p.subclase or p.clase)[:11], tx, cr.y + 41, 11, C_TEXTO_DIM)
            estado = {"activo": "", "inconsciente": "INCONSCIENTE", "muerto": "MUERTO",
                      "retirado": "RETIRADO"}[p.estado] if p.estado in ("activo", "inconsciente", "muerto", "retirado") else p.estado
            if p.estado == "activo" and p.puntos_golpe == 0:
                estado = "PELIGRO MORTAL"
            if estado:
                draw_text(surf, estado, tx, cr.y + 58, 11, C_ERROR, bold=True)
            elif p.traumas or p.ruinas:
                draw_text(surf, f"T:{len(p.traumas)} R:{len(p.ruinas)}", tx, cr.y + 58, 11, ORANGE)
            # barras
            by = cr.y + tam + 14
            self._barra(surf, cr.x + 8, by, cr.w - 16, "PG", p.puntos_golpe, p.pg_max,
                        C_VERDE if p.puntos_golpe > 7 else (YELLOW if p.puntos_golpe > 5 else C_ERROR))
            self._barra(surf, cr.x + 8, by + 15, cr.w - 16, "ES", p.estres, reglas.BARRA_ESTRES, (120, 140, 220))
            self._barra(surf, cr.x + 8, by + 30, cr.w - 16, "CO", p.corrupcion, reglas.BARRA_CORRUPCION, (150, 70, 160))

    def _barra(self, surf, x, y, w, etq, v, mx, col):
        draw_text(surf, etq, x, y - 1, 11, C_TEXTO_DIM, bold=True)
        x0 = x + 24
        seg = (w - 24) / mx
        for k in range(mx):
            rr = pygame.Rect(int(x0 + k * seg), y, max(2, int(seg) - 2), 11)
            pygame.draw.rect(surf, col if k < v else (40, 30, 20), rr)

    # ══════════════════════════════════════════════════════════════════════
    # UTILIDADES DE ACCIONES
    # ══════════════════════════════════════════════════════════════════════
    @property
    def actual(self):
        return self.grupo[self.sel] if self.grupo else None

    def _opc_pj(self, solo_activos=False, excluir=None):
        return [(i, p.nombre) for i, p in enumerate(self.grupo)
                if (not solo_activos or p.puede_actuar) and i != excluir]

    def _deshab_pj(self):
        return [i for i, p in enumerate(self.grupo) if not p.puede_actuar]

    def _pj_inicial(self):
        if self.actual and self.actual.puede_actuar:
            return self.sel
        for i, p in enumerate(self.grupo):
            if p.puede_actuar:
                return i
        return None

    def mostrar_tirada(self, titulo, res, extra=None, pedir_dano=False):
        """Muestra dados y resultado. Si pedir_dano, devuelve los PG de daño elegidos."""
        datos = {"dano": res.get("dano_sugerido", 0)}
        r = res["resultado"]

        def b(d):
            c = [Dados(res["dados"], res.get("cero_dados", False),
                       etiqueta="Dados (el marcado es el que cuenta)" + ("  — sin dados: 2d6 y el peor"
                                                                        if res.get("cero_dados") else ""))]
            c.append(Titulo(NOMBRE_RESULTADO[r].upper(), 22, COLOR_RESULTADO[r]))
            for t in (extra or []):
                c.append(Info(t, 13))
            for e in res.get("eventos", []):
                c.append(Info("• " + e, 13, C_SUBTITULO))
            if pedir_dano and r in ("parcial", "fallo"):
                c += [Separador(), Opciones("dano", f"Daño al personaje (sugerido por la situación: "
                                            f"{res.get('dano_sugerido', 0)}). El DJ decide:", OPC_DANO, cols=5)]
            return c
        dialogo(self.screen, titulo, b, datos, botones=[("ok", "Continuar")], ancho=820)
        return datos["dano"] if pedir_dano and r in ("parcial", "fallo") else 0

    def resolver_dano(self, p, puntos, contra=""):
        """El personaje recibe daño: puede aceptarlo, resistir o usar una casilla de armadura."""
        if puntos <= 0 or p.estado in ("muerto", "retirado"):
            return
        libres = p.armadura - p.armadura_usada
        datos = {"resp": "resistir", "atributo": "CUE", "contra": contra, "efecto_res": "reducir"}

        def b(d):
            c = [Info(f"{p.nombre} va a sufrir {NOMBRE_DANO.get(puntos, 'una herida enorme')} "
                      f"({puntos} PG). Tiene {p.puntos_golpe} PG.", 15, C_TEXTO, True),
                 Opciones("resp", "¿Qué hace?", [("aceptar", "Aceptar el daño"), ("resistir", "Tirada de resistencia"),
                                                 ("armadura", f"Usar armadura ({libres} casillas)")], cols=3,
                          deshabilitadas=() if libres > 0 else ("armadura",))]
            if d["resp"] == "resistir":
                calc = reglas.dados_resistencia(p, d["atributo"], d["contra"])
                c += [Opciones("atributo", "Atributo (en combate, evitar golpes suele ser Cuerpo)",
                               [(a, NOMBRE_ATRIBUTO[a]) for a in reglas.ATRIBUTOS], cols=3),
                      Opciones("contra", "Contra", TIPOS_RESISTENCIA, cols=5, size=11),
                      Opciones("efecto_res", "El DJ decide: la resistencia...",
                               [("anular", "Anula el daño"), ("reducir", "Lo reduce un grado (-1 PG)")], cols=2),
                      Info(f"Tirará {calc['total']}d6 ({calc['base']} habilidades con puntos"
                           + (" +1 racial" if calc["bonus"] else "") + "). Ganará 6 − el resultado más alto de "
                           "estrés (crítico: pierde 1).", 12, C_TEXTO_DIM)]
            return c
        dialogo(self.screen, f"DAÑO — {p.nombre}", b, datos, botones=[("ok", "Aceptar")], ancho=820)
        if datos["resp"] == "armadura" and libres > 0:
            p.armadura_usada += 1
            self.log(f"{p.nombre} usa una casilla de armadura y evita el daño.")
            return
        if datos["resp"] == "resistir":
            res = tirada_res = reglas.tirada_resistencia(p, datos["atributo"], datos["contra"])
            if datos["efecto_res"] == "anular":
                puntos = 0
            else:
                puntos = max(0, puntos - 1)
            self.log(f"{p.nombre} resiste con {NOMBRE_ATRIBUTO[datos['atributo']]}: {tirada_res['dados']}.",
                     res["eventos"])
            self.mostrar_tirada(f"RESISTENCIA — {p.nombre}", res,
                                [f"El daño queda en {puntos} PG ({NOMBRE_DANO.get(puntos, '')})."])
        self.aplicar_dano(p, puntos)

    def aplicar_dano(self, p, puntos):
        if puntos <= 0:
            return
        antes = p.recibir_dano(puntos)
        self.log(f"¡{p.nombre} sufre {NOMBRE_DANO.get(puntos, 'una herida enorme')}! PG {antes} → {p.puntos_golpe}.")
        if p.puntos_golpe == 0 and antes > 0:
            self.peligro_mortal(p, antes)

    def peligro_mortal(self, p, antes):
        datos = {"m": "tirar"}
        dialogo(self.screen, f"¡PELIGRO MORTAL! — {p.nombre}", lambda d: [
            Info(f"{p.nombre} ha llegado a 0 puntos de golpe.", 15, C_ERROR, True),
            Info("Puede hacer una tirada de resistencia a la muerte (cuesta estrés). Crítico: evita el daño; "
                 "éxito: queda con 1 PG; éxito parcial: cae inconsciente; fracaso: el DJ decide si muere "
                 "o queda inconsciente.", 13),
            Opciones("m", "", [("tirar", "Tirar resistencia a la muerte"), ("dj", "Que decida el DJ")], cols=2)],
            datos, botones=[("ok", "Aceptar")])
        if datos["m"] == "tirar":
            res = reglas.tirada_muerte(p, antes)
            self.log(res["eventos"])
            self.mostrar_tirada(f"RESISTENCIA A LA MUERTE — {p.nombre}", res)
            if res["desenlace"] != "dj":
                return
        datos = {"f": "inconsciente"}
        dialogo(self.screen, f"EL DJ DECIDE — {p.nombre}", lambda d: [
            Opciones("f", "Destino del personaje", [("inconsciente", "Cae inconsciente"), ("muerto", "Muere")], cols=2)],
            datos, botones=[("ok", "Aceptar")])
        p.estado = datos["f"]
        p.puntos_golpe = 0
        self.log(f"{p.nombre} {'ha MUERTO' if datos['f'] == 'muerto' else 'queda inconsciente'}.")

    def resolver_pendientes(self):
        for p in self.grupo:
            while p.traumas_pendientes > 0:
                datos = {"t": None}
                opciones = [t for t in reglas.TRAUMAS if t not in p.traumas] or reglas.TRAUMAS
                dialogo(self.screen, f"TRAUMA — {p.nombre}", lambda d: [
                    Info(f"La barra de estrés de {p.nombre} se ha llenado. Elige un trauma "
                         f"({len(p.traumas) + 1}º de {reglas.TRAUMAS_RETIRO}; con el cuarto se retira).", 13),
                    Opciones("t", "", opciones, cols=4)], datos, botones=[("ok", "Aceptar")],
                    validar=lambda d, k: None if d["t"] else "Elige un trauma.")
                self.log(p.anadir_trauma(datos["t"]))
            while p.ruinas_pendientes > 0:
                datos = {"t": None}
                opciones = [t for t in reglas.RUINAS if t not in p.ruinas] or reglas.RUINAS
                dialogo(self.screen, f"RUINA — {p.nombre}", lambda d: [
                    Info(f"La corrupción de {p.nombre} se ha completado. Elige una ruina "
                         f"({len(p.ruinas) + 1}ª de {reglas.RUINAS_RETIRO}; con la tercera se retira).", 13),
                    Opciones("t", "", opciones, cols=4)], datos, botones=[("ok", "Aceptar")],
                    validar=lambda d, k: None if d["t"] else "Elige una ruina.")
                self.log(p.anadir_ruina(datos["t"]))
            for atr in list(p.puntos_habilidad_pendientes):
                while p.puntos_habilidad_pendientes.get(atr, 0) > 0:
                    posibles = reglas.habilidades_subibles(p, atr)
                    p.puntos_habilidad_pendientes[atr] -= 1
                    if not posibles:
                        self.log(f"{p.nombre} no puede subir ninguna habilidad de {NOMBRE_ATRIBUTO[atr]}.")
                        continue
                    datos = {"h": None}
                    dialogo(self.screen, f"SUBIR HABILIDAD — {p.nombre}", lambda d: [
                        Info(f"Se ha llenado la barra de {NOMBRE_ATRIBUTO[atr]}: sube un punto una habilidad.", 13),
                        Opciones("h", "", [(h, f"{h} ({p.habilidades[h]})") for h in posibles], cols=4)],
                        datos, botones=[("ok", "Aceptar")], validar=lambda d, k: None if d["h"] else "Elige una.")
                    p.habilidades[datos["h"]] += 1
                    self.log(f"{p.nombre} mejora {datos['h']} a {p.habilidades[datos['h']]}.")
                if not p.puntos_habilidad_pendientes.get(atr):
                    p.puntos_habilidad_pendientes.pop(atr, None)
            while p.talentos_pendientes > 0:
                datos = {"n": "", "d": ""}
                dialogo(self.screen, f"NUEVO TALENTO — {p.nombre}", lambda d: [
                    Info("Un talento es una mejora permanente relativa a la clase: un nuevo conjuro, oración "
                         "o poder (o mejorar uno), quitarse 3 de estrés una vez por sesión, dos ataques "
                         "simultáneos una vez por sesión... Acuérdalo con el DJ.", 12),
                    Texto("n", "Nombre del talento", "Ej.: Curar herida grave"),
                    Texto("d", "Descripción (opcional)", "Qué hace")], datos, botones=[("ok", "Aceptar")],
                    validar=lambda d, k: None if d["n"].strip() else "Escribe el nombre.")
                p.talentos.append({"nombre": datos["n"].strip(), "descripcion": datos["d"].strip()})
                p.talentos_pendientes -= 1
                self.log(f"{p.nombre} aprende el talento «{datos['n'].strip()}».")
        if self.grupo and all(p.estado in ("muerto", "retirado") for p in self.grupo):
            if not getattr(self, "_aviso_fin", False):
                self._aviso_fin = True
                mensaje(self.screen, "FIN", "Todo el grupo ha muerto o se ha retirado. La aventura termina aquí...")

    # ══════════════════════════════════════════════════════════════════════
    # ACCIONES
    # ══════════════════════════════════════════════════════════════════════
    def accion_tirada(self):
        ini = self._pj_inicial()
        if ini is None:
            mensaje(self.screen, "TIRADA", "Nadie puede actuar.")
            return
        datos = {"pj": ini, "hab": None, "sit": "arriesgada", "efe": "estándar", "esf": False, "mot": False,
                 "ayu": -1, "paga": "actor", "obj": ""}

        def calc(d):
            p = self.grupo[d["pj"]]
            if not d["hab"]:
                return None
            return reglas.calcular_dados(p, d["hab"], d["esf"] or d["ayu"] >= 0)

        def b(d):
            p = self.grupo[d["pj"]]
            c = [Opciones("pj", "Personaje", self._opc_pj(), cols=6, deshabilitadas=self._deshab_pj()),
                 Texto("obj", "Objetivo (qué quiere hacer en la ficción)", "Ej.: escalar el muro"),
                 Opciones("hab", "Habilidad", [(h, f"{h} ({p.habilidades.get(h, 0)})") for h in TODAS_LAS_HABILIDADES],
                          cols=4, alto_boton=28, size=12)]
            if d["hab"]:
                c.append(Info(reglas.DESCRIPCION_HABILIDAD[d["hab"]], 11, C_TEXTO_DIM))
            c += [Fila([Opciones("sit", "Situación (la fija el DJ)", reglas.SITUACIONES, cols=3, alto_boton=28, size=12),
                        Opciones("efe", "Efecto (lo fija el DJ)", reglas.EFECTOS, cols=3, alto_boton=28, size=12)]),
                  Check("esf", "Esforzarse: +1d6 ganando 2 de estrés")]
            if d["esf"]:
                c.append(Check("mot", f"La acción se relaciona con su motivación ({p.motivacion or '?'}): solo 1 de estrés"))
            c.append(Opciones("ayu", "Ayuda de un compañero (+1d6, el que ayuda gana 1 de estrés)",
                              [(-1, "Nadie")] + self._opc_pj(True, d["pj"]), cols=6, alto_boton=28, size=12))
            if d["esf"] and d["ayu"] >= 0:
                c.append(Opciones("paga", "Esfuerzo y ayuda: solo se gana un dado. ¿Quién gana el estrés?",
                                  [("actor", p.nombre), ("ayudante", self.grupo[d["ayu"]].nombre)], cols=2))
            k = calc(d)
            if k:
                c.append(Info("Dados: " + k["explicacion"], 14, C_TITULO, True))
                if not k["puede"]:
                    c.append(Info(k["motivo"], 13, C_ERROR))
            return c

        def v(d, k):
            if not d["hab"]:
                return "Elige una habilidad."
            kk = calc(d)
            return None if kk["puede"] else kk["motivo"]
        k, d = dialogo(self.screen, "TIRADA DE HABILIDAD", b, datos, v, ancho=900,
                       botones=[("aceptar", "¡Tirar!"), ("cancelar", "Cancelar")])
        if k != "aceptar":
            return
        p = self.grupo[d["pj"]]
        ayudante = self.grupo[d["ayu"]] if d["ayu"] >= 0 else None
        res = reglas.tirada_habilidad(p, d["hab"], d["esf"], ayudante, d["mot"], d["paga"], d["sit"], d["efe"])
        obj = f" para {d['obj'].strip()}" if d["obj"].strip() else ""
        self.log(f"{p.nombre} tira {d['hab']}{obj} ({d['sit']}, efecto {d['efe']}): {res['dados']} → "
                 f"{NOMBRE_RESULTADO[res['resultado']]}.", res["eventos"])
        dano = self.mostrar_tirada(f"{p.nombre.upper()} — {d['hab'].upper()}", res,
                                   reglas.texto_consecuencias(res["resultado"], d["sit"], d["efe"]), pedir_dano=True)
        self.resolver_pendientes()
        if dano:
            self.resolver_dano(p, dano)

    def accion_resistir(self):
        datos = {"pj": self.sel, "atributo": "CUE", "contra": ""}

        def b(d):
            p = self.grupo[d["pj"]]
            calc = reglas.dados_resistencia(p, d["atributo"], d["contra"])
            return [Info("Para resistir una consecuencia que no sea daño (veneno, magia, miedo...). Para daño "
                         "usa la opción que aparece al recibirlo.", 12, C_TEXTO_DIM),
                    Opciones("pj", "Personaje", self._opc_pj(), cols=6),
                    Opciones("atributo", "Atributo (lo decide el DJ)", [(a, NOMBRE_ATRIBUTO[a]) for a in reglas.ATRIBUTOS], cols=3),
                    Opciones("contra", "Contra", TIPOS_RESISTENCIA, cols=5, size=11),
                    Info(f"Tirará {calc['total']}d6" + (" (+1 racial)" if calc["bonus"] else "")
                         + ". Sin dados de bonificación por esfuerzo o ayuda.", 13, C_TITULO, True)]
        k, d = dialogo(self.screen, "TIRADA DE RESISTENCIA", b, datos, botones=[("aceptar", "¡Tirar!"), ("cancelar", "Cancelar")])
        if k != "aceptar":
            return
        p = self.grupo[d["pj"]]
        res = reglas.tirada_resistencia(p, d["atributo"], d["contra"])
        self.log(f"{p.nombre} resiste ({NOMBRE_ATRIBUTO[d['atributo']]}): {res['dados']}.", res["eventos"])
        self.mostrar_tirada(f"RESISTENCIA — {p.nombre}", res,
                            ["La consecuencia se reduce o se anula (lo decide el DJ)."])

    def accion_equipo(self):
        activos = self._opc_pj(True)
        if len(activos) < 2:
            mensaje(self.screen, "TIRADA EN EQUIPO", "Hacen falta al menos dos personajes en condiciones de actuar.")
            return
        datos = {"lider": activos[0][0], "part": [i for i, _ in activos], "hab": None,
                 "sit": "arriesgada", "efe": "estándar"}

        def b(d):
            return [Info("Varios personajes trabajan en equipo dirigidos por uno. Todos tiran, se usa la mejor "
                         "tirada para todos y el líder gana 1 de estrés por cada fracaso.", 12, C_TEXTO_DIM),
                    Opciones("lider", "Líder", activos, cols=6),
                    Multi("part", "Participantes (incluye al líder)", activos, cols=6),
                    Opciones("hab", "Habilidad", TODAS_LAS_HABILIDADES, cols=4, alto_boton=28, size=12),
                    Fila([Opciones("sit", "Situación", reglas.SITUACIONES, cols=3, alto_boton=28, size=12),
                          Opciones("efe", "Efecto", reglas.EFECTOS, cols=3, alto_boton=28, size=12)])]
        k, d = dialogo(self.screen, "TIRADA EN EQUIPO", b, datos,
                       lambda d, k: None if d["hab"] and len(d["part"]) >= 2 else "Elige habilidad y al menos dos participantes.",
                       botones=[("aceptar", "¡Tirar!"), ("cancelar", "Cancelar")], ancho=880)
        if k != "aceptar":
            return
        lider = self.grupo[d["lider"]]
        part = [self.grupo[i] for i in d["part"]]
        if lider not in part:
            part.insert(0, lider)
        res = reglas.tirada_equipo(lider, part, d["hab"])
        if res["resultado"] is None:
            mensaje(self.screen, "TIRADA EN EQUIPO", res["eventos"])
            return
        sug = reglas.DANO_SUGERIDO[d["sit"]]
        datos2 = {"dano": sug[0] if res["resultado"] == "parcial" else sug[1] if res["resultado"] == "fallo" else 0}

        def b2(dd):
            c = []
            for t in res["tiradas"]:
                if t["puede"]:
                    c.append(Dados(t["dados"], t["cero"],
                                   tam=34, etiqueta=f"{t['personaje'].nombre}: {NOMBRE_RESULTADO[t['resultado']]}"))
                else:
                    c.append(Info(f"{t['personaje'].nombre}: {t['motivo']}", 12, C_TEXTO_DIM))
            r = res["resultado"]
            c.append(Titulo(f"RESULTADO DEL EQUIPO: {NOMBRE_RESULTADO[r].upper()}", 20, COLOR_RESULTADO[r]))
            for t in reglas.texto_consecuencias(r, d["sit"], d["efe"]):
                c.append(Info(t, 12))
            for e in res["eventos"]:
                c.append(Info("• " + e, 13, C_SUBTITULO))
            if r in ("parcial", "fallo"):
                c.append(Opciones("dano", "Daño a cada participante (el DJ decide)", OPC_DANO, cols=5))
            return c
        dialogo(self.screen, "TIRADA EN EQUIPO", b2, datos2, botones=[("ok", "Continuar")], ancho=860)
        self.log(f"Tirada en equipo de {d['hab']} dirigida por {lider.nombre}: {NOMBRE_RESULTADO[res['resultado']]}.",
                 res["eventos"])
        self.resolver_pendientes()
        if datos2["dano"]:
            for q in part:
                self.resolver_dano(q, datos2["dano"])

    def accion_curar(self):
        datos = {"modo": "tirada", "cur": self._pj_inicial() if self._pj_inicial() is not None else 0,
                 "hab": "trastear", "obj": self.sel, "cant": 1, "esf": False}

        def b(d):
            c = [Opciones("modo", "Forma de curar", [("tirada", "Con tirada (trastear o sobrenatural)"),
                                                     ("directa", "Poción, planta o remedio (sin tirada)")], cols=2),
                 Opciones("obj", "Paciente", self._opc_pj(), cols=6)]
            if d["modo"] == "tirada":
                c += [Opciones("cur", "Quién cura", self._opc_pj(True), cols=6),
                      Opciones("hab", "Habilidad", [("trastear", "Trastear (primeros auxilios)"),
                                                    ("sobrenatural", "Sobrenatural (conjuro/oración/poder)")], cols=2),
                      Opciones("cant", "Cuánto cura con éxito (crítico: el doble)",
                               [(1, "1 (vendas / herida leve)"), (2, "2 (pomada / herida grave)"),
                                (3, "3 (equipo de cirujano / muy grave)"), (4, "4")], cols=4, size=11),
                      Check("esf", "Esforzarse (+1d6, 2 de estrés)"),
                      Info("Trastear siempre requiere algo (vendas, pomada...). En combate es muy difícil curar "
                           "con trastear; lo sobrenatural es más rápido.", 11, C_TEXTO_DIM)]
            else:
                c.append(Opciones("cant", "Puntos de golpe que cura", [(1, "1"), (2, "2"), (3, "3"), (4, "4"), (10, "Todo")], cols=5))
            return c
        k, d = dialogo(self.screen, "CURAR", b, datos, ancho=860,
                       botones=[("aceptar", "Curar"), ("cancelar", "Cancelar")])
        if k != "aceptar":
            return
        obj = self.grupo[d["obj"]]
        if d["modo"] == "directa":
            n = obj.curar(d["cant"])
            self.log(f"{obj.nombre} recupera {n} PG con un remedio.")
            return
        cur = self.grupo[d["cur"]]
        res = reglas.tirada_curacion(cur, d["hab"], obj, d["cant"], d["esf"])
        if res["resultado"] is None:
            mensaje(self.screen, "CURAR", res["eventos"])
            return
        self.log(f"{cur.nombre} intenta curar a {obj.nombre} con {d['hab']}: {res['dados']} → "
                 f"{NOMBRE_RESULTADO[res['resultado']]}.", res["eventos"])
        self.mostrar_tirada(f"CURACIÓN — {cur.nombre} → {obj.nombre}", res)

    def accion_examinar(self):
        if not self.room:
            return
        rm = self.room
        datos = {"derrotar": [], "ver": None}

        def b(d):
            c = [Titulo(f"#{rm.numero} {rm.nombre}", 16), Info(rm.descripcion or "Nada especial a simple vista.", 13)]
            for m in rm.monstruos:
                if m.presente:
                    c.append(Info(f"CRIATURA — {m.nombre}: {m.descripcion}", 13, (255, 130, 90)))
            for p in rm.pnjs:
                if p.presente:
                    c.append(Info(f"PNJ — {p.nombre} ({p.actitud}): {p.descripcion}", 13, C_SUBTITULO))
            for i in rm.items:
                if i.estado == "en_room":
                    c.append(Info(f"OBJETO — {i.nombre}: {i.descripcion}", 13))
            for m in rm.mecanismos:
                c.append(Info(f"MECANISMO — {m.nombre} [{m.estado}]: {m.descripcion}", 13))
            vivos = [(m.id, m.nombre) for m in rm.monstruos if m.presente]
            if vivos:
                c += [Separador(), Multi("derrotar", "Marcar criaturas como derrotadas o ahuyentadas", vivos, cols=3)]
            return c
        dialogo(self.screen, "EXAMINAR", b, datos, botones=[("ok", "Cerrar")], ancho=860)
        for m in rm.monstruos:
            if m.id in datos["derrotar"]:
                m.presente = False
                self.log(f"{m.nombre} ya no es una amenaza.")

    def accion_objetos(self):
        if not self.room:
            return
        while True:
            rm = self.room
            en_room = [i for i in rm.items if i.estado == "en_room"]
            opciones = [(f"c:{i.id}", f"Coger: {i.nombre}") for i in en_room] + \
                       [(f"s:{i.id}", f"Dejar: {i.nombre}") for i in self.partida.inventario]
            datos = {"op": None}

            def b(d):
                c = [Info(f"Monedas del grupo: {self.partida.monedas}", 14, YELLOW, True),
                     Info("Inventario: " + (", ".join(i.nombre for i in self.partida.inventario) or "vacío"), 13)]
                if opciones:
                    c.append(Opciones("op", "Elige", opciones, cols=2))
                else:
                    c.append(Info("No hay objetos aquí.", 13, C_TEXTO_DIM))
                return c
            k, d = dialogo(self.screen, "OBJETOS", b, datos, botones=[("aceptar", "Hacer"), ("cancelar", "Cerrar")])
            if k != "aceptar" or not d["op"]:
                return
            tipo, iid = d["op"].split(":", 1)
            if tipo == "c":
                it = next(i for i in rm.items if i.id == iid)
                rm.items.remove(it)
                it.estado = "inventario"
                self.partida.inventario.append(it)
                self.log(f"Cogéis: {it.nombre}.")
            else:
                it = next(i for i in self.partida.inventario if i.id == iid)
                self.partida.inventario.remove(it)
                it.estado = "en_room"
                rm.items.append(it)
                self.log(f"Dejáis: {it.nombre}.")

    def accion_mecanismo(self):
        if not self.room or not self.room.mecanismos:
            mensaje(self.screen, "MECANISMO", "No hay mecanismos aquí.")
            return
        datos = {"m": self.room.mecanismos[0].id, "acc": "accionar"}

        def b(d):
            m = next(x for x in self.room.mecanismos if x.id == d["m"])
            return [Opciones("m", "Mecanismo", [(x.id, f"{x.nombre} [{x.estado}]") for x in self.room.mecanismos], cols=2),
                    Info(m.descripcion or "", 13),
                    Info(m.texto_on if m.estado == "on" else m.texto_off if m.estado == "off" else m.texto_ya_destruido, 13, C_SUBTITULO),
                    Opciones("acc", "Acción", [("accionar", "Accionar (cambiar estado)"), ("destruir", "Destruir")], cols=2),
                    Info("Si la acción es peligrosa o difícil, haz antes una tirada de habilidad (trastear, destruir...).",
                         11, C_TEXTO_DIM)]
        k, d = dialogo(self.screen, "MECANISMO", b, datos, botones=[("aceptar", "Hacer"), ("cancelar", "Cancelar")], ancho=820)
        if k != "aceptar":
            return
        m = next(x for x in self.room.mecanismos if x.id == d["m"])
        if m.estado == "destruido":
            self.log(m.texto_ya_destruido or f"{m.nombre} ya está destruido.")
            return
        if d["acc"] == "destruir":
            m.estado = "destruido"
            self.log(m.texto_destruido or f"Destruís {m.nombre}.")
            return
        if m.estado == "on":
            m.estado = "off"
            self.log(m.texto_on_a_off or f"{m.nombre} se desactiva.")
            self.aplicar_efecto(m.efecto_off)
        else:
            m.estado = "on"
            self.log(m.texto_off_a_on or f"{m.nombre} se activa.")
            self.aplicar_efecto(m.efecto_on)

    def aplicar_efecto(self, ef):
        """Aplica el efecto de un mecanismo creado con el Editor de Dungeons."""
        t = (ef.tipo or "").lower()
        if t in ("", "ninguno"):
            return
        p = self.actual
        if ("dan" in t or "dañ" in t or "herida" in t) and p:
            self.resolver_dano(p, max(1, ef.puntos))
        elif "cur" in t and p:
            self.log(f"{p.nombre} recupera {p.curar(max(1, ef.puntos))} PG.")
        elif "estres" in t or "estrés" in t:
            if p:
                self.log(p.ganar_estres(ef.puntos, "mecanismo"))
        elif "corrup" in t:
            if p:
                self.log(p.ganar_corrupcion(ef.puntos, "mecanismo"))
        elif "moneda" in t or "oro" in t:
            self.partida.monedas += ef.monedas or ef.puntos
            self.log(f"Conseguís {ef.monedas or ef.puntos} monedas.")
        elif ("item" in t or "objeto" in t) and ef.item_id:
            it = next((i for i in self.dungeon.items_globales if i.id == ef.item_id), None)
            if it:
                from models import Item
                nuevo = Item.from_dict(it.to_dict())
                nuevo.estado = "en_room"
                self.room.items.append(nuevo)
                self.log(f"Aparece: {nuevo.nombre}.")
        elif ("abr" in t or "cerr" in t or "salida" in t or "puerta" in t) and ef.direccion:
            estado = "cerrada" if "cerr" in t else "abierta"
            s = self.room.salida_en(ef.direccion)
            dest = self.dungeon.destino_salida(self.room, s) if s else None
            if s:
                if ef.sentido in ("ambos", "ida", "destino", ""):
                    s.estado_hacia_destino = estado
                if ef.sentido in ("ambos", "vuelta", "origen"):
                    s.estado_hacia_origen = estado
            if dest:
                sv = dest.salida_en(OPPOSITE[ef.direccion])
                if sv:
                    if ef.sentido in ("ambos", "ida", "destino", ""):
                        sv.estado_hacia_origen = estado
                    if ef.sentido in ("ambos", "vuelta", "origen"):
                        sv.estado_hacia_destino = estado
            self.log(f"La salida {ef.direccion} queda {estado}.")

    def accion_fortuna(self):
        v = reglas.tirada_fortuna()
        vivos = [p for p in self.grupo if p.estado not in ("muerto", "retirado")]
        azar = random.choice(vivos).nombre if vivos else "—"
        self.log(f"Tirada de fortuna: {v}. Personaje al azar: {azar}.")
        dialogo(self.screen, "TIRADA DE FORTUNA", lambda d: [
            Info("Para decidir si ocurre algo o a quién afecta (lo decide el DJ). Ej.: 1-2 uno, 3-4 otro, 5-6 otro.", 12),
            Dados([v], tam=60), Info(f"Resultado: {v}", 18, C_TITULO, True),
            Info(f"Personaje elegido al azar del grupo: {azar}", 14)], botones=[("ok", "Aceptar")])

    def accion_corrupcion(self):
        datos = {"pj": self.sel, "n": 1, "res": True, "contra": "corrupcion_arcana", "efecto": "reducir", "motivo": ""}

        def b(d):
            c = [Info("La corrupción se gana por acciones malvadas o por el contacto con poderes oscuros "
                      "(lugares corruptos, tratos con entidades oscuras, magia u objetos malvados). La decide el DJ.", 12, C_TEXTO_DIM),
                 Opciones("pj", "Personaje", self._opc_pj(), cols=6),
                 Texto("motivo", "Motivo", "Ej.: leer el grimorio negro"),
                 Opciones("n", "Puntos", [(-1, "Limpiar 1"), (1, "+1"), (2, "+2"), (3, "+3")], cols=4)]
            if d["n"] > 0:
                c.append(Check("res", "El DJ permite una tirada de resistencia a la corrupción (Voluntad)"))
                if d["res"]:
                    c += [Opciones("contra", "Origen", [("corrupcion_arcana", "Magia arcana corrupta"),
                                                        ("corrupcion_divina", "Magia divina corrupta")], cols=2),
                          Opciones("efecto", "El DJ decide: la resistencia...",
                                   [("anular", "Evita la corrupción"), ("reducir", "La reduce en 1")], cols=2)]
            return c
        k, d = dialogo(self.screen, "CORRUPCIÓN", b, datos, ancho=820)
        if k != "aceptar":
            return
        p = self.grupo[d["pj"]]
        n = d["n"]
        motivo = d["motivo"].strip() or "poderes oscuros"
        if n > 0 and d["res"]:
            res = reglas.tirada_resistencia(p, "VOL", d["contra"])
            n = 0 if d["efecto"] == "anular" else n - 1
            self.log(f"{p.nombre} resiste la corrupción: {res['dados']}.", res["eventos"])
            self.mostrar_tirada(f"RESISTENCIA A LA CORRUPCIÓN — {p.nombre}", res, [f"Gana {n} de corrupción."])
        self.log(p.ganar_corrupcion(n, motivo))

    def accion_experiencia(self):
        while True:
            datos = {"pj": self.sel, "dest": None}

            def b(d):
                p = self.grupo[d["pj"]]
                usados = set(p.xp_sesion)
                ops = [(a, f"{NOMBRE_ATRIBUTO[a]} ({p.atributos.get(a, 0)}/6)") for a in reglas.ATRIBUTOS] + \
                      [("nivel", f"Barra de nivel ({p.barra_nivel}/9)")]
                return [Info(f"Sesión {self.partida.sesion}. El DJ da de 1 a 3 puntos de experiencia por sesión, "
                             "sobre todo por implicarse y rolear. Cada punto sube una casilla de un atributo o de la "
                             "barra de nivel; en la misma sesión no se puede repetir destino.", 12, C_TEXTO_DIM),
                        Opciones("pj", "Personaje", self._opc_pj(), cols=6),
                        Opciones("dest", "Invertir 1 punto de experiencia en", ops, cols=4, deshabilitadas=usados),
                        Info("Ya usados esta sesión: " + (", ".join(p.xp_sesion) or "ninguno"), 12)]
            k, d = dialogo(self.screen, "EXPERIENCIA", b, datos, ancho=860,
                           botones=[("aceptar", "Dar punto"), ("sesion", "Nueva sesión"), ("cancelar", "Cerrar")],
                           validar=lambda d, k: None if k != "aceptar" or d["dest"] else "Elige destino.")
            if k == "cancelar":
                return
            if k == "sesion":
                if confirmar(self.screen, "¿Empezar una nueva sesión de juego? (se reinicia el límite de experiencia)"):
                    self.partida.sesion += 1
                    for p in self.grupo:
                        p.xp_sesion = []
                    self.log(f"— Comienza la sesión {self.partida.sesion} —")
                continue
            p = self.grupo[d["pj"]]
            ok, ev = reglas.gastar_experiencia(p, d["dest"])
            self.log(ev)
            self.resolver_pendientes()

    def accion_descanso(self):
        if not confirmar(self.screen, "FASE DE DESCANSO: solo si el grupo llega a una población o refugio donde "
                         "pueda parar varios días. En mitad de un dungeon NO hay fase de descanso. ¿Concede el DJ "
                         "una fase de descanso?", "FASE DE DESCANSO"):
            return
        self.log("— Fase de descanso —")
        for p in self.grupo:
            if p.estado in ("muerto", "retirado"):
                continue
            self.log(reglas.curacion_joven(p))
            if p.armadura_usada:
                p.armadura_usada = 0
                self.log(f"{p.nombre} repara su armadura.")
            datos = {"tareas": [], "sanador": "pnj", "pnj_pts": 2, "hab": "trastear", "cant": 1, "largo": False,
                     "entreno": None, "proy_hab": None, "proy": ""}
            sanadores = [(str(i), q.nombre) for i, q in enumerate(self.grupo) if q.puede_actuar and q is not p]

            def b(d, p=p):
                c = [Info(f"{p.nombre}: PG {p.puntos_golpe}/{p.pg_max}, estrés {p.estres}/9. Elige DOS tareas distintas.", 13, C_TEXTO, True),
                     Multi("tareas", "Tareas", list(reglas.TAREAS_DESCANSO.items()), maximo=2, cols=4)]
                t = d["tareas"]
                if "curacion" in t:
                    c += [Separador(), Opciones("sanador", "Quién cura", [("pnj", "Un sanador PNJ")] + sanadores, cols=5),
                          Check("largo", "Descanso muy largo (días en un hospital o templo): cura todas las heridas")]
                    if d["sanador"] == "pnj":
                        c.append(Opciones("pnj_pts", "Nivel del sanador (cura sus puntos; crítico el doble)",
                                          [(1, "1 tribu"), (2, "2 villa"), (3, "3 ciudad"), (4, "4 gran ciudad")], cols=4))
                    else:
                        c += [Opciones("hab", "Habilidad", ["trastear", "sobrenatural"], cols=2),
                              Opciones("cant", "Cura con éxito", [(1, "1"), (2, "2"), (3, "3"), (4, "4")], cols=4)]
                if "estres" in t:
                    c += [Separador(), Info(f"Reducir estrés: {p.nombre} se entrega a su vicio ({p.vicio or '?'}).", 12)]
                if "entrenar" in t:
                    c += [Separador(), Opciones("entreno", "Entrenar: sube una casilla de",
                                                [(a, NOMBRE_ATRIBUTO[a]) for a in reglas.ATRIBUTOS] + [("nivel", "Barra de nivel")], cols=4)]
                if "proyecto" in t:
                    c += [Separador(), Texto("proy", "Proyecto a largo plazo", "Ej.: averiguar quién paga a los bandidos"),
                          Opciones("proy_hab", "Habilidad para la tirada", TODAS_LAS_HABILIDADES, cols=6, alto_boton=26, size=11)]
                return c

            def v(d, k):
                if len(d["tareas"]) != 2:
                    return "Elige dos tareas distintas."
                if "entrenar" in d["tareas"] and not d["entreno"]:
                    return "Elige qué entrenar."
                if "proyecto" in d["tareas"] and not d["proy_hab"]:
                    return "Elige la habilidad del proyecto."
                return None
            dialogo(self.screen, f"DESCANSO — {p.nombre}", b, datos, v, botones=[("ok", "Realizar")], ancho=900)
            resumen = []
            for t in datos["tareas"]:
                if t == "curacion":
                    if datos["largo"]:
                        n = p.curar(p.pg_max)
                        resumen.append(f"Descanso largo: {p.nombre} cura todas sus heridas (+{n} PG).")
                    elif datos["sanador"] == "pnj":
                        r = reglas.tirada_curacion_pnj(datos["pnj_pts"], p)
                        resumen.append(f"Sanador: {r['dados']} → {NOMBRE_RESULTADO[r['resultado']]}. " + r["eventos"][0])
                    else:
                        cur = self.grupo[int(datos["sanador"])]
                        r = reglas.tirada_curacion(cur, datos["hab"], p, datos["cant"])
                        if r["resultado"]:
                            resumen.append(f"{cur.nombre} cura: {r['dados']} → {NOMBRE_RESULTADO[r['resultado']]}.")
                        resumen += r["eventos"]
                elif t == "estres":
                    r = reglas.tirada_reducir_estres(p)
                    resumen.append(f"Vicio: {r['dados']}" + (" (2d6, el peor)" if r["cero_dados"] else "") + ". " + r["eventos"][0])
                elif t == "entrenar":
                    ok, ev = reglas.gastar_experiencia(p, datos["entreno"], entrenamiento=True)
                    resumen += ev
                elif t == "proyecto":
                    r = reglas.tirada_habilidad(p, datos["proy_hab"], situacion="controlada")
                    if r["resultado"]:
                        resumen.append(f"Proyecto «{datos['proy'] or 'sin nombre'}» ({datos['proy_hab']}): {r['dados']} → "
                                       f"{NOMBRE_RESULTADO[r['resultado']]}. El DJ narra el avance.")
                    else:
                        resumen += r["eventos"]
            self.log(resumen)
            mensaje(self.screen, f"DESCANSO — {p.nombre}", resumen or ["Sin cambios."])
            self.resolver_pendientes()

    def accion_ficha(self):
        p = self.actual
        if not p:
            return
        W, H = self.screen.get_size()
        dialogo(self.screen, f"FICHA — {p.nombre}", builder_ficha(p), {}, botones=[("ok", "Cerrar")],
                ancho=W - 120, alto=H - 60)

    def accion_guardar(self):
        persistence.guardar_partida(self.partida, self.dungeon)
        self.log(f"Partida guardada ({self.partida.fecha_guardado}).")

    def accion_salir(self):
        datos = {"fichas": False}
        k, d = dialogo(self.screen, "SALIR DE LA PARTIDA", lambda d: [
            Info("¿Qué quieres hacer?", 15),
            Check("fichas", "Actualizar también las fichas de los personajes (data/personajes) con su estado y progreso")],
            datos, botones=[("guardar", "Guardar y salir"), ("salir", "Salir sin guardar"), ("cancelar", "Seguir jugando")],
            ancho=760, tecla_enter="guardar")
        if k == "cancelar":
            return
        if d["fichas"]:
            for p in self.grupo:
                persistence.guardar_personaje(p)
        self.guardar_al_salir = k == "guardar"
        self.salir = True


def run_game(screen, partida: Partida, dungeon: Dungeon):
    """Punto de entrada usado por la pantalla de partidas."""
    return Juego(screen, partida, dungeon).run()

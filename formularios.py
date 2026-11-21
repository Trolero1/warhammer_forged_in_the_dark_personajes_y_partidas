# formularios.py - Formularios y diálogos reutilizables
#
# Un "formulario" es una lista de campos (opciones, casillas, textos...) que se
# dibujan uno debajo de otro y modifican un diccionario de datos. La lista de
# campos la genera una función ("builder") que recibe los datos, así un
# formulario puede cambiar según lo que el usuario va eligiendo (por ejemplo,
# mostrar los dados que se van a tirar).
#
# Se usa tanto en el creador de personajes como en los diálogos del juego.

from __future__ import annotations
import pygame
from constants import *
from ui_utils import get_font, draw_text


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES DE DIBUJO
# ══════════════════════════════════════════════════════════════════════════════

def envolver(texto: str, size: int, ancho: int, bold: bool = False) -> list[str]:
    font = get_font(size, bold)
    lineas = []
    for parrafo in str(texto).split("\n"):
        linea = ""
        for w in parrafo.split(" "):
            prueba = (linea + " " + w).strip()
            if font.size(prueba)[0] <= ancho or not linea:
                linea = prueba
            else:
                lineas.append(linea)
                linea = w
        lineas.append(linea)
    return lineas


def texto_ajustado(surf, texto, x, y, size, color, ancho, bold=False) -> int:
    lineas = envolver(texto, size, ancho, bold)
    font = get_font(size, bold)
    for i, l in enumerate(lineas):
        surf.blit(font.render(l, True, color), (x, y + i * (size + 3)))
    return len(lineas) * (size + 3)


def boton(surf, rect, texto, size=14, seleccionado=False, deshabilitado=False, color=None, hover=None):
    if hover is None:
        hover = rect.collidepoint(pygame.mouse.get_pos())
    base = color or C_BOTON
    if deshabilitado:
        bg, tc = tuple(max(0, c - 45) for c in base), C_TEXTO_DIM
    elif seleccionado:
        bg, tc = C_BOTON_SEL, (20, 10, 5)
    elif hover:
        bg, tc = C_BOTON_HOV, C_BOTON_TXT
    else:
        bg, tc = base, C_BOTON_TXT
    pygame.draw.rect(surf, bg, rect, border_radius=6)
    pygame.draw.rect(surf, C_BORDE if not seleccionado else C_TITULO, rect, 2, border_radius=6)
    font = get_font(size, True)
    t = texto
    while font.size(t)[0] > rect.w - 10 and len(t) > 3:
        t = t[:-2]
    if t != texto:
        t = t[:-1] + "…"
    s = font.render(t, True, tc)
    surf.blit(s, (rect.centerx - s.get_width() // 2, rect.centery - s.get_height() // 2))


_PIPS = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)],
         4: [(0, 0), (2, 0), (0, 2), (2, 2)], 5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
         6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}


def dibujar_dado(surf, x, y, tam, valor, usado=False, apagado=False):
    r = pygame.Rect(x, y, tam, tam)
    fondo = (235, 225, 200) if not apagado else (120, 110, 95)
    if valor == 6 and not apagado:
        fondo = (250, 215, 120)
    pygame.draw.rect(surf, fondo, r, border_radius=tam // 6)
    pygame.draw.rect(surf, C_TITULO if usado else (60, 40, 20), r, 3 if usado else 2, border_radius=tam // 6)
    paso = tam // 4
    rad = max(2, tam // 11)
    for cx, cy in _PIPS.get(valor, []):
        pygame.draw.circle(surf, (40, 20, 10), (x + paso + cx * paso, y + paso + cy * paso), rad)


# ══════════════════════════════════════════════════════════════════════════════
# CAMPOS
# ══════════════════════════════════════════════════════════════════════════════
# Cada campo sabe: calcular su alto para un ancho dado, dibujarse en un rect y
# procesar un evento (devolviendo True si cambió los datos).

class Campo:
    es_texto = False

    def alto(self, ancho, datos):
        return 0

    def dibujar(self, surf, rect, datos, form):
        pass

    def evento(self, ev, rect, datos, form):
        return False


class Titulo(Campo):
    def __init__(self, texto, size=17, color=C_TITULO):
        self.texto, self.size, self.color = texto, size, color

    def alto(self, ancho, datos):
        return len(envolver(self.texto, self.size, ancho, True)) * (self.size + 3) + 4

    def dibujar(self, surf, rect, datos, form):
        texto_ajustado(surf, self.texto, rect.x, rect.y, self.size, self.color, rect.w, True)


class Info(Campo):
    def __init__(self, texto, size=13, color=C_TEXTO, bold=False):
        self.texto, self.size, self.color, self.bold = texto, size, color, bold

    def alto(self, ancho, datos):
        if not self.texto:
            return 0
        return len(envolver(self.texto, self.size, ancho, self.bold)) * (self.size + 3) + 2

    def dibujar(self, surf, rect, datos, form):
        texto_ajustado(surf, self.texto, rect.x, rect.y, self.size, self.color, rect.w, self.bold)


class Separador(Campo):
    def alto(self, ancho, datos):
        return 10

    def dibujar(self, surf, rect, datos, form):
        pygame.draw.line(surf, C_SEPARADOR, (rect.x, rect.y + 4), (rect.right, rect.y + 4), 1)


class Espacio(Campo):
    def __init__(self, h=8):
        self.h = h

    def alto(self, ancho, datos):
        return self.h


class Opciones(Campo):
    """Grupo de botones de los que se elige uno. opciones: [(valor, texto)] o [texto]."""

    def __init__(self, key, etiqueta, opciones, cols=4, deshabilitadas=(), alto_boton=34,
                 size=13, permitir_ninguna=False, al_elegir=None):
        self.key, self.etiqueta = key, etiqueta
        self.opciones = [o if isinstance(o, tuple) else (o, str(o)) for o in opciones]
        self.cols = max(1, cols)
        self.deshab = set(deshabilitadas)
        self.ab, self.size = alto_boton, size
        self.permitir_ninguna = permitir_ninguna
        self.al_elegir = al_elegir

    def _cab(self, ancho):
        return (len(envolver(self.etiqueta, 13, ancho, True)) * 16 + 4) if self.etiqueta else 0

    def alto(self, ancho, datos):
        filas = (len(self.opciones) + self.cols - 1) // self.cols
        return self._cab(ancho) + filas * (self.ab + 6)

    def _rects(self, rect):
        y0 = rect.y + self._cab(rect.w)
        gap = 6
        bw = (rect.w - gap * (self.cols - 1)) // self.cols
        out = []
        for i, (v, t) in enumerate(self.opciones):
            c, f = i % self.cols, i // self.cols
            out.append((pygame.Rect(rect.x + c * (bw + gap), y0 + f * (self.ab + 6), bw, self.ab), v, t))
        return out

    def dibujar(self, surf, rect, datos, form):
        if self.etiqueta:
            texto_ajustado(surf, self.etiqueta, rect.x, rect.y, 13, C_SUBTITULO, rect.w, True)
        for r, v, t in self._rects(rect):
            boton(surf, r, t, self.size, seleccionado=(datos.get(self.key) == v),
                  deshabilitado=(v in self.deshab))

    def evento(self, ev, rect, datos, form):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for r, v, t in self._rects(rect):
                if r.collidepoint(ev.pos) and v not in self.deshab:
                    if self.permitir_ninguna and datos.get(self.key) == v:
                        datos[self.key] = None
                    else:
                        datos[self.key] = v
                    if self.al_elegir:
                        self.al_elegir(datos, v)
                    return True
        return False


class Multi(Opciones):
    """Botones de selección múltiple (datos[key] es una lista)."""

    def __init__(self, key, etiqueta, opciones, maximo=99, cols=4, deshabilitadas=(), alto_boton=30, size=12):
        super().__init__(key, etiqueta, opciones, cols, deshabilitadas, alto_boton, size)
        self.maximo = maximo

    def dibujar(self, surf, rect, datos, form):
        sel = datos.get(self.key) or []
        if self.etiqueta:
            texto_ajustado(surf, f"{self.etiqueta}  ({len(sel)} elegidos)", rect.x, rect.y, 13,
                           C_SUBTITULO, rect.w, True)
        for r, v, t in self._rects(rect):
            boton(surf, r, ("• " if v in sel else "") + t, self.size, seleccionado=(v in sel),
                  deshabilitado=(v in self.deshab))

    def evento(self, ev, rect, datos, form):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            sel = list(datos.get(self.key) or [])
            for r, v, t in self._rects(rect):
                if r.collidepoint(ev.pos) and v not in self.deshab:
                    if v in sel:
                        sel.remove(v)
                    elif len(sel) < self.maximo:
                        sel.append(v)
                    elif self.maximo == 1:
                        sel = [v]
                    datos[self.key] = sel
                    return True
        return False


class Check(Campo):
    def __init__(self, key, etiqueta, deshabilitado=False):
        self.key, self.etiqueta, self.deshab = key, etiqueta, deshabilitado

    def alto(self, ancho, datos):
        return max(26, len(envolver(self.etiqueta, 13, ancho - 30)) * 16 + 6)

    def dibujar(self, surf, rect, datos, form):
        caja = pygame.Rect(rect.x, rect.y + 2, 20, 20)
        on = bool(datos.get(self.key))
        hov = rect.collidepoint(pygame.mouse.get_pos()) and not self.deshab
        pygame.draw.rect(surf, C_ENTRADA_SEL if on else C_FONDO, caja, border_radius=3)
        pygame.draw.rect(surf, C_TEXTO_DIM if self.deshab else (C_TITULO if on or hov else C_BORDE), caja, 2, border_radius=3)
        if on:
            pygame.draw.line(surf, C_TITULO, (caja.x + 4, caja.y + 10), (caja.x + 8, caja.y + 15), 3)
            pygame.draw.line(surf, C_TITULO, (caja.x + 8, caja.y + 15), (caja.x + 16, caja.y + 4), 3)
        texto_ajustado(surf, self.etiqueta, rect.x + 30, rect.y + 3, 13,
                       C_TEXTO_DIM if self.deshab else C_TEXTO, rect.w - 30)

    def evento(self, ev, rect, datos, form):
        if self.deshab:
            return False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and rect.collidepoint(ev.pos):
            datos[self.key] = not datos.get(self.key)
            return True
        return False


class Texto(Campo):
    """Campo de texto de una línea. Usa eventos TEXTINPUT, así funcionan acentos y ñ."""
    es_texto = True

    def __init__(self, key, etiqueta, placeholder="", max_len=120, solo_numeros=False):
        self.key, self.etiqueta, self.placeholder = key, etiqueta, placeholder
        self.max_len, self.solo_numeros = max_len, solo_numeros

    def alto(self, ancho, datos):
        return (18 if self.etiqueta else 0) + 32

    def _caja(self, rect):
        return pygame.Rect(rect.x, rect.y + (18 if self.etiqueta else 0), rect.w, 30)

    def dibujar(self, surf, rect, datos, form):
        if self.etiqueta:
            draw_text(surf, self.etiqueta, rect.x, rect.y, 13, C_SUBTITULO, bold=True)
        caja = self._caja(rect)
        foco = form.foco == self.key
        pygame.draw.rect(surf, C_ENTRADA_SEL if foco else C_ENTRADA, caja, border_radius=4)
        pygame.draw.rect(surf, C_TITULO if foco else C_BORDE, caja, 2, border_radius=4)
        valor = str(datos.get(self.key) or "")
        font = get_font(14)
        if valor:
            vis = valor
            while font.size(vis + "_")[0] > caja.w - 12 and vis:
                vis = vis[1:]
            s = font.render(vis + ("_" if foco and (pygame.time.get_ticks() // 500) % 2 else ""), True, C_TEXTO)
        else:
            s = font.render(self.placeholder if not foco else "_", True, C_TEXTO_DIM)
        surf.blit(s, (caja.x + 6, caja.y + 6))

    def evento(self, ev, rect, datos, form):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self._caja(rect).collidepoint(ev.pos):
            form.foco = self.key
            return False
        if form.foco != self.key:
            return False
        valor = str(datos.get(self.key) or "")
        if ev.type == pygame.TEXTINPUT:
            t = ev.text
            if self.solo_numeros:
                t = "".join(c for c in t if c.isdigit())
            if t and len(valor) < self.max_len:
                datos[self.key] = (valor + t)[:self.max_len]
                return True
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_BACKSPACE:
            datos[self.key] = valor[:-1]
            return True
        return False


class Sugerencias(Campo):
    """Botones que copian su texto al primer campo de texto vacío de 'destinos'."""

    def __init__(self, etiqueta, opciones, destinos, cols=3):
        self.etiqueta, self.opciones, self.destinos, self.cols = etiqueta, opciones, destinos, cols

    def alto(self, ancho, datos):
        filas = (len(self.opciones) + self.cols - 1) // self.cols
        return 18 + filas * 30

    def _rects(self, rect):
        bw = (rect.w - 6 * (self.cols - 1)) // self.cols
        return [(pygame.Rect(rect.x + (i % self.cols) * (bw + 6), rect.y + 18 + (i // self.cols) * 30, bw, 26), t)
                for i, t in enumerate(self.opciones)]

    def dibujar(self, surf, rect, datos, form):
        draw_text(surf, self.etiqueta, rect.x, rect.y, 12, C_TEXTO_DIM)
        for r, t in self._rects(rect):
            boton(surf, r, t, 11, color=(60, 40, 18))

    def evento(self, ev, rect, datos, form):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for r, t in self._rects(rect):
                if r.collidepoint(ev.pos):
                    for k in self.destinos:
                        if not str(datos.get(k) or "").strip():
                            datos[k] = t
                            return True
        return False


class Dados(Campo):
    """Muestra una tirada de dados. 'usado' = índice del dado que cuenta."""

    def __init__(self, dados, cero=False, tam=46, etiqueta=""):
        self.dados, self.cero, self.tam, self.etiqueta = dados, cero, tam, etiqueta

    def alto(self, ancho, datos):
        return self.tam + 8 + (18 if self.etiqueta else 0)

    def dibujar(self, surf, rect, datos, form):
        y = rect.y
        if self.etiqueta:
            draw_text(surf, self.etiqueta, rect.x, y, 13, C_SUBTITULO, bold=True)
            y += 18
        if not self.dados:
            return
        objetivo = min(self.dados) if self.cero else max(self.dados)
        usado = self.dados.index(objetivo)
        for i, v in enumerate(self.dados):
            dibujar_dado(surf, rect.x + i * (self.tam + 10), y, self.tam, v, usado=(i == usado))


class Fila(Campo):
    """Varios campos en la misma línea, repartiendo el ancho."""

    def __init__(self, campos, gap=14):
        self.campos, self.gap = campos, gap

    def _anchos(self, ancho):
        w = (ancho - self.gap * (len(self.campos) - 1)) // len(self.campos)
        return w

    def alto(self, ancho, datos):
        w = self._anchos(ancho)
        return max(c.alto(w, datos) for c in self.campos)

    def subrects(self, rect):
        w = self._anchos(rect.w)
        return [pygame.Rect(rect.x + i * (w + self.gap), rect.y, w, rect.h) for i in range(len(self.campos))]

    def dibujar(self, surf, rect, datos, form):
        for c, r in zip(self.campos, self.subrects(rect)):
            c.dibujar(surf, r, datos, form)

    def evento(self, ev, rect, datos, form):
        cambio = False
        for c, r in zip(self.campos, self.subrects(rect)):
            cambio = c.evento(ev, r, datos, form) or cambio
        return cambio


# ══════════════════════════════════════════════════════════════════════════════
# FORMULARIO
# ══════════════════════════════════════════════════════════════════════════════

class Formulario:
    def __init__(self, builder, datos, rect):
        self.builder = builder
        self.datos = datos
        self.rect = pygame.Rect(rect)
        self.offset = 0
        self.foco = None
        self._layout = []
        self.alto_contenido = 0
        self.relayout()
        textos = self._claves_texto()
        if textos:
            self.foco = textos[0]

    def _claves_texto(self):
        out = []
        for c, _ in self._layout:
            for sub in (c.campos if isinstance(c, Fila) else [c]):
                if sub.es_texto:
                    out.append(sub.key)
        return out

    def relayout(self):
        campos = self.builder(self.datos)
        y = 0
        self._layout = []
        for c in campos:
            h = c.alto(self.rect.w - 14, self.datos)
            self._layout.append((c, pygame.Rect(self.rect.x, self.rect.y + y, self.rect.w - 14, h)))
            if h:
                y += h + 8
        self.alto_contenido = y
        self.offset = max(0, min(self.offset, max(0, y - self.rect.h)))

    def evento(self, ev) -> bool:
        if ev.type == pygame.MOUSEWHEEL and self.alto_contenido > self.rect.h:
            mp = pygame.mouse.get_pos()
            if self.rect.collidepoint(mp):
                self.offset = max(0, min(self.offset - ev.y * 40, self.alto_contenido - self.rect.h))
                return False
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_TAB:
            claves = self._claves_texto()
            if claves:
                i = claves.index(self.foco) if self.foco in claves else -1
                self.foco = claves[(i + 1) % len(claves)]
            return False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and not self.rect.collidepoint(ev.pos):
            return False
        cambio = False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.foco_anterior = self.foco
        for c, r in self._layout:
            rr = r.move(0, -self.offset)
            if c.evento(ev, rr, self.datos, self):
                cambio = True
        if cambio:
            self.relayout()
        return cambio

    def dibujar(self, surf):
        self.relayout()
        clip = surf.get_clip()
        surf.set_clip(self.rect)
        for c, r in self._layout:
            rr = r.move(0, -self.offset)
            if rr.bottom < self.rect.y - 5 or rr.y > self.rect.bottom + 5:
                continue
            c.dibujar(surf, rr, self.datos, self)
        surf.set_clip(clip)
        if self.alto_contenido > self.rect.h:
            total = self.alto_contenido
            bh = max(30, int(self.rect.h * self.rect.h / total))
            by = self.rect.y + int(self.offset / total * self.rect.h)
            pygame.draw.rect(surf, C_BORDE, (self.rect.right - 8, by, 6, bh), border_radius=3)


# ══════════════════════════════════════════════════════════════════════════════
# DIÁLOGOS MODALES
# ══════════════════════════════════════════════════════════════════════════════

ACEPTAR_CANCELAR = [("aceptar", "Aceptar"), ("cancelar", "Cancelar")]

# Si una pantalla asigna aquí una función que redibuja su contenido, cada diálogo la
# llama antes de abrirse; así un diálogo nunca queda pintado encima del anterior.
fondo_base = None


def dialogo(screen, titulo, builder, datos=None, validar=None, botones=None, ancho=780,
            alto=None, tecla_enter="aceptar"):
    """Muestra un formulario modal. Devuelve (clave_boton, datos).
    validar(datos, boton) -> texto de error o None. ESC equivale a 'cancelar'."""
    datos = {} if datos is None else datos
    botones = botones or ACEPTAR_CANCELAR
    if fondo_base:
        try:
            fondo_base()
        except Exception:
            pass
    fondo = screen.copy()
    clock = pygame.time.Clock()
    error = ""
    sw, sh = screen.get_size()
    ancho = min(ancho, sw - 40)
    tmp = Formulario(builder, datos, (0, 0, ancho - 40, 10000))
    h_cont = tmp.alto_contenido
    alto_total = alto or (h_cont + 60 + 70)
    alto_total = min(alto_total, sh - 40)
    rect = pygame.Rect((sw - ancho) // 2, (sh - alto_total) // 2, ancho, alto_total)
    form = Formulario(builder, datos, (rect.x + 20, rect.y + 48, ancho - 40, alto_total - 48 - 70))
    form.foco = tmp.foco
    nb = len(botones)
    bw = min(200, (ancho - 40 - 12 * (nb - 1)) // nb)

    def rects_botones():
        total = nb * bw + (nb - 1) * 12
        x0 = rect.centerx - total // 2
        return [(pygame.Rect(x0 + i * (bw + 12), rect.bottom - 52, bw, 40), k, t)
                for i, (k, t) in enumerate(botones)]

    def intentar(k):
        nonlocal error
        if validar and k != "cancelar":
            e = validar(datos, k)
            if e:
                error = e
                return False
        return True

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return "cancelar", datos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                if any(k == "cancelar" for k, _ in botones):
                    return "cancelar", datos
                if nb == 1:
                    return botones[0][0], datos
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and tecla_enter:
                k = tecla_enter if any(k == tecla_enter for k, _ in botones) else botones[0][0]
                if intentar(k):
                    return k, datos
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for r, k, _ in rects_botones():
                    if r.collidepoint(ev.pos) and intentar(k):
                        return k, datos
            if form.evento(ev):
                error = ""

        screen.blit(fondo, (0, 0))
        sombra = pygame.Surface((sw, sh), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 170))
        screen.blit(sombra, (0, 0))
        pygame.draw.rect(screen, C_PANEL, rect, border_radius=10)
        pygame.draw.rect(screen, C_TITULO, rect, 2, border_radius=10)
        draw_text(screen, titulo, rect.x + 20, rect.y + 14, 19, C_TITULO, bold=True)
        pygame.draw.line(screen, C_BORDE, (rect.x + 14, rect.y + 42), (rect.right - 14, rect.y + 42), 1)
        form.dibujar(screen)
        if error:
            texto_ajustado(screen, error, rect.x + 20, rect.bottom - 74, 13, C_ERROR, rect.w - 40)
        for r, k, t in rects_botones():
            boton(screen, r, t, 14, color=(C_ERROR if k == "cancelar" else None))
        pygame.display.flip()
        clock.tick(30)


def mensaje(screen, titulo, lineas, ancho=700):
    if isinstance(lineas, str):
        lineas = [lineas]
    dialogo(screen, titulo, lambda d: [Info(l) for l in lineas], botones=[("ok", "Aceptar")], ancho=ancho)


def confirmar(screen, texto, titulo="CONFIRMAR"):
    k, _ = dialogo(screen, titulo, lambda d: [Info(texto, 15)],
                   botones=[("si", "Sí"), ("cancelar", "No")], ancho=560, tecla_enter="si")
    return k == "si"


def elegir(screen, titulo, opciones, texto="", cols=1, ancho=700):
    """Elige una opción de una lista. Devuelve el índice o None."""
    datos = {"_sel": None}
    items = [(i, str(o)) for i, o in enumerate(opciones)]

    def b(d):
        c = [Info(texto)] if texto else []
        return c + [Opciones("_sel", "", items, cols=cols, alto_boton=32)]

    k, d = dialogo(screen, titulo, b, datos, ancho=ancho,
                   validar=lambda d, k: None if d.get("_sel") is not None else "Elige una opción.")
    return d["_sel"] if k == "aceptar" else None


def pedir_texto(screen, titulo, etiqueta, inicial="", placeholder=""):
    datos = {"_t": inicial}
    k, d = dialogo(screen, titulo, lambda d: [Texto("_t", etiqueta, placeholder)], datos, ancho=620,
                   validar=lambda d, k: None if str(d.get("_t", "")).strip() else "Escribe algo.")
    return d["_t"].strip() if k == "aceptar" else None

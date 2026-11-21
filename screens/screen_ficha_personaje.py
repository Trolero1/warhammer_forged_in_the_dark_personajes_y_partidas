# screens/screen_ficha_personaje.py
# Ficha de personaje: texto de la ficha, dibujo de retratos y pantalla de consulta.

import os
import pygame
from constants import *
from ui_utils import draw_text
import reglas
from reglas import HABILIDADES_POR_ATRIBUTO, NOMBRE_ATRIBUTO, ETAPAS_TRASFONDO
from formularios import Formulario, Titulo, Info, Separador, Campo, boton, texto_ajustado


# ══════════════════════════════════════════════════════════════════════════════
# RETRATOS
# ══════════════════════════════════════════════════════════════════════════════

COLOR_CLASE = {
    "Guerrero": (150, 50, 40), "Explorador": (60, 120, 60), "Ladrón": (70, 70, 90),
    "Comerciante": (160, 120, 40), "Bardo": (130, 60, 130), "Extraño": (50, 80, 150),
}
_cache_retratos = {}


def _imagen_retrato(nombre, tam):
    clave = (nombre, tam)
    if clave in _cache_retratos:
        return _cache_retratos[clave]
    img = None
    ruta = os.path.join(RETRATOS_DIR, nombre) if nombre else ""
    if ruta and os.path.isfile(ruta):
        try:
            raw = pygame.image.load(ruta).convert()
            w, h = raw.get_size()
            lado = min(w, h)
            raw = raw.subsurface(((w - lado) // 2, (h - lado) // 2, lado, lado))
            img = pygame.transform.smoothscale(raw, tam)
        except Exception:
            img = None
    _cache_retratos[clave] = img
    return img


def dibujar_retrato(surf, rect, p, apagado=False):
    """Dibuja el retrato del personaje (imagen o silueta generada)."""
    rect = pygame.Rect(rect)
    img = _imagen_retrato(p.retrato, rect.size)
    if img:
        surf.blit(img, rect.topleft)
    else:
        clip = surf.get_clip()
        surf.set_clip(rect.clip(clip) if clip else rect)
        col = COLOR_CLASE.get(p.clase, (90, 70, 50))
        pygame.draw.rect(surf, tuple(c // 3 for c in col), rect)
        cx = rect.centerx
        cab = rect.w // 5
        pygame.draw.ellipse(surf, col, (cx - rect.w // 2 + 6, rect.y + rect.h * 0.62, rect.w - 12, rect.h * 0.7))
        pygame.draw.circle(surf, tuple(min(255, c + 40) for c in col), (cx, int(rect.y + rect.h * 0.42)), cab)
        f = pygame.font.SysFont("monospace", max(10, rect.w // 7), bold=True)
        ini = (p.raza[:1] + p.clase[:1]).upper()
        s = f.render(ini, True, (240, 230, 200))
        surf.blit(s, (rect.x + 4, rect.y + 2))
        surf.set_clip(clip)
    if apagado:
        sombra = pygame.Surface(rect.size, pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 160))
        surf.blit(sombra, rect.topleft)
    pygame.draw.rect(surf, C_BORDE, rect, 2)


# ══════════════════════════════════════════════════════════════════════════════
# TEXTO DE LA FICHA
# ══════════════════════════════════════════════════════════════════════════════

def _puntos(v, mx=4):
    return "●" * v + "○" * (mx - v)


def lineas_ficha(p):
    """Devuelve [(titulo, texto)] con toda la ficha. Se usa en la ficha y en el resumen."""
    L = []
    cab = f"{p.nombre}" + (f" «{p.apodo}»" if p.apodo else "")
    sub = f"{p.raza} · {p.descripcion_clase} · {p.edad} años ({p.etapa or '?'})"
    if p.deidad:
        sub += f" · Deidad: {p.deidad}"
    L.append((cab, sub))
    hc = p.habilidad_clase
    for atr in reglas.ATRIBUTOS:
        partes = [f"{'♦' if h == hc else ''}{h} {_puntos(p.habilidades.get(h, 0))}"
                  for h in HABILIDADES_POR_ATRIBUTO[atr]]
        L.append((f"{NOMBRE_ATRIBUTO[atr].upper()}  [barra {p.atributos.get(atr, 0)}/{reglas.BARRA_ATRIBUTO}]",
                  "   ".join(partes)))
    L.append(("ESTADO", f"Puntos de golpe {p.puntos_golpe}/{p.pg_max}   ·   Estrés {p.estres}/{reglas.BARRA_ESTRES}"
              f"   ·   Corrupción {p.corrupcion}/{reglas.BARRA_CORRUPCION}   ·   Barra de nivel "
              f"{p.barra_nivel}/{reglas.BARRA_NIVEL}   ·   Armadura {p.armadura - p.armadura_usada}/{p.armadura}"
              f"   ·   {p.estado.capitalize()}"))
    if p.traumas or p.ruinas:
        L.append(("TRAUMAS Y RUINAS", f"Traumas: {', '.join(p.traumas) or '—'}   ·   Ruinas: {', '.join(p.ruinas) or '—'}"))
    tal = "; ".join(t["nombre"] + (f" ({t['descripcion']})" if t.get("descripcion") else "") for t in p.talentos)
    L.append(("TALENTOS", tal or "Ninguno"))
    extras = []
    if reglas.RAZAS.get(p.raza, {}).get("infravision"):
        extras.append("Infravisión a 18 m")
    res = reglas.RAZAS.get(p.raza, {}).get("resistencias", [])
    if res:
        nombres = dict(reglas.TIPOS_RESISTENCIA)
        extras.append("+1d6 a resistir: " + ", ".join(nombres[r].lower() for r in res))
    extras.append("Sabe leer y escribir" if p.sabe_leer else "No sabe leer ni escribir")
    L.append(("RASGOS DE RAZA Y CLASE", ". ".join(extras) + "."))
    L.append(("MOTIVACIÓN Y VICIO", f"Motivación: {p.motivacion or '—'}   ·   Vicio: {p.vicio or '—'}"))
    tf = []
    for c, nombre, _ in ETAPAS_TRASFONDO:
        e = p.trasfondo.get(c, {})
        if e.get("texto") or e.get("habilidad"):
            tf.append(f"{nombre.capitalize()}: {e.get('texto') or '—'}" + (f" (+1 {e['habilidad']})" if e.get("habilidad") else ""))
    if tf:
        L.append(("TRASFONDO", "\n".join(tf)))
    ap = []
    if p.cabello or p.ojos:
        ap.append(f"Cabello {p.cabello or '?'}, ojos {p.ojos or '?'}")
    if p.rasgos_apariencia:
        ap.append(", ".join(p.rasgos_apariencia))
    if ap:
        L.append(("APARIENCIA", ". ".join(ap)))
    if p.personalidad:
        L.append(("PERSONALIDAD", ", ".join(p.personalidad)))
    if p.recuerdos:
        L.append(("RECUERDOS", " · ".join(p.recuerdos)))
    if p.amigos or p.enemigos:
        L.append(("AMIGOS Y ENEMIGOS", f"Amigos: {', '.join(p.amigos) or '—'}\nEnemigos: {', '.join(p.enemigos) or '—'}"))
    if p.lazos:
        L.append(("LAZOS", p.lazos))
    if p.equipo:
        L.append(("EQUIPO", p.equipo))
    return L


class _Retrato(Campo):
    def __init__(self, p):
        self.p = p

    def alto(self, ancho, datos):
        return 130

    def dibujar(self, surf, rect, datos, form):
        dibujar_retrato(surf, (rect.x, rect.y, 120, 120), self.p)


def builder_ficha(p):
    def b(_d):
        c = [_Retrato(p)]
        for titulo, texto in lineas_ficha(p):
            c.append(Titulo(titulo, 15))
            if texto:
                c.append(Info(texto, 13))
            c.append(Separador())
        return c
    return b


# ══════════════════════════════════════════════════════════════════════════════
# PANTALLA DE CONSULTA
# ══════════════════════════════════════════════════════════════════════════════

class ScreenFichaPersonaje:
    def __init__(self, app, personaje):
        self.app = app
        self.personaje = personaje
        W, H = app.screen.get_size()
        self.form = Formulario(builder_ficha(personaje), {}, (80, 130, W - 160, H - 210))

    def _volver(self):
        from screens.screen_personajes import ScreenPersonajesManager
        self.app.current_screen = ScreenPersonajesManager(self.app)

    def _rect_volver(self):
        W, H = self.app.screen.get_size()
        return pygame.Rect(W // 2 - 100, H - 64, 200, 44)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self._volver()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._rect_volver().collidepoint(event.pos):
            self._volver()
            return
        self.form.evento(event)

    def update(self, dt):
        pass

    def draw(self, surf):
        W, H = surf.get_size()
        surf.fill(C_FONDO)
        draw_text(surf, "FICHA DE PERSONAJE", 80, 40, 30, C_TITULO, bold=True)
        draw_text(surf, f"#{self.personaje.numero}  ·  creado {self.personaje.fecha_creacion}", 82, 82, 13, C_TEXTO_DIM)
        pygame.draw.line(surf, C_TITULO, (60, 110), (W - 60, 110), 2)
        self.form.dibujar(surf)
        boton(surf, self._rect_volver(), "VOLVER", 15)

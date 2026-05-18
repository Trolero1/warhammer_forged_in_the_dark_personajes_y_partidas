# screens/screen_personaje_creador.py
# Creador de Personajes — WARHAMMER FORGED IN THE DARK

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button, TextInput, ScrollArea, Checkbox
from models import Personaje, TODAS_LAS_HABILIDADES, HABILIDADES_POR_ATRIBUTO
import persistence


RAZAS = ["Humano", "Halfling", "Enano", "Alto Elfo", "Elfo de los bosques"]

CARACTERISTICAS = {
    "Humano":      "Dos puntos de habilidad a repartir entre las habilidades, pero no los dos en la misma.",
    "Halfling":    "Visión mejorada, un punto en sigilo o en cazar, 1d6 más para resistir contra magia y venenos",
    "Enano":       "Visión en la oscuridad, un punto en destruir o en trastear, 1d6 más para resistir contra magia y venenos",
    "Alto Elfo":   "Visión mejorada y un punto en mover o en sobrenatural",
    "Elfo de los bosques":  "Visión mejorada y un punto en mover o en cazar",
}

BONOS_RAZA = {
    "Humano":      {"tipo": "elegir", "cantidad": 2, "habilidades": TODAS_LAS_HABILIDADES, "max_por_habilidad": 1},
    "Halfling":    {"tipo": "elegir", "cantidad": 1, "habilidades": ["sigilo", "cazar"]},
    "Enano":       {"tipo": "elegir", "cantidad": 1, "habilidades": ["destruir", "trastear"]},
    "Alto Elfo":   {"tipo": "elegir", "cantidad": 1, "habilidades": ["mover", "sobrenatural"]},
    "Elfo de los bosques": {"tipo": "elegir", "cantidad": 1, "habilidades": ["mover", "cazar"]},
}

PROFESIONES = {
    "Guerrero": {
        "bonos": [("mover", None), (None, ["luchar", "destruir"])],
        "apodos": ["Fabricatumbas", "Mandíbulagris", "Deshielosviento", "Acerofrio", "ElSinMiedo", "ElCarnicero"],
    },
    "Explorador": {
        "bonos": [("cazar", None), (None, ["mover", "sigilo"])],
        "apodos": ["ZorroDelBosque", "Matalobo", "Explorador", "ElCurtido", "Hambredesangre", "Flechadesombra"],
    },
    "Ladrón": {
        "bonos": [("sigilo", None), (None, ["cazar", "mover"])],
        "apodos": ["MedioDedo", "RataNegra", "OjoRojo", "PiesRápidos", "DobleLengua", "PuñalNocturno"],
    },
    "Comerciante": {
        "bonos": [("trastear", None), ("influir", None)],
        "apodos": ["SonrisaDePlata", "DienteDeOro", "LenguaDeSeda", "ElCeceosoYVeridico", "PanzaGorda", "Tacaño"],
    },
    "Bardo": {
        "bonos": [("socializar", None), ("sigilo", None)],
        "apodos": ["Hacedordeodas", "Hilacuentos", "Vozdeargento", "Clavededorado", "Lenguademiel", "Forjadorderrimas"],
    },
    "Mago": {
        "bonos": [("sobrenatural", None), ("estudiar", None)],
        "apodos": ["CorazónRaíz", "EspaldalaTorcida", "CapaGris", "ManoDeTormenta", "BastónCojo", "InvocadorDeSombras"],
    },
    "Clérigo": {
        "bonos": [("sobrenatural", None), (None, TODAS_LAS_HABILIDADES)],
        "apodos": ["MenteClara", "PulmónDePolvo", "VistaLarga", "ElLetrado", "ElOmnisciente", "ElGordoYErudito"],
    },
}

ORIGENES = {
    "Nobles": {"habilidad": "liderar", "desc": "+1 liderar"},
    "Comerciantes": {"habilidad": "influir", "desc": "+1 influir"},
    "Pobres": {"habilidad": "mover", "desc": "+1 mover"},
}

NINEZ = {
    "Fuerza": {"habilidad": "destruir", "desc": "+1 destruir"},
    "Carisma": {"habilidad": "socializar", "desc": "+1 socializar"},
    "Intuición": {"habilidad": "percibir", "desc": "+1 percibir"},
}

ADOLESCENCIA = {
    "Entrenaste con armas": {"habilidad": "luchar", "desc": "+1 luchar"},
    "Aprendiste a leer y escribir": {"habilidad": None, "desc": "Sabes leer y escribir"},
    "Cazabas animales": {"habilidad": "cazar", "desc": "+1 cazar"},
}

JUVENTUD = {
    "Taller o herrería": {"habilidad": "trastear", "desc": "+1 trastear"},
    "Fuiste un ladrón": {"habilidad": "sigilo", "desc": "+1 sigilo"},
    "Poder extraño": {"habilidad": "sobrenatural", "desc": "+1 sobrenatural"},
    "Estudiaste con tu maestro": {"habilidad": "estudiar", "desc": "+1 estudiar"},
}

EDADES = {
    "Joven": {"atributo": "CUE", "desc": "Un punto en una habilidad de Cuerpo"},
    "Adulto": {"atributo": "VOL", "desc": "Un punto en una habilidad de Voluntad"},
    "Anciano": {"atributo": "INT", "desc": "Un punto en una habilidad de Inteligencia"},
}

DEBILIDADES = [
    "Crédulo: me creo todo lo que me dicen.",
    "Codicioso: quiero una mayor parte de todo el tesoro.",
    "Susceptible: nunca tolero una provocación.",
    "Temerario: siempre voy el primero al peligro.",
    "Cobardón: siempre me quedo en la retaguardia.",
    "Cazamonstruos: todos los monstruos son malvados y deben ser eliminados.",
    "Intolerante: los nightkin como los orcos o goblins son malvados.",
    "Perezoso: aprovecho cualquier oportunidad para descansar.",
    "Glotón: aprovecho cualquier oportunidad para comer algo sabroso.",
    "Cleptómano: no puedo evitar robar objetos de valor.",
    "Vanidoso: ayudo a cualquiera que me alabe.",
    "Imprudente: siempre asumo grandes riesgos sin pensar en las consecuencias.",
    "Miedo a la magia: la magia es una fuerza maligna y los magos no son de fiar.",
    "Sed de conocimiento: la búsqueda del conocimiento importa más que mis amigos.",
    "Hijo de la naturaleza: nunca duermo bajo techo.",
    "Fanfarrón: siempre exagero mis logros.",
    "Violento: recurro a la violencia ante cualquier obstáculo.",
    "Dominante: siempre digo a los demás lo que deben hacer.",
    "Cínico: siempre pienso que las cosas saldrán mal.",
    "Arrogante: menosprecio a todo el que me encuentro.",
]

RECUERDOS = [
    "Tus viejos zapatos de confianza",
    "Un sencillo medallón de plata",
    "Una carta de un viejo amigo o familiar",
    "Un viejo diario deshilachado",
    "Un brazalete heredado de tu familia",
    "Una figurilla de madera que tenías de niño",
    "Una piedra de forma extraña",
    "Una moneda de cobre de un tesoro que buscaban tu madre o tu padre",
    "Una vieja jarra de peltre",
    "Un cuerno arrancado como trofeo a un monstruo",
    "Un colmillo tomado como trofeo de una bestia",
    "Un par de dados simples hechos de hueso",
    "Un medallón que contiene un mechón de pelo",
    "Una llave ornamentada",
    "Un mapa dibujado a mano que heredaste",
    "Un anillo con una inscripción",
    "Un silbato de hueso",
    "El viejo sombrero deshilachado de tu madre o padre",
    "Una pluma de grifo",
    "Una pipa bellamente tallada",
]

DETALLES_ASPECTO = [
    "Una fea cicatriz en la mejilla",
    "Un sombrero extraño",
    "Anormalmente pálido y pastoso",
    "Una sonrisa constante en los labios",
    "Una mirada fría y penetrante",
    "Un poco de sobrepeso en la cintura",
    "Delgado y enjuto",
    "Cantidad anormal de vello corporal",
    "Calvo",
    "Tatuaje prominente",
    "Olor corporal desagradable",
    "Peinado glorioso",
    "Cojera",
    "Sucio",
    "Ojos azules honestos",
    "Diente de plata",
    "Muy perfumado",
    "Ojos de diferente color",
    "Voz sibilante",
    "Cara curtida por la intemperie",
]

MOTIVACIONES = ["Riquezas", "Conocimiento", "Poder", "Venganza", "Explorar", "Amistad", "Justicia"]
VICIOS = ["Juego", "Alcohol", "Sexo", "Drogas", "Lujo", "Obligación"]


def text_size(text, size, bold=False):
    font = get_font(size, bold=bold)
    return font.size(text)


class ScreenElegirHabilidades:
    def __init__(self, creator, titulo, descripcion, habilidades_posibles, cantidad,  max_por_habilidad=1, max_nivel_creacion=3):
        self.creator = creator
        self.scroll = ScrollArea()
        self.titulo = titulo
        self.descripcion = descripcion
        self.habilidades_posibles = habilidades_posibles
        self.cantidad = cantidad
        self.max_por_habilidad = max_por_habilidad
        self.max_nivel = max_nivel_creacion
        self.seleccion = {}
        self.error = ""
        W = creator.app.screen.get_width()
        cols = min(4, len(habilidades_posibles))
        cols = max(1, cols)
        cb_w = min(220, (W - 160) // cols)
        start_x = W // 2 - (cols * cb_w) // 2
        self.checks = []
        for i, hab in enumerate(habilidades_posibles):
            col, row = i % cols, i // cols
            x = start_x + col * cb_w
            y = 280 + row * 36
            actual = creator.personaje.habilidades.get(hab, 0)
            label = f"{hab} ({actual})" if actual > 0 else hab
            cb = Checkbox(x, y, label, font_size=13, max_label_w=cb_w - 10)
            self.checks.append((cb, hab))
        num_filas = ((len(habilidades_posibles) - 1) // cols + 1)
        botones_y = 280 + num_filas * 36 + 40
        self.btn_atras = Button((W // 2 - 220, botones_y, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, botones_y, 180, 44), "Siguiente", color=C_BOTON_HOV)
        self.scroll.set_content_height(botones_y + 100, creator.app.screen.get_height() - 120)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for cb, hab in self.checks:
            if cb.handle_event(event, self.scroll.offset):
                if cb.checked:
                    total_seleccionado = sum(self.seleccion.values())
                    if total_seleccionado >= self.cantidad:
                        cb.checked = False
                    else:
                        actual_en_habilidad = self.seleccion.get(hab, 0)
                        if actual_en_habilidad >= self.max_por_habilidad:
                            cb.checked = False
                        else:
                            self.seleccion[hab] = actual_en_habilidad + 1
                else:
                    self.seleccion[hab] = max(0, self.seleccion.get(hab, 0) - 1)
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            total = sum(self.seleccion.values())
            if total != self.cantidad:
                self.error = f"Debes elegir exactamente {self.cantidad} puntos. Has asignado {total}."
            else:
                for hab, pts in self.seleccion.items():
                    if pts > 0:
                        actual = self.creator.personaje.habilidades.get(hab, 0)
                        nuevo = actual + pts
                        if nuevo > self.max_nivel:
                            self.error = f"{hab} no puede superar nivel {self.max_nivel} al crear el personaje."
                            return
                        self.creator.personaje.habilidades[hab] = nuevo
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for cb, _ in self.checks:
            cb.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, self.titulo, W // 2 - len(self.titulo) * 6, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        total = sum(self.seleccion.values())
        draw_text(surf, f"{self.descripcion}  (Asignados: {total}/{self.cantidad})",
                  80, 250, 13, C_TEXTO_DIM, max_width=W - 160)
        for cb, _ in self.checks:
            cb.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, 80, self.btn_atras.rect.y - 24 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)
        self.scroll.draw_scrollbar(surf, pygame.Rect(0, 120, W, surf.get_height() - 120))


class ScreenPersonajeCreador:
    def __init__(self, app):
        self.app = app
        self.scroll = ScrollArea()
        self.personaje = Personaje()
        self.current_step = 0
        self.flow_screens = self._build_flow()
        self.current_screen = self.flow_screens[0](self)
        self.btn_inicio = Button((app.screen.get_width() - 160, 20, 140, 40),
                                 "INICIO", font_size=14, bold=True)

    def _build_flow(self):
        flow = [ScreenRaza]
        flow.append(ScreenBonoRaza)
        flow.append(ScreenProfesion)
        flow.append(ScreenBonoProfesion)
        flow.append(ScreenEdad)
        flow.append(ScreenBonoEdad)
        flow.extend([
            ScreenOrigen, ScreenNinez, ScreenAdolescencia, ScreenJuventud,
            ScreenDebilidad, ScreenRecuerdos, ScreenAspecto,
            ScreenMotivacion, ScreenVicio,
            ScreenNombre, ScreenApodo,
            ScreenFichaFinal
        ])
        return flow

    def handle_event(self, event):
        if self.btn_inicio.handle_event(event):
            from screens.screen_partidas import ScreenPartidasManager
            from screens.screen_personajes import ScreenPersonajesManager
            if hasattr(self.app, '_party_state') and self.app._party_state is not None:
                self.app.current_screen = ScreenPartidasManager(self.app)
            else:
                self.app.current_screen = ScreenPersonajesManager(self.app)
            return
        self.current_screen.handle_event(event)

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.btn_inicio.update_hover(mp)
        self.current_screen.update(dt)

    def draw(self, surf):
        surf.fill(C_FONDO)
        self._draw_header(surf)
        self.current_screen.draw(surf)
        self.btn_inicio.draw(surf)

    def _draw_header(self, surf):
        W = surf.get_width()
        draw_text(surf, "WARHAMMER", W // 2 - 180, 40, 60, C_TITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)

    def go_next(self):
        self.current_step += 1
        if self.current_step < len(self.flow_screens):
            self.current_screen = self.flow_screens[self.current_step](self)
        else:
            self._guardar_y_volver()

    def go_back(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.current_screen = self.flow_screens[self.current_step](self)

    def _guardar_y_volver(self):
        try:
            persistence.guardar_personaje(self.personaje)
            from screens.screen_partidas import ScreenPartidasManager
            from screens.screen_personajes import ScreenPersonajesManager
            if hasattr(self.app, '_party_state') and self.app._party_state is not None:
                self.app.current_screen = ScreenPartidasManager(self.app)
            else:
                self.app.current_screen = ScreenPersonajesManager(self.app)
        except Exception as e:
            print(f"Error al guardar: {e}")


class ScreenRaza:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.raza
        self.error = ""
        W = creator.app.screen.get_width()
        cols, btn_w, btn_h = 3, 200, 52
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 16) // 2
        self.botones_raza = []
        for i, raza in enumerate(RAZAS):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 16)
            y = 220 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), raza, font_size=14, selected=(raza == self.seleccion))
            self.botones_raza.append((b, raza))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Inicio")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, raza in self.botones_raza:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = raza
                for b2, _ in self.botones_raza:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            from screens.screen_personajes import ScreenPersonajesManager
            self.creator.app.current_screen = ScreenPersonajesManager(self.creator.app)
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir una raza."
            else:
                self.creator.personaje.raza = self.seleccion
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones_raza:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 1 — RAZA", W // 2 - 120, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige la raza de tu personaje.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones_raza:
            btn.draw(surf, self.scroll.offset)
        if self.seleccion:
            draw_text(surf, CARACTERISTICAS[self.seleccion], 80, 420 - self.scroll.offset, 12, C_SUBTITULO, max_width=W - 160)
        if self.error:
            draw_text(surf, self.error, W // 2 - 160, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenBonoRaza:
    """Elige qué habilidades mejora tu raza (si aplica)."""
    def __init__(self, creator):
        self.creator = creator
        self._skip = False
        raza = creator.personaje.raza
        bono = BONOS_RAZA.get(raza)
        if bono is None or bono["tipo"] != "elegir":
            self._skip = True
            return
        titulo = f"PASO 1b — BONO RACIAL: {raza.upper()}"
        desc = f"Distribuye {bono['cantidad']} punto(s) entre las habilidades disponibles."
        max_por = bono.get("max_por_habilidad", 1)
        self._screen = ScreenElegirHabilidades(
            creator, titulo, desc,
            bono["habilidades"], bono["cantidad"], max_por_habilidad=max_por
        )

    def handle_event(self, e):
        if self._skip:
            self.creator.go_next()
            return
        if hasattr(self, '_screen'): self._screen.handle_event(e)
    def update(self, dt):
        if self._skip:
            self.creator.go_next()
            return
        if hasattr(self, '_screen'): self._screen.update(dt)
    def draw(self, s):
        if hasattr(self, '_screen'): self._screen.draw(s)


class ScreenProfesion:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.profesion
        self.error = ""
        W = creator.app.screen.get_width()
        nombres = list(PROFESIONES.keys())
        cols, btn_w, btn_h = 4, 180, 48
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 12) // 2
        self.botones_prof = []
        for i, prof in enumerate(nombres):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 12)
            y = 210 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), prof, font_size=13, selected=(prof == self.seleccion))
            self.botones_prof.append((b, prof))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, prof in self.botones_prof:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = prof
                for b2, _ in self.botones_prof:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir una profesión."
            else:
                self.creator.personaje.profesion = self.seleccion
                bonos = PROFESIONES[self.seleccion]["bonos"]
                for bono in bonos:
                    fija, _ = bono
                    if fija:
                        actual = self.creator.personaje.habilidades.get(fija, 0)
                        if actual < 4:
                            self.creator.personaje.habilidades[fija] = actual + 1
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones_prof:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 2 — PROFESIÓN", W // 2 - 130, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige la profesión de tu personaje.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones_prof:
            btn.draw(surf, self.scroll.offset)
        if self.seleccion:
            bonos = PROFESIONES[self.seleccion]["bonos"]
            partes = []
            for fija, opciones in bonos:
                if fija:
                    partes.append(fija)
                elif opciones:
                    partes.append("(" + "/".join(opciones) + ")")
            draw_text(surf, "Bonos: " + ", ".join(partes), 80, 520 - self.scroll.offset, 12, C_SUBTITULO, max_width=W - 160)
        if self.error:
            draw_text(surf, self.error, W // 2 - 180, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenBonoProfesion:
    """Elige la habilidad opcional de la profesión cuando hay elección."""
    def __init__(self, creator):
        self.creator = creator
        self._skip = False
        prof = creator.personaje.profesion
        bono_opcional = None
        for fija, opciones in PROFESIONES[prof]["bonos"]:
            if fija is None and opciones:
                bono_opcional = opciones
                break
        if bono_opcional is None:
            self._skip = True
            return
        titulo = f"BONO DE {prof.upper()}"
        desc = f"Elige 1 habilidad adicional para tu {prof}."
        self._screen = ScreenElegirHabilidades(creator, titulo, desc, bono_opcional, 1)

    def handle_event(self, e):
        if self._skip:
            self.creator.go_next()
            return
        if hasattr(self, '_screen'): self._screen.handle_event(e)
    def update(self, dt):
        if self._skip:
            self.creator.go_next()
            return
        if hasattr(self, '_screen'): self._screen.update(dt)
    def draw(self, s):
        if hasattr(self, '_screen'): self._screen.draw(s)


class ScreenEdad:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.edad
        self.error = ""
        W = creator.app.screen.get_width()
        card_w, card_h = 260, 120
        total_w = len(EDADES) * card_w + (len(EDADES) - 1) * 24
        start_x = W // 2 - total_w // 2
        self.cards = []
        for i, (edad, info) in enumerate(EDADES.items()):
            x = start_x + i * (card_w + 24)
            self.cards.append({"rect": pygame.Rect(x, 210, card_w, card_h), "edad": edad, "info": info["desc"],
                               "selected": edad == self.seleccion, "hovered": False})
        self.btn_atras = Button((W // 2 - 220, 360, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 360, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        mp = pygame.mouse.get_pos()
        for card in self.cards:
            r = card["rect"].move(0, -self.scroll.offset)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if r.collidepoint(mp):
                    self.seleccion = card["edad"]
                    for c2 in self.cards:
                        c2["selected"] = False
                    card["selected"] = True
                    self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir una edad."
            else:
                self.creator.personaje.edad = self.seleccion
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for card in self.cards:
            r = card["rect"].move(0, -self.scroll.offset)
            card["hovered"] = r.collidepoint(mp)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 3 — EDAD", W // 2 - 100, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige la edad de tu personaje.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for card in self.cards:
            r = card["rect"].move(0, -self.scroll.offset)
            if card["selected"]:
                bg = C_ENTRADA_SEL
                border = C_TITULO
            elif card["hovered"]:
                bg = (52, 36, 14)
                border = C_BORDE
            else:
                bg = C_ENTRADA
                border = C_BORDE
            pygame.draw.rect(surf, bg, r, border_radius=8)
            pygame.draw.rect(surf, border, r, 2, border_radius=8)
            ew = text_size(card["edad"], 22, bold=True)[0]
            draw_text(surf, card["edad"], r.x + (r.width - ew) // 2, r.y + 10, 22, C_TITULO, bold=True)
            draw_text(surf, card["info"], r.x + 12, r.y + 46, 12, C_TEXTO, max_width=r.width - 24)
        if self.error:
            draw_text(surf, self.error, W // 2 - 180, 350 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenBonoEdad:
    """Elige la habilidad que mejora por la edad."""
    def __init__(self, creator):
        edad = creator.personaje.edad
        atr = EDADES[edad]["atributo"]
        habilidades_atr = HABILIDADES_POR_ATRIBUTO[atr]
        titulo = f"BONO DE EDAD: {edad.upper()}"
        desc = f"Elige 1 habilidad de {atr} para mejorar."
        self._screen = ScreenElegirHabilidades(creator, titulo, desc, habilidades_atr, 1)

    def handle_event(self, e):
        if hasattr(self, '_screen'): self._screen.handle_event(e)
    def update(self, dt):
        if hasattr(self, '_screen'): self._screen.update(dt)
    def draw(self, s):
        if hasattr(self, '_screen'): self._screen.draw(s)


class ScreenOrigen:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.trasfondo_origen
        self.error = ""
        W = creator.app.screen.get_width()
        nombres = list(ORIGENES.keys())
        cols, btn_w, btn_h = 3, 220, 52
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 16) // 2
        self.botones = []
        for i, key in enumerate(nombres):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 16)
            y = 240 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), key, font_size=14, selected=(key == self.seleccion))
            self.botones.append((b, key))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, key in self.botones:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = key
                for b2, _ in self.botones:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir un origen."
            else:
                self.creator.personaje.trasfondo_origen = self.seleccion
                hab = ORIGENES[self.seleccion]["habilidad"]
                if hab:
                    actual = self.creator.personaje.habilidades.get(hab, 0)
                    if actual < 3:
                        self.creator.personaje.habilidades[hab] = actual + 1
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 4 — ORIGEN", W // 2 - 110, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige el origen de tu personaje.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones:
            btn.draw(surf, self.scroll.offset)
        if self.seleccion:
            draw_text(surf, ORIGENES[self.seleccion]["desc"], 80, 380 - self.scroll.offset, 12, C_SUBTITULO)
        if self.error:
            draw_text(surf, self.error, W // 2 - 160, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenNinez:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.trasfondo_ninez
        self.error = ""
        W = creator.app.screen.get_width()
        nombres = list(NINEZ.keys())
        cols, btn_w, btn_h = 3, 220, 52
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 16) // 2
        self.botones = []
        for i, key in enumerate(nombres):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 16)
            y = 240 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), key, font_size=14, selected=(key == self.seleccion))
            self.botones.append((b, key))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, key in self.botones:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = key
                for b2, _ in self.botones:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir un trasfondo de niñez."
            else:
                self.creator.personaje.trasfondo_ninez = self.seleccion
                hab = NINEZ[self.seleccion]["habilidad"]
                if hab:
                    actual = self.creator.personaje.habilidades.get(hab, 0)
                    if actual < 3:
                        self.creator.personaje.habilidades[hab] = actual + 1
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 5 — NIÑEZ", W // 2 - 100, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige en qué destacabas de niño.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones:
            btn.draw(surf, self.scroll.offset)
        if self.seleccion:
            draw_text(surf, NINEZ[self.seleccion]["desc"], 80, 380 - self.scroll.offset, 12, C_SUBTITULO)
        if self.error:
            draw_text(surf, self.error, W // 2 - 160, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenAdolescencia:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.trasfondo_adolescencia
        self.error = ""
        W = creator.app.screen.get_width()
        nombres = list(ADOLESCENCIA.keys())
        cols, btn_w, btn_h = 3, 260, 52
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 16) // 2
        self.botones = []
        for i, key in enumerate(nombres):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 16)
            y = 240 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), key, font_size=13, selected=(key == self.seleccion))
            self.botones.append((b, key))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, key in self.botones:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = key
                for b2, _ in self.botones:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir un trasfondo de adolescencia."
            else:
                self.creator.personaje.trasfondo_adolescencia = self.seleccion
                hab = ADOLESCENCIA[self.seleccion]["habilidad"]
                if hab:
                    actual = self.creator.personaje.habilidades.get(hab, 0)
                    if actual < 3:
                        self.creator.personaje.habilidades[hab] = actual + 1
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 6 — ADOLESCENCIA", W // 2 - 160, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige qué hiciste en tu adolescencia.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones:
            btn.draw(surf, self.scroll.offset)
        if self.seleccion:
            draw_text(surf, ADOLESCENCIA[self.seleccion]["desc"], 80, 380 - self.scroll.offset, 12, C_SUBTITULO)
        if self.error:
            draw_text(surf, self.error, W // 2 - 160, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenJuventud:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.trasfondo_juventud
        self.error = ""
        W = creator.app.screen.get_width()
        nombres = list(JUVENTUD.keys())
        cols, btn_w, btn_h = 4, 220, 52
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 14) // 2
        self.botones = []
        for i, key in enumerate(nombres):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 14)
            y = 240 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), key, font_size=13, selected=(key == self.seleccion))
            self.botones.append((b, key))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, key in self.botones:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = key
                for b2, _ in self.botones:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir un trasfondo de juventud."
            else:
                self.creator.personaje.trasfondo_juventud = self.seleccion
                hab = JUVENTUD[self.seleccion]["habilidad"]
                if hab:
                    actual = self.creator.personaje.habilidades.get(hab, 0)
                    if actual < 3:
                        self.creator.personaje.habilidades[hab] = actual + 1
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 7 — JUVENTUD", W // 2 - 130, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige qué hiciste en tu juventud.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones:
            btn.draw(surf, self.scroll.offset)
        if self.seleccion:
            draw_text(surf, JUVENTUD[self.seleccion]["desc"], 80, 380 - self.scroll.offset, 12, C_SUBTITULO)
        if self.error:
            draw_text(surf, self.error, W // 2 - 160, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenDebilidad:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.debilidad
        self.error = ""
        W = creator.app.screen.get_width()
        cols, cb_w = 3, 380
        start_x = W // 2 - (cols * cb_w) // 2
        self.checks = []
        for i, item in enumerate(DEBILIDADES):
            col, row = i % cols, i // cols
            x = start_x + col * cb_w
            y = 280 + row * 44
            cb = Checkbox(x, y, item, font_size=13, max_label_w=340, checked=(item == self.seleccion))
            self.checks.append(cb)
        num_filas = (len(DEBILIDADES) + cols - 1) // cols
        botones_y = 280 + num_filas * 44 + 60
        self.btn_atras = Button((W // 2 - 220, botones_y, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, botones_y, 180, 44), "Siguiente", color=C_BOTON_HOV)
        self.scroll.set_content_height(botones_y + 100, creator.app.screen.get_height() - 120)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for cb in self.checks:
            if cb.handle_event(event, self.scroll.offset):
                if cb.checked:
                    for other in self.checks:
                        if other != cb:
                            other.checked = False
                    self.seleccion = cb.text
                else:
                    self.seleccion = ""
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir una debilidad."
            else:
                self.creator.personaje.debilidad = self.seleccion
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for cb in self.checks:
            cb.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 8 — DEBILIDAD", W // 2 - 120, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige una debilidad.", 80, 250, 13, C_TEXTO_DIM, max_width=W - 160)
        for cb in self.checks:
            cb.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, 80, self.btn_atras.rect.y - 24 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)
        self.scroll.draw_scrollbar(surf, pygame.Rect(0, 120, W, surf.get_height() - 120))


class ScreenRecuerdos:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = set(creator.personaje.recuerdos)
        self.error = ""
        W = creator.app.screen.get_width()
        cols, cb_w = 3, 380
        start_x = W // 2 - (cols * cb_w) // 2
        self.checks = []
        for i, item in enumerate(RECUERDOS):
            col, row = i % cols, i // cols
            x = start_x + col * cb_w
            y = 280 + row * 44
            cb = Checkbox(x, y, item, font_size=13, max_label_w=340, checked=(item in self.seleccion))
            self.checks.append(cb)
        num_filas = (len(RECUERDOS) + cols - 1) // cols
        botones_y = 280 + num_filas * 44 + 60
        self.btn_atras = Button((W // 2 - 220, botones_y, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, botones_y, 180, 44), "Siguiente", color=C_BOTON_HOV)
        self.scroll.set_content_height(botones_y + 100, creator.app.screen.get_height() - 120)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for cb in self.checks:
            if cb.handle_event(event, self.scroll.offset):
                if cb.checked:
                    if len(self.seleccion) >= 2:
                        cb.checked = False
                    else:
                        self.seleccion.add(cb.text)
                else:
                    self.seleccion.discard(cb.text)
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if len(self.seleccion) != 2:
                self.error = f"Debes elegir exactamente 2 recuerdos. Tienes {len(self.seleccion)}."
            else:
                self.creator.personaje.recuerdos = list(self.seleccion)
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for cb in self.checks:
            cb.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 9 — RECUERDOS", W // 2 - 140, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, f"Elige DOS recuerdos. ({len(self.seleccion)}/2)", 80, 250, 13, C_TEXTO_DIM, max_width=W - 160)
        for cb in self.checks:
            cb.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, 80, self.btn_atras.rect.y - 24 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)
        self.scroll.draw_scrollbar(surf, pygame.Rect(0, 120, W, surf.get_height() - 120))


class ScreenAspecto:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = set(creator.personaje.aspecto)
        self.error = ""
        W = creator.app.screen.get_width()
        cols, cb_w = 3, 380
        start_x = W // 2 - (cols * cb_w) // 2
        self.checks = []
        for i, item in enumerate(DETALLES_ASPECTO):
            col, row = i % cols, i // cols
            x = start_x + col * cb_w
            y = 280 + row * 44
            cb = Checkbox(x, y, item, font_size=13, max_label_w=340, checked=(item in self.seleccion))
            self.checks.append(cb)
        num_filas = (len(DETALLES_ASPECTO) + cols - 1) // cols
        botones_y = 280 + num_filas * 44 + 60
        self.btn_atras = Button((W // 2 - 220, botones_y, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, botones_y, 180, 44), "Siguiente", color=C_BOTON_HOV)
        self.scroll.set_content_height(botones_y + 100, creator.app.screen.get_height() - 120)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for cb in self.checks:
            if cb.handle_event(event, self.scroll.offset):
                if cb.checked:
                    if len(self.seleccion) >= 2:
                        cb.checked = False
                    else:
                        self.seleccion.add(cb.text)
                else:
                    self.seleccion.discard(cb.text)
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if len(self.seleccion) != 2:
                self.error = f"Debes elegir exactamente 2 rasgos. Tienes {len(self.seleccion)}."
            else:
                self.creator.personaje.aspecto = list(self.seleccion)
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for cb in self.checks:
            cb.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 10 — ASPECTO", W // 2 - 120, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, f"Elige DOS rasgos f�sicos. ({len(self.seleccion)}/2)", 80, 250, 13, C_TEXTO_DIM, max_width=W - 160)
        for cb in self.checks:
            cb.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, 80, self.btn_atras.rect.y - 24 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)
        self.scroll.draw_scrollbar(surf, pygame.Rect(0, 120, W, surf.get_height() - 120))


class ScreenMotivacion:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.motivacion
        self.error = ""
        W = creator.app.screen.get_width()
        cols, btn_w, btn_h = 4, 180, 50
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 14) // 2
        self.botones = []
        for i, mot in enumerate(MOTIVACIONES):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 14)
            y = 240 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), mot, font_size=14, selected=(mot == self.seleccion))
            self.botones.append((b, mot))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, mot in self.botones:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = mot
                for b2, _ in self.botones:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir una motivación."
            else:
                self.creator.personaje.motivacion = self.seleccion
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 11 — MOTIVACIÓN", W // 2 - 140, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige la motivación de tu personaje.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones:
            btn.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, W // 2 - 160, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenVicio:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        self.seleccion = creator.personaje.vicio
        self.error = ""
        W = creator.app.screen.get_width()
        cols, btn_w, btn_h = 3, 200, 50
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 14) // 2
        self.botones = []
        for i, v in enumerate(VICIOS):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 14)
            y = 240 + row * (btn_h + 12)
            b = Button((x, y, btn_w, btn_h), v, font_size=14, selected=(v == self.seleccion))
            self.botones.append((b, v))
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, v in self.botones:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = v
                for b2, _ in self.botones:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            if not self.seleccion:
                self.error = "Debes elegir un vicio."
            else:
                self.creator.personaje.vicio = self.seleccion
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 12 — VICIO", W // 2 - 100, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "Elige el vicio de tu personaje.", 80, 200, 13, C_TEXTO_DIM, max_width=W - 160)
        for btn, _ in self.botones:
            btn.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, W // 2 - 160, 730 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenNombre:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        W = creator.app.screen.get_width()
        self.input = TextInput((W // 2 - 280, 260, 560, 56), font_size=22, prompt="", center=True)
        self.input.text = creator.personaje.nombre
        self.input.active = True
        self.error = ""
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        self.input.handle_event(event, self.scroll.offset)
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            nombre = self.input.text.strip()
            if not nombre:
                self.error = "El nombre no puede estar vacío."
            else:
                self.creator.personaje.nombre = nombre
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)
        self.input.update(dt)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 13 — NOMBRE", W // 2 - 120, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        draw_text(surf, "¿Cómo se llama tu personaje?", W // 2 - text_size("¿Cómo se llama tu personaje?", 18, bold=True)[0] // 2, 220, 18, C_SUBTITULO, bold=True)
        self.input.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, W // 2 - 200, 340 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenApodo:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        prof = creator.personaje.profesion
        self.apodos = PROFESIONES[prof]["apodos"] if prof in PROFESIONES else []
        self.seleccion = creator.personaje.apodo
        self.error = ""
        W = creator.app.screen.get_width()
        cols, btn_w, btn_h = 3, 200, 46
        start_x = W // 2 - (cols * btn_w + (cols - 1) * 14) // 2
        self.botones_ap = []
        for i, ap in enumerate(self.apodos):
            col, row = i % cols, i // cols
            x = start_x + col * (btn_w + 14)
            y = 210 + row * (btn_h + 10)
            b = Button((x, y, btn_w, btn_h), ap, font_size=13, selected=(ap == self.seleccion))
            self.botones_ap.append((b, ap))
        self.input_custom = TextInput((W // 2 - 200, 400, 400, 44), font_size=16, prompt="", center=True)
        if self.seleccion and self.seleccion not in self.apodos:
            self.input_custom.text = self.seleccion
        self.btn_atras = Button((W // 2 - 220, 750, 180, 44), "Atrás")
        self.btn_siguiente = Button((W // 2 + 40, 750, 180, 44), "Siguiente", color=C_BOTON_HOV)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        for btn, ap in self.botones_ap:
            if btn.handle_event(event, self.scroll.offset):
                self.seleccion = ap
                self.input_custom.text = ""
                for b2, _ in self.botones_ap:
                    b2.selected = False
                btn.selected = True
                self.error = ""
        self.input_custom.handle_event(event, self.scroll.offset)
        if self.input_custom.text:
            for b2, _ in self.botones_ap:
                b2.selected = False
        if self.btn_atras.handle_event(event, self.scroll.offset):
            self.creator.go_back()
        if self.btn_siguiente.handle_event(event, self.scroll.offset):
            apodo_final = self.input_custom.text.strip() or self.seleccion
            if not apodo_final:
                self.error = "Debes elegir o escribir un apodo."
            else:
                self.creator.personaje.apodo = apodo_final
                self.creator.go_next()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn, _ in self.botones_ap:
            btn.update_hover(mp, self.scroll.offset)
        self.btn_atras.update_hover(mp, self.scroll.offset)
        self.btn_siguiente.update_hover(mp, self.scroll.offset)
        self.input_custom.update(dt)

    def draw(self, surf):
        W = surf.get_width()
        draw_text(surf, "PASO 14 — APODO", W // 2 - 110, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)
        for btn, _ in self.botones_ap:
            btn.draw(surf, self.scroll.offset)
        draw_text(surf, "O escribe tu propio apodo:", W // 2 - text_size("O escribe tu propio apodo:", 13)[0] // 2, 380, 13, C_TEXTO_DIM)
        self.input_custom.draw(surf, self.scroll.offset)
        if self.error:
            draw_text(surf, self.error, W // 2 - 180, 405 - self.scroll.offset, 13, C_ERROR)
        self.btn_atras.draw(surf, self.scroll.offset)
        self.btn_siguiente.draw(surf, self.scroll.offset)


class ScreenFichaFinal:
    def __init__(self, creator):
        self.creator = creator
        self.scroll = ScrollArea()
        p = creator.personaje
        W = creator.app.screen.get_width()
        self.btn_guardar = Button((W // 2 - 280, 0, 220, 48), "Guardar personaje", font_size=15, bold=True, color=(50, 100, 50))
        self.btn_cancelar = Button((W // 2 + 60, 0, 220, 48), "Cancelar", font_size=15, bold=True, color=C_ERROR)
        self._build_content_height()

    def _build_content_height(self):
        h = 800
        self.scroll.set_content_height(h, self.creator.app.screen.get_height() - 120)

    def handle_event(self, event):
        self.scroll.handle_event(event)
        if self.btn_guardar.handle_event(event, self.scroll.offset):
            self.creator._guardar_y_volver()
        if self.btn_cancelar.handle_event(event, self.scroll.offset):
            from screens.screen_partidas import ScreenPartidasManager
            from screens.screen_personajes import ScreenPersonajesManager
            app = self.creator.app
            if hasattr(app, '_party_state') and app._party_state is not None:
                app.current_screen = ScreenPartidasManager(app)
            else:
                app.current_screen = ScreenPersonajesManager(app)

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.btn_guardar.update_hover(mp, self.scroll.offset)
        self.btn_cancelar.update_hover(mp, self.scroll.offset)

    def draw(self, surf):
        W = surf.get_width()
        off = self.scroll.offset
        p = self.creator.personaje

        draw_text(surf, "FICHA DE PERSONAJE", W // 2 - 150, 160, 26, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (80, 196), (W - 80, 196), 2)

        y = 210
        draw_text(surf, f"{p.nombre} '{p.apodo}'", 80, y - off, 20, C_TITULO, bold=True)
        y += 28
        draw_text(surf, f"{p.raza}  ·  {p.profesion}  ·  {p.edad}", 80, y - off, 14, C_SUBTITULO)
        y += 24

        atrib_txt = f"CUE:{p.atributos['CUE']}  INT:{p.atributos['INT']}  VOL:{p.atributos['VOL']}"
        draw_text(surf, f"Atributos: {atrib_txt}", 80, y - off, 13, C_TEXTO)
        y += 22

        habs_con_valor = {h: v for h, v in p.habilidades.items() if v > 0}
        if habs_con_valor:
            draw_text(surf, "Habilidades:", 80, y - off, 13, C_TITULO, bold=True)
            y += 18
            for hab, val in sorted(habs_con_valor.items()):
                draw_text(surf, f"  {hab}: {val}", 100, y - off, 12, C_TEXTO)
                y += 16

        draw_text(surf, f"Estrés: {p.estres}/10  ·  Corrupción: {p.corrupcion}/10  ·  Nivel: {p.nivel}", 80, y - off, 13, C_TEXTO)
        y += 22
        draw_text(surf, f"Heridas: Leves {p.heridas_leves}/3  Graves {p.heridas_graves}/2  Muy Graves {p.heridas_muy_graves}/1", 80, y - off, 13, C_TEXTO)
        y += 22

        draw_text(surf, f"Debilidad: {p.debilidad}", 80, y - off, 13, C_TEXTO_DIM)
        y += 18
        draw_text(surf, f"Motivación: {p.motivacion}  ·  Vicio: {p.vicio}", 80, y - off, 13, C_TEXTO_DIM)
        y += 18

        if p.recuerdos:
            draw_text(surf, "Recuerdos: " + ", ".join(p.recuerdos), 80, y - off, 12, C_TEXTO_DIM, max_width=W - 160)
            y += 16
        if p.aspecto:
            draw_text(surf, "Aspecto: " + ", ".join(p.aspecto), 80, y - off, 12, C_TEXTO_DIM, max_width=W - 160)
            y += 16

        for label, val in [("Origen", p.trasfondo_origen), ("Niñez", p.trasfondo_ninez),
                           ("Adolescencia", p.trasfondo_adolescencia), ("Juventud", p.trasfondo_juventud)]:
            if val:
                draw_text(surf, f"{label}: {val}", 80, y - off, 12, C_TEXTO_DIM)
                y += 16

        nav_y = y + 20
        self.btn_guardar.rect.y = nav_y
        self.btn_cancelar.rect.y = nav_y
        self.btn_guardar.draw(surf, off)
        self.btn_cancelar.draw(surf, off)

        self.scroll.set_content_height(nav_y + 80, self.creator.app.screen.get_height() - 120)
        self.scroll.draw_scrollbar(surf, pygame.Rect(0, 120, W, surf.get_height() - 120))

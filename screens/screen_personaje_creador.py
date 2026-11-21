# screens/screen_personaje_creador.py
# Creador de personajes según el reglamento FORGED IN THE DARK FANTASY (capítulo 1)
#
# Todas las elecciones se guardan en el diccionario self.datos. Las habilidades
# NO se suman paso a paso: se recalculan desde cero con reglas.calcular_habilidades,
# así el botón "Atrás" nunca duplica puntos.

import os
import pygame
from constants import *
from ui_utils import draw_text
import reglas
from reglas import (RAZAS, CLASES, TIPOS_MAGIA, TODAS_LAS_HABILIDADES, HABILIDADES_POR_ATRIBUTO,
                    NOMBRE_ATRIBUTO, ETAPAS_TRASFONDO)
from formularios import (Formulario, Titulo, Info, Opciones, Multi, Check, Texto, Sugerencias,
                         Fila, Separador, Espacio, boton, texto_ajustado)
from models import Personaje
import persistence


def _hab_label(h, habs):
    v = habs.get(h, 0)
    return f"{h} ({v})" if v else h


def lista_retratos():
    if not os.path.isdir(RETRATOS_DIR):
        return []
    return sorted(f for f in os.listdir(RETRATOS_DIR)
                  if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")))


# ══════════════════════════════════════════════════════════════════════════════
# PASOS
# ══════════════════════════════════════════════════════════════════════════════

class Paso:
    def __init__(self, titulo, builder, validar=None, visible=None, al_entrar=None):
        self.titulo = titulo
        self.builder = builder
        self.validar = validar or (lambda d: None)
        self.visible = visible or (lambda d: True)
        self.al_entrar = al_entrar


# ── 1. Raza ───────────────────────────────────────────────────────────────────
def _raza_elegida(d, v):
    if v != "Humano":
        d["bono_raza"] = []
    if not reglas.puede_usar_arcana(v) and d.get("tipo_magia") == "arcana":
        d["tipo_magia"], d["subclase"] = "", ""


def b_raza(d):
    c = [Info("Elige la raza de tu personaje."),
         Opciones("raza", "", list(RAZAS), cols=5, alto_boton=44, size=15, al_elegir=_raza_elegida)]
    if d.get("raza"):
        c.append(Info(RAZAS[d["raza"]]["desc"], 13, C_SUBTITULO))
    if d.get("raza") == "Humano":
        habs = reglas.calcular_habilidades({**d, "bono_raza": []})
        c += [Separador(),
              Multi("bono_raza", "Bono humano: elige DOS habilidades distintas (+1 cada una)",
                    [(h, _hab_label(h, habs)) for h in TODAS_LAS_HABILIDADES], maximo=2, cols=4)]
    return c


def v_raza(d):
    if not d.get("raza"):
        return "Debes elegir una raza."
    if d["raza"] == "Humano" and len(d.get("bono_raza") or []) != 2:
        return "Un humano debe elegir dos habilidades distintas."
    if "sobrenatural" in (d.get("bono_raza") or []) and d.get("clase") != "Extraño":
        pass  # se comprueba con el permiso del DJ en el paso de trasfondo
    return None


# ── 2. Clase ──────────────────────────────────────────────────────────────────
def _clase_elegida(d, v):
    d["eleccion_clase"] = ""
    if v != "Extraño":
        d["tipo_magia"], d["subclase"], d["habilidad_divina"] = "", "", ""


def _tipo_elegido(d, v):
    subs = TIPOS_MAGIA[v]["subclases"]
    d["subclase"] = subs[0] if len(subs) == 1 else ""
    d["habilidad_divina"] = "influir" if v == "divina" else ""


def b_clase(d):
    c = [Info("Elige la clase de tu personaje."),
         Opciones("clase", "", list(CLASES), cols=3, alto_boton=42, size=15, al_elegir=_clase_elegida)]
    clase = d.get("clase")
    if not clase:
        return c
    info = CLASES[clase]
    c.append(Info(f"Arquetipo: {info['arquetipo']}. {info['desc']}", 13, C_SUBTITULO))
    if info["elegir"]:
        c += [Separador(), Opciones("eleccion_clase", "Elige tu segundo punto"
                                    + (" (será tu habilidad de clase)" if not info["clase"] else ""),
                                    info["elegir"], cols=2)]
    if clase == "Extraño":
        arcana_ok = reglas.puede_usar_arcana(d.get("raza", ""))
        c += [Separador(),
              Opciones("tipo_magia", "Tipo de poder sobrenatural",
                       [(k, v["nombre"]) for k, v in TIPOS_MAGIA.items()], cols=3,
                       deshabilitadas=() if arcana_ok else ("arcana",), al_elegir=_tipo_elegido)]
        if not arcana_ok:
            c.append(Info("Los enanos y los halflings no pueden usar magia arcana.", 12, C_TEXTO_DIM))
        tipo = d.get("tipo_magia")
        if tipo:
            seg = TIPOS_MAGIA[tipo]["segunda"]
            c.append(Info(f"Un punto en sobrenatural y otro en {seg}. "
                          "En mecánica no hay diferencias entre subclases: es algo narrativo.", 12))
            c.append(Opciones("subclase", "Subclase", TIPOS_MAGIA[tipo]["subclases"], cols=3))
            if tipo == "divina":
                c += [Texto("deidad", "Deidad o credo", "Nombre de tu dios o credo"),
                      Opciones("habilidad_divina", "Tu dios otorga un punto en (por defecto influir):",
                               [h for h in TODAS_LAS_HABILIDADES if h != "sobrenatural"], cols=6,
                               alto_boton=28, size=11)]
    return c


def v_clase(d):
    clase = d.get("clase")
    if not clase:
        return "Debes elegir una clase."
    if CLASES[clase]["elegir"] and not d.get("eleccion_clase"):
        return "Elige tu segundo punto de clase."
    if clase == "Extraño":
        if not d.get("tipo_magia"):
            return "Elige el tipo de poder sobrenatural."
        if d["tipo_magia"] == "arcana" and not reglas.puede_usar_arcana(d.get("raza", "")):
            return "Tu raza no puede usar magia arcana."
        if not d.get("subclase"):
            return "Elige la subclase."
    e = reglas.errores_creacion(d)
    return e[0] if e else None


# ── 3. Edad ───────────────────────────────────────────────────────────────────
def b_edad(d):
    c = [Texto("edad", "Edad en años", "Ej.: 25", max_len=4, solo_numeros=True)]
    if d.get("raza") == "Humano":
        try:
            et = reglas.etapa_humana(int(d.get("edad") or 0))
            d["etapa"] = et
            c.append(Info(f"Etapa: {et.upper()}  (humano: joven 18-30, adulto 31-60, anciano 61+)",
                          14, C_SUBTITULO, True))
        except ValueError:
            pass
    else:
        c += [Info("Para razas no humanas, joven, adulto o anciano se decide según la edad media de "
                   "esa raza comparada con la humana. Elige la etapa:", 12, C_TEXTO_DIM),
              Opciones("etapa", "Etapa de la vida", reglas.ETAPAS_EDAD, cols=3)]
    if d.get("etapa"):
        c.append(Info(reglas.DESC_ETAPA[d["etapa"]], 13))
    return c


def v_edad(d):
    if not str(d.get("edad") or "").strip():
        return "Indica la edad."
    if d.get("raza") == "Humano" and int(d["edad"]) < 18:
        return "Las reglas no contemplan personajes menores de 18 años."
    if not d.get("etapa"):
        return "Elige la etapa de la vida."
    e = reglas.errores_creacion(d)
    return e[0] if e else None


# ── 4-7. Trasfondo ────────────────────────────────────────────────────────────
def hacer_paso_trasfondo(idx):
    clave, nombre, ejemplos = ETAPAS_TRASFONDO[idx]
    k_txt, k_hab = f"tf_{clave}_txt", f"tf_{clave}_hab"

    def b(d):
        otros = {d.get(f"tf_{c}_hab") for c, _, _ in ETAPAS_TRASFONDO if c != clave} - {None, ""}
        habs = reglas.calcular_habilidades({**d, k_hab: ""})
        c = [Info(f"Trasfondo ({idx + 1}/4). Cuenta esta etapa de la vida de tu personaje y elige la "
                  "habilidad que ganó (+1). Las cuatro etapas deben dar habilidades distintas.", 12, C_TEXTO_DIM),
             Info("Ejemplos: " + ejemplos, 12, C_SUBTITULO),
             Texto(k_txt, f"{nombre}: ¿qué pasó?", "Escribe una frase breve...", max_len=200),
             Opciones(k_hab, "Habilidad ganada", [(h, _hab_label(h, habs)) for h in TODAS_LAS_HABILIDADES],
                      cols=4, deshabilitadas=otros, alto_boton=30, size=12)]
        if d.get(k_hab):
            c.append(Info(reglas.DESCRIPCION_HABILIDAD[d[k_hab]], 12, C_TEXTO_DIM))
        if d.get(k_hab) == "sobrenatural" and d.get("clase") != "Extraño":
            c.append(Check("permiso_dj_sobrenatural",
                           "El DJ permite a este personaje (no extraño) tener un punto en sobrenatural. "
                           "Tendrá un talento: un conjuro, oración o poder de nivel 0-1."))
        return c

    def v(d):
        if not d.get(k_hab):
            return "Elige la habilidad que ganó tu personaje en esta etapa."
        if d.get(k_hab) == "sobrenatural" and d.get("clase") != "Extraño" and not d.get("permiso_dj_sobrenatural"):
            return "Sobrenatural en un personaje no extraño necesita el permiso del DJ."
        e = reglas.errores_creacion(d)
        return e[0] if e else None

    return Paso(f"TRASFONDO — {nombre}", b, v)


# ── 8. Motivación y vicio ─────────────────────────────────────────────────────
def b_motivacion(d):
    return [Opciones("motivacion", "Motivación", reglas.MOTIVACIONES, cols=4),
            Info("Cuenta para rolear, y esforzarte solo cuesta 1 de estrés si puedes relacionarlo "
                 "con tu motivación.", 12, C_TEXTO_DIM),
            Separador(),
            Opciones("vicio", "Obsesión o vicio", reglas.VICIOS, cols=3),
            Info("Cuenta para rolear y sirve para quitarse estrés en la fase de descanso.", 12, C_TEXTO_DIM),
            Texto("vicio_detalle", "Detalle (opcional)", "Ej.: vino de las tierras del sur, dados...")]


def v_motivacion(d):
    if not d.get("motivacion"):
        return "Elige una motivación."
    if not d.get("vicio"):
        return "Elige una obsesión o vicio."
    return None


# ── 9. Apariencia ─────────────────────────────────────────────────────────────
def b_apariencia(d):
    return [Fila([Texto("cabello", "Color del cabello", "Ej.: negro"),
                  Texto("ojos", "Color de los ojos", "Ej.: grises")]),
            Multi("rasgos", "Al menos otros dos rasgos físicos", reglas.RASGOS_APARIENCIA, cols=4),
            Texto("rasgo_extra", "Otro rasgo propio (opcional)", "Ej.: una oreja mordida")]


def _rasgos(d):
    r = list(d.get("rasgos") or [])
    if str(d.get("rasgo_extra") or "").strip():
        r.append(d["rasgo_extra"].strip())
    return r


def v_apariencia(d):
    if not str(d.get("cabello") or "").strip() or not str(d.get("ojos") or "").strip():
        return "Indica el color del cabello y de los ojos."
    if len(_rasgos(d)) < 2:
        return "Elige al menos dos rasgos físicos."
    return None


# ── 10. Personalidad ──────────────────────────────────────────────────────────
def b_personalidad(d):
    return [Info("Estos rasgos no tienen consecuencias mecánicas sino narrativas: tenlos en cuenta "
                 "para interpretar al personaje.", 12, C_TEXTO_DIM),
            Multi("personalidad", "Al menos dos rasgos de personalidad", reglas.RASGOS_PERSONALIDAD, cols=4),
            Texto("personalidad_extra", "Otro rasgo propio (opcional)", "Ej.: supersticioso")]


def _personalidad(d):
    r = list(d.get("personalidad") or [])
    if str(d.get("personalidad_extra") or "").strip():
        r.append(d["personalidad_extra"].strip())
    return r


def v_personalidad(d):
    return None if len(_personalidad(d)) >= 2 else "Elige al menos dos rasgos de personalidad."


# ── 11. Recuerdos, amigos y enemigos ──────────────────────────────────────────
def b_recuerdos(d):
    return [Info("Dos pequeños objetos de su pasado, de valor sentimental.", 12, C_TEXTO_DIM),
            Fila([Texto("recuerdo1", "Recuerdo 1", "Ej.: un medallón"),
                  Texto("recuerdo2", "Recuerdo 2", "Ej.: un silbato")]),
            Sugerencias("Sugerencias (pulsa para usar):", reglas.RECUERDOS_SUGERIDOS, ["recuerdo1", "recuerdo2"], cols=4),
            Separador(),
            Info("Dos amigos y dos enemigos, intentando relacionarlos con el trasfondo.", 12, C_TEXTO_DIM),
            Fila([Texto("amigo1", "Amigo 1", "Nombre y quién es"), Texto("amigo2", "Amigo 2", "")]),
            Fila([Texto("enemigo1", "Enemigo 1", "Nombre y por qué"), Texto("enemigo2", "Enemigo 2", "")]),
            Texto("lazos", "Lazos con otros personajes del grupo (opcional)", "Ej.: hermano de armas de...")]


def v_recuerdos(d):
    for k, n in [("recuerdo1", "dos recuerdos"), ("recuerdo2", "dos recuerdos"), ("amigo1", "dos amigos"),
                 ("amigo2", "dos amigos"), ("enemigo1", "dos enemigos"), ("enemigo2", "dos enemigos")]:
        if not str(d.get(k) or "").strip():
            return f"Debes indicar {n}."
    return None


# ── 12. Talentos ──────────────────────────────────────────────────────────────
def _n_talentos(d):
    return reglas.talentos_iniciales(d)


def b_talentos(d):
    n = _n_talentos(d)
    c = []
    if d.get("clase") != "Extraño":
        arcana_ok = reglas.puede_usar_arcana(d.get("raza", ""))
        c += [Info("Tu personaje tiene un punto en sobrenatural: ¿de qué tipo es su poder?", 13),
              Opciones("tipo_magia", "", [(k, v["nombre"]) for k, v in TIPOS_MAGIA.items()], cols=3,
                       deshabilitadas=() if arcana_ok else ("arcana",))]
    tipo = d.get("tipo_magia") or "arcana"
    nombre = TIPOS_MAGIA[tipo]["talentos"]
    c.append(Info(f"Empieza con {n} talento(s): {nombre}. Propón al DJ efectos parecidos a los de nivel "
                  "0 o 1 de otros juegos (causar una herida leve, curar una herida leve, crear una luz, "
                  "abrir cerraduras...). Se usan con una tirada de sobrenatural.", 12, C_TEXTO_DIM))
    ejemplos = ["Curar herida leve", "Globo de luz", "Causar herida leve"]
    for i in range(n):
        c.append(Texto(f"talento{i + 1}", f"Talento {i + 1}", f"Ej.: {ejemplos[i % 3]}", max_len=80))
    return c


def v_talentos(d):
    if d.get("clase") != "Extraño" and not d.get("tipo_magia"):
        return "Elige el tipo de poder sobrenatural."
    for i in range(_n_talentos(d)):
        if not str(d.get(f"talento{i + 1}") or "").strip():
            return "Escribe todos los talentos iniciales."
    return None


# ── 13. Otros datos ───────────────────────────────────────────────────────────
def _entrar_otros(d):
    if "sabe_leer" not in d:
        d["sabe_leer"] = d.get("clase") in ("Comerciante", "Bardo") or d.get("tipo_magia") == "arcana"
    if d.get("tipo_magia") == "arcana" and d.get("clase") == "Extraño":
        d["sabe_leer"] = True


def b_otros(d):
    forzado = d.get("tipo_magia") == "arcana" and d.get("clase") == "Extraño"
    c = [Check("sabe_leer", "Sabe leer y escribir" + (" (los magos siempre saben)" if forzado else
               " (comerciantes y bardos de ciudad casi siempre; para el resto decide el DJ)"),
               deshabilitado=forzado),
         Texto("equipo", "Equipo inicial (lo decide el DJ)", "Ej.: espada, escudo, cuerda, vendas", max_len=200),
         Opciones("armadura", "Casillas de protección por armadura (2.2)",
                  [(0, "Ninguna"), (1, "1 (armadura)"), (2, "2 (armadura pesada)")], cols=3)]
    retratos = lista_retratos()
    if retratos:
        c.append(Opciones("retrato", "Retrato (assets/images/retratos)", [("", "Sin retrato")] + retratos,
                          cols=3, alto_boton=28, size=11))
    else:
        c.append(Info("Consejo: si pones imágenes en assets/images/retratos podrás elegir un retrato "
                      "para el personaje.", 11, C_TEXTO_DIM))
    return c


# ── 14. Nombre ────────────────────────────────────────────────────────────────
def b_nombre(d):
    apodos = CLASES.get(d.get("clase"), {}).get("apodos", [])
    return [Texto("nombre", "Nombre", "Nombre del personaje", max_len=40),
            Texto("apodo", "Apodo", "Cómo le llaman", max_len=40),
            Sugerencias("Apodos sugeridos:", apodos, ["apodo"], cols=3)]


def v_nombre(d):
    return None if str(d.get("nombre") or "").strip() else "El personaje necesita un nombre."


# ── 15. Resumen ───────────────────────────────────────────────────────────────
def b_resumen(d):
    p = construir_personaje(d)
    from screens.screen_ficha_personaje import lineas_ficha
    c = [Info("Revisa la ficha. Pulsa GUARDAR para terminar.", 13, C_SUBTITULO, True)]
    for titulo, texto in lineas_ficha(p):
        if titulo:
            c.append(Titulo(titulo, 14))
        if texto:
            c.append(Info(texto, 12))
    return c


PASOS = [
    Paso("RAZA", b_raza, v_raza),
    Paso("CLASE", b_clase, v_clase),
    Paso("EDAD", b_edad, v_edad),
    hacer_paso_trasfondo(0), hacer_paso_trasfondo(1), hacer_paso_trasfondo(2), hacer_paso_trasfondo(3),
    Paso("MOTIVACIÓN Y VICIO", b_motivacion, v_motivacion),
    Paso("APARIENCIA FÍSICA", b_apariencia, v_apariencia),
    Paso("PERSONALIDAD", b_personalidad, v_personalidad),
    Paso("RECUERDOS, AMIGOS Y ENEMIGOS", b_recuerdos, v_recuerdos),
    Paso("TALENTOS INICIALES", b_talentos, v_talentos, visible=lambda d: _n_talentos(d) > 0),
    Paso("OTROS DATOS", b_otros, al_entrar=_entrar_otros),
    Paso("NOMBRE Y APODO", b_nombre, v_nombre),
    Paso("RESUMEN", b_resumen),
]


def construir_personaje(d) -> Personaje:
    habs = reglas.calcular_habilidades(d)
    tipo = d.get("tipo_magia", "") if (d.get("clase") == "Extraño" or habs["sobrenatural"]) else ""
    vicio = d.get("vicio", "")
    if str(d.get("vicio_detalle") or "").strip():
        vicio = f"{vicio} ({d['vicio_detalle'].strip()})"
    p = Personaje(
        nombre=str(d.get("nombre") or "").strip(), apodo=str(d.get("apodo") or "").strip(),
        raza=d.get("raza", ""), clase=d.get("clase", ""), eleccion_clase=d.get("eleccion_clase", ""),
        tipo_magia=tipo, subclase=d.get("subclase", "") if d.get("clase") == "Extraño" else "",
        deidad=str(d.get("deidad") or "").strip(),
        edad=str(d.get("edad") or ""), etapa=d.get("etapa", ""),
        motivacion=d.get("motivacion", ""), vicio=vicio,
        trasfondo={c: {"texto": str(d.get(f"tf_{c}_txt") or "").strip(), "habilidad": d.get(f"tf_{c}_hab", "")}
                   for c, _, _ in ETAPAS_TRASFONDO},
        bono_raza=list(d.get("bono_raza") or []),
        cabello=str(d.get("cabello") or "").strip(), ojos=str(d.get("ojos") or "").strip(),
        rasgos_apariencia=_rasgos(d), personalidad=_personalidad(d),
        recuerdos=[str(d.get(k) or "").strip() for k in ("recuerdo1", "recuerdo2") if str(d.get(k) or "").strip()],
        amigos=[str(d.get(k) or "").strip() for k in ("amigo1", "amigo2") if str(d.get(k) or "").strip()],
        enemigos=[str(d.get(k) or "").strip() for k in ("enemigo1", "enemigo2") if str(d.get(k) or "").strip()],
        lazos=str(d.get("lazos") or "").strip(),
        sabe_leer=bool(d.get("sabe_leer")), equipo=str(d.get("equipo") or "").strip(),
        retrato=d.get("retrato") or "", armadura=int(d.get("armadura") or 0),
        habilidades=habs,
    )
    p.talentos = [{"nombre": str(d.get(f"talento{i + 1}") or "").strip(), "descripcion": ""}
                  for i in range(reglas.talentos_iniciales(d, habs))
                  if str(d.get(f"talento{i + 1}") or "").strip()]
    return p


# ══════════════════════════════════════════════════════════════════════════════
# PANTALLA
# ══════════════════════════════════════════════════════════════════════════════

class ScreenPersonajeCreador:
    def __init__(self, app):
        self.app = app
        self.datos = {"armadura": 0}
        self.i = 0
        self.error = ""
        self.closed = False
        self._crear_form()

    # ── navegación ────────────────────────────────────────────────────────
    def _visibles(self):
        return [p for p in PASOS if p.visible(self.datos)]

    def _paso(self):
        return PASOS[self.i]

    def _crear_form(self):
        W, H = self.app.screen.get_size()
        paso = self._paso()
        if paso.al_entrar:
            paso.al_entrar(self.datos)
        self.form = Formulario(paso.builder, self.datos, (60, 200, max(500, W - 520), H - 200 - 90))
        self.error = ""

    def _siguiente(self):
        e = self._paso().validar(self.datos)
        if e:
            self.error = e
            return
        j = self.i + 1
        while j < len(PASOS) and not PASOS[j].visible(self.datos):
            j += 1
        if j >= len(PASOS):
            self._guardar()
            return
        self.i = j
        self._crear_form()

    def _atras(self):
        j = self.i - 1
        while j >= 0 and not PASOS[j].visible(self.datos):
            j -= 1
        if j < 0:
            self._salir()
            return
        self.i = j
        self._crear_form()

    def _salir(self):
        from screens.screen_partidas import ScreenPartidasManager
        from screens.screen_personajes import ScreenPersonajesManager
        if getattr(self.app, "_party_state", None) is not None:
            self.app.current_screen = ScreenPartidasManager(self.app)
        else:
            self.app.current_screen = ScreenPersonajesManager(self.app)

    def _guardar(self):
        p = construir_personaje(self.datos)
        errores = reglas.errores_creacion(self.datos)
        if errores:
            self.error = errores[0]
            return
        try:
            persistence.guardar_personaje(p)
        except Exception as e:
            self.error = f"Error al guardar: {e}"
            return
        state = getattr(self.app, "_party_state", None)
        if state is not None:
            state.setdefault("seleccionados_ids", []).append(p.id)
        self._salir()

    # ── bucle ─────────────────────────────────────────────────────────────
    def _rect_botones(self):
        W, H = self.app.screen.get_size()
        return (pygame.Rect(60, H - 70, 170, 44), pygame.Rect(250, H - 70, 200, 44),
                pygame.Rect(W - 230, 20, 190, 40))

    def handle_event(self, event):
        atras, sig, cancelar = self._rect_botones()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if atras.collidepoint(event.pos):
                self._atras()
                return
            if sig.collidepoint(event.pos):
                self._siguiente()
                return
            if cancelar.collidepoint(event.pos):
                self._salir()
                return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._siguiente()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._atras()
            return
        if self.form.evento(event):
            self.error = ""

    def update(self, dt):
        pass

    def draw(self, surf):
        W, H = surf.get_size()
        surf.fill(C_FONDO)
        draw_text(surf, TITLE, 60, 24, 34, C_TITULO, bold=True)
        draw_text(surf, "CREACIÓN DE PERSONAJE", 62, 68, 16, C_SUBTITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (40, 100), (W - 40, 100), 2)
        vis = self._visibles()
        paso = self._paso()
        n = vis.index(paso) + 1 if paso in vis else self.i + 1
        draw_text(surf, f"PASO {n}/{len(vis)} — {paso.titulo}", 60, 120, 24, C_TITULO, bold=True)
        pygame.draw.line(surf, C_BORDE, (60, 160), (W - 480, 160), 1)
        # progreso
        for k in range(len(vis)):
            col = C_TITULO if k < n else C_SEPARADOR
            pygame.draw.rect(surf, col, (60 + k * 28, 172, 22, 8), border_radius=3)

        self.form.dibujar(surf)
        self._panel(surf, pygame.Rect(W - 440, 120, 400, H - 210))

        atras, sig, cancelar = self._rect_botones()
        boton(surf, atras, "◄ Atrás", 15)
        boton(surf, sig, "GUARDAR" if paso is PASOS[-1] else "Siguiente ►", 15, color=C_BOTON_HOV)
        boton(surf, cancelar, "Cancelar", 13, color=C_ERROR)
        if self.error:
            texto_ajustado(surf, self.error, 470, H - 66, 14, C_ERROR, W - 940)

    def _panel(self, surf, r):
        d = self.datos
        pygame.draw.rect(surf, C_PANEL, r, border_radius=8)
        pygame.draw.rect(surf, C_BORDE, r, 2, border_radius=8)
        x, y = r.x + 16, r.y + 12
        draw_text(surf, "TU PERSONAJE", x, y, 15, C_TITULO, bold=True)
        y += 26
        clase = d.get("clase", "")
        if clase == "Extraño" and d.get("subclase"):
            clase = f"Extraño ({d['subclase']})"
        for etq, val in [("Raza", d.get("raza")), ("Clase", clase), ("Edad",
                         f"{d.get('edad', '')} {('(' + d['etapa'] + ')') if d.get('etapa') else ''}".strip())]:
            draw_text(surf, f"{etq}: {val or '—'}", x, y, 13, C_TEXTO)
            y += 19
        y += 6
        habs = reglas.calcular_habilidades(d)
        hc = reglas.habilidad_de_clase(d)
        for atr in reglas.ATRIBUTOS:
            draw_text(surf, NOMBRE_ATRIBUTO[atr].upper(), x, y, 13, C_SUBTITULO, bold=True)
            y += 18
            for h in HABILIDADES_POR_ATRIBUTO[atr]:
                v = habs[h]
                col = C_TEXTO if v else C_TEXTO_DIM
                draw_text(surf, ("♦ " if h == hc else "  ") + h, x + 4, y, 13, C_TITULO if h == hc else col)
                for k in range(4):
                    cx = r.right - 110 + k * 22
                    if k < v:
                        pygame.draw.circle(surf, C_TITULO, (cx, y + 8), 7)
                    else:
                        pygame.draw.circle(surf, C_SEPARADOR, (cx, y + 8), 7, 2)
                y += 19
            y += 4
        nt = reglas.talentos_iniciales(d, habs)
        draw_text(surf, f"Talentos iniciales: {nt}   PG: 10   Estrés: 0", x, y, 12, C_TEXTO_DIM)
        y += 20
        errores = reglas.errores_creacion(d, habs)
        for e in errores[:4]:
            y += texto_ajustado(surf, "! " + e, x, y, 12, C_ERROR, r.w - 32)
        if hc:
            draw_text(surf, "♦ = habilidad de clase", x, r.bottom - 24, 11, C_TEXTO_DIM)

# reglas.py - Motor de reglas de FORGED IN THE DARK FANTASY
#
# Aquí está TODO el reglamento que se puede mecanizar: razas, clases, límites
# de creación, tiradas de habilidad, resistencia, muerte, equipo, curación,
# fase de descanso, experiencia, estrés, corrupción, traumas y ruinas.
#
# Las pantallas (creador, juego) NO calculan reglas: llaman a estas funciones.
# Así, si el DJ quiere cambiar una regla, solo hay que tocar este archivo.
#
# Cada función de tirada devuelve un diccionario con toda la información
# (dados, resultado, estrés ganado, textos para el registro...) para que la
# interfaz pueda mostrarlo.

from __future__ import annotations
import random

# ══════════════════════════════════════════════════════════════════════════════
# 1. ATRIBUTOS Y HABILIDADES (reglamento 1.8)
# ══════════════════════════════════════════════════════════════════════════════

ATRIBUTOS = ["INT", "CUE", "VOL"]
NOMBRE_ATRIBUTO = {"INT": "Inteligencia", "CUE": "Cuerpo", "VOL": "Voluntad"}

HABILIDADES_POR_ATRIBUTO = {
    "INT": ["sigilo", "estudiar", "percibir", "trastear"],
    "CUE": ["cazar", "mover", "luchar", "destruir"],
    "VOL": ["sobrenatural", "liderar", "socializar", "influir"],
}
TODAS_LAS_HABILIDADES = [h for a in ATRIBUTOS for h in HABILIDADES_POR_ATRIBUTO[a]]
ATRIBUTO_DE = {h: a for a, hs in HABILIDADES_POR_ATRIBUTO.items() for h in hs}

DESCRIPCION_HABILIDAD = {
    "sigilo": "Esconderse y moverse en silencio.",
    "estudiar": "Examinar con tiempo y minuciosidad personas, documentos u objetos; investigar.",
    "percibir": "Presentir algo, ver u oír lo difícil, descubrir una trampa antes de pisarla.",
    "trastear": "Cerraduras, trampas en interiores, arreglar o mejorar equipo, primeros auxilios.",
    "cazar": "Armas arrojadizas y a distancia, rastrear, trampas al aire libre.",
    "mover": "Correr, saltar, escalar, nadar, esquivar.",
    "luchar": "Sin armas, armas a una mano o arma y escudo.",
    "destruir": "Armas a dos manos.",
    "sobrenatural": "Usar conjuros, oraciones o poderes psiónicos.",
    "liderar": "Intimidar, mandar, amenazar.",
    "socializar": "Relacionarse usando carisma y atractivo.",
    "influir": "Convencer con argumentos racionales.",
}

# Las heridas no afectan a estas habilidades (reglamento 2.1.1 y 2.3)
HABILIDADES_SOCIALES = {"influir", "socializar", "liderar"}

MAX_DADOS = 4            # nunca se tiran 5d6
MAX_HABILIDAD = 4        # ninguna habilidad puede tener 5 puntos
PG_MAX = 10
BARRA_ESTRES = 9         # al llegar a 9: trauma y vuelve a 0
BARRA_CORRUPCION = 9     # al llegar a 9: ruina y vuelve a 0
BARRA_NIVEL = 9          # al llegar a 9: talento y vuelve a 0
BARRA_ATRIBUTO = 6       # al llegar a 6: +1 habilidad de ese atributo y vuelve a 0
TRAUMAS_RETIRO = 4
RUINAS_RETIRO = 3

# ══════════════════════════════════════════════════════════════════════════════
# 2. RAZAS (reglamento 1.1)
# ══════════════════════════════════════════════════════════════════════════════

RAZAS = {
    "Humano": {
        "desc": "La raza más adaptable y la mayoría de la población. Elige un punto "
                "en una habilidad y otro punto en otra distinta.",
        "fijas": [], "elegir": 2, "infravision": False, "arcana": True,
        "resistencias": [],
    },
    "Elfo": {
        "desc": "Altos (media 2,10 m) y delgados, sin vello facial ni corporal. "
                "Infravisión a 18 metros. Un punto en mover.",
        "fijas": ["mover"], "elegir": 0, "infravision": True, "arcana": True,
        "resistencias": [],
    },
    "Semielfo": {
        "desc": "Altura media 1,80 m. Solitarios, desconfiados, supervivientes; les cuesta "
                "ser aceptados por humanos y elfos. Infravisión a 18 m. Un punto en percibir.",
        "fijas": ["percibir"], "elegir": 0, "infravision": True, "arcana": True,
        "resistencias": [],
    },
    "Enano": {
        "desc": "Altura media 1,4 m, peso medio 90 kg. Infravisión a 18 m. Un punto en "
                "trastear. +1d6 para resistir magia arcana y venenos. No usan magia arcana.",
        "fijas": ["trastear"], "elegir": 0, "infravision": True, "arcana": False,
        "resistencias": ["magia_arcana", "veneno", "corrupcion_arcana"],
    },
    "Halfling": {
        "desc": "Altura media 1 m, 22-27 kg, cabello muy largo y cara de niño. Un punto en "
                "cazar y otro en sigilo. +1d6 para resistir magia arcana, corrupción y "
                "venenos. Nunca más de 2 puntos en destruir. No usan magia arcana.",
        "fijas": ["cazar", "sigilo"], "elegir": 0, "infravision": False, "arcana": False,
        "resistencias": ["magia_arcana", "veneno", "corrupcion_arcana", "corrupcion_divina"],
        "max": {"destruir": 2},
    },
}

TIPOS_RESISTENCIA = [
    ("", "Normal"),
    ("magia_arcana", "Magia arcana"),
    ("veneno", "Veneno"),
    ("corrupcion_arcana", "Corrupción arcana"),
    ("corrupcion_divina", "Corrupción divina"),
]

# ══════════════════════════════════════════════════════════════════════════════
# 3. CLASES (reglamento 1.2)
# ══════════════════════════════════════════════════════════════════════════════
# "fijas": puntos automáticos. "elegir": lista entre la que se elige UN punto.
# "clase": habilidad de clase (None = la elegida).

CLASES = {
    "Guerrero": {
        "arquetipo": "sajador", "clase": None, "fijas": ["mover"],
        "elegir": ["luchar", "destruir"],
        "desc": "Habilidad de clase: luchar (armas a una mano) o destruir (armas a dos "
                "manos), debe elegir una. Un punto en mover y otro en la elegida.",
        "apodos": ["Fabricatumbas", "Mandíbula Gris", "Acero Frío", "El Sin Miedo", "El Carnicero", "Rompeescudos"],
    },
    "Explorador": {
        "arquetipo": "cazador", "clase": "cazar", "fijas": ["cazar"],
        "elegir": ["mover", "sigilo"],
        "desc": "Habilidad de clase: cazar. Un punto en cazar y otro a elegir entre mover o sigilo.",
        "apodos": ["Zorro del Bosque", "Matalobos", "El Curtido", "Flecha de Sombra", "Pisaventisca"],
    },
    "Ladrón": {
        "arquetipo": "acechador", "clase": "sigilo", "fijas": ["sigilo"],
        "elegir": ["cazar", "mover"],
        "desc": "Habilidad de clase: sigilo. Un punto en sigilo y otro a elegir entre cazar "
                "(armas a distancia o arrojadizas) o mover.",
        "apodos": ["Medio Dedo", "Rata Negra", "Pies Rápidos", "Doble Lengua", "Puñal Nocturno"],
    },
    "Comerciante": {
        "arquetipo": "araña/sanguijuela", "clase": "influir", "fijas": ["trastear", "influir"],
        "elegir": [],
        "desc": "Habilidad de clase: influir. Un punto en trastear y otro en influir. Casi "
                "siempre saben leer y escribir.",
        "apodos": ["Sonrisa de Plata", "Diente de Oro", "Lengua de Seda", "Panza Gorda", "El Tacaño"],
    },
    "Bardo": {
        "arquetipo": "máscara", "clase": "socializar", "fijas": ["socializar", "sigilo"],
        "elegir": [],
        "desc": "Habilidad de clase: socializar. Un punto en socializar y otro en sigilo. "
                "Un bardo de ciudad sabe leer y escribir y toca un instrumento.",
        "apodos": ["Hilacuentos", "Voz de Argento", "Lengua de Miel", "Forjarrimas", "El Ruiseñor"],
    },
    "Extraño": {
        "arquetipo": "poderes sobrenaturales", "clase": "sobrenatural", "fijas": ["sobrenatural"],
        "elegir": [],
        "desc": "Habilidad de clase: sobrenatural. Mago, hechicero o brujo (magia arcana), "
                "clérigo o druida (magia divina) o psiónico. Empieza con 3 talentos.",
        "apodos": ["Capa Gris", "Mano de Tormenta", "Bastón Cojo", "Mente Clara", "Ojo de Ceniza"],
    },
}

TIPOS_MAGIA = {
    "arcana": {"nombre": "Magia arcana", "subclases": ["Mago", "Hechicero", "Brujo"],
               "segunda": "estudiar", "talento": "conjuro", "talentos": "conjuros"},
    "divina": {"nombre": "Magia divina", "subclases": ["Clérigo", "Druida"],
               "segunda": "influir", "talento": "oración", "talentos": "oraciones"},
    "psionica": {"nombre": "Psiónica", "subclases": ["Psiónico"],
                 "segunda": "percibir", "talento": "poder", "talentos": "poderes psiónicos"},
}

MOTIVACIONES = ["Riquezas", "Conocimiento", "Poder", "Venganza", "Viajar", "Amistad", "Justicia"]
VICIOS = ["Alcohol", "Drogas", "Sexo", "Juego", "Lujo", "Fuertes obligaciones o creencias"]

ETAPAS_EDAD = ["Joven", "Adulto", "Anciano"]
DESC_ETAPA = {
    "Joven": "No puede empezar con 3 en percibir, estudiar o trastear. En la fase de "
             "descanso cura sin tirada una herida leve.",
    "Adulto": "Sin restricciones especiales.",
    "Anciano": "Nunca puede tener 3 en mover, luchar, cazar o destruir (salvo su habilidad de clase).",
}

ETAPAS_TRASFONDO = [
    ("origen", "FAMILIA Y ORIGEN",
     "Padres y hermanos: nobles (liderar), comerciantes (influir), esclavos (mover)..."),
    ("ninez", "NIÑEZ",
     "Destacabas por tu fuerza (destruir), carisma (socializar), intuición (percibir)..."),
    ("adolescencia", "ADOLESCENCIA",
     "Entrenaste con armas (luchar o destruir), cazabas animales (cazar)..."),
    ("juventud", "JUVENTUD",
     "Trabajabas en un taller (trastear), descubriste extraños poderes (sobrenatural), "
     "eras un furtivo ladrón (sigilo o trastear)..."),
]

RASGOS_APARIENCIA = [
    "Delgado", "Gordo", "Muy musculoso", "Débil", "Alto", "Bajo", "Atractivo",
    "Das miedo", "Feo", "Calvo", "Mirada fría y penetrante", "Ojos de diferente color",
    "Fea cicatriz en la mejilla", "Tatuaje prominente", "Cojera", "Diente de plata",
    "Cara curtida", "Voz sibilante",
]
RASGOS_PERSONALIDAD = [
    "Avaro", "Cruel", "Generoso", "Justo", "Desconfiado", "Extrovertido", "Introvertido",
    "Temerario", "Cobarde", "Perezoso", "Arrogante", "Fanfarrón", "Violento", "Curioso",
    "Leal", "Orgulloso",
]
RECUERDOS_SUGERIDOS = [
    "Un medallón familiar", "Un brazalete heredado", "Un mapa dibujado a mano", "Una pipa tallada",
    "Un anillo con una inscripción", "Una llave ornamentada", "Un silbato de hueso",
    "Un par de dados de hueso", "Una carta de un viejo amigo", "Una figurilla de madera",
]

TRAUMAS = ["Atormentado", "Imprudente", "Blando", "Feroz", "Frío", "Inestable", "Paranoico"]
RUINAS = ["Sed de sangre", "Huésped", "Miasma", "Alucinaciones"]

SITUACIONES = ["controlada", "arriesgada", "desesperada"]
EFECTOS = ["excelente", "estándar", "limitado"]

# Daño SUGERIDO (puntos de golpe) para (situación) -> (éxito parcial, fracaso).
# Es solo una sugerencia: el DJ decide siempre la consecuencia real.
DANO_SUGERIDO = {
    "controlada": (0, 0),   # normalmente sin heridas: tiempo, ruido, algo se rompe...
    "arriesgada": (1, 1),
    "desesperada": (1, 2),  # puede ser muy grave (3) si la acción podía matarte
}

NOMBRE_DANO = {0: "sin daño", 1: "herida leve", 2: "herida grave", 3: "herida muy grave"}

TEXTO_RESULTADO = {
    "critico": "¡CRÍTICO! La acción funciona y produce un efecto más que excelente.",
    "exito": "ÉXITO. La acción funciona y no hay complicaciones.",
    "parcial": "ÉXITO PARCIAL. La acción funciona, pero hay una complicación.",
    "fallo": "FRACASO. La acción no funciona y habrá complicaciones.",
}
NOMBRE_RESULTADO = {"critico": "Crítico", "exito": "Éxito", "parcial": "Éxito parcial", "fallo": "Fracaso"}
ORDEN_RESULTADO = {"fallo": 0, "parcial": 1, "exito": 2, "critico": 3}


# ══════════════════════════════════════════════════════════════════════════════
# 4. CREACIÓN: CÁLCULO DE HABILIDADES Y LÍMITES (reglamento 1.1 - 1.6)
# ══════════════════════════════════════════════════════════════════════════════

def etapa_humana(edad: int) -> str:
    """Etapa de edad de un humano: joven 18-30, adulto 31-60, anciano 61+."""
    if edad <= 30:
        return "Joven"
    if edad <= 60:
        return "Adulto"
    return "Anciano"


def habilidad_de_clase(datos: dict) -> str:
    clase = datos.get("clase", "")
    info = CLASES.get(clase)
    if not info:
        return ""
    if info["clase"]:
        return info["clase"]
    return datos.get("eleccion_clase", "")


def segunda_habilidad_extrano(datos: dict) -> str:
    tipo = datos.get("tipo_magia", "")
    if tipo == "divina":
        return datos.get("habilidad_divina") or "influir"
    return TIPOS_MAGIA.get(tipo, {}).get("segunda", "")


def calcular_habilidades(datos: dict) -> dict:
    """Calcula las habilidades a partir de las elecciones de creación.
    Se recalcula siempre desde cero, así volver atrás no duplica puntos."""
    h = {k: 0 for k in TODAS_LAS_HABILIDADES}
    raza = RAZAS.get(datos.get("raza", ""))
    if raza:
        for k in raza["fijas"]:
            h[k] += 1
        for k in datos.get("bono_raza", []):
            if k in h:
                h[k] += 1
    clase = CLASES.get(datos.get("clase", ""))
    if clase:
        for k in clase["fijas"]:
            h[k] += 1
        if clase["elegir"] and datos.get("eleccion_clase") in clase["elegir"]:
            h[datos["eleccion_clase"]] += 1
        if datos.get("clase") == "Extraño":
            seg = segunda_habilidad_extrano(datos)
            if seg:
                h[seg] += 1
    for clave, _, _ in ETAPAS_TRASFONDO:
        k = datos.get(f"tf_{clave}_hab")
        if k in h:
            h[k] += 1
    return h


def errores_creacion(datos: dict, h: dict | None = None) -> list[str]:
    """Devuelve la lista de límites de creación que se incumplen (1.6)."""
    if h is None:
        h = calcular_habilidades(datos)
    err = []
    for k, v in h.items():
        if v >= 4:
            err.append(f"Ningún personaje inicial tiene 4 puntos ({k}).")
    etapa = datos.get("etapa", "")
    if etapa == "Joven":
        for k in ("percibir", "estudiar", "trastear"):
            if h[k] >= 3:
                err.append(f"Un joven no puede empezar con 3 en {k}.")
    if etapa == "Anciano":
        hc = habilidad_de_clase(datos)
        for k in ("mover", "luchar", "cazar", "destruir"):
            if h[k] >= 3 and k != hc:
                err.append(f"Un anciano no puede tener 3 en {k} (no es su habilidad de clase).")
    raza = RAZAS.get(datos.get("raza", ""), {})
    for k, mx in raza.get("max", {}).items():
        if h[k] > mx:
            err.append(f"Un {datos.get('raza','').lower()} no puede tener más de {mx} en {k}.")
    if datos.get("clase") != "Extraño" and h["sobrenatural"] > 1:
        err.append("Un personaje que no es extraño no puede tener más de 1 en sobrenatural.")
    return err


def talentos_iniciales(datos: dict, h: dict | None = None) -> int:
    if h is None:
        h = calcular_habilidades(datos)
    if datos.get("clase") == "Extraño":
        return 3
    if h["sobrenatural"] >= 1:
        return 1
    return 0


def puede_usar_arcana(raza: str) -> bool:
    return RAZAS.get(raza, {}).get("arcana", True)


# ══════════════════════════════════════════════════════════════════════════════
# 5. DADOS
# ══════════════════════════════════════════════════════════════════════════════

def d6(n: int) -> list[int]:
    return [random.randint(1, 6) for _ in range(n)]


def interpretar(dados: list[int], cero_dados: bool) -> tuple[str, int]:
    """Devuelve (resultado, valor_usado) según el reglamento 2.1.1 punto 7.
    Con cero dados se tiran 2 y se usa el más bajo (dos seises = éxito)."""
    if cero_dados:
        if dados.count(6) >= 2:
            return "exito", 6
        v = min(dados)
    else:
        if dados.count(6) >= 2:
            return "critico", 6
        v = max(dados)
    if v == 6:
        return "exito", v
    if v >= 4:
        return "parcial", v
    return "fallo", v


# ══════════════════════════════════════════════════════════════════════════════
# 6. TIRADA DE HABILIDAD (reglamento 2.1.1)
# ══════════════════════════════════════════════════════════════════════════════

def calcular_dados(p, habilidad: str, bonificacion: bool = False) -> dict:
    """Calcula cuántos dados tira un personaje en una habilidad.
    bonificacion = el jugador quiere esforzarse o recibe ayuda."""
    base = p.habilidades.get(habilidad, 0)
    social = habilidad in HABILIDADES_SOCIALES
    penal = 1 if (p.puntos_golpe <= 5 and not social) else 0
    n = max(0, base - penal)
    bonus_posible = n < MAX_DADOS
    bonus = 1 if (bonificacion and bonus_posible) else 0
    total = min(MAX_DADOS, n + bonus)
    puede = True
    motivo = ""
    if p.estado in ("muerto", "retirado"):
        puede, motivo = False, f"{p.nombre} está {p.estado}."
    elif p.estado == "inconsciente" or p.puntos_golpe <= 0:
        puede, motivo = False, f"{p.nombre} está inconsciente o en peligro mortal."
    elif p.puntos_golpe == 1 and not social and not bonus:
        puede, motivo = False, (f"{p.nombre} tiene un solo punto de golpe: solo puede actuar "
                                "si se esfuerza o le ayudan.")
    partes = [f"{base} por habilidad"]
    if penal:
        partes.append("-1 por heridas")
    if bonus:
        partes.append("+1 de bonificación")
    elif bonificacion and not bonus_posible:
        partes.append("(ya tira 4 dados: sin bonificación ni estrés)")
    return {"base": base, "penal": penal, "bonus": bonus, "bonus_posible": bonus_posible,
            "total": total, "puede": puede, "motivo": motivo,
            "explicacion": ", ".join(partes) + f" = {total}d6" + (" (0 dados: 2d6 y el peor)" if total == 0 else "")}


def tirada_habilidad(p, habilidad: str, esfuerzo: bool = False, ayudante=None,
                     motivacion: bool = False, paga: str = "actor",
                     situacion: str = "arriesgada", efecto: str = "estándar") -> dict:
    """Realiza una tirada de habilidad completa, aplicando estrés.
    ayudante: otro Personaje que ayuda (o None).
    paga: si hay esfuerzo y ayuda, quién gana el estrés ("actor" o "ayudante")."""
    bonificacion = esfuerzo or (ayudante is not None)
    calc = calcular_dados(p, habilidad, bonificacion)
    res = {"personaje": p, "habilidad": habilidad, "situacion": situacion, "efecto": efecto,
           "calculo": calc, "eventos": [], "dados": [], "resultado": None}
    if not calc["puede"]:
        res["eventos"].append(calc["motivo"])
        return res

    # Estrés por la bonificación (solo si realmente se aplica el dado)
    if calc["bonus"]:
        if esfuerzo and ayudante is not None:
            if paga == "ayudante":
                res["eventos"] += ayudante.ganar_estres(1, "ayuda")
            else:
                res["eventos"] += p.ganar_estres(1 if motivacion else 2, "esfuerzo")
        elif esfuerzo:
            res["eventos"] += p.ganar_estres(1 if motivacion else 2, "esfuerzo")
        else:
            res["eventos"] += ayudante.ganar_estres(1, "ayuda")

    n = calc["total"]
    cero = n == 0
    dados = d6(2 if cero else n)
    resultado, valor = interpretar(dados, cero)
    # Heridas: con 7 o menos PG un crítico es éxito normal salvo bonificación (2.3)
    if (resultado == "critico" and p.puntos_golpe <= 7
            and habilidad not in HABILIDADES_SOCIALES and not calc["bonus"]):
        resultado = "exito"
        res["eventos"].append("Por las heridas (7 PG o menos) el crítico cuenta como éxito.")
    res.update({"dados": dados, "cero_dados": cero, "valor": valor, "resultado": resultado})
    pa, fa = DANO_SUGERIDO.get(situacion, (0, 0))
    res["dano_sugerido"] = pa if resultado == "parcial" else fa if resultado == "fallo" else 0
    return res


def texto_consecuencias(resultado: str, situacion: str, efecto: str) -> list[str]:
    """Guía para el DJ: qué tipo de consecuencias aplicar (2.1.1 punto 8)."""
    t = [TEXTO_RESULTADO[resultado]]
    if resultado in ("critico", "exito", "parcial"):
        t.append(f"Impacto positivo según efecto {efecto}: " + {
            "excelente": "gran impacto, supera un gran obstáculo.",
            "estándar": "impacto importante, supera un obstáculo medio.",
            "limitado": "poco impacto, quizá hagan falta más tiradas.",
        }[efecto])
    if resultado in ("parcial", "fallo"):
        t.append(f"Complicación según situación {situacion}: " + {
            "controlada": "consecuencia menor (tardar, hacer ruido, romper algo) o ninguna.",
            "arriesgada": "consecuencia moderada (p. ej. una herida leve).",
            "desesperada": "consecuencia seria (p. ej. herida leve con éxito parcial; grave, o muy grave si podía matarte, con fracaso).",
        }[situacion])
    return t


# ══════════════════════════════════════════════════════════════════════════════
# 7. TIRADA DE RESISTENCIA (reglamento 2.1.2) Y A LA MUERTE (2.4)
# ══════════════════════════════════════════════════════════════════════════════

def dados_resistencia(p, atributo: str, contra: str = "") -> dict:
    n = p.habilidades_con_puntos(atributo)
    bonus = 1 if contra and contra in RAZAS.get(p.raza, {}).get("resistencias", []) else 0
    total = min(MAX_DADOS, n + bonus)
    return {"base": n, "bonus": bonus, "total": total}


def tirada_resistencia(p, atributo: str = "CUE", contra: str = "", aplicar_estres: bool = True) -> dict:
    """Tira resistencia: tantos dados como habilidades del atributo con al menos un punto.
    Crítico: -1 estrés. Si no: +estrés = 6 - resultado más alto."""
    calc = dados_resistencia(p, atributo, contra)
    n = calc["total"]
    cero = n == 0
    dados = d6(2 if cero else n)
    resultado, valor = interpretar(dados, cero)
    res = {"personaje": p, "atributo": atributo, "contra": contra, "calculo": calc,
           "dados": dados, "cero_dados": cero, "valor": valor, "resultado": resultado, "eventos": []}
    if resultado == "critico":
        res["estres"] = -1
        if aplicar_estres:
            res["eventos"] += p.ganar_estres(-1, "resistencia (crítico)")
    else:
        res["estres"] = 6 - valor
        if aplicar_estres and res["estres"]:
            res["eventos"] += p.ganar_estres(res["estres"], "resistencia")
    return res


def tirada_muerte(p, pg_previos: int, atributo: str = "CUE") -> dict:
    """Resistencia a la muerte al llegar a 0 PG. Cuesta estrés como todas.
    Devuelve 'desenlace': 'evitado', 'un_pg', 'inconsciente' o 'dj' (el DJ decide)."""
    res = tirada_resistencia(p, atributo)
    r = res["resultado"]
    if r == "critico":
        p.puntos_golpe = pg_previos
        p.estado = "activo"
        res["desenlace"] = "evitado"
        res["eventos"].append(f"¡{p.nombre} evita milagrosamente el daño! Vuelve a {pg_previos} PG.")
    elif r == "exito":
        p.puntos_golpe = 1
        p.estado = "activo"
        res["desenlace"] = "un_pg"
        res["eventos"].append(f"{p.nombre} sobrevive con 1 punto de golpe.")
    elif r == "parcial":
        p.puntos_golpe = 0
        p.estado = "inconsciente"
        res["desenlace"] = "inconsciente"
        res["eventos"].append(f"{p.nombre} cae al suelo inconsciente.")
    else:
        res["desenlace"] = "dj"
        res["eventos"].append(f"{p.nombre} fracasa: el DJ decide si muere o queda inconsciente.")
    return res


# ══════════════════════════════════════════════════════════════════════════════
# 8. TIRADA EN EQUIPO (2.1.4) Y FORTUNA (2.1.3)
# ══════════════════════════════════════════════════════════════════════════════

def tirada_equipo(lider, participantes: list, habilidad: str) -> dict:
    """Todos tiran (sin bonificación); se usa la mejor; el líder gana 1 estrés por fracaso."""
    tiradas = []
    for q in participantes:
        calc = calcular_dados(q, habilidad, False)
        if not calc["puede"]:
            tiradas.append({"personaje": q, "puede": False, "motivo": calc["motivo"]})
            continue
        n = calc["total"]
        dados = d6(2 if n == 0 else n)
        r, v = interpretar(dados, n == 0)
        if r == "critico" and q.puntos_golpe <= 7 and habilidad not in HABILIDADES_SOCIALES:
            r = "exito"
        tiradas.append({"personaje": q, "puede": True, "dados": dados, "resultado": r, "valor": v, "cero": n == 0})
    validas = [t for t in tiradas if t["puede"]]
    eventos = []
    if not validas:
        return {"tiradas": tiradas, "resultado": None, "eventos": ["Nadie puede realizar la tirada."]}
    mejor = max(validas, key=lambda t: (ORDEN_RESULTADO[t["resultado"]], t["valor"]))
    fallos = sum(1 for t in validas if t["resultado"] == "fallo")
    if fallos:
        eventos += lider.ganar_estres(fallos, f"{fallos} fracaso(s) en la tirada en equipo")
    return {"tiradas": tiradas, "resultado": mejor["resultado"], "mejor": mejor, "eventos": eventos}


def tirada_fortuna() -> int:
    return random.randint(1, 6)


# ══════════════════════════════════════════════════════════════════════════════
# 9. CURACIÓN (2.3)
# ══════════════════════════════════════════════════════════════════════════════

def tirada_curacion(curador, habilidad: str, objetivo, cantidad: int, esfuerzo: bool = False) -> dict:
    """Curación con trastear (necesita vendas u otro elemento) o sobrenatural.
    Crítico: cura el doble. Éxito/parcial: cura la cantidad. Fracaso: no cura."""
    res = tirada_habilidad(curador, habilidad, esfuerzo=esfuerzo, situacion="controlada")
    if res["resultado"] is None:
        res["curado"] = 0
        return res
    r = res["resultado"]
    cura = cantidad * 2 if r == "critico" else cantidad if r in ("exito", "parcial") else 0
    res["curado"] = objetivo.curar(cura)
    res["eventos"].append(f"{objetivo.nombre} recupera {res['curado']} PG." if cura else "No se cura nada.")
    return res


def tirada_curacion_pnj(puntos_pnj: int, objetivo, cantidad: int | None = None) -> dict:
    """Un sanador PNJ (1 a 4 puntos) en la fase de descanso: cura tantos PG como sus
    puntos (el doble con crítico), salvo que se indique otra cantidad."""
    n = max(0, min(MAX_DADOS, puntos_pnj))
    dados = d6(2 if n == 0 else n)
    r, v = interpretar(dados, n == 0)
    base = cantidad if cantidad is not None else max(1, puntos_pnj)
    cura = base * 2 if r == "critico" else base if r in ("exito", "parcial") else 0
    curado = objetivo.curar(cura)
    return {"dados": dados, "resultado": r, "valor": v, "curado": curado, "cero_dados": n == 0,
            "eventos": [f"El sanador ({puntos_pnj} pts) cura {curado} PG a {objetivo.nombre}."]}


# ══════════════════════════════════════════════════════════════════════════════
# 10. FASE DE DESCANSO (2.6)
# ══════════════════════════════════════════════════════════════════════════════

TAREAS_DESCANSO = {
    "curacion": "Curación",
    "estres": "Reducir estrés (vicio)",
    "proyecto": "Proyecto a largo plazo",
    "entrenar": "Entrenar",
}


def tirada_reducir_estres(p) -> dict:
    """Tantos dados como habilidades con punto en el atributo con menos habilidades con
    punto. Se resta el más alto. Si algún atributo no tiene ninguna: 2d6 y el más bajo."""
    n = min(p.habilidades_con_puntos(a) for a in ATRIBUTOS)
    n = min(n, MAX_DADOS)
    cero = n == 0
    dados = d6(2 if cero else n)
    valor = min(dados) if cero else max(dados)
    antes = p.estres
    p.estres = max(0, p.estres - valor)
    return {"dados": dados, "cero_dados": cero, "valor": valor, "reducido": antes - p.estres,
            "eventos": [f"{p.nombre} se entrega a su vicio ({p.vicio or 'vicio'}) y reduce "
                        f"{antes - p.estres} de estrés."]}


def curacion_joven(p) -> list[str]:
    if p.etapa == "Joven" and p.estado not in ("muerto", "retirado") and p.puntos_golpe < p.pg_max:
        p.curar(1)
        return [f"{p.nombre} es joven: cura automáticamente una herida leve."]
    return []


# ══════════════════════════════════════════════════════════════════════════════
# 11. EXPERIENCIA (2.7)
# ══════════════════════════════════════════════════════════════════════════════

def gastar_experiencia(p, destino: str, entrenamiento: bool = False) -> tuple[bool, list[str]]:
    """destino: 'INT', 'CUE', 'VOL' o 'nivel'. En la misma sesión no se puede repetir
    destino con puntos de experiencia (el entrenamiento del descanso no cuenta)."""
    if not entrenamiento and destino in p.xp_sesion:
        return False, [f"{p.nombre} ya invirtió experiencia en {destino} en esta sesión."]
    if not entrenamiento:
        p.xp_sesion.append(destino)
    eventos = []
    if destino == "nivel":
        p.barra_nivel += 1
        eventos.append(f"{p.nombre}: barra de nivel {p.barra_nivel}/{BARRA_NIVEL}.")
        if p.barra_nivel >= BARRA_NIVEL:
            p.barra_nivel = 0
            p.talentos_pendientes += 1
            eventos.append(f"¡{p.nombre} llena la barra de nivel y gana un talento!")
    else:
        p.atributos[destino] = p.atributos.get(destino, 0) + 1
        eventos.append(f"{p.nombre}: barra de {NOMBRE_ATRIBUTO[destino]} {p.atributos[destino]}/{BARRA_ATRIBUTO}.")
        if p.atributos[destino] >= BARRA_ATRIBUTO:
            p.atributos[destino] = 0
            p.puntos_habilidad_pendientes[destino] = p.puntos_habilidad_pendientes.get(destino, 0) + 1
            eventos.append(f"¡{p.nombre} llena la barra de {NOMBRE_ATRIBUTO[destino]}: "
                           "puede subir una habilidad de ese atributo!")
    return True, eventos


def habilidades_subibles(p, atributo: str) -> list[str]:
    """Habilidades de un atributo que se pueden subir un punto."""
    r = []
    for h in HABILIDADES_POR_ATRIBUTO[atributo]:
        if p.habilidades[h] >= MAX_HABILIDAD:
            continue
        mx = RAZAS.get(p.raza, {}).get("max", {}).get(h)
        if mx is not None and p.habilidades[h] >= mx:
            continue
        if h == "sobrenatural" and p.clase != "Extraño":
            continue  # salvo permiso del DJ (reglamento 1.8)
        if p.etapa == "Anciano" and h in ("mover", "luchar", "cazar", "destruir") \
                and h != p.habilidad_clase and p.habilidades[h] >= 2:
            continue
        r.append(h)
    return r

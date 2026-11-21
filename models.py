# models.py - Modelos de datos para FORGED IN THE DARK FANTASY

from __future__ import annotations
import uuid
import datetime as _datetime
from dataclasses import dataclass, field, fields
from typing import Optional

import reglas
from reglas import (HABILIDADES_POR_ATRIBUTO, TODAS_LAS_HABILIDADES, BARRA_ESTRES,
                    BARRA_CORRUPCION, PG_MAX, TRAUMAS_RETIRO, RUINAS_RETIRO)


# Equivalencias para leer personajes creados con la versión anterior (Warhammer)
_RAZAS_ANTIGUAS = {"Alto Elfo": "Elfo", "Elfo de los bosques": "Elfo"}
_CLASES_ANTIGUAS = {"Mago": ("Extraño", "arcana", "Mago"), "Clérigo": ("Extraño", "divina", "Clérigo")}


@dataclass
class Personaje:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    apodo: str = ""
    raza: str = ""
    clase: str = ""
    eleccion_clase: str = ""        # luchar/destruir, mover/sigilo, cazar/mover
    tipo_magia: str = ""            # arcana / divina / psionica
    subclase: str = ""              # Mago, Hechicero, Brujo, Clérigo, Druida, Psiónico
    deidad: str = ""
    edad: str = ""
    etapa: str = ""                 # Joven / Adulto / Anciano
    motivacion: str = ""
    vicio: str = ""
    trasfondo: dict = field(default_factory=dict)   # {"origen": {"texto":..,"habilidad":..}, ...}
    bono_raza: list = field(default_factory=list)
    cabello: str = ""
    ojos: str = ""
    rasgos_apariencia: list = field(default_factory=list)
    personalidad: list = field(default_factory=list)
    recuerdos: list = field(default_factory=list)
    amigos: list = field(default_factory=list)
    enemigos: list = field(default_factory=list)
    lazos: str = ""
    sabe_leer: bool = False
    equipo: str = ""
    retrato: str = ""
    notas: str = ""

    habilidades: dict = field(default_factory=lambda: {h: 0 for h in TODAS_LAS_HABILIDADES})
    atributos: dict = field(default_factory=lambda: {"INT": 0, "CUE": 0, "VOL": 0})  # barras 0-5
    barra_nivel: int = 0
    estres: int = 0
    corrupcion: int = 0
    puntos_golpe: int = PG_MAX
    pg_max: int = PG_MAX
    traumas: list = field(default_factory=list)
    ruinas: list = field(default_factory=list)
    talentos: list = field(default_factory=list)     # [{"nombre":..,"descripcion":..}]
    armadura: int = 0                # casillas de protección
    armadura_usada: int = 0
    estado: str = "activo"           # activo / inconsciente / muerto / retirado

    # Avances pendientes de que el jugador elija (los resuelve la interfaz)
    traumas_pendientes: int = 0
    ruinas_pendientes: int = 0
    talentos_pendientes: int = 0
    puntos_habilidad_pendientes: dict = field(default_factory=dict)
    xp_sesion: list = field(default_factory=list)   # destinos de XP usados esta sesión

    fecha_creacion: str = field(
        default_factory=lambda: _datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    # ── Consultas ──────────────────────────────────────────────────────────
    @property
    def habilidad_clase(self) -> str:
        info = reglas.CLASES.get(self.clase)
        if not info:
            return ""
        return info["clase"] or self.eleccion_clase

    @property
    def descripcion_clase(self) -> str:
        if self.clase == "Extraño" and self.subclase:
            return f"Extraño ({self.subclase})"
        return self.clase

    @property
    def puede_actuar(self) -> bool:
        return self.estado == "activo" and self.puntos_golpe > 0

    @property
    def tiene_pendientes(self) -> bool:
        return bool(self.traumas_pendientes or self.ruinas_pendientes or self.talentos_pendientes
                    or any(self.puntos_habilidad_pendientes.values()))

    def habilidades_con_puntos(self, atributo: str) -> int:
        return sum(1 for h in HABILIDADES_POR_ATRIBUTO[atributo] if self.habilidades.get(h, 0) > 0)

    # ── Cambios de estado (devuelven textos para el registro) ──────────────
    def ganar_estres(self, n: int, motivo: str = "") -> list[str]:
        if n == 0 or self.estado in ("muerto", "retirado"):
            return []
        ev = []
        if n < 0:
            antes = self.estres
            self.estres = max(0, self.estres + n)
            if antes != self.estres:
                ev.append(f"{self.nombre} pierde {antes - self.estres} de estrés ({motivo}).")
            return ev
        self.estres += n
        ev.append(f"{self.nombre} gana {n} de estrés ({motivo}).")
        if self.estres >= BARRA_ESTRES:
            self.estres = 0
            self.traumas_pendientes += 1
            ev.append(f"¡La barra de estrés de {self.nombre} se llena: gana un TRAUMA!")
        return ev

    def ganar_corrupcion(self, n: int, motivo: str = "") -> list[str]:
        if self.estado in ("muerto", "retirado"):
            return []
        if n <= 0:
            if n < 0:
                self.corrupcion = max(0, self.corrupcion + n)
                return [f"{self.nombre} limpia {-n} punto(s) de corrupción."]
            return []
        ev = [f"{self.nombre} gana {n} de corrupción ({motivo})."]
        self.corrupcion += n
        if self.corrupcion >= BARRA_CORRUPCION:
            self.corrupcion = 0
            self.ruinas_pendientes += 1
            ev.append(f"¡La corrupción de {self.nombre} se completa: gana una RUINA!")
        return ev

    def anadir_trauma(self, trauma: str) -> list[str]:
        self.traumas.append(trauma)
        self.traumas_pendientes = max(0, self.traumas_pendientes - 1)
        ev = [f"{self.nombre} sufre el trauma «{trauma}»."]
        if len(self.traumas) >= TRAUMAS_RETIRO:
            self.estado = "retirado"
            ev.append(f"Con su cuarto trauma, {self.nombre} se retira: pasa a ser un PNJ traumatizado.")
        return ev

    def anadir_ruina(self, ruina: str) -> list[str]:
        self.ruinas.append(ruina)
        self.ruinas_pendientes = max(0, self.ruinas_pendientes - 1)
        ev = [f"{self.nombre} sufre la ruina «{ruina}»."]
        if len(self.ruinas) >= RUINAS_RETIRO:
            self.estado = "retirado"
            ev.append(f"Con su tercera ruina, {self.nombre} se retira: pasa a ser un PNJ malvado.")
        return ev

    def recibir_dano(self, puntos: int) -> int:
        """Resta PG (nunca negativos). Devuelve los PG que tenía antes."""
        antes = self.puntos_golpe
        self.puntos_golpe = max(0, self.puntos_golpe - max(0, puntos))
        return antes

    def curar(self, puntos: int) -> int:
        if self.estado in ("muerto", "retirado") or puntos <= 0:
            return 0
        antes = self.puntos_golpe
        self.puntos_golpe = min(self.pg_max, self.puntos_golpe + puntos)
        if self.puntos_golpe > 0 and self.estado == "inconsciente":
            self.estado = "activo"
        return self.puntos_golpe - antes

    # ── Persistencia ───────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        d = {}
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, (list, dict)):
                v = _copia(v)
            d[f.name] = v
        d["version"] = 2
        return d

    @staticmethod
    def from_dict(d: dict) -> "Personaje":
        d = dict(d)
        if d.get("version", 1) < 2:
            d = _migrar_personaje_v1(d)
        validos = {f.name for f in fields(Personaje)}
        p = Personaje(**{k: _copia(v) for k, v in d.items() if k in validos})
        for h in TODAS_LAS_HABILIDADES:
            p.habilidades.setdefault(h, 0)
        for a in ("INT", "CUE", "VOL"):
            p.atributos.setdefault(a, 0)
        return p


def _copia(v):
    if isinstance(v, dict):
        return {k: _copia(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_copia(x) for x in v]
    return v


def _migrar_personaje_v1(d: dict) -> dict:
    """Convierte un personaje de la versión anterior del programa al reglamento actual.
    Conserva sus habilidades tal cual (el DJ puede revisarlas)."""
    n = dict(d)
    n["raza"] = _RAZAS_ANTIGUAS.get(d.get("raza", ""), d.get("raza", ""))
    prof = d.get("profesion", "")
    if prof in _CLASES_ANTIGUAS:
        n["clase"], n["tipo_magia"], n["subclase"] = _CLASES_ANTIGUAS[prof]
    else:
        n["clase"] = prof
    n["etapa"] = d.get("edad", "") if d.get("edad") in reglas.ETAPAS_EDAD else ""
    n["edad"] = "" if n["etapa"] else d.get("edad", "")
    n["trasfondo"] = {k: {"texto": d.get(f"trasfondo_{k}", ""), "habilidad": ""}
                      for k in ("origen", "ninez", "adolescencia", "juventud")}
    n["rasgos_apariencia"] = list(d.get("aspecto", []))
    if d.get("debilidad"):
        n["personalidad"] = [d["debilidad"]]
    heridas = d.get("heridas_leves", 0) + 2 * d.get("heridas_graves", 0) + 3 * d.get("heridas_muy_graves", 0)
    n["puntos_golpe"] = max(0, PG_MAX - heridas)
    n["barra_nivel"] = d.get("nivel", 0)
    n["estres"] = min(d.get("estres", 0), BARRA_ESTRES - 1)
    n["corrupcion"] = min(d.get("corrupcion", 0), BARRA_CORRUPCION - 1)
    if n["clase"] == "Extraño":
        n["sabe_leer"] = n.get("tipo_magia") == "arcana"
    if n["clase"] in ("Comerciante", "Bardo"):
        n["sabe_leer"] = True
    if n.get("habilidades"):
        for h in TODAS_LAS_HABILIDADES:
            n["habilidades"].setdefault(h, 0)
    return n


# ══════════════════════════════════════════════════════════════════════════════
# CLASES PARA DUNGEONS (formato del Editor de Dungeons)
# ══════════════════════════════════════════════════════════════════════════════

def _filtrar(cls, d):
    """Ignora claves desconocidas para que un JSON con campos nuevos no rompa la carga."""
    validos = {f.name for f in fields(cls)}
    return {k: v for k, v in d.items() if k in validos}


DIRECTIONS = ["norte", "sur", "este", "oeste", "arriba", "abajo", "especial"]
OPPOSITE = {"norte": "sur", "sur": "norte", "este": "oeste", "oeste": "este",
            "arriba": "abajo", "abajo": "arriba", "especial": "especial"}
DIR_DELTA = {
    "norte": (0, 1, 0), "sur": (0, -1, 0), "este": (1, 0, 0), "oeste": (-1, 0, 0),
    "arriba": (0, 0, 1), "abajo": (0, 0, -1), "especial": (0, 0, 0),
}


@dataclass
class Item:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    estado: str = "en_room"

    def to_dict(self): return self.__dict__.copy()
    @staticmethod
    def from_dict(d): return Item(**_filtrar(Item, d))


@dataclass
class Monstruo:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    presente: bool = True

    def to_dict(self): return self.__dict__.copy()
    @staticmethod
    def from_dict(d): return Monstruo(**_filtrar(Monstruo, d))


@dataclass
class PNJ:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    presente: bool = True
    actitud: str = "neutral"

    def to_dict(self): return self.__dict__.copy()
    @staticmethod
    def from_dict(d): return PNJ(**_filtrar(PNJ, d))


@dataclass
class EfectoMecanismo:
    tipo: str = "ninguno"
    puntos: int = 0
    monedas: int = 0
    item_id: str = ""
    direccion: str = ""
    sentido: str = "ambos"

    def to_dict(self): return self.__dict__.copy()
    @staticmethod
    def from_dict(d): return EfectoMecanismo(**_filtrar(EfectoMecanismo, d))


@dataclass
class Mecanismo:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    estado: str = "off"
    texto_on: str = ""
    texto_off: str = ""
    texto_on_a_off: str = ""
    texto_off_a_on: str = ""
    texto_destruido: str = ""
    texto_ya_destruido: str = ""
    efecto_on: EfectoMecanismo = field(default_factory=EfectoMecanismo)
    efecto_off: EfectoMecanismo = field(default_factory=EfectoMecanismo)

    def to_dict(self):
        d = self.__dict__.copy()
        d["efecto_on"] = self.efecto_on.to_dict()
        d["efecto_off"] = self.efecto_off.to_dict()
        return d

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["efecto_on"] = EfectoMecanismo.from_dict(d.get("efecto_on", {}))
        d["efecto_off"] = EfectoMecanismo.from_dict(d.get("efecto_off", {}))
        return Mecanismo(**_filtrar(Mecanismo, d))


@dataclass
class Salida:
    direccion: str = ""
    room_destino_id: str = ""
    estado_hacia_destino: str = "abierta"
    estado_hacia_origen: str = "abierta"
    especial_destino_id: str = ""

    def to_dict(self): return self.__dict__.copy()
    @staticmethod
    def from_dict(d): return Salida(**_filtrar(Salida, d))


@dataclass
class Room:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    imagen: str = ""
    sonido: str = ""
    x: int = 0
    y: int = 0
    z: int = 0
    items: list = field(default_factory=list)
    monstruos: list = field(default_factory=list)
    pnjs: list = field(default_factory=list)
    mecanismos: list = field(default_factory=list)
    salidas: list = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id, "numero": self.numero, "nombre": self.nombre,
            "descripcion": self.descripcion, "imagen": self.imagen, "sonido": self.sonido,
            "x": self.x, "y": self.y, "z": self.z,
            "items": [i.to_dict() for i in self.items],
            "monstruos": [m.to_dict() for m in self.monstruos],
            "pnjs": [p.to_dict() for p in self.pnjs],
            "mecanismos": [m.to_dict() for m in self.mecanismos],
            "salidas": [s.to_dict() for s in self.salidas],
        }

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["items"] = [Item.from_dict(i) for i in d.get("items", [])]
        d["monstruos"] = [Monstruo.from_dict(m) for m in d.get("monstruos", [])]
        d["pnjs"] = [PNJ.from_dict(p) for p in d.get("pnjs", [])]
        d["mecanismos"] = [Mecanismo.from_dict(m) for m in d.get("mecanismos", [])]
        d["salidas"] = [Salida.from_dict(s) for s in d.get("salidas", [])]
        validos = {f.name for f in fields(Room)}
        filtrado = {k: v for k, v in d.items() if k in validos}
        return Room(**filtrado)

    def salida_en(self, direccion: str) -> Optional[Salida]:
        for s in self.salidas:
            if s.direccion == direccion:
                return s
        return None


@dataclass
class Dungeon:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    fecha_creacion: str = ""
    rooms: list = field(default_factory=list)
    items_globales: list = field(default_factory=list)
    monstruos_globales: list = field(default_factory=list)
    pnjs_globales: list = field(default_factory=list)
    mecanismos_globales: list = field(default_factory=list)
    _next_room: int = 1
    _next_item: int = 1
    _next_monstruo: int = 1
    _next_pnj: int = 1
    _next_mecanismo: int = 1

    def next_room_num(self): n = self._next_room; self._next_room += 1; return n
    def next_item_num(self): n = self._next_item; self._next_item += 1; return n
    def next_monstruo_num(self): n = self._next_monstruo; self._next_monstruo += 1; return n
    def next_pnj_num(self): n = self._next_pnj; self._next_pnj += 1; return n
    def next_mecanismo_num(self): n = self._next_mecanismo; self._next_mecanismo += 1; return n

    def room_en(self, x, y, z) -> Optional[Room]:
        for r in self.rooms:
            if r.x == x and r.y == y and r.z == z:
                return r
        return None

    def room_por_id(self, rid) -> Optional[Room]:
        for r in self.rooms:
            if r.id == rid:
                return r
        return None

    def destino_salida(self, room: Room, salida: Salida) -> Optional[Room]:
        """Room a la que lleva una salida (por id, o por coordenadas si falta el id)."""
        rid = salida.especial_destino_id if (salida.direccion == "especial" and salida.especial_destino_id) \
            else salida.room_destino_id
        dest = self.room_por_id(rid) if rid else None
        if dest is None and salida.direccion != "especial":
            dx, dy, dz = DIR_DELTA[salida.direccion]
            dest = self.room_en(room.x + dx, room.y + dy, room.z + dz)
        return dest

    def paso(self, room: Room, direccion: str):
        """Comprueba si el grupo puede salir de 'room' en 'direccion'.
        Devuelve (room_destino o None, estado) con estado 'abierta', 'cerrada' o 'sin_salida'.
        Respeta el sentido de las salidas: una salida puede permitir ir de A a B y no de B a A."""
        if room is None:
            return None, "sin_salida"
        s = room.salida_en(direccion)
        if s is not None:
            dest = self.destino_salida(room, s)
            if dest is None:
                return None, "sin_salida"
            return dest, ("abierta" if s.estado_hacia_destino == "abierta" else "cerrada")
        # La salida solo está guardada en la room vecina: miramos su sentido "hacia origen"
        if direccion == "especial":
            return None, "sin_salida"
        dx, dy, dz = DIR_DELTA[direccion]
        vecina = self.room_en(room.x + dx, room.y + dy, room.z + dz)
        if vecina is None:
            return None, "sin_salida"
        sv = vecina.salida_en(OPPOSITE[direccion])
        if sv is None or (sv.room_destino_id and sv.room_destino_id != room.id):
            return None, "sin_salida"
        return vecina, ("abierta" if sv.estado_hacia_origen == "abierta" else "cerrada")

    def to_dict(self):
        return {
            "id": self.id, "numero": self.numero, "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion,
            "rooms": [r.to_dict() for r in self.rooms],
            "items_globales": [i.to_dict() for i in self.items_globales],
            "monstruos_globales": [m.to_dict() for m in self.monstruos_globales],
            "pnjs_globales": [p.to_dict() for p in self.pnjs_globales],
            "mecanismos_globales": [m.to_dict() for m in self.mecanismos_globales],
            "_next_room": self._next_room, "_next_item": self._next_item,
            "_next_monstruo": self._next_monstruo, "_next_pnj": self._next_pnj,
            "_next_mecanismo": self._next_mecanismo,
        }

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["rooms"] = [Room.from_dict(r) for r in d.get("rooms", [])]
        d["items_globales"] = [Item.from_dict(i) for i in d.get("items_globales", [])]
        d["monstruos_globales"] = [Monstruo.from_dict(m) for m in d.get("monstruos_globales", [])]
        d["pnjs_globales"] = [PNJ.from_dict(p) for p in d.get("pnjs_globales", [])]
        d["mecanismos_globales"] = [Mecanismo.from_dict(m) for m in d.get("mecanismos_globales", [])]
        # Solo pasar los campos que existen en el dataclass
        validos = {f.name for f in fields(Dungeon)}
        filtrado = {k: v for k, v in d.items() if k in validos}
        return Dungeon(**filtrado)


# ══════════════════════════════════════════════════════════════════════════════
# CLASE PARTIDA
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Partida:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    nombre: str = ""
    dungeon_id: str = ""
    fecha_guardado: str = ""
    personajes: list = field(default_factory=list)
    room_actual_id: str = ""
    orientacion: str = "norte"                    # hacia dónde mira el grupo
    visitadas: list = field(default_factory=list)  # ids de rooms ya exploradas (mapa)
    registro: list = field(default_factory=list)   # últimas líneas del diario
    inventario: list = field(default_factory=list)
    monedas: int = 0
    sesion: int = 1
    dungeon_snapshot: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id, "nombre": self.nombre, "dungeon_id": self.dungeon_id,
            "fecha_guardado": self.fecha_guardado,
            "personajes": [p.to_dict() for p in self.personajes],
            "room_actual_id": self.room_actual_id,
            "orientacion": self.orientacion,
            "visitadas": list(self.visitadas),
            "registro": list(self.registro[-200:]),
            "inventario": [i.to_dict() for i in self.inventario],
            "monedas": self.monedas,
            "sesion": self.sesion,
            "dungeon_snapshot": self.dungeon_snapshot,
        }

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["personajes"] = [Personaje.from_dict(p) for p in d.get("personajes", [])]
        d["inventario"] = [Item.from_dict(i) for i in d.get("inventario", [])]
        validos = {f.name for f in fields(Partida)}
        return Partida(**{k: v for k, v in d.items() if k in validos})

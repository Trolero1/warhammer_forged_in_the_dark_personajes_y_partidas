# models.py - Modelos de datos para WARHAMMER FORGED IN THE DARK

from __future__ import annotations
import uuid
import datetime as _datetime
from dataclasses import dataclass, field, fields
from typing import Optional


HABILIDADES_POR_ATRIBUTO = {
    "INT": ["cazar", "estudiar", "percibir", "trastear"],
    "CUE": ["sigilo", "mover", "luchar", "destruir"],
    "VOL": ["sobrenatural", "liderar", "socializar", "influir"],
}

TODAS_LAS_HABILIDADES = [
    "cazar", "estudiar", "percibir", "trastear",
    "sigilo", "mover", "luchar", "destruir",
    "sobrenatural", "liderar", "socializar", "influir",
]


@dataclass
class Personaje:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    nombre: str = ""
    apodo: str = ""
    numero: int = 0
    raza: str = ""
    profesion: str = ""
    edad: str = ""
    atributos: dict = field(default_factory=lambda: {
        "CUE": 0, "INT": 0, "VOL": 0
    })
    habilidades: dict = field(default_factory=lambda: {h: 0 for h in TODAS_LAS_HABILIDADES})
    debilidad: str = ""
    motivacion: str = ""
    vicio: str = ""
    equipo: str = ""
    recuerdos: list = field(default_factory=list)
    aspecto: list = field(default_factory=list)
    trasfondo_origen: str = ""
    trasfondo_ninez: str = ""
    trasfondo_adolescencia: str = ""
    trasfondo_juventud: str = ""
    estres: int = 0
    corrupcion: int = 0
    nivel: int = 0
    heridas_leves: int = 0
    heridas_graves: int = 0
    heridas_muy_graves: int = 0
    fecha_creacion: str = field(
        default_factory=lambda: _datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "nombre": self.nombre, "apodo": self.apodo,
            "numero": self.numero, "raza": self.raza, "profesion": self.profesion,
            "edad": self.edad,
            "atributos": self.atributos.copy(),
            "habilidades": dict(self.habilidades),
            "debilidad": self.debilidad, "motivacion": self.motivacion,
            "vicio": self.vicio, "equipo": self.equipo,
            "recuerdos": list(self.recuerdos), "aspecto": list(self.aspecto),
            "trasfondo_origen": self.trasfondo_origen,
            "trasfondo_ninez": self.trasfondo_ninez,
            "trasfondo_adolescencia": self.trasfondo_adolescencia,
            "trasfondo_juventud": self.trasfondo_juventud,
            "estres": self.estres, "corrupcion": self.corrupcion, "nivel": self.nivel,
            "heridas_leves": self.heridas_leves,
            "heridas_graves": self.heridas_graves,
            "heridas_muy_graves": self.heridas_muy_graves,
            "fecha_creacion": self.fecha_creacion,
        }

    @staticmethod
    def from_dict(d: dict) -> "Personaje":
        habs = d.get("habilidades", {})
        for h in TODAS_LAS_HABILIDADES:
            if h not in habs:
                habs[h] = 0
        return Personaje(
            id=d.get("id", str(uuid.uuid4())[:8]),
            nombre=d.get("nombre", ""), apodo=d.get("apodo", ""),
            numero=d.get("numero", 0), raza=d.get("raza", ""),
            profesion=d.get("profesion", ""),
            edad=d.get("edad", ""),
            atributos=d.get("atributos", {"CUE": 0, "INT": 0, "VOL": 0}),
            habilidades=habs,
            debilidad=d.get("debilidad", ""),
            motivacion=d.get("motivacion", ""),
            vicio=d.get("vicio", ""),
            equipo=d.get("equipo", ""),
            recuerdos=d.get("recuerdos", []),
            aspecto=d.get("aspecto", []),
            trasfondo_origen=d.get("trasfondo_origen", ""),
            trasfondo_ninez=d.get("trasfondo_ninez", ""),
            trasfondo_adolescencia=d.get("trasfondo_adolescencia", ""),
            trasfondo_juventud=d.get("trasfondo_juventud", ""),
            estres=d.get("estres", 0),
            corrupcion=d.get("corrupcion", 0),
            nivel=d.get("nivel", 0),
            heridas_leves=d.get("heridas_leves", 0),
            heridas_graves=d.get("heridas_graves", 0),
            heridas_muy_graves=d.get("heridas_muy_graves", 0),
            fecha_creacion=d.get("fecha_creacion",
                _datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
        )


# ══════════════════════════════════════════════════════════════════════════════
# CLASES PARA DUNGEONS (sin cambios respecto al original)
# ══════════════════════════════════════════════════════════════════════════════

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
    def from_dict(d): return Item(**d)


@dataclass
class Monstruo:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    presente: bool = True

    def to_dict(self): return self.__dict__.copy()
    @staticmethod
    def from_dict(d): return Monstruo(**d)


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
    def from_dict(d): return PNJ(**d)


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
    def from_dict(d): return EfectoMecanismo(**d)


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
        return Mecanismo(**d)


@dataclass
class Salida:
    direccion: str = ""
    room_destino_id: str = ""
    estado_hacia_destino: str = "abierta"
    estado_hacia_origen: str = "abierta"
    especial_destino_id: str = ""

    def to_dict(self): return self.__dict__.copy()
    @staticmethod
    def from_dict(d): return Salida(**d)


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
    inventario: list = field(default_factory=list)
    monedas: int = 0
    dungeon_snapshot: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id, "nombre": self.nombre, "dungeon_id": self.dungeon_id,
            "fecha_guardado": self.fecha_guardado,
            "personajes": [p.to_dict() for p in self.personajes],
            "room_actual_id": self.room_actual_id,
            "inventario": [i.to_dict() for i in self.inventario],
            "monedas": self.monedas,
            "dungeon_snapshot": self.dungeon_snapshot,
        }

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["personajes"] = [Personaje.from_dict(p) for p in d.get("personajes", [])]
        d["inventario"] = [Item.from_dict(i) for i in d.get("inventario", [])]
        return Partida(**d)

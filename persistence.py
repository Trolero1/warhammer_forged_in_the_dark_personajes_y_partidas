# persistence.py - Guardado y carga de personajes, partidas y dungeons

import json
import os
from datetime import datetime
from models import Personaje, Partida, Dungeon
from constants import PERSONAJES_DIR, SAVES_DIR, DUNGEONS_DIR


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — OPERACIONES CON PERSONAJES
# ══════════════════════════════════════════════════════════════════════════════

def guardar_personaje(personaje: Personaje):
    """Guarda un personaje en un archivo JSON."""
    if personaje.numero == 0:
        personaje.numero = obtener_siguiente_numero_personaje()
    
    nombre_base = personaje.nombre.replace(" ", "_").replace("/", "-")
    path = os.path.join(PERSONAJES_DIR, f"{nombre_base}_{personaje.id}.json")
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(personaje.to_dict(), f, ensure_ascii=False, indent=2)


def cargar_personaje(personaje_id: str) -> Personaje:
    """Carga un personaje desde su archivo JSON."""
    for fname in os.listdir(PERSONAJES_DIR):
        if fname.endswith(".json") and personaje_id in fname:
            path = os.path.join(PERSONAJES_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("id") == personaje_id:
                return Personaje.from_dict(d)
    
    for fname in os.listdir(PERSONAJES_DIR):
        if fname.endswith(".json"):
            path = os.path.join(PERSONAJES_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if str(d.get("numero")) == personaje_id or d.get("nombre") == personaje_id:
                return Personaje.from_dict(d)
    
    raise FileNotFoundError(f"Personaje con ID {personaje_id} no encontrado")


def listar_personajes() -> list[dict]:
    """Devuelve lista de todos los personajes."""
    result = []
    
    if not os.path.isdir(PERSONAJES_DIR):
        return result
    
    for fname in os.listdir(PERSONAJES_DIR):
        if fname.endswith(".json"):
            path = os.path.join(PERSONAJES_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                result.append({
                    "id": d.get("id", fname.replace(".json", "")),
                    "numero": d.get("numero", 0),
                    "nombre": d.get("nombre", "?"),
                    "raza": d.get("raza", "?"),
                    "profesion": d.get("profesion", "?"),
                    "fecha_creacion": d.get("fecha_creacion", "?"),
                })
            except Exception:
                pass
    
    result.sort(key=lambda x: x["numero"])
    return result


def eliminar_personaje(personaje_id: str):
    """Elimina un personaje."""
    for fname in os.listdir(PERSONAJES_DIR):
        if fname.endswith(".json") and personaje_id in fname:
            path = os.path.join(PERSONAJES_DIR, fname)
            if os.path.exists(path):
                os.remove(path)
                return


def obtener_siguiente_numero_personaje() -> int:
    """Devuelve el siguiente número disponible para un personaje."""
    max_n = 0
    if os.path.isdir(PERSONAJES_DIR):
        for fname in os.listdir(PERSONAJES_DIR):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(PERSONAJES_DIR, fname), "r", encoding="utf-8") as f:
                        d = json.load(f)
                        n = d.get("numero", 0)
                        if n > max_n:
                            max_n = n
                except Exception:
                    continue
    return max_n + 1


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — OPERACIONES CON DUNGEONS (solo lectura)
# ══════════════════════════════════════════════════════════════════════════════

def listar_dungeons() -> list[dict]:
    """Devuelve lista de dungeons disponibles para jugar."""
    result = []
    
    if not os.path.isdir(DUNGEONS_DIR):
        return result
    
    for fname in os.listdir(DUNGEONS_DIR):
        if fname.endswith(".json"):
            path = os.path.join(DUNGEONS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                result.append({
                    "id": d.get("id", fname.replace(".json", "")),
                    "nombre": d.get("nombre", "?"),
                    "fecha_creacion": d.get("fecha_creacion", "?"),
                    "num_rooms": len(d.get("rooms", [])),
                })
            except Exception:
                pass
    
    result.sort(key=lambda x: x["nombre"])
    return result


def cargar_dungeon(dungeon_id: str) -> Dungeon:
    """Carga un dungeon desde su archivo JSON."""
    path = os.path.join(DUNGEONS_DIR, f"{dungeon_id}.json")
    
    with open(path, "r", encoding="utf-8") as f:
        return Dungeon.from_dict(json.load(f))


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — OPERACIONES CON PARTIDAS
# ══════════════════════════════════════════════════════════════════════════════

def guardar_partida(partida: Partida, dungeon: Dungeon):
    """Guarda una partida con snapshot del dungeon."""
    partida.fecha_guardado = datetime.now().strftime("%d/%m/%Y %H:%M")
    partida.dungeon_snapshot = dungeon.to_dict()
    
    save_dir = os.path.join(SAVES_DIR, partida.nombre)
    os.makedirs(save_dir, exist_ok=True)
    
    fname = f"{partida.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(save_dir, fname)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(partida.to_dict(), f, ensure_ascii=False, indent=2)
    
    return path


def listar_nombres_partidas() -> list[str]:
    """Devuelve lista de nombres de partidas."""
    result = []
    
    if not os.path.isdir(SAVES_DIR):
        return result
    
    for d in os.listdir(SAVES_DIR):
        if os.path.isdir(os.path.join(SAVES_DIR, d)):
            result.append(d)
    
    result.sort()
    return result


def listar_guardados_partida(nombre_partida: str) -> list[dict]:
    """Lista todos los guardados de una partida."""
    save_dir = os.path.join(SAVES_DIR, nombre_partida)
    result = []
    
    if not os.path.isdir(save_dir):
        return result
    
    for fname in os.listdir(save_dir):
        if fname.endswith(".json"):
            path = os.path.join(save_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                result.append({
                    "path": path,
                    "nombre": d.get("nombre", "?"),
                    "fecha_guardado": d.get("fecha_guardado", "?"),
                    "dungeon_nombre": d.get("dungeon_snapshot", {}).get("nombre", "?"),
                })
            except Exception:
                pass
    
    result.sort(key=lambda x: x["fecha_guardado"], reverse=True)
    return result


def cargar_guardado(path: str) -> tuple[Partida, Dungeon]:
    """Carga una partida y reconstruye el dungeon desde el snapshot."""
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    partida = Partida.from_dict(d)
    dungeon = Dungeon.from_dict(d["dungeon_snapshot"])
    
    return partida, dungeon


def eliminar_partida(nombre_partida: str):
    """Elimina una partida completa."""
    import shutil
    save_dir = os.path.join(SAVES_DIR, nombre_partida)
    if os.path.isdir(save_dir):
        shutil.rmtree(save_dir)
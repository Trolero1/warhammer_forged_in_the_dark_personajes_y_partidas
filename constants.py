# constants.py - Configuración global

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DUNGEONS_DIR = os.path.join(DATA_DIR, "dungeons")
SAVES_DIR = os.path.join(DATA_DIR, "saves")
PERSONAJES_DIR = os.path.join(DATA_DIR, "personajes")

for d in (DUNGEONS_DIR, SAVES_DIR, PERSONAJES_DIR):
    os.makedirs(d, exist_ok=True)

# Pantalla
SCREEN_W = 1400
SCREEN_H = 900
FPS = 60
TITLE = "WARHAMMER FORGED IN THE DARK"

# Colores base
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
DARK_GRAY = (40, 40, 40)
MID_GRAY = (100, 100, 100)
GREEN = (50, 200, 80)
RED = (200, 50, 50)
YELLOW = (220, 200, 50)
BLUE = (60, 120, 220)
ORANGE = (220, 130, 40)
LIGHT_GRAY = (200, 200, 200)
GOLD = (212, 175, 55)
DEEP_RED = (120, 20, 20)

# Colores Dragonbane
C_FONDO = (26, 16, 8)
C_PANEL = (42, 28, 14)
C_TITULO = (200, 146, 42)
C_SUBTITULO = (224, 192, 112)
C_TEXTO = (240, 230, 200)
C_TEXTO_DIM = (154, 128, 96)
C_BOTON = (90, 48, 16)
C_BOTON_HOV = (138, 80, 32)
C_BOTON_SEL = (200, 146, 42)
C_BOTON_TXT = (240, 230, 200)
C_BORDE = (106, 72, 32)
C_SEPARADOR = (74, 48, 16)
C_ENTRADA = (58, 37, 16)
C_ENTRADA_SEL = (90, 58, 16)
C_ERROR = (200, 80, 32)
C_VERDE = (80, 180, 80)

# Editor
ROOM_FILL = (60, 60, 60)
ROOM_BORDER = (200, 200, 200)
BG_MAP = (10, 10, 10)
BG_PANEL = (5, 5, 15)
BG_TEXT = (5, 5, 5)
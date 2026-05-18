#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Warhammer Forged in the Dark — Standalone entry point.
Delega en el módulo screens para el creador de personajes.

Puedes ejecutar este archivo directamente para abrir el creador
o usar main.py para el programa completo con dungeons y partidas.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import WarhammerGame

if __name__ == "__main__":
    game = WarhammerGame()
    game.run()

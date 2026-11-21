#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada alternativo (se mantiene por compatibilidad): arranca el
mismo programa que main.py.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import FantasyGame

if __name__ == "__main__":
    game = FantasyGame()
    game.run()

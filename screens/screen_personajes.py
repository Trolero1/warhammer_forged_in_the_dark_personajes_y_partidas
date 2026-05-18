# screens/screen_personajes.py
# Pantalla de gestión de personajes

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button, MessageDialog, ConfirmDialog, ScrollList
import persistence


class ScreenPersonajesManager:
    """Pantalla de gestión de personajes."""
    
    def __init__(self, app):
        self.app = app
        W = app.screen.get_width()
        
        # 4 botones centrados como en la pantalla principal
        btn_w, btn_h, gap = 200, 56, 24
        total_w = 4 * btn_w + 3 * gap
        start_x = W // 2 - total_w // 2
        
        # Botón CREAR (verde oscuro)
        self.btn_crear = Button((start_x, 390, btn_w, btn_h),
                                "⚔  CREAR", font_size=16, bold=True,
                                color=(106, 48, 16))
        
        # Botón CARGAR (gris)
        self.btn_cargar = Button((start_x + btn_w + gap, 390, btn_w, btn_h),
                                 "📂  CARGAR", font_size=16, bold=True)
        
        # Botón ELIMINAR (rojo oscuro)
        self.btn_eliminar = Button((start_x + 2 * (btn_w + gap), 390, btn_w, btn_h),
                                   "🗑  ELIMINAR", font_size=16, bold=True,
                                   color=C_ERROR)
        
        # Botón INICIO (azul oscuro) - vuelve a la pantalla principal
        self.btn_inicio = Button((start_x + 3 * (btn_w + gap), 390, btn_w, btn_h),
                                 "🏠  INICIO", font_size=16, bold=True,
                                 color=(40, 40, 80))
        
        self.buttons = [self.btn_crear, self.btn_cargar, self.btn_eliminar, self.btn_inicio]
    
    def handle_event(self, event):
        # Botón INICIO: vuelve a la pantalla principal
        if self.btn_inicio.handle_event(event):
            from screens.screen_main import ScreenMain
            self.app.current_screen = ScreenMain(self.app)
            return
        
        # Botón CREAR: nuevo personaje
        if self.btn_crear.handle_event(event):
            from screens.screen_personaje_creador import ScreenPersonajeCreador
            self.app.current_screen = ScreenPersonajeCreador(self.app)
        
        # Botón CARGAR: ver personaje existente
        elif self.btn_cargar.handle_event(event):
            self._cargar_personaje()
        
        # Botón ELIMINAR: borrar personaje
        elif self.btn_eliminar.handle_event(event):
            self._eliminar_personaje()
    
    def _cargar_personaje(self):
        """Muestra la lista de personajes para cargar."""
        personajes = persistence.listar_personajes()
        
        if not personajes:
            MessageDialog(self.app.screen, "No hay personajes guardados.").run()
            return
        
        idx = self._pick_personaje(personajes, "SELECCIONA PERSONAJE PARA VER")
        if idx is None:
            return
        
        personaje = persistence.cargar_personaje(personajes[idx]["id"])
        from screens.screen_ficha_personaje import ScreenFichaPersonaje
        self.app.current_screen = ScreenFichaPersonaje(self.app, personaje)
    
    def _eliminar_personaje(self):
        """Muestra la lista de personajes para eliminar."""
        personajes = persistence.listar_personajes()
        
        if not personajes:
            MessageDialog(self.app.screen, "No hay personajes guardados.").run()
            return
        
        idx = self._pick_personaje(personajes, "SELECCIONA PERSONAJE A ELIMINAR")
        if idx is None:
            return
        
        p = personajes[idx]
        if ConfirmDialog(self.app.screen, f"¿Eliminar personaje '{p['nombre']}'?").run():
            persistence.eliminar_personaje(p["id"])
            MessageDialog(self.app.screen, f"Personaje '{p['nombre']}' eliminado.").run()
    
    def _pick_personaje(self, personajes, title):
        """Muestra una lista de personajes y devuelve el índice seleccionado."""
        W, H = self.app.screen.get_width(), self.app.screen.get_height()
        rect = pygame.Rect(W // 2 - 350, H // 2 - 200, 700, 400)
        
        labels = [f"#{p['numero']} {p['nombre']} — {p['raza']} {p['profesion']}" for p in personajes]
        sl = ScrollList(rect, labels, font_size=14, title=title)
        
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                idx = sl.handle_event(event)
                if idx is not None:
                    return idx
            
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.app.screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(self.app.screen, DARK_GRAY, rect, border_radius=6)
            pygame.draw.rect(self.app.screen, GOLD, rect, 2, border_radius=6)
            
            sl.draw(self.app.screen)
            
            hint = get_font(12).render("ESC para cancelar", True, MID_GRAY)
            self.app.screen.blit(hint, (rect.x + 10, rect.bottom - 18))
            
            pygame.display.flip()
            clock.tick(30)
    
    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update_hover(mp)
    
    def draw(self, surf):
        surf.fill(C_FONDO)
        self._draw_header(surf)
        
        W = surf.get_width()
        sub = "GESTIÓN DE PERSONAJES"
        draw_text(surf, sub, W // 2 - 150, 190, 28, C_SUBTITULO, bold=True)
        
        draw_text(surf, "Crea nuevos héroes, carga personajes existentes o elimínalos",
                  W // 2 - 280, 240, 14, C_TEXTO_DIM, max_width=560)
        
        for btn in self.buttons:
            btn.draw(surf)
    
    def _draw_header(self, surf):
        W = surf.get_width()
        draw_text(surf, "WARHAMMER", W // 2 - 180, 40, 60, C_TITULO, bold=True)
        pygame.draw.line(surf, C_TITULO, (60, 130), (W - 60, 130), 2)
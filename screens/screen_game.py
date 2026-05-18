# screens/screen_game.py - Pantalla de juego

import pygame
from constants import *
from ui_utils import get_font, draw_text, Button, MessageDialog
from models import Dungeon, Partida
import persistence


def run_game(screen, partida: Partida, dungeon: Dungeon):
    """Pantalla principal del juego."""
    clock = pygame.time.Clock()
    W, H = screen.get_size()

    top_h = H * 2 // 3
    bot_h = H - top_h
    img_w = W * 2 // 3
    panel_w = W - img_w

    img_rect = pygame.Rect(0, 0, img_w, top_h)
    panel_rect = pygame.Rect(img_w, 0, panel_w, top_h)
    text_zone = pygame.Rect(0, top_h, W, bot_h)

    room = dungeon.room_por_id(partida.room_actual_id) if partida.room_actual_id else None

    text_log = ["Bienvenido a Warhammer Forged in the Dark!", "Usa los botones para moverte y actuar."]

    running = True
    save_requested = False

    dirs = ["N", "S", "E", "O", "U", "D", "Esp"]
    dir_keys = ["norte", "sur", "este", "oeste", "arriba", "abajo", "especial"]

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if ConfirmDialog(screen, "Guardar y salir?").run():
                    save_requested = True
                    running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                btn_y = text_zone.bottom - 40
                for i, d in enumerate(dirs):
                    bx = text_zone.x + 10 + i * 54
                    if pygame.Rect(bx, btn_y, 50, 30).collidepoint(mx, my):
                        if room:
                            salida = room.salida_en(dir_keys[i])
                            if salida and salida.estado_hacia_destino == "abierta":
                                dest = dungeon.room_por_id(salida.room_destino_id)
                                if dest:
                                    partida.room_actual_id = dest.id
                                    room = dest
                                    text_log.append(f"Te mueves hacia {dir_keys[i]}. Llegas a: {dest.nombre}")
                                    if len(text_log) > 20:
                                        text_log.pop(0)
                            else:
                                text_log.append(f"No hay salida al {dir_keys[i]} o esta cerrada.")

                if pygame.Rect(text_zone.x + 400, btn_y, 140, 30).collidepoint(mx, my):
                    persistence.guardar_partida(partida, dungeon)
                    text_log.append("Partida guardada.")

        screen.fill(BLACK)

        pygame.draw.rect(screen, (20, 20, 30), img_rect)
        pygame.draw.rect(screen, MID_GRAY, img_rect, 1)
        if room:
            draw_text(screen, f"#{room.numero}  {room.nombre}", img_rect.x + 10, img_rect.y + 10, 18, GOLD, bold=True)
            draw_text(screen, room.descripcion, img_rect.x + 10, img_rect.y + 40, 13, WHITE, max_width=img_w - 20)

        pygame.draw.rect(screen, BG_PANEL, panel_rect)
        pygame.draw.rect(screen, MID_GRAY, panel_rect, 1)
        draw_text(screen, "GRUPO", panel_rect.x + 10, panel_rect.y + 8, 14, GOLD, bold=True)

        y = panel_rect.y + 35
        for p in partida.personajes:
            draw_text(screen, f"#{p.numero} {p.nombre}", panel_rect.x + 10, y, 13, WHITE, bold=True)
            draw_text(screen, f"E:{p.estres}/10  C:{p.corrupcion}/10  N:{p.nivel}", panel_rect.x + 15, y + 15, 11, WHITE)
            heridas = f"L:{p.heridas_leves} G:{p.heridas_graves} MG:{p.heridas_muy_graves}"
            draw_text(screen, heridas, panel_rect.x + 15, y + 28, 11, WHITE)
            y += 48

        draw_text(screen, "INVENTARIO", panel_rect.x + 10, y + 10, 14, GOLD, bold=True)
        y += 30
        for it in partida.inventario[:5]:
            draw_text(screen, f"  {it.nombre}", panel_rect.x + 10, y, 11, WHITE)
            y += 15
        draw_text(screen, f"Monedas: {partida.monedas}", panel_rect.x + 10, y + 10, 12, YELLOW)

        pygame.draw.rect(screen, BG_TEXT, text_zone)
        pygame.draw.rect(screen, MID_GRAY, text_zone, 1)
        for i, line in enumerate(text_log[-8:]):
            draw_text(screen, line, text_zone.x + 10, text_zone.y + 8 + i * 16, 12, WHITE)

        btn_y = text_zone.bottom - 40
        for i, d in enumerate(dirs):
            bx = text_zone.x + 10 + i * 54
            salida = room.salida_en(dir_keys[i]) if room else None
            color = GREEN if (salida and salida.estado_hacia_destino == "abierta") else DEEP_RED
            pygame.draw.rect(screen, color, (bx, btn_y, 50, 30), border_radius=3)
            draw_text(screen, d, bx + 18, btn_y + 6, 16, WHITE, bold=True)

        pygame.draw.rect(screen, DARK_GRAY, (text_zone.x + 400, btn_y, 140, 30), border_radius=3)
        draw_text(screen, "Guardar", text_zone.x + 445, btn_y + 6, 14, WHITE)

        pygame.display.flip()
        clock.tick(60)

    if save_requested:
        persistence.guardar_partida(partida, dungeon)
        MessageDialog(screen, f"Partida '{partida.nombre}' guardada.").run()

    return partida, dungeon


class ConfirmDialog:
    def __init__(self, screen, message):
        self.screen = screen
        self.message = message
        self.result = None
        w, h = 400, 140
        sw, sh = screen.get_size()
        self.rect = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)

    def run(self):
        clock = pygame.time.Clock()
        btn_yes = pygame.Rect(self.rect.x + 50, self.rect.bottom - 50, 120, 36)
        btn_no = pygame.Rect(self.rect.x + 230, self.rect.bottom - 50, 120, 36)

        while self.result is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.result = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_yes.collidepoint(event.pos):
                        self.result = True
                    if btn_no.collidepoint(event.pos):
                        self.result = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.result = True
                    if event.key == pygame.K_ESCAPE:
                        self.result = False

            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, DARK_GRAY, self.rect, border_radius=8)
            pygame.draw.rect(self.screen, GOLD, self.rect, 2, border_radius=8)
            draw_text(self.screen, self.message, self.rect.x + 20, self.rect.y + 30, 16, WHITE)
            pygame.draw.rect(self.screen, GREEN, btn_yes, border_radius=4)
            pygame.draw.rect(self.screen, RED, btn_no, border_radius=4)
            draw_text(self.screen, "SI", btn_yes.x + 45, btn_yes.y + 8, 16, BLACK, bold=True)
            draw_text(self.screen, "NO", btn_no.x + 45, btn_no.y + 8, 16, BLACK, bold=True)
            pygame.display.flip()
            clock.tick(30)

        return self.result

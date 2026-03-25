import time
import pygame
import asyncio
from scripts.gui import Toolbar
from scripts.board import ChessBoard
from scripts.engine import events_engine
from scripts.players import Model
from config import TILE_SIZE

class UserPlayer:
    def __init__(self, game, color: str, enable_tips: bool = False):
        self.game = game
        self.chess_board: ChessBoard = self.game.chess_board
        self.color = color
        self.s_timer = 60 * 30
        self.timer = self.s_timer
        self.rating = 0

        self.move = None
        self.from_pos = None
        self.pending_promotion = None       
        if enable_tips:
            self.model = Model("resources\chess-q1")

    async def step(self):
        self.move = None
        self.was_tip = False
        self.running = True
        self.chess_board.dragging_piece = None
        if self.color != self.chess_board.get_turn():
            return
        
        self.create_events()
        while not self.move:
            step_timer = time.time()
            await asyncio.sleep(0)

            if not self.running:
                break

            if hasattr(self, 'model') and not self.was_tip:
                move_code = await self.get_tip()
                if move_code:
                    self.chess_board.select(move_code)
                    self.was_tip = True
            
            if self.pending_promotion:
                move_code = self.pending_promotion
                self.pending_promotion = None
                self.move = await self._draw_bar(move_code)

            self.timer -= time.time() - step_timer

        if self.running:
            self.chess_board.dragging_piece = None
            await self.chess_board.move(self.move)

        self.remove_events()
    
    def create_events(self):
        events_engine.on(str(pygame.MOUSEBUTTONDOWN))(self.handle_mouse_down)
        events_engine.on(str(pygame.MOUSEBUTTONUP))(self.handle_mouse_up)
        events_engine.on(str(pygame.MOUSEMOTION))(self.handle_mouse_move)
    
    def remove_events(self):
        events_engine.remove(str(pygame.MOUSEBUTTONDOWN), self.handle_mouse_down)
        events_engine.remove(str(pygame.MOUSEBUTTONUP), self.handle_mouse_up)
        events_engine.remove(str(pygame.MOUSEMOTION), self.handle_mouse_move)
    
    def mark_from_pos(self, new_row:int, new_col:int, moves:list):
        move_code = self.chess_board.pos_to_uci((new_col, new_row))
        moves = [move[:2] for move in moves]
        if move_code in moves:
            piece = self.chess_board.map[new_row][new_col]
            if piece != '.':
                self.chess_board.select(move_code)
                self.from_pos = None

    def set_from_pos(self, from_row:int, from_col:int, moves:list):
        self.from_pos_timer = time.time()
        if 0 <= from_col < 8 and 0 <= from_row < 8:
            piece = self.chess_board.map[from_row][from_col]
            if piece != '.':
                piece_color = 'w' if piece.isupper() else 'b'
                if piece_color == self.color:
                    move_code = self.chess_board.pos_to_uci((from_col, from_row))
                    if any(move.startswith(move_code) for move in moves):
                        self.from_pos = (from_col, from_row)
                        self.chess_board.select(move_code)
                        self.chess_board.dragging_piece = (from_row, from_col, piece)
                        self.game.play_piece_impact()
    
    def set_to_pos(self, new_row:int, new_col:int, moves:list):
        _return = self.from_pos != (new_col, new_row)
        if (0 <= new_col < 8 and 0 <= new_row < 8) and _return:
            move_code = self.chess_board.pos_to_uci(self.from_pos, (new_col, new_row))
            for move in moves:
                if len(move) > 4:
                    self.pending_promotion = move_code
                else:
                    self.move = move_code

        self.chess_board.dragging_piece = None
        self.from_pos = None   
        self.game.play_piece_impact()
    
    async def handle_mouse_down(self, event):
        """Обработка клика мыши"""
        if self.color != self.chess_board.get_turn():
            return
        
        if event.button == 3:
            if self.from_pos:
                self.chess_board.dragging_piece = None
                self.from_pos = None   
            else:
                self.game.handle_undo_move()
        elif event.button == 2:
            self.game.handle_reset_board()
        elif event.button == 1:
            col, row = self._get_board_position(event.pos)
            if (col is None) or (row is None):
                return
            
            action = self.set_to_pos if self.from_pos else self.set_from_pos
            action(row, col, self.game.chess_board.get_legal_moves())

    async def handle_mouse_up(self, event):
        """Обработка отпускания кнопки"""
        if self.color != self.chess_board.get_turn():
            return
    
        if event.button == 1 and hasattr(self, 'from_pos_timer'):
            if time.time() - self.from_pos_timer > 0.5:
                col, row = self._get_board_position(event.pos)
                if col and row and self.from_pos:
                    self.set_to_pos(row, col, self.game.chess_board.get_legal_moves())

    async def handle_mouse_move(self, event):
        """Обработка движения мыши"""
        if self.color != self.chess_board.get_turn():
            return
        
        col, row = self._get_board_position(event.pos)
        if (col is None) or (row is None):
            return
        
        if self.chess_board.dragging_piece:
            piece = self.chess_board.dragging_piece[2]
            self.chess_board.dragging_piece = (row, col, piece)
        else:
            legal_moves = self.chess_board.get_legal_moves()
            """if hasattr(self, 'mouse_pos_timer'):
                if time.time() - self.mouse_pos_timer > 2:
                    self.set_from_pos(row, col, legal_moves)
                    self.mouse_pos_timer = time.time()"""

            self.mark_from_pos(row, col, legal_moves)

    def _get_board_position(self, mouse_pos):
        """Конвертация координат мыши в доску"""
        pos_x, pos_y = mouse_pos
        pos_y -= self.game.board_margin
        
        col = pos_x // TILE_SIZE
        row = pos_y // TILE_SIZE
        if not hasattr(self, 'old_pos'):
            self.old_pos = (col, row)

        if self.old_pos != (col, row):
            self.old_pos = (col, row)
            self.mouse_pos_timer = time.time()

        return (col, row) if (0 <= col < 8 and 0 <= row < 8) else (None, None)

    async def _draw_bar(self, move_code):
        """Асинхронное отображение панели для выбора фигуры."""
        position = 'bottom' if self.chess_board.get_turn() == 'w' else 'top'
        bar = Toolbar(
            surface=self.game.screen,
            height=50,
            position=position,
            buttons_dict={
                'Ферзь': 'q',
                'Ладья': 'r',
                'Слон': 'b',
                'Конь': 'n'
            }
        )

        self.game.dim_screen()
        while True:
            self.game.clock.tick(60)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.game.quit()
                if bar.handle_event(event):
                    move_code += bar.result
                    if len(move_code) == 5:
                        return move_code
            bar.draw()
            pygame.display.flip()

    async def get_tip(self):
        """Генерация подсказки."""
        if len(self.chess_board.moves) > 0:
            legal_moves = self.chess_board.get_legal_moves()
            moves = " ".join(self.chess_board.moves)
            step = self.model.generate(moves)
            step = step.split()[-1]
            if step in legal_moves:
                self.chess_board.select(step[:2])
                from_row, from_col = self.chess_board.uci_to_pos(step[:2])
                self.from_pos = (from_col, from_row)
                piece = self.chess_board.map[from_row][from_col]
                self.chess_board.dragging_piece = (from_row, from_col, piece)
                return step
        return None
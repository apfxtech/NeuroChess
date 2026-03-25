from typing import Tuple
import chess, pygame, asyncio
from scripts.gui import ModalWindow

class ChessBoard:
    def __init__(self, game=None):
        self.game = game
        self.status = False
        self.board = chess.Board()
        self.moves = []
        self.selected_square = ""
        self.dragging_piece = None
        self.last_move_code = ""
        self.update()
        self.move_flags = ["<WHITE_WIN>", "<BLACK_WIN>", "<DRAW>", "<WHITE_PASS>", "<BLACK_PASS>", "<WHITE_TIMER>", "<BLACK_TIMER>"]

        # Таблицы позиционной оценки
        self.pawn_eval_white = [
            [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
            [5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0],
            [1.0,  1.0,  2.0,  3.0,  3.0,  2.0,  1.0,  1.0],
            [0.5,  0.5,  1.0,  2.5,  2.5,  1.0,  0.5,  0.5],
            [0.0,  0.0,  0.0,  2.0,  2.0,  0.0,  0.0,  0.0],
            [0.5, -0.5, -1.0,  0.0,  0.0, -1.0, -0.5,  0.5],
            [0.5,  1.0, 1.0,  -2.0, -2.0,  1.0,  1.0,  0.5],
            [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0]
        ]
        self.pawn_eval_black = list(reversed(self.pawn_eval_white))
        
        self.knight_eval = [
            [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0],
            [-4.0, -2.0,  0.0,  0.0,  0.0,  0.0, -2.0, -4.0],
            [-3.0,  0.0,  1.0,  1.5,  1.5,  1.0,  0.0, -3.0],
            [-3.0,  0.5,  1.5,  2.0,  2.0,  1.5,  0.5, -3.0],
            [-3.0,  0.0,  1.5,  2.0,  2.0,  1.5,  0.0, -3.0],
            [-3.0,  0.5,  1.0,  1.5,  1.5,  1.0,  0.5, -3.0],
            [-4.0, -2.0,  0.0,  0.5,  0.5,  0.0, -2.0, -4.0],
            [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0]
        ]
        
        self.bishop_eval_white = [
            [ -2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0],
            [ -1.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -1.0],
            [ -1.0,  0.0,  0.5,  1.0,  1.0,  0.5,  0.0, -1.0],
            [ -1.0,  0.5,  0.5,  1.0,  1.0,  0.5,  0.5, -1.0],
            [ -1.0,  0.0,  1.0,  1.0,  1.0,  1.0,  0.0, -1.0],
            [ -1.0,  1.0,  1.0,  1.0,  1.0,  1.0,  1.0, -1.0],
            [ -1.0,  0.5,  0.0,  0.0,  0.0,  0.0,  0.5, -1.0],
            [ -2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0]
        ]
        self.bishop_eval_black = list(reversed(self.bishop_eval_white))
        
        self.rook_eval_white = [
            [  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
            [  0.5,  1.0,  1.0,  1.0,  1.0,  1.0,  1.0,  0.5],
            [ -0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
            [ -0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
            [ -0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
            [ -0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
            [ -0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
            [  0.0,   0.0, 0.0,  0.5,  0.5,  0.0,  0.0,  0.0]
        ]
        self.rook_eval_black = list(reversed(self.rook_eval_white))
        
        self.queen_eval = [
            [ -2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0],
            [ -1.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -1.0],
            [ -1.0,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -1.0],
            [ -0.5,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -0.5],
            [  0.0,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -0.5],
            [ -1.0,  0.5,  0.5,  0.5,  0.5,  0.5,  0.0, -1.0],
            [ -1.0,  0.0,  0.5,  0.0,  0.0,  0.0,  0.0, -1.0],
            [ -2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0]
        ]
        
        self.king_eval_white = [
            [ -3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [ -3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [ -3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [ -3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
            [ -2.0, -3.0, -3.0, -4.0, -4.0, -3.0, -3.0, -2.0],
            [ -1.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -1.0],
            [  2.0,  2.0,  0.0,  0.0,  0.0,  0.0,  2.0,  2.0 ],
            [  2.0,  3.0,  1.0,  0.0,  0.0,  1.0,  3.0,  2.0 ]
        ]
        self.king_eval_black = list(reversed(self.king_eval_white))

    def load(self, fen: str) -> None:
        fen = None if fen == "" else fen
        self.board = chess.Board(fen)

    def mark(self, move_code = None):
        x, y = self.uci_to_pos(move_code[:2])
        piece = self.map[x][y]
        if len(piece) < 2:
            self.map[x][y] = ('R' if piece.isupper() else 'r') + piece

    def select(self, move_code = None):
        #print(f"Выбранна фигура: {move_code}")
        if not move_code:
            self.selected_square = None
            self.selected_piece = None

        if move_code and not (move_code in self.move_flags):
            self.update()
            self.selected_square = move_code[:2]
            self.selected_piece = self.uci_to_pos(move_code[:2])

        self.update()

    async def move(self, move_code:str) -> bool:
        """Выполняет ход, заданный в UCI-формате"""
        if self.is_game_over(move_code):
            self.status = True
            await self.check()
            return
        
        move = chess.Move.from_uci(move_code)
        if move in self.board.legal_moves:
            self.update()
            self.board.push(move)
            self.moves.append(move_code)
            self.select()
            await self.check()
    
    def pop(self) -> None:
        """Отменяет последний ход."""
        if self.moves:
            self.board.pop()
            self.moves.pop()
    
    def reset(self) -> None:
        """Сбрасывает доску в начальную позицию."""
        self.board.reset()
        self.moves = []
        self.game.player1.timer = self.game.player1.s_timer
        self.game.player2.timer = self.game.player2.s_timer
        
    def update(self):
        self.map = [row.split() for row in str(self.board).strip().split('\n')]
        self.highlight_map = [[0 for _ in range(8)] for _ in range(8)]
        
        if not self.selected_square:
            return
        try:
            square = chess.parse_square(self.selected_square)
        except ValueError:
            return

        # Отметка выбранной клетки (1)
        x_sel = chess.square_file(square)
        y_sel = 7 - chess.square_rank(square)
        if 0 <= x_sel < 8 and 0 <= y_sel < 8:
            self.highlight_map[y_sel][x_sel] = 1

        # Отметка легальных ходов (2)
        legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
        for move in legal_moves:
            to_square = move.to_square
            x, y = chess.square_file(to_square), 7 - chess.square_rank(to_square)
            if 0 <= x < 8 and 0 <= y < 8:
                self.highlight_map[y][x] = 2

        piece = self.board.piece_at(square)
        if not piece:
            return
        
        # Отметка атакованных вражеских фигур (3)
        for attacked_square in self.board.attacks(square):
            x = chess.square_file(attacked_square)
            y = 7 - chess.square_rank(attacked_square)
            if 0 <= x < 8 and 0 <= y < 8:
                attacked_piece = self.board.piece_at(attacked_square)
                # Проверяем, что фигура существует, вражеская и клетка помечена как легальный ход
                if attacked_piece and attacked_piece.color != piece.color and self.highlight_map[y][x] == 2:
                    self.highlight_map[y][x] = 3  

    def uci_to_pos(self, uci_move: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        if uci_move in self.move_flags:
            return 
        
        def move_to_col(file: str) -> int:
            return ord(file) - ord('a')

        def move_to_row(rank: str) -> int:
            return 8 - int(rank)
        
        start_file = uci_move[0]
        start_rank = uci_move[1]
        from_col = move_to_col(start_file)
        from_row = move_to_row(start_rank)

        if len(uci_move) >= 4:
            end_file = uci_move[2]
            end_rank = uci_move[3]
            to_col = move_to_col(end_file)
            to_row = move_to_row(end_rank)
            return ((from_row, from_col), (to_row, to_col))
        
        return (from_row, from_col)
    
    def pos_to_uci(self, pos_from: Tuple[int, int], pos_to: Tuple[int, int] = None) -> str:
        x, y = pos_from
        result = f"{chr(x + ord('a'))}{8 - y}"
        if pos_to:
            x, y = pos_to
            result += f"{chr(x + ord('a'))}{8 - y}"
        return result
    
    async def check(self):
        if self.is_game_over() or self.status:
            self.status = True
            await self.game.handle_save_board()
            modal = ModalWindow(
                self.game.screen,
                "Игра завершена!",
                self.get_message(),
                {"Продолжить": "c", "Новая игра": "n", "Выйти": "q"},
                width=480,
                height=220
            )
            self.update()
            enable_draw = True
            while self.game.core.running:
                await asyncio.sleep(0)
                for event in pygame.event.get():
                    if type(event) == str:
                        continue

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            enable_draw = not enable_draw
                    else:
                        modal.handle_event(event)

                if modal.result == 'c':
                    self.game.handle_player_new_game()
                    break

                elif modal.result == 'n':
                    self.reset()
                    self.update()
                    self.game.setup()
                    break
                
                elif modal.result == 'q':
                    self.game.exit()
                    break

                obj = modal.draw
                if enable_draw:
                    if obj not in self.game.core.drawing:
                        self.game.core.drawing.append(obj)
                else:
                    if obj in self.game.core.drawing:
                        self.game.core.drawing.remove(obj)

            if obj in self.game.core.drawing:
                self.game.core.drawing.remove(obj)

    def get_message(self) -> str:
        text = "Игра завершена: "
        if self.last_move_code in self.move_flags:
            text = "Соперник сообщает о завершении партии."
            if self.last_move_code == self.move_flags[0]:
                text += " Победа белых."
            elif self.last_move_code == self.move_flags[1]:
                text += " Победа чёрных."
            elif self.last_move_code == self.move_flags[2]:
                text += " Игра завершилась вничью."
            elif self.last_move_code == self.move_flags[3]:
                text += " Белые сдались."
            elif self.last_move_code == self.move_flags[4]:
                text += " Чёрные сдались."
            elif self.last_move_code == self.move_flags[5]:
                text += " Истек таймер, победа начисляется черным."
            elif self.last_move_code == self.move_flags[6]:
                text += " Истек таймер, победа начисляется белым."

        elif self.is_checkmate():
            text += "мат."
        elif self.is_stalemate():
            text += "пат."
        elif self.is_seventyfive_moves():
            text += "ничья по правилу 75 ходов."
        elif self.is_fivefold_repetition():
            text += "ничья по правилу пятикратного повторения позиции."
        elif self.is_insufficient_material():
            text += "пат из-за недостаточности материала для мата."

        text += ' Нажмите клавишу "пробел" для отображения шахматной доски.'
        return text
    
    def is_game_over(self, move_code:str=None) -> bool:
        """Проверяет, завершена ли игра."""
        results = [
            self.board.is_game_over(),
            self.is_checkmate(),
            self.is_stalemate(),
            self.is_fivefold_repetition(), 
            self.is_seventyfive_moves(), 
            self.is_insufficient_material(), 
            move_code in self.move_flags
        ]
        for result in results:
            if result:
                print("Игра завершена")
                return True
        return False
    
    def is_valid(self) -> bool:
        """Проверяет, является ли текущая доска возможной."""
        result = self.board.is_valid()
        #print(f"Ходы верны: {result}")
        return result

    def is_checkmate(self) -> bool:
        """Проверяет, является ли текущая позиция матом."""
        result = self.board.is_checkmate()
        #print(f"Мат: {result}")
        return result
    
    def is_check(self) -> bool:
        """Проверяет, находится ли текущий игрок под шахом."""
        result = self.board.is_check()
        #print(f"Шах: {result}")
        return result

    def is_stalemate(self) -> bool:
        """Проверяет, является ли текущая позиция патом."""
        result = self.board.is_stalemate()
        #print(f"Пат: {result}")
        return result

    def is_insufficient_material(self) -> bool:
        """Проверяет недостаточность материала для мата."""
        result = self.board.is_insufficient_material()
        #print(f"Недостаточность материала: {result}")
        return result

    def is_fivefold_repetition(self) -> bool:
        """Проверяет пятикратное повторение позиции."""
        return self.board.is_fivefold_repetition()

    def is_seventyfive_moves(self) -> bool:
        """Проверяет правило 75 ходов."""
        return self.board.is_seventyfive_moves()
    
    def is_attacked_by(self, color: chess.Color, square: chess.Square) -> bool:
        """Проверяет, атаковано ли поле указанным цветом."""
        return self.board.is_attacked_by(color, square)
    
    def get_legal_moves(self) -> list:
        """Возвращает список всех допустимых ходов в текущей позиции."""
        return [str(move) for move in list(self.board.legal_moves)]
    
    def get_fullmove_number(self) -> int:
        """Подсчитывает количество ходов. Начинается с 1 и увеличивается после каждого хода чёрной стороны."""
        return self.board.fullmove_number

    def get_fen(self) -> str:
        """Возвращает текущую позицию в FEN-формате."""
        return self.board.fen()
    
    def get_turn(self) -> str:
        """Возвращает цвет, который должен делать ход."""
        return 'w' if self.board.turn else 'b'

    def get_attackers(self, color: chess.Color, square: chess.Square) -> chess.SquareSet:
        """Возвращает множество фигур, атакующих заданное поле."""
        return self.board.attackers(color, square)

    def get_san(self, move: chess.Move) -> str:
        """Преобразует ход в SAN-нотацию."""
        return self.board.san(move)

    def get_outcome(self) -> chess.Outcome:
        """Возвращает результат игры (если игра завершена)."""
        return self.board.outcome()

    def get_pgn(self) -> str:
        """Генерирует PGN-представление игры."""
        game = chess.pgn.Game.from_board(self.board)
        return str(game)

    def get_shredder_fen(self) -> str:
        """Возвращает Shredder FEN текущей позиции."""
        return self.board.shredder_fen()

    def get_epd(self) -> str:
        """Возвращает EPD текущей позиции."""
        return self.board.epd()
    
    def parse_san(self, san: str) -> chess.Move:
        """Преобразует SAN-нотацию хода в объект Move."""
        return self.board.parse_san(san)
    
    '''def can_claim_draw(self) -> bool:
        """Можно ли заявить ничью."""
        return self.board.can_claim_draw()

    def can_claim_threefold_repetition(self) -> bool:
        """Проверяет возможность заявления ничьи по трёхкратному повторению."""
        return self.board.can_claim_threefold_repetition()

    def can_claim_fifty_moves(self) -> bool:
        """Проверяет возможность заявления ничьи по правилу 50 ходов."""
        return self.board.can_claim_fifty_moves()'''


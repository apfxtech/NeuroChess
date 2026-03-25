import json
import chess
import random
import time
import pygame
import numpy as np
from scripts.gui import Toolbar
from scripts.utils import get_resource_path
from scripts.board import ChessBoard

PLAYER_DELAY = 0.5

class Model:
    _instances = {}
    def __new__(cls, _path: str):
        if _path not in cls._instances:
            instance = super(Model, cls).__new__(cls)
            instance.__init__(_path)
            cls._instances[_path] = instance
        return cls._instances[_path]

    def __init__(self, _path: str):
        # Инициализация выполняется только один раз
        if hasattr(self, '_initialized'):
            return
        
        # Оригинальная логика инициализацнейросети
        import onnxruntime as rt
        path = get_resource_path(_path)
        self.session = rt.InferenceSession(path + "/model.onnx")
        self.tokenizer = self.Tokenize(path)
        self.input_name = self.session.get_inputs()[0].name
        
        self._initialized = True  # Флаг инициализацнейросети

    class Tokenize:
        def __init__(self, model_path):
            with open(model_path + '/tokenizer.json', 'r') as t:
                self.jtokenizer = json.load(t)
                self.model = self.jtokenizer['model']['vocab']

        def ids(self, input_str):
            tokens = input_str.split()
            token_ids = [self.model.get(token, self.model["[UNK]"]) for token in tokens]
            return token_ids

        def str(self, input_ids):
            result = ""
            for token_id in input_ids:
                for key, value in self.model.items():
                    if value == token_id:
                        result += key + " "
                        break
            return result.strip()

    def generate(self, input_string):
        token_ids = self.tokenizer.ids(input_string)
        input_array = np.array(token_ids, dtype=np.int64).reshape(1, -1)
        attention_mask = np.ones(input_array.shape, dtype=np.int64)
        position_ids = np.arange(input_array.shape[1]).reshape(1, -1)
        input_feed = {
            self.input_name: input_array,
            'attention_mask': attention_mask,
            'position_ids': position_ids
        }
        pred_onx = self.session.run(None, input_feed)[0]
        token_ids = np.argmax(pred_onx, axis=-1).flatten()
        decoded_text = self.tokenizer.str(token_ids)
        return decoded_text

class NeuroPlayer():
    def __init__(self, game, color: str, path: str):
        self.game = game
        self.chess_board:  ChessBoard = self.game.chess_board
        self.model = Model(path)
        self.color = color
        self.s_timer = (PLAYER_DELAY + 0.12) * 75
        self.timer = self.s_timer
        self.score = 0
        self.first_random_step = True

    def step(self):
        if self.color != self.chess_board.get_turn():
            return
        
        self.running = True
        print("Очередь нейросети")
        step_timer = time.time()
        if not self.chess_board.moves:
            moves = self.chess_board.get_legal_moves()
            step = random.choice(moves)
            self.chess_board.move(step)
        else:
            moves = " ".join(self.chess_board.moves)
            step = self.model.generate(moves).split(' ')[-1]

        if self.running:
            print(f"Ход нейросети: {step}")
            self.chess_board.select(step)
            self.game.render()

        start_time = time.time()
        while time.time() - start_time < PLAYER_DELAY and self.running:           
            events = self.game.events()
            for event in events:
                if event == "timer_win":
                    self.chess_board.check(self.color)
                    return
                
        if not self.running:
            return

        self.chess_board.move(step.split(' ')[-1])
        self.game.render()
        self.timer -= time.time() - step_timer
        print(f"Время генерации: {time.time() - step_timer}")
        if self.timer < 0.0:
            self.timer = 0

class MinimaxPlayer:
    def __init__(self, game, color):
        self.game = game
        self.chess_board: ChessBoard = game.chess_board
        self.color = color
        self.s_timer = (PLAYER_DELAY + 5) * 75
        self.timer = self.s_timer
        self.score = 0
        self.depth = 4  # Увеличена глубина поиска после оптимизацнейросети

    def evaluate_board(self, board):
        total = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.get_piece_value(piece, square)
                total += value if piece.color == (self.color == 'w') else -value
        # Добавляем оценку мобильности
        mobility = len(list(board.legal_moves))
        if board.turn == (self.color == 'w'):
            total += mobility * 0.5
        else:
            total -= mobility * 0.5
        return total

    def get_piece_value(self, piece, square):
        x = chess.square_file(square)
        y = chess.square_rank(square)
        if piece.color != (self.color == 'w'):
            y = 7 - y

        if piece.piece_type == chess.PAWN:
            table = self.chess_board.pawn_eval_white if piece.color == chess.WHITE else self.chess_board.pawn_eval_black
            return 10 + table[y][x]
        elif piece.piece_type == chess.KNIGHT:
            return 30 + self.chess_board.knight_eval[y][x]
        elif piece.piece_type == chess.BISHOP:
            table = self.chess_board.bishop_eval_white if piece.color == chess.WHITE else self.chess_board.bishop_eval_black
            return 30 + table[y][x]
        elif piece.piece_type == chess.ROOK:
            table = self.chess_board.rook_eval_white if piece.color == chess.WHITE else self.chess_board.rook_eval_black
            return 50 + table[y][x]
        elif piece.piece_type == chess.QUEEN:
            return 90 + self.chess_board.queen_eval[y][x]
        elif piece.piece_type == chess.KING:
            table = self.chess_board.king_eval_white if piece.color == chess.WHITE else self.chess_board.king_eval_black
            return 900 + table[y][x]
        return 0

    def minimax_root(self):
        current_board = self.chess_board.board.copy()
        legal_moves = list(current_board.legal_moves)
        if not legal_moves:
            return None
        
        legal_moves.sort(key=lambda move: self._move_score(current_board, move), reverse=(self.color == 'w'))
        
        best_move = None
        best_value = -float('inf') if self.color == 'w' else float('inf')
        alpha = -float('inf')
        beta = float('inf')
        maximizing = self.color == 'w'
        
        for move in legal_moves:
            if not self.running:
                break
            self.game.events()
            self.game.render()
            new_board = current_board.copy()
            new_board.push(move)
            current_value = self.minimax(new_board, self.depth - 1, alpha, beta, not maximizing)
            if (maximizing and current_value > best_value) or (not maximizing and current_value < best_value):
                best_value = current_value
                best_move = move
                if maximizing:
                    alpha = max(alpha, best_value)
                else:
                    beta = min(beta, best_value)
            if alpha >= beta:
                break
        
        return best_move

    def _move_score(self, board, move):
        new_board = board.copy()
        new_board.push(move)
        return self.evaluate_board(new_board)

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        if depth == 0 or board.is_game_over():
            return self.evaluate_board(board)
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in board.legal_moves:
                new_board = board.copy()
                new_board.push(move)
                eval = self.minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                new_board = board.copy()
                new_board.push(move)
                eval = self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
        
    def step(self):
        if self.color != self.chess_board.get_turn():
            return
        
        self.running = True
        step_timer = time.time()
        print("Очередь Minimax")
        move = self.minimax_root()
        
        if move is None:
            color = "WHITE" if self.color == 'w' else "BLACK" 
            self.chess_board.move(f"<{color}_CLAIM>")
            return
        
        if self.running:
            move_code = move.uci()
            self.chess_board.select(move_code)
            self.game.render()

        start_time = time.time()
        while time.time() - start_time < PLAYER_DELAY and self.running:            
            events = self.game.events()
            if "timer_win" in events:
                self.chess_board.check(self.color)
                return
            
        if not self.running:
            return 
                        
        print(f"Ход Алгоритма: {move_code}")
        self.chess_board.move(move_code)
        self.game.render()
        self.timer -= time.time() - step_timer
        print(f"Время генерации: {time.time() - step_timer}")
        if self.timer < 0.0:
            self.timer = 0

class UserPlayer():
    def __init__(self, game, color: str):
        self.game = game
        self.move = None
        self.color = color
        self.s_timer = 60 * 30
        self.timer = self.s_timer
        self.score = 0
        self.chess_board:  ChessBoard = self.game.chess_board
        self.from_pos = (0, 0)
        
    def step(self):
        self.move = None
        self.was_tip = False
        self.running = True
        self.chess_board.dragging_piece = None
        if self.color != self.chess_board.get_turn():
            return
        
        print("Очередь игрока")
        while (not self.move) and self.running:
            step_timer = time.time()
            if hasattr(self, 'model') and not self.was_tip:
                move_code = self.get_tip()
                self.chess_board.select(move_code)
                self.was_tip = True

            events = self.game.events()
            for event in events:
                if event == "timer_win":
                    self.chess_board.check(self.color)
                    return
                
                self.events(event)
                
            self.game.render()
            self.timer -= time.time() - step_timer
            if self.timer < 0.0:
                self.timer = 0
        
        if not self.running:
            return

        print(f"Ход игрока: {self.move}")
        self.chess_board.dragging_piece = None
        self.chess_board.move(self.move)
        self.game.render()

    def events(self, event):
        pos_x, pos_y = pygame.mouse.get_pos()
        legal_moves = self.chess_board.get_legal_moves()

        if pos_x > self.game.TILE_SIZE * 8:
            return
    
        # Обработка нажатия кнопки мыши
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.from_pos = (
                pos_x // self.game.TILE_SIZE,
                pos_y // self.game.TILE_SIZE
            )
            new_col, new_row = self.from_pos
            move_code = self.chess_board.pos_to_uci((new_col, new_row))

            # Проверка совпадения с допустимыми ходами
            for legal_move in legal_moves:
                if move_code == legal_move[:2]:
                    piece = self.chess_board.map[new_row][new_col]
                    
                    if piece != '.':
                        self.chess_board.select(move_code)
                        # Сохраняем перетаскиваемую фигуру с координатами
                        self.chess_board.dragging_piece = (pos_x, pos_y, piece)
                    break

        # Обработка отпускания кнопки мыши
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.chess_board.dragging_piece:
                new_col = pos_x // self.game.TILE_SIZE
                new_row = pos_y // self.game.TILE_SIZE
                move_code = self.chess_board.pos_to_uci(self.from_pos, (new_col, new_row))

                # Проверка на допустимость хода
                for move in legal_moves:
                    if move_code == move[:4]:
                        # Обработка превращения пешки
                        if len(move) > 4:
                            self.move = self._draw_bar(move_code)
                            break
                        self.move = move_code
                        
                self.chess_board.dragging_piece = None

        # Обработка движения мыши при перетаскивании
        elif event.type == pygame.MOUSEMOTION:
            if self.chess_board.dragging_piece != "tip":
                if self.chess_board.dragging_piece:
                    new_col = pos_x // self.game.TILE_SIZE
                    new_row = pos_y // self.game.TILE_SIZE
                    _x, _y, piece = self.chess_board.dragging_piece
                    # Обновляем позицию перетаскиваемой фигуры
                    self.chess_board.dragging_piece = (pos_x, pos_y, piece)
                else:
                    self.from_pos = (
                        pos_x // self.game.TILE_SIZE,
                        pos_y // self.game.TILE_SIZE
                    )
                    new_col, new_row = self.from_pos
                    move_code = self.chess_board.pos_to_uci((new_col, new_row))
                    
                    # Подсветка допустимых ходов при наведении
                    for legal_move in legal_moves:
                        if move_code == legal_move[:2]:
                            piece = self.chess_board.map[new_row][new_col]
                            
                            if piece != '.':
                                self.chess_board.select(move_code)

    def _draw_bar(self, move_code):
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
            events = self.game.events()
            
            for sub_event in events:
                if type(sub_event) == str:
                    continue
                    
                if sub_event.type == pygame.QUIT:
                    self.game.quit()
                
                # Обработка выбора на панели
                if bar.handle_event(sub_event):
                    move_code += bar.result
                
                if len(move_code) == 5:
                    return move_code
                    
            bar.draw()

    def get_tip(self):
        if len(self.chess_board.moves) > 0:
            legal_moves = self.chess_board.get_legal_moves()
            print(f"Выполненные шаги: {self.chess_board.moves}")
            moves = " ".join(self.chess_board.moves)
            step = self.model.generate(moves).split(' ')[-1]
            print(f"Подсказка нейросети: {step}")
            if step in legal_moves:
                self.chess_board.dragging_piece = "tip"
                return step
    
    def enable_tips(self, path: str):
        self.model = Model(path)
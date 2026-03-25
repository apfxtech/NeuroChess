import chess
import time
import asyncio
from scripts.board import ChessBoard

class MinimaxPlayer:
    def __init__(self, game, color, _value: bool = False):
        self.game = game
        self.chess_board: ChessBoard = game.chess_board
        self.color = color
        self.s_timer = 3 * 75
        self.timer = self.s_timer
        self.rating = 0

        self.depth = 3

    async def evaluate_board(self, board):
        total = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = await self.get_piece_value(piece, square)
                total += value if piece.color == (self.color == 'w') else -value
        
        mobility = len(list(board.legal_moves))
        if board.turn == (self.color == 'w'):
            total += mobility * 0.5
        else:
            total -= mobility * 0.5
        
        return total

    async def get_piece_value(self, piece, square):
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

    async def minimax_root(self):
        current_board = self.chess_board.board.copy()
        legal_moves = list(current_board.legal_moves)
        if not legal_moves:
            return None

        move_scores = []
        for move in legal_moves:
            score = await self._move_score(current_board, move)
            move_scores.append((move, score))

        move_scores.sort(key=lambda x: x[1], reverse=(self.color == 'w'))
        legal_moves = [move for move, _ in move_scores]

        best_move = None
        best_value = -float('inf') if self.color == 'w' else float('inf')
        alpha = -float('inf')
        beta = float('inf')
        maximizing = self.color == 'w'

        for move in legal_moves:
            await asyncio.sleep(0)
            if not self.running:
                break

            new_board = current_board.copy()
            new_board.push(move)
            current_value = await self.minimax(new_board, self.depth - 1, alpha, beta, not maximizing)
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

    async def _move_score(self, board, move):
        new_board = board.copy()
        new_board.push(move)
        return await self.evaluate_board(new_board)

    async def minimax(self, board, depth, alpha, beta, maximizing_player):
        if depth == 0 or board.is_game_over():
            return await self.evaluate_board(board)
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in board.legal_moves:
                new_board = board.copy()
                new_board.push(move)
                eval = await self.minimax(new_board, depth - 1, alpha, beta, False)
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
                eval = await self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
        
    async def step(self):
        if self.color != self.chess_board.get_turn():
            return
        
        await asyncio.sleep(1)
        self.running = True
        step_timer = time.time()
        for i in range(2):
            move = await self.minimax_root()
            if move is None:
                self.depth += 1
            
        if move is None:
            color = "WHITE" if self.color == 'w' else "BLACK" 
            await self.chess_board.move(f"<{color}_PASS>")
            return
        
        if self.running:
            move_code = move.uci()
            self.chess_board.select(move_code)
            await asyncio.sleep(0.8)
            animation = self.chess_board.uci_to_pos(move_code)
            if animation:
                from_pos, to_pos = animation
                self.game.make_move(from_pos, to_pos)
                self.game.play_piece_move()
            await self.chess_board.move(move_code)
            self.timer -= time.time() - step_timer
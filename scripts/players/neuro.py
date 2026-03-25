import random
import time
import asyncio
from scripts.board import ChessBoard
from scripts.players import Model

class NeuroPlayer():
    def __init__(self, game, color:str, path:str):
        self.game = game
        self.chess_board:  ChessBoard = self.game.chess_board
        self.model = Model(path)
        self.color = color
        self.s_timer = 75
        self.timer = self.s_timer
        self.rating = 0

    async def step(self):
        if self.color != self.chess_board.get_turn():
            return

        await asyncio.sleep(1)
        self.running = True
        step_timer = time.time()
        if not self.chess_board.moves:
            moves = self.chess_board.get_legal_moves()
            step = random.choice(moves)
        else:
            moves = " ".join(self.chess_board.moves)
            step = self.model.generate(moves)
            step = step.split()[-1]

        if self.running:
            self.chess_board.select(step)
            await asyncio.sleep(0.8)
            animation = self.chess_board.uci_to_pos(step)
            if animation:
                from_pos, to_pos = animation
                self.game.make_move(from_pos, to_pos)
                self.game.play_piece_move()
            await self.chess_board.move(step)
            self.timer -= time.time() - step_timer

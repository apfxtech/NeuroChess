import asyncio
import aiofiles
import pygame
import time
import math
import json
import webbrowser

from datetime import datetime
from scripts.board import ChessBoard
from scripts.players import NeuroPlayer, UserPlayer, MinimaxPlayer, Model
from scripts.gui import ModalWindow
from scripts.board import ChessBoard

from config import SCREEN_SIZE, BOARD_SIZE, TILE_SIZE, COLORS, EVENTS
from scripts.engine import events_engine, get_resource_path

VERSION = "(Alpha 2.0.2)"

class Core:
    def __init__(self):
        self.running = True
        self.framerate = 90
        self.drawing = []

        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption(f"NeuroChess {VERSION} by apfx32")
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.screen.fill((10, 10, 10))
        self.load_assets()

        self.game = Game(self)
        events_engine.on('256')(self.exit)

    def load_assets(self):
        def load_image(file_path):
            image = pygame.image.load(get_resource_path(file_path)).convert_alpha()
            original_width, original_height = image.get_size()
            new_width = TILE_SIZE // 1.5
            new_height = int(original_height * (new_width / original_width))
            return pygame.transform.scale(image, (new_width, new_height))
        
        def load_sound(file_path):
            file_path = get_resource_path(file_path)
            return pygame.mixer.Sound(file_path)

        font_path = get_resource_path('resources/fonts/PressStart2P.ttf')
        self.font = pygame.font.Font(font_path if font_path else 'couriernew', 14)      

        self.images = {}
        images = {
            "icon": "icon.png",
            "arrow0": "element/arrow0.png", "arrow1": "element/arrow1.png",
            "emptyBase": "element/emptyBase.png", "shadow": "element/shadow.png",
            "rpb": "pieces/Red/pawnBack.png", "rrb": "pieces/Red/rookBack.png",
            "rnb": "pieces/Red/knightBack.png", "rbb": "pieces/Red/bishopBack.png",
            "rkb": "pieces/Red/kingBack.png",  "rqb": "pieces/Red/queenBack.png",
            "rpf": "pieces/Red/pawnFront.png", "rrf": "pieces/Red/rookFront.png",
            "rnf": "pieces/Red/knightFront.png", "rbf": "pieces/Red/bishopFront.png",
            "rkf": "pieces/Red/kingFront.png", "rqf": "pieces/Red/queenFront.png",
            "wpb": "pieces/White/pawnBack.png", "wrb": "pieces/White/rookBack.png",
            "wnb": "pieces/White/knightBack.png", "wbb": "pieces/White/bishopBack.png",
            "wkb": "pieces/White/kingBack.png",  "wqb": "pieces/White/queenBack.png",
            "wpf": "pieces/White/pawnFront.png", "wrf": "pieces/White/rookFront.png",
            "wnf": "pieces/White/knightFront.png", "wbf": "pieces/White/bishopFront.png",
            "wkf": "pieces/White/kingFront.png", "wqf": "pieces/White/queenFront.png",
            "bpb": "pieces/Blue/pawnFront.png", "brb": "pieces/Blue/rookFront.png",
            "bnb": "pieces/Blue/knightFront.png", "bbb": "pieces/Blue/bishopFront.png",
            "bkb": "pieces/Blue/kingFront.png", "bqb": "pieces/Blue/queenFront.png",
            "bpf": "pieces/Blue/pawnFront.png", "brf": "pieces/Blue/rookFront.png",
            "bnf": "pieces/Blue/knightFront.png", "bbf": "pieces/Blue/bishopFront.png",
            "bkf": "pieces/Blue/kingFront.png", "bqf": "pieces/Blue/queenFront.png"
        }
        for obj, path in images.items():
            path = "resources/images/" + path
            self.images[obj] = load_image(path)

        pygame.display.set_icon(self.images['icon'])

        self.sounds = {}
        sfx = {
            "piece-impact1":"resources/sfx/piece-impact1.mp3", "piece-impact2":"resources/sfx/piece-impact2.mp3",
            "piece-move1":"resources/sfx/piece-move1.mp3", "piece-move2":"resources/sfx/piece-move2.mp3",
        }
        for obj, path in sfx.items():
            self.sounds[obj] = load_sound(path)

    def play_sfx(self, name:str, replay=0):
        try:
            self.sounds[name].play(replay)
        except Exception as e:
            print(e)

    def create_task(self, task):
        self.tasks.append(asyncio.create_task(task()))

    def update_caption(self):
        if not hasattr(self, '_update_caption_timer'):
           self._update_caption_timer = time.time()

        if time.time() - self._update_caption_timer > 1:
            caption = f"NeuroChess, FPS: {self.fps:.2f}"
            pygame.display.set_caption(caption)
            self._update_caption_timer = time.time()

    async def render(self):
        while self.running:
            start_time = time.time()
            if self.game.game_mode:
                self.game.draw_background()
                self.game.draw_pieces()
                
            for obj in self.drawing:
                obj()

            pygame.display.update()
            elapsed = time.time() - start_time
            delay = max(0, 1/self.framerate - elapsed)

            await asyncio.sleep(delay)            
            self.clock.tick(self.framerate)
            self.fps = self.clock.get_fps()
            self.update_caption()

    async def events(self):
        while self.running:
            await asyncio.sleep(0.01)
            for event in pygame.event.get():
                await events_engine.trigger(str(event.type), event)
    
    async def players(self):
        """Handle player actions asynchronously"""
        while self.running:
            await asyncio.sleep(0.05)
            game = self.game
            if game.game_mode:
                if hasattr(game, 'player1') and hasattr(game, 'player2'):
                    if game.player1 and game.player2:
                        await game.player1.step()
                        await game.player2.step()
                        await game.handle_save_board()

    async def run(self):
        self.tasks = [
            asyncio.create_task(self.render()),
            asyncio.create_task(self.events()),
            asyncio.create_task(self.players()),
            asyncio.create_task(self.game.setup())
        ]
        try: await asyncio.gather(*self.tasks)
        except asyncio.exceptions.CancelledError: pass
        self.running = False
    
    async def exit(self, event):
        self.running = False
        for task in self.tasks:
            task.cancel()
        pygame.quit()

class Game:
    def __init__(self, core:Core):
        self.chess_board = ChessBoard(self)
        self.game_mode = False
        self.framerate = 60
        self.active_animations = []

        self.core = core        
        self.screen = core.screen
        self.height = core.screen.get_height()
        self.width = core.screen.get_width()
        self.board_margin = self.height - BOARD_SIZE - TILE_SIZE // 5
        self.images = core.images
        self.font = core.font

        self.player_types = {
            'human':    (UserPlayer, False),                    # игрок
            'cyber':    (UserPlayer, True),                     # игрок с помощью нейросети
            'martin':   (MinimaxPlayer, ""),                    # минимакс алгоритм
            'neuro':    (NeuroPlayer, "resources/chess-o1"),    # нейросеть полная
            'master':   (NeuroPlayer, "resources/chess-q1"),    # нейросеть сжатая
        }

        self.play_piece_impact_counter = 1
        self.play_piece_move_counter = 1
    
    def play_piece_impact(self):
        self.play_piece_impact_counter = 2 if self.play_piece_impact_counter == 1 else 1
        self.core.play_sfx(f"piece-impact{self.play_piece_impact_counter}")
    
    def play_piece_move(self):
        self.play_piece_move_counter = 2 if self.play_piece_move_counter == 1 else 1
        self.core.play_sfx(f"piece-move{self.play_piece_move_counter}")
    
    def draw_background(self, update:bool=False):
        margin = self.board_margin
        def draw_tile(color, row, col, trim: bool = False):
            color_tile = COLORS['light'] if color == 'light' else COLORS['dark']
            color_trim = COLORS['light_dim'] if color == 'dark' else COLORS['dark_dim']
            pygame.draw.rect(
                self.screen, 
                color_trim if trim else color_tile, 
                (col * TILE_SIZE, row * TILE_SIZE + margin, TILE_SIZE, TILE_SIZE)
            )

        if (not update) and hasattr(self, '_cached_background'):
            self.screen.blit(self._cached_background, (0, 0))
            return
        
        self.screen.fill((10, 10, 10))
        for row in range(9):
            for col in range(8):
                color = 'light' if (row + col) % 2 == 0 else 'dark'
                draw_tile(color, row, col, row == 8)

        self._cached_background = self.screen.copy()
        
    def draw_piece(self, piece:str, row:int, col:int, alpha:int = 255, arrow:bool = False, shadow:bool = False, label:str = ''):
        _piece = piece[1] if len(piece) > 1 else piece
        if _piece in ['', '.']:
            return
        
        if not hasattr(self, 'draw_piece_timer'):
            self.draw_piece_timer = time.time()
            self.draw_piece_itter = 0

        image = self.images[piece]
        image.set_alpha(alpha)
        image_rect = image.get_rect()
        image_rect.midbottom = (col * TILE_SIZE + TILE_SIZE // 2, (row + 1) * TILE_SIZE + (self.board_margin - TILE_SIZE/6))
        tl, br = image_rect.topleft, image_rect.bottomright

        if shadow:
            self.draw_piece('shadow', row, col, alpha=230, shadow=False)
            self.draw_piece(piece, row - 0.25, col, alpha=alpha, arrow=False, shadow=False)
        else:
            self.screen.blit(image, image_rect.topleft)
            if arrow:
                center_x, center_y = image_rect.center
                if time.time() - self.draw_piece_timer > 0.5:
                    self.draw_piece_timer = time.time()
                    self.draw_piece_itter += 1

                arrow_image = self.images['arrow0'] if self.draw_piece_itter % 2 == 0 else self.images['arrow1']
                arrow_rect = arrow_image.get_rect()
                piece_type = (piece if len(piece) == 1 else piece[1]).lower()
                arrow_k = 48 if piece_type == 'p' else 26
                arrow_rect.midbottom = (center_x, center_y - image_rect.height // 2 + arrow_k)
                self.screen.blit(arrow_image, arrow_rect.topleft)
            
            if label != '':
                lines = label.split('\n')
                line_height = self.font.get_height()
                y_position = br[1] + 18
                line_count = 0  # Счетчик непустых строк
                
                for line in lines:
                    if not line:  # Пропускаем пустые строки
                        continue
                    line_count += 1  # Увеличиваем только для видимых строк
                    
                    # Определяем цвет текста для четных строк
                    text_color = (218, 56, 65) if line_count % 2 == 0 else (255, 255, 255)
                    
                    # Создаем поверхности для текста и тени
                    text_surface = self.font.render(line, True, text_color)
                    shadow_surface = self.font.render(line, True, (0, 0, 0))
                    
                    # Вычисляем позицию для текущей строки
                    text_rect = text_surface.get_rect(
                        centerx=(tl[0] + br[0]) // 2,
                        top=y_position
                    )
                    
                    # Рисуем тень со смещением
                    self.screen.blit(shadow_surface, text_rect.move(2, 2))
                    # Рисуем основной текст
                    self.screen.blit(text_surface, text_rect)
                    
                    # Сдвигаем позицию для следующей строки
                    y_position += line_height + 6

            mouse = pygame.mouse.get_pos()
            return tl[0] <= mouse[0] <= br[0] and tl[1] <= mouse[1] <= br[1]

    def draw_pieces(self):
        """Отрисовать все шахматные фигуры на доске"""
        def get_piece_color(piece:str, red:bool=False) -> str:
            color = 'r' if red else ('b' if piece.islower() else 'w')
            return color + piece.lower() + ('f' if piece.islower() else 'b')
    
        current_time = pygame.time.get_ticks() / 1000
        self.active_animations = [anim for anim in self.active_animations if current_time - anim['start_time'] < anim['duration']]
        dragging_piece = self.chess_board.dragging_piece 
        
        for row in range(8):
            for col in range(8):
                skip = False
                for anim in self.active_animations:
                    if ((anim['from_row'], anim['from_col']) == (row, col) or
                        (anim['to_row'], anim['to_col']) == (row, col)) and \
                        (current_time - anim['start_time'] < anim['duration']):
                        skip = True
                        break
                if skip:
                    continue
                
                color_code = self.chess_board.highlight_map[row][col] if hasattr(self.chess_board, 'highlight_map') else None
                is_dragging_piece = dragging_piece and dragging_piece[0] == row and dragging_piece[1] == col
                is_highlights_piece = color_code and self.chess_board.selected_piece

                # Отрисовка подсветки
                if color_code:
                    overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    overlay.fill(COLORS['highlights'][color_code-1])
                    self.screen.blit(overlay, (col * TILE_SIZE, row * TILE_SIZE + self.board_margin))

                # Отрисовка передвигаемой фигуры (dragging)
                if is_dragging_piece:
                    if color_code and color_code == 1:
                        src_row, src_col = self.chess_board.selected_piece
                        piece = self.chess_board.map[src_row][src_col]
                        piece = get_piece_color(piece)
                        self.draw_piece(piece, row, col, 180, True)
                    else:
                        x, y, piece = dragging_piece
                        piece = get_piece_color(piece, red=not color_code in [2, 3])
                        self.draw_piece(piece, x, y, 230, shadow=True)    
                
                # Отрисовка подсвечиваемых фигур
                elif is_highlights_piece:
                    src_row, src_col = self.chess_board.selected_piece
                    piece = self.chess_board.map[src_row][src_col]
                    piece = get_piece_color(piece)

                    if color_code == 1:
                        self.draw_piece(piece, row, col, 180, True)
                    elif color_code == 2:
                        if not self.is_user_turn():
                            self.draw_piece(piece, row, col, 40)
                    elif color_code == 3:
                        piece = self.chess_board.map[row][col]
                        piece = get_piece_color(piece, red=(len(piece) < 2))
                        self.draw_piece(piece, row, col, 180)
                                
                # Отрисовка остальных фигур
                else:       
                    piece = self.chess_board.map[row][col]
                    piece = get_piece_color(piece)
                    self.draw_piece(piece, row, col)
        
        # Отрисовка анимированных фигур
        for anim in self.active_animations:
            elapsed = current_time - anim['start_time']
            progress = elapsed / anim['duration']
            progress = self.ease_in_out(progress)
            if anim['piece'].lower() == 'n':
                dr = anim['to_row'] - anim['from_row']
                dc = anim['to_col'] - anim['from_col']
                if abs(dr) == 2:
                    mid_row = anim['to_row']
                    mid_col = anim['from_col']
                else:
                    mid_row = anim['from_row']
                    mid_col = anim['to_col']
                
                if progress < 0.5:
                    # Движение к промежуточной точке
                    current_row = anim['from_row'] + (mid_row - anim['from_row']) * (progress * 2)
                    current_col = anim['from_col'] + (mid_col - anim['from_col']) * (progress * 2)
                else:
                    # Движение от промежуточной точки к конечной
                    current_row = mid_row + (anim['to_row'] - mid_row) * ((progress - 0.5) * 2)
                    current_col = mid_col + (anim['to_col'] - mid_col) * ((progress - 0.5) * 2)
            else:
                # Линейная анимация для других фигур
                current_row = anim['from_row'] + (anim['to_row'] - anim['from_row']) * progress
                current_col = anim['from_col'] + (anim['to_col'] - anim['from_col']) * progress
            
            piece = anim['piece']
            piece = get_piece_color(piece)
            self.draw_piece(piece, current_row-0.25, current_col, 230, shadow=True)

    def ease_in_out(self, t):
        """Функция плавности для ускорения и замедления"""
        return 0.5 * (1 - math.cos(t * math.pi))

    def make_move(self, from_pos, to_pos):
        """Добавление анимации при перемещении фигуры"""
        piece = self.chess_board.map[from_pos[0]][from_pos[1]]
        self.chess_board.map[from_pos[0]][from_pos[1]] = ''
        self.chess_board.map[to_pos[0]][to_pos[1]] = piece
        
        # Добавление анимации
        self.active_animations.append({
            'from_row': from_pos[0],
            'from_col': from_pos[1],
            'to_row': to_pos[0],
            'to_col': to_pos[1],
            'start_time': pygame.time.get_ticks() / 1000,
            'duration': 0.4, 
            'piece': piece
        })
            
    def select_player(self, type: str):
        player_type, value = self.player_types.get(type.lower())
        color = 'b' if hasattr(self, 'player1') else 'w'
        player = player_type(self, color, value)
        if isinstance(player, NeuroPlayer):
            if not player.model.check(value):
                return 
            
        if not hasattr(self, 'player1'):
            self.player1 = player 
        elif not hasattr(self, 'player2'):
            self.player2 = player
    
    def is_user_turn(self):
        return self.chess_board.get_turn() in self.get_colors_user()
    
    def get_colors_user(self):
        users_colors = []
        if isinstance(self.player1, UserPlayer):
            users_colors.append(self.player1.color)
        if isinstance(self.player2, UserPlayer):
            users_colors.append(self.player2.color)
        return users_colors

    def handle_player_new_game(self):
        color_pl1 = self.player1.color
        color_pl2 = self.player2.color
        self.player1.color = color_pl2
        self.player2.color = color_pl1
        self.chess_board.status = False
        self.chess_board.reset()
        self.chess_board.update()

    def handle_undo_move(self):
        self.player1.running = False
        self.player2.running = False
        self.chess_board.status = False
        self.chess_board.pop()
        self.chess_board.update()

    def handle_reset_board(self):
        self.player1.running = False
        self.player2.running = False
        self.chess_board.status = False
        self.chess_board.reset()
        self.chess_board.update()
    
    async def handle_save_board(self):
        """Сохранение игры"""
        def get_player_type(player):
            types = ['human', 'martin', 'neuro', 'cyber']
            players = [UserPlayer, MinimaxPlayer, NeuroPlayer]
            for obj in players:
                if isinstance(player, obj):
                    index = players.index(obj)
                    if index == 1 and hasattr(player, 'model'):
                        index = 4
                    return types[index] 
        
        path = get_resource_path("resources/save.json", not_exist=True)
        async with aiofiles.open(path, 'r') as f:
            data = json.loads(await f.read())
     
        data["date"] = datetime.now().strftime("%d.%m.%Y")
        data["time"] = datetime.now().strftime("%H.%M")
        data["status"] = "..." if self.chess_board.status else "ongoing"
        data["moves"] = self.chess_board.moves
        data["fen"] = self.chess_board.get_fen()
        players_data = []
        for player in [self.player1, self.player2]:
            player_type = get_player_type(player)
            players_data.append({
                "type": player_type,
                "color": player.color,
                "timer": player.timer
            })
            if "rating" not in data:
                data["rating"] = {"human": 0,"martin": 0,"neuro": 0,"cyber": 0}
            data["rating"][player_type] = player.rating
        
        data["players"] = players_data
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(data, ensure_ascii=False))
    
    
    async def setup(self):
        """Создание новых игроков"""
        rows = [{ 
                'y': 0, 'labels': ['', '', 'Веб-сайт', '', '', 'Телеграм', '', ''],
                'urls': ['', '', 'https://aperturefox.ru', '', '', 'https://t.me/apfxchannel', '', ''],
                'is_player': False
            },{
                'y': 3, 'labels': ['', 'Human', '', '', '', '', 'Martin', ''],
                'is_player': True
            },{
                'y': 6, 'labels': ['', '', 'Neuro\n1800mb', '', '', 'Cyber\n250mb', '', ''],
                'is_player': True
        }]

        @events_engine.on('1025')
        async def handle_mouse_click(event):
            """Асинхронная бработка клика (setup_players)"""
            if self.game_mode:
                return
            mouse_pos = event.pos
            for btn in self.current_buttons:
                if btn['rect'].collidepoint(mouse_pos):
                    btn['callback']()
                    break

        while not self.game_mode:
            self.current_buttons = []
            if not hasattr(self, 'player1'):
                color_piece = 'w?f'
            elif not hasattr(self, 'player2'):
                color_piece = 'b?f'
            else:
                self.game_mode = True
                break

            self.draw_background()
            for idx_row, row in enumerate(rows):
                y = row['y']
                labels = row['labels']
                urls = row.get('urls', [])
                is_player = row['is_player']

                for col in range(len(labels)):
                    label = labels[col]
                    if label == '':
                        continue

                    grid_x = col
                    grid_y = y
                    rect = self.calculate_button_rect(grid_y, grid_x)

                    if is_player:
                        _piece = color_piece.replace('?', 'q' if "Human" in labels else 'k')
                        hover = self.draw_piece(_piece, y, grid_x, 200, label=label)
                        if hover:
                            self.draw_piece(_piece, y, grid_x, 200, arrow=True)
                        self.current_buttons.append({
                            'piece': _piece,
                            'rect': rect,
                            'callback': lambda lbl=label: self.select_player(lbl)
                        })

                    else:
                        hover = self.draw_piece('rpf', y, grid_x, 200, label=label)
                        if hover:
                            self.draw_piece('rpf', y, grid_x, 200, arrow=True)
                        self.current_buttons.append({
                            "piece": 'rpf',
                            'rect': rect,
                            'callback': lambda u=urls[col]: webbrowser.open(u)
                        })

            # Обработка hover (без клика)
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.current_buttons:
                if btn['rect'].collidepoint(mouse_pos):
                    self.draw_piece(btn['piece'], btn['rect'].x, btn['rect'].y, 200, arrow=True)

            await asyncio.sleep(0.01)
        
        self.draw_background(update=True)
        events_engine.remove('1025', handle_mouse_click)

    def calculate_button_rect(self, grid_y, grid_x):
        return pygame.Rect(
            grid_x * TILE_SIZE,
            grid_y * TILE_SIZE + self.board_margin,
            TILE_SIZE, TILE_SIZE
        )

if __name__ == '__main__':
    asyncio.run(Core().run())

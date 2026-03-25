import pygame
import time
import sys
import gc
import json
from scripts.utils import get_resource_path
from scripts.board import ChessBoard
from scripts.player import NeuroPlayer, UserPlayer, MinimaxPlayer, Model
from scripts.gui import ModalWindow, Button
import webbrowser

VERSION = "(Beta 1.8.9)"

class Game:
    TILE_SIZE = 64
    TILE_TRIM = TILE_SIZE * 1.3 + 1
    BOARD_SIZE = TILE_SIZE * 8
    COLORS = {
        'light': (228, 166, 114),
        'dark': (184, 111, 80),
        'light_dim': (194, 133, 105),
        'dark_dim': (116, 63, 57),
        'highlights': [
            (255, 255, 0, 200),
            (10, 255, 0, 75),
            (255, 0, 0, 150),
            (255, 0, 0, 200)
        ]
    }

    def __init__(self):
        self.screen = pygame.display.set_mode(
            (self.BOARD_SIZE, self.BOARD_SIZE + self.TILE_SIZE*1.5)
        )
        self.clock = pygame.time.Clock()
        self.chess_board = ChessBoard(self)
        self.images = {}
        self.game_mode = False
        
        pygame.init()
        self.screen.fill((10, 10, 10))
        pygame.display.set_caption(f"NeuroChess {VERSION} от Кравченко Ивана 3ИСП9-30")
        self.load_assets()
        self.setup()

    def load_assets(self):
        """Load all game images and icons"""  
        temp = get_resource_path('resources/fonts/PressStart2P.ttf')
        self.pixel_font = pygame.font.Font(temp if temp else 'couriernew', 14)      
        with open(get_resource_path("resources/images/load.json"), 'r') as file:
            images = json.load(file)
            for obj, path in images.items():
                path, scale = path.split(';')
                scale = scale == 'true'
                self.images[obj] = self.load_scaled_image(path, scale)

        pygame.display.set_icon(self.images['icon'])

    def load_scaled_image(self, path, scale: bool = True):
        """Load and scale an image from resources, maintaining the aspect ratio."""
        image = pygame.image.load(get_resource_path(path)).convert_alpha()
        if not scale:
            return image
        original_width, original_height = image.get_size()
        new_width = self.TILE_SIZE // 1.5
        new_height = int(original_height * (new_width / original_width))
        return pygame.transform.scale(image, (new_width, new_height))
    
    def draw_board_background(self):
        """Нарисовать базовый узор шахматной доски"""
        font = pygame.font.SysFont('Arial', 20)
        font.set_bold(200)
        for row in range(8):
            for col in range(8):
                color = 'light' if (row + col) % 2 == 0 else 'dark'
                self.draw_tile(color, row, col, row == 7)
        
    def draw_tile(self, color, row, col, trim: bool = False):
        """Draw single board tile"""
        color_tile = self.COLORS['light'] if color == 'light' else self.COLORS['dark']
        color_trim = self.COLORS['light_dim'] if color == 'dark' else self.COLORS['dark_dim']
        pygame.draw.rect(
            self.screen, 
            color_tile, 
            (col * self.TILE_SIZE, row * self.TILE_SIZE + self.TILE_TRIM, self.TILE_SIZE, self.TILE_SIZE)
        )
        if trim:
            pygame.draw.rect(
                self.screen, 
                color_trim, 
                (col * self.TILE_SIZE, (row + 1) * self.TILE_SIZE + self.TILE_TRIM, self.TILE_SIZE, self.TILE_SIZE // 5)
            )

    def draw_piece(self, piece: str, row: int, col: int, alpha: int = 255, arrow: bool = False):
        """Отрисовать шахматную фигуру на доске и вернуть координаты углов"""
        if not hasattr(self, 'draw_piece_timer'):
            self.draw_piece_timer = time.time()
            self.draw_piece_itter = 0

        if piece != '.':
            image = self.images[piece]
            image.set_alpha(alpha)
            image_rect = image.get_rect()
            image_rect.midbottom = (col * self.TILE_SIZE + self.TILE_SIZE // 2, (row + 1) * self.TILE_SIZE - 5 + self.TILE_TRIM)
            self.screen.blit(image, image_rect.topleft)
            if arrow:
                center_x, center_y = image_rect.center
                if time.time() - self.draw_piece_timer > 0.5:
                    self.draw_piece_timer = time.time()
                    self.draw_piece_itter += 1

                if self.draw_piece_itter % 2 == 0:
                    arrow_image = self.images['arrow0']
                    self.draw_piece_itter = 0
                else:
                    arrow_image = self.images['arrow1']

                arrow_rect = arrow_image.get_rect()
                arrow_k = 46 if piece.lower() in ['p', 'rp'] else 24
                arrow_rect.midbottom = (center_x, center_y - image_rect.height // 2 + arrow_k)
                self.screen.blit(arrow_image, arrow_rect.topleft)
            
            return image_rect.topleft, image_rect.bottomright
        else:
            return None, None

    def draw_pieces(self):
        """Отрисовать все шахматные фигуры на доске"""
        dragging_piece = self.chess_board.dragging_piece if self.chess_board.dragging_piece != "tip" else None
        for row in range(8):
            for col in range(8):
                color_code = self.chess_board.highlight_map[row][col] if hasattr(self.chess_board, 'highlight_map') else None
                is_dragging_piece = dragging_piece and dragging_piece[0] == row and dragging_piece[1] == col
                is_highlights_piece = color_code and self.chess_board.selected_piece

                # отрисовка подсветки
                if color_code:
                    overlay = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA)
                    overlay.fill(self.COLORS['highlights'][color_code-1])
                    self.screen.blit(overlay, (col * self.TILE_SIZE, row * self.TILE_SIZE + self.TILE_TRIM))

                # отрисовка передвигаемой фигуры
                if is_dragging_piece:  
                    if color_code and color_code == 1:
                        src_row, src_col = self.chess_board.selected_piece
                        piece = self.chess_board.map[src_row][src_col]
                        self.draw_piece(piece, row, col, 180, True)
                    else:
                        x, y, img = dragging_piece
                        self.draw_piece('shadow', x, y, 230)
                        self.draw_piece(img, x - 0.25, y, 230)    
                
                # отрисовка подсвечиваемых фигур
                elif is_highlights_piece:
                    src_row, src_col = self.chess_board.selected_piece
                    piece = self.chess_board.map[src_row][src_col]
                    # отрисовка выбранной фигуры
                    if color_code == 1:
                        self.draw_piece(piece, row, col, 180, True)

                    # отрисовка возможных фигур
                    elif color_code == 2:
                        # отрисовка фигур если текущий игрок не человек
                        if not self.is_user_turn():
                            self.draw_piece(piece, row, col, 130)

                    # отрисовка фигур под атакой
                    elif color_code == 3:
                        piece = self.chess_board.map[row][col]
                        self.draw_piece(piece, row, col, 130)
                        
                # отрисовка остальных фигур
                else:       
                    piece = self.chess_board.map[row][col]
                    self.draw_piece(piece, row, col)
    
    def select_player(self, type: int):
        value = False
        if type == 0:
            player = UserPlayer
        elif type == 2:
            player = MinimaxPlayer
        elif type == 4:
            player = NeuroPlayer
        elif type == 6:
            player = UserPlayer
            value = True
        else:
            raise ValueError("Неправильный тип игрока")

        if not hasattr(self, 'player1'):
            self.player1 = player(self, 'w', value)
        elif not hasattr(self, 'player2'):
            self.player2 = player(self, 'b', value)

    """-----------------------------------------------------------------------------------------------------------------------"""
    def is_user_turn(self):
        return self.chess_board.get_turn() in self.get_colors_user()
    
    def get_colors_user(self):
        users_colors = []
        if isinstance(self.player1, UserPlayer):
            users_colors.append(self.player1.color)
        if isinstance(self.player2, UserPlayer):
            users_colors.append(self.player2.color)
        return users_colors
    
    def update_caption(self):
        """Update window caption with FPS counter"""
        if not hasattr(self, 'uptimer'):
            self.uptimer = time.time()

        frame = self.clock.get_fps()
        steps = self.chess_board.get_fullmove_number()
        t_min = int(self.player1.timer) // 60, int(self.player2.timer) // 60
        t_sec = int(self.player1.timer % 60), int(self.player2.timer % 60)
        if self.player1.color == "w":
            timer = f"({t_min[0]}:{t_sec[0]}, {t_min[1]}:{t_sec[1]})"
        else:
            timer = f"({t_min[1]}:{t_sec[1]}, {t_min[0]}:{t_sec[0]})"

        if time.time() - self.uptimer > 0.5:
            pygame.display.set_caption(f"NeuroChess, FPS: {frame:.2f}, Steps: {steps}, Timer: {timer}")
            self.uptimer = time.time()

    def handle_player_new_game(self):
        color_pl1 = self.player1.color
        color_pl2 = self.player2.color
        self.player1.color = color_pl2
        self.player2.color = color_pl1
        self.chess_board.reset()
        self.chess_board.update()
        self.render()

    def handle_undo_move(self):
        self.chess_board.pop()
        self.chess_board.update()
        self.render()

    def handle_reset_board(self):
        self.player1.running = False
        self.player2.running = False
        self.chess_board.reset()
        self.chess_board.update()
        self.render()
    
    """-----------------------------------------------------------------------------------------------------------------------"""

    def setup(self):
        """Initialize game settings and player selection"""
        gc.collect()
        while not self.game_mode:
            if not hasattr(self, 'player1'):
                color_piece = 'player1'
            elif not hasattr(self, 'player2'):
                color_piece = 'player2'
            else:
                print(type(self.player1), type(self.player2))
                self.game_mode = True
                break

            rows = [
                {  # Верхний ряд (ссылки)
                    'y': 0.5,
                    'cols': 3,
                    'col_center': 2.5,
                    'labels': ['Веб-сайт', '', 'Телеграм'],
                    'hints': ['Веб-сайт разработчика', '', 'Телеграм канал разработчика'],
                    'urls': ['https://aperturefox.ru', '', 'https://t.me/aegis_APFX32Bot'],
                    'is_player': False
                },
                {  # Нижний ряд (игроки)
                    'y': 3.75,
                    'cols': 7 if Model.check() else 3,
                    'col_center': 0.5 if Model.check() else 2.5,
                    'labels': ['Human', '', 'Martin', '', 'Neuro', '', 'Cyper'] if Model.check() else ['Human', '', 'Martin'],
                    'hints': {
                        0: "Человек: управление с помощью мыши или сенсора. Правая кнопка отменяет ход.",
                        2: "Мартин: базовая minimax стратегия. Ходы выполняются медленно и не всегда оптимально.",
                        4: "Нейро: нейросетевая модель, обученная на >1M игр, делает ходы быстро и логично.",
                        6: "Кибер: игрок с подсказками от нейросети, подходит для обучения."
                    } if Model.check() else {
                        0: "Человек: управление с помощью мыши или сенсора. Правая кнопка отменяет ход.",
                        2: "Мартин: базовая minimax стратегия. Ходы выполняются медленно и не всегда оптимально."
                    },
                    'is_player': True
                }
            ]

            for row in rows:
                y = row['y']
                cols = row['cols']
                col_center = row['col_center']
                labels = row['labels']
            
                for col in range(cols):
                    # Определение стиля плитки и фишки
                    if row['is_player']:
                        tile_color = 'light' if col % 2 == 0 else 'dark'
                        piece = color_piece if col % 2 == 0 else '.'
                    else:
                        tile_color = 'light' if col % 2 == 0 else 'dark'
                        piece = 'RP' if col % 2 == 0 else '.'

                    # Отрисовка элементов
                    self.draw_tile(tile_color, y, col + col_center, True)
                    lt, rb = self.draw_piece(piece, y, col + col_center, 200)
                    
                    if lt:
                        label = labels[col]
                        # Отрисовка текста
                        text = self.pixel_font.render(label, True, (255,255,255))
                        text_rect = text.get_rect(
                            centerx=(lt[0]+rb[0])//2,
                            top=rb[1]+30
                        )
                        self.screen.blit(
                            self.pixel_font.render(label, True, (0,0,0)), 
                            text_rect.move(2,2)
                        )
                        self.screen.blit(text, text_rect)
                        
                        # Обработка взаимодействий
                        mouse = pygame.mouse.get_pos()
                        if lt[0] <= mouse[0] <= rb[0] and lt[1] <= mouse[1] <= rb[1]:
                            self.draw_piece(piece, y, col + col_center, 200, True)
                            if label:
                                hint = row['hints'].get(col, '') if row['is_player'] else row['hints'][col]
                                if hint: self.draw_tooltip(hint)
                            
                            # Обработка кликов
                            for e in pygame.event.get():
                                if e.type == pygame.MOUSEBUTTONDOWN:
                                    if row['is_player']:
                                        self.select_player(col)
                                    else:
                                        if row['urls'][col]: 
                                            webbrowser.open(row['urls'][col])

            self.events()
            self.render()

    def wrap_text(self, text, max_width):
        """Перенос текста на несколько строк"""
        lines = []
        words = text.split()
        current_line = []
        current_width = 0
        space_width = self.pixel_font.size(' ')[0]
        
        for word in words:
            word_width = self.pixel_font.size(word)[0]
            if current_width + word_width + (len(current_line)*space_width) > max_width:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width
                
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def draw_tooltip(self, text: str, size: int = 450):
        """Отрисовка всплывающей подсказки"""
        # Рассчет размеров
        lines = self.wrap_text(text, size)
        line_height = self.pixel_font.get_height() + 5
        padding = 15
        max_width = max(self.pixel_font.size(line)[0] for line in lines)
        total_height = line_height * len(lines) + padding*2
        
        # Позиционирование
        x = self.screen.get_width() // 2
        y = self.screen.get_height() // 1.2
        rect = pygame.Rect(0, 0, max_width + padding*2, total_height)
        rect.center = (x, y)
        
        # Фон
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        self.screen.blit(bg, rect.topleft)
        
        # Текст
        y_pos = rect.top + padding
        for line in lines:
            text = self.pixel_font.render(line, True, (255, 255, 255))
            text_rect = text.get_rect(centerx=rect.centerx, top=y_pos)
            self.screen.blit(text, text_rect)
            y_pos += line_height

        # Обводка
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
        
    def dim_screen(self, value: int = 10):
        """Dim the entire screen"""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA) 
        overlay.fill((0,0,0, value)) 
        self.screen.blit(overlay, (0, 0))

    def render(self, update_display: bool = True):
        """Main rendering method"""
        if self.game_mode:
            self.draw_board_background()
            self.draw_pieces()
            self.update_caption()
        
        if update_display:
            self.clock.tick(60)
            pygame.display.flip()
            try:
                self.screen.blit(self.images['background'], (0,0))
                self.dim_screen(90)
            except:
                self.screen.fill((10,10,10))

    def events(self):
        """Process system events"""      
        events = pygame.event.get()
        if hasattr(self, "player1") and hasattr(self, "player2"):
            if self.player1.timer == 0.0 or self.player1.timer == 0.0:
                events.append("timer_win")
            
        for event in events:
            if type(event) == str:
                continue
            
            if event.type == pygame.QUIT:
                self.quit()
        
        return events
    
    def quit(self):
        """Cleanup and exit game"""
        pygame.quit()
        sys.exit(1)

    def run(self):
        """Main game loop"""
        while self.game_mode:
            self.events()
            self.player1.step()
            self.player2.step()
            self.render()
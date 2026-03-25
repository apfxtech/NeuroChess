import pygame
import time
import sys
from scripts.utils import get_resource_path
from scripts.board import ChessBoard
from scripts.player import NeuroPlayer, UserPlayer, MinimaxPlayer
from scripts.gui import ModalWindow, Button
import webbrowser

VERSION = "(Альфа 0.7.2)"
MODEL_PATH = "resources/chess-o1"
PIECES = {
    'P': "white/Pawn.png",
    'p': "black/Pawn.png",
    'R': "white/Rook.png",
    'r': "black/Rook.png",
    'N': "white/Knight.png",
    'n': "black/Knight.png",
    'B': "white/Bishop.png",
    'b': "black/Bishop.png",
    'K': "white/King.png", 
    'k': "black/King.png",
    'Q': "white/Queen.png",
    'q': "black/Queen.png",
    '.': None
}

class Game:
    TILE_SIZE = 70
    BOARD_SIZE = TILE_SIZE * 8
    COLORS = {
        'light': (200, 162, 113),
        'dark': (139, 69, 19),
        'highlights': [
            (255, 255, 0, 200),
            (10, 255, 0, 75),
            (255, 0, 0, 150),
            (255, 0, 0, 200)
        ],
        'button_face': (200, 162, 113),
        'button_text': (0, 0, 0),
        'border_light': (255, 255, 255),
        'border_dark': (139, 69, 19),
        'title_bar': (139, 69, 19),
        'text': (0, 0, 0),
    }

    def __init__(self):
        self.running = True
        self.uptimer = 0
        self.screen_width = self.BOARD_SIZE + 220
        self.screen = pygame.display.set_mode((self.screen_width, self.BOARD_SIZE))
        self.clock = pygame.time.Clock()
        self.images = {}
        self.chess_board = ChessBoard(self)
        self.active_button = None
        
        pygame.init()
        self.screen.fill((10, 10, 10))
        pygame.display.set_caption(f"NeuroChess {VERSION} от Кравченко Ивана 3ИСП9-30")
        self.load_images()
        self.handle_start_message()
        self.setup()
    
    def handle_start_message(self):
        self.draw_board_background()
        self.dim_screen()
        modal = ModalWindow(
            self.screen,
            "Добро пожаловать в игру!",
            f"Вы можете играть против обученной нейросети локально без подключения к интернету, для этого потребуется не менее 2GB свободной оперативной памяти. Также вы можете играть против другого человека или простого алгоритма. Нейросеть обучалась на базе 1 024 000 игр, чтобы предоставлять достойный уровень соперничества. Управление: Нажатие клавиши R отменяет последний ход, клавиша E сбрасывает доску до начального состояния, клавиша Esc завершает игру. Версия: {VERSION}.",
            {"Сайт": "web", "Телеграм": "telegram", "Продолжить": "c"},
            width=520,
            height=500
        )
        while True:
            events = self.events()
            for event in events:
                if type(event) == str:
                    continue

                elif modal.handle_event(event):
                    if modal.result == 'c':
                        return
                    elif modal.result == 'telegram':
                        webbrowser.open("https://t.me/apfxchannel")
                    elif modal.result == 'web':
                        webbrowser.open("https://aperturefox.ru")
            modal.draw()

    def handle_player_selection(self):
        """Show modal window for player selection"""
        self.player1 = self.handle_player_choice('w')
        self.player2 = self.handle_player_choice('b')
        if get_resource_path(MODEL_PATH):
            self.draw_board_background()
            self.dim_screen()
            if isinstance(self.player1, UserPlayer):
                self.handle_player_enable_tips(self.player1)
            if isinstance(self.player2, UserPlayer):
                self.handle_player_enable_tips(self.player2)

    def handle_player_enable_tips(self, player):
        color = 'белые' if player.color == 'w' else 'черные'
        modal = ModalWindow(
            self.screen,
            "Загрузка...",
            f"Ваши фигуры {color}. Желаете ли вы получать советы от нейросети?",
            {"Нет": "n", "Да": "y"},
            width=470,
            height=220
        )
        while True:
            events = self.events()
            for event in events:
                if type(event) == str:
                    continue

                elif modal.handle_event(event):
                    if modal.result == 'n':
                        return 
                    elif modal.result == 'y':
                        self.show_modal_message("Загрузка...", "Инициализация нейросетевой модели соперника для проведения шахматного матча.", 0)
                        player.enable_tips(MODEL_PATH)
                        return

            modal.draw()

    def handle_player_new_game(self):
        color_pl1 = self.player1.color
        color_pl2 = self.player2.color
        self.player1.color = color_pl2
        self.player2.color = color_pl1
        self.chess_board.reset()
        self.chess_board.update()
        self.render()
        
    def handle_player_choice(self, mode: str):
        """Show modal window for player selection"""
        color = "белых" if mode == 'w' else "черных"
        modal = ModalWindow(
            self.screen,
            "Загрузка...",
            f"Кто играет за {color}? Пожалуйста, выберите участника:",
            {"Человек": "user", "Мартин": "minimax", "Нейросеть": "neuro"},
            width=470,
            height=220
        )
        while True:
            events = self.events()
            for event in events:
                if type(event) == str:
                    continue

                elif modal.handle_event(event):
                    if modal.result == 'user':
                        return UserPlayer(self, mode)
                    
                    elif modal.result == 'minimax':
                        return MinimaxPlayer(self, mode)
                    
                    elif modal.result == 'neuro':
                        try:
                            m_error = "Ошибка запуска нейросетевой модели соперника. "
                            if get_resource_path(MODEL_PATH):
                                self.show_modal_message("Загрузка...", "Инициализация нейросетевой модели соперника для проведения шахматного матча.", 0)
                                return NeuroPlayer(self, mode, path = MODEL_PATH)
                            self.show_modal_message(message =  m_error + "Файл не найден. Пожалуйста, поместите папку 'resources' рядом с приложением.")
                            self.setup()
                        except Exception as e:
                            self.show_modal_message(message =  m_error + "Возможно, системе не хватает оперативной памяти.")
                            self.setup()

            modal.draw()          

    def show_modal_message(self, title: str = "Ошибка", message: str = "Возникла неизвестная ошибка!", time: int = 5) -> ModalWindow:
        """Display error modal window"""
        modal = ModalWindow(
            self.screen,
            title,
            message,
            width=470,
            height=220,
            auto_close_time=time
        )
        if time == 0:
            modal.draw()
        else:
            while not modal.should_close():
                self.events()
                modal.draw()

    def load_images(self):
        """Load all game images and icons"""
        self.images['board'] = pygame.image.load(get_resource_path('./resources/board.png'))
        self.images['icon'] = pygame.image.load(get_resource_path('./resources/ks54.png'))
        pygame.display.set_icon(self.images['icon'])
        
        for piece, path in PIECES.items():
            if path:
                self.images[piece] = self.load_scaled_image(f"./resources/pieces/{path}")

    def load_scaled_image(self, path):
        """Load and scale an image from resources"""
        image = pygame.image.load(get_resource_path(path)).convert_alpha()
        return pygame.transform.scale(image, (self.TILE_SIZE, self.TILE_SIZE))

    def draw_board_background(self):
        """Нарисовать доску с текстурой дерева и полупрозрачными клетками, сохраняя насыщенность"""
        texture = pygame.transform.scale(self.images['board'], (self.TILE_SIZE * 8, self.TILE_SIZE * 8))
        self.screen.blit(texture, (0, 0))
        board_surface = pygame.Surface((self.TILE_SIZE * 8, self.TILE_SIZE * 8), pygame.SRCALPHA)
        
        for row in range(8):
            for col in range(8):
                color = self.COLORS['light'] if (row + col) % 2 == 0 else self.COLORS['dark']
                tile_surface = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA)
                tile_surface.fill((*color, int(250)))
                texture_tile = texture.subsurface((col * self.TILE_SIZE, row * self.TILE_SIZE, 
                                                self.TILE_SIZE, self.TILE_SIZE)).copy()
                texture_tile.blit(tile_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                board_surface.blit(texture_tile, (col * self.TILE_SIZE, row * self.TILE_SIZE))

        self.screen.blit(board_surface, (0, 0))
        font = pygame.font.SysFont('Arial', 22)
        font.set_bold(200)
        for row in range(8):
            for col in range(8):
                label_color = (129, 59, 9) if (row + col) % 2 == 0 else (170, 132, 83)
                if row == 7:
                    label = font.render(chr(97 + col).upper(), True, label_color)
                    self.screen.blit(label, (col * self.TILE_SIZE + self.TILE_SIZE - label.get_width() - 8, 
                                        row * self.TILE_SIZE + self.TILE_SIZE - label.get_height() - 4))
                if col == 0:
                    label = font.render(str(8 - row), True, label_color)
                    self.screen.blit(label, (col * self.TILE_SIZE + 4, row * self.TILE_SIZE + 4))

        self.draw_table()

    def draw_table(self):
        # Основная панель
        main_panel_width = 220
        main_panel_rect = pygame.Rect(
            self.TILE_SIZE * 8, 0,
            main_panel_width, self.TILE_SIZE * 8
        )
        # Заливка фона
        pygame.draw.rect(self.screen, self.COLORS['button_face'], main_panel_rect)
        
        # Границы основной панели
        border_width = 3
        pygame.draw.line(self.screen, self.COLORS['border_light'], 
                        (main_panel_rect.left, main_panel_rect.top), 
                        (main_panel_rect.right, main_panel_rect.top), border_width)
        pygame.draw.line(self.screen, self.COLORS['border_light'],
                        (main_panel_rect.left, main_panel_rect.top),
                        (main_panel_rect.left, main_panel_rect.bottom), border_width)
        pygame.draw.line(self.screen, self.COLORS['border_dark'],
                        (main_panel_rect.left, main_panel_rect.bottom-1),
                        (main_panel_rect.right, main_panel_rect.bottom-1), border_width)
        pygame.draw.line(self.screen, self.COLORS['border_dark'],
                        (main_panel_rect.right-1, main_panel_rect.top),
                        (main_panel_rect.right-1, main_panel_rect.bottom), border_width)

        # Заголовок панели
        header_height = 38
        header_rect = pygame.Rect(
            main_panel_rect.x, main_panel_rect.y,
            main_panel_rect.width, header_height
        )
        pygame.draw.rect(self.screen, self.COLORS['title_bar'], header_rect)
        
        # Границы заголовка
        pygame.draw.line(self.screen, self.COLORS['border_light'],
                        (header_rect.left, header_rect.top),
                        (header_rect.right, header_rect.top), border_width)
        pygame.draw.line(self.screen, self.COLORS['border_light'],
                        (header_rect.left, header_rect.top),
                        (header_rect.left, header_rect.bottom), border_width)
        pygame.draw.line(self.screen, self.COLORS['border_dark'],
                        (header_rect.left, header_rect.bottom-1),
                        (header_rect.right, header_rect.bottom-1), border_width)
        pygame.draw.line(self.screen, self.COLORS['border_dark'],
                        (header_rect.right-1, header_rect.top),
                        (header_rect.right-1, header_rect.bottom), border_width)

        # Область для ходов
        cube_padding = 10
        objects_width = main_panel_rect.width - 2*cube_padding
        cube_rect = pygame.Rect(
            main_panel_rect.x + cube_padding,
            header_rect.bottom + cube_padding,
            objects_width,
            main_panel_rect.height - header_rect.height - 160
        )
        pressed_color = tuple(max(c-20, 0) for c in self.COLORS['button_face'])
        pygame.draw.rect(self.screen, pressed_color, cube_rect)
        
        # Границы области ходов
        cube_border_width = 2
        pygame.draw.line(self.screen, self.COLORS['border_dark'],
                        (cube_rect.left, cube_rect.top),
                        (cube_rect.right, cube_rect.top), cube_border_width)
        pygame.draw.line(self.screen, self.COLORS['border_dark'],
                        (cube_rect.left, cube_rect.top),
                        (cube_rect.left, cube_rect.bottom), cube_border_width)
        pygame.draw.line(self.screen, self.COLORS['border_light'],
                        (cube_rect.left, cube_rect.bottom-1),
                        (cube_rect.right, cube_rect.bottom-1), cube_border_width)
        pygame.draw.line(self.screen, self.COLORS['border_light'],
                        (cube_rect.right-1, cube_rect.top),
                        (cube_rect.right-1, cube_rect.bottom), cube_border_width)

        # Отображение ходов в строчку с переносом
        if hasattr(self.chess_board, 'moves'):
            font = pygame.font.Font(None, 22)
            text_color = self.COLORS['button_text']
            line_height = font.get_height() + 2
            x_start = cube_rect.x + 10
            y_start = cube_rect.y + 10
            current_x, current_y = x_start, y_start
            moves = [move[2:4] for move in self.chess_board.moves]
            
            for move in moves:
                text_surf = font.render(move, True, text_color)
                text_width = text_surf.get_width()
                
                # Проверка на перенос строки
                if current_x + text_width > cube_rect.right - 10:
                    current_x = x_start
                    current_y += line_height
                    # Проверка выхода за нижнюю границу
                    if current_y + line_height > cube_rect.bottom - 10:
                        break
                # Отрисовка хода
                self.screen.blit(text_surf, (current_x, current_y))
                current_x += text_width + 5  # Отступ между ходами

        # Создание и отрисовка кнопок
        button_padding = 10
        button_spacing = 10
        button_y = cube_rect.bottom + button_padding
        
        if not hasattr(self, 'undo_btn'):
            self.undo_btn = Button(
                main_panel_rect.x + cube_padding,
                button_y,
                'Вернуть',
                'undo',
                min_width=objects_width,
                padding=20,
                height=35
            )
            self.tip_btn = Button(
                main_panel_rect.x + button_padding,
                self.undo_btn.rect.bottom + button_spacing,
                'Подсказка',
                'tip',
                min_width=objects_width,
                padding=20,
                height=35
            )
            self.reset_btn = Button(
                main_panel_rect.x + button_padding,
                self.tip_btn.rect.bottom + button_spacing,
                'Сбросить',
                'reset',
                min_width=objects_width,
                padding=20,
                height=35
            )
        
        # Отрисовка кнопок
        self.undo_btn.draw(self.screen)
        self.tip_btn.draw(self.screen)
        self.reset_btn.draw(self.screen)

    def dim_screen(self, value: int = 10):
        """Dim the entire screen"""
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA) 
        overlay.fill((0,0,0, value)) 
        self.screen.blit(overlay, (0, 0))

    def draw_highlights(self):
        """Draw movement highlights and previews"""
        if not hasattr(self.chess_board, 'highlight_map'):
            return

        for row in range(8):
            for col in range(8):
                color_code = self.chess_board.highlight_map[row][col]
                if color_code:
                    self.draw_highlight(row, col, color_code)
                    self.draw_move_preview(row, col, color_code)

    def draw_highlight(self, row, col, color_code):
        """Draw single highlight tile"""
        overlay = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA)
        overlay.fill(self.COLORS['highlights'][color_code-1])
        self.screen.blit(overlay, (col * self.TILE_SIZE, row * self.TILE_SIZE))

    def draw_move_preview(self, row, col, color_code):
        """Draw semi-transparent piece preview"""
        if color_code == 2 and self.chess_board.selected_piece:
            src_row, src_col = self.chess_board.selected_piece
            piece = self.chess_board.map[src_row][src_col]
            if piece != '.':
                img = self.images[piece].copy()
                img.set_alpha(128)
                self.screen.blit(img, (col * self.TILE_SIZE, row * self.TILE_SIZE))

    def draw_pieces(self):
        """Draw all chess pieces on the board"""
        for row in range(8):
            for col in range(8):
                piece = self.chess_board.map[row][col]
                if piece != '.':
                    self.screen.blit(self.images[piece], (col * self.TILE_SIZE, row * self.TILE_SIZE))

    def draw_dragging_piece(self):
        """Draw piece being dragged by player"""
        piece = self.chess_board.dragging_piece
        if piece and piece != "tip":
            x, y, img = piece
            self.screen.blit(self.images[img], (x - self.TILE_SIZE//2, y - self.TILE_SIZE//2))

    def update_caption(self):
        """Update window caption with FPS counter"""
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
    
    def handle_quit(self):
        self.draw_board_background()
        self.dim_screen()
        modal_buttons = {"Выйти": "quit" , "Новая игра": "new"}
        modal_width = 520

        if self.chess_board.get_fullmove_number() > 1:
            modal_buttons["Сохранить"] = "save"
            modal_width += 80
        
        modal_buttons["Продолжить"] = "continue"       
        modal = ModalWindow(
            self.screen,
            "Выход",
            "Вы уверены, что хотите выйти? Нажатие клавиши R отменяет ход, а нажатие клавиши E сбрасывает доску.",
            modal_buttons,
            width=modal_width,
            height=220
        )

        while True:
            events = self.events()
            for event in events:
                if type(event) == str:
                    continue

                elif modal.handle_event(event):
                    if modal.result == 'continue':
                        return
                    
                    elif modal.result == 'new':
                        self.handle_reset_board()
                        self.setup()
                        return

                    elif modal.result == 'quit':
                        self.quit()

                    elif modal.result == 'draw':
                        pass

            modal.draw()

    def handle_undo_move(self):
        min_moves = 0
        if isinstance(self.player1, NeuroPlayer):
            min_moves += 1
        if isinstance(self.player2, NeuroPlayer):
            min_moves += 1

        if len(self.chess_board.moves) > min_moves:
            self.dim_screen(28)
            pygame.display.flip()
            if min_moves > 0:
                self.chess_board.pop()
                self.chess_board.pop()
            else:
                self.chess_board.pop()

            time.sleep(0.12)
            self.chess_board.update()
            self.render()

    def handle_reset_board(self):
        self.dim_screen(28)
        pygame.display.flip()
        time.sleep(0.1)
        self.player1.running = False
        self.player2.running = False
        self.chess_board.reset()
        self.chess_board.update()
        self.render()

    def btn_events(self, event):
        buttons = [self.undo_btn, self.tip_btn, self.reset_btn]
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_mouse_pos = (event.pos[0], event.pos[1])
            for button in buttons:
                if button.handle_event(event, local_mouse_pos):
                    self.active_button = button
                    return False
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_button:
                local_mouse_pos = (event.pos[0], event.pos[1])
                result = self.active_button.handle_event(event, local_mouse_pos)
                if result:
                    self.result_button = result
                    self.active_button = None
                    return True
                self.active_button = None
        return False
    
    def screen_mode(self):
        if self.screen.get_width() > self.TILE_SIZE * 8:
            self.screen = pygame.display.set_mode((self.BOARD_SIZE, self.BOARD_SIZE))
            return
        
        self.screen = pygame.display.set_mode((self.screen_width, self.BOARD_SIZE))

    def events(self, futures: list = None):
        """Process system events"""      
        events = pygame.event.get()
        if hasattr(self, "player1") and hasattr(self, "player2"):
            if self.player1.timer == 0.0 or self.player1.timer == 0.0:
                events.append("timer_win")
            
        for event in events:
            if type(event) == str:
                continue
            
            if self.btn_events(event):
                if self.tip_btn.action == self.result_button:
                    if self.player1.color == self.chess_board.get_turn():
                        if isinstance(self.player1, UserPlayer):
                            self.player1.get_tip()

                    elif self.player2.color == self.chess_board.get_turn():
                        if isinstance(self.player2, UserPlayer):
                            self.player2.get_tip()
                    
                elif self.undo_btn.action == self.result_button:   
                    self.handle_undo_move()

                elif self.reset_btn.action == self.result_button:   
                    self.handle_reset_board()
                
                self.render()
            
            if event.type == pygame.QUIT:
                self.running = False
                if futures:
                    for future in futures:
                        future.cancel()

                self.quit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.handle_quit()

                elif event.key == pygame.K_r:
                    self.handle_undo_move()

                elif event.key == pygame.K_e:
                    self.handle_reset_board()

                elif event.key == pygame.K_F11:
                    self.screen_mode()
                    self.draw_board_background()
        
        return events
    
    def setup(self):
        """Initialize game settings and player selection"""
        self.draw_board_background()
        self.dim_screen()
        self.handle_player_selection()

    def render(self, update_display = True):
        """Main rendering method"""
        self.draw_board_background()
        self.draw_highlights()
        self.draw_pieces()
        self.draw_dragging_piece()
        self.update_caption()
        
        if update_display:
            self.clock.tick(60)
            pygame.display.flip()

    def run(self):
        """Main game loop"""
        while self.running:
            self.events()
            self.player1.step()
            self.player2.step()
            self.render()
    
    def quit(self):
        """Cleanup and exit game"""
        pygame.quit()
        sys.exit(1)
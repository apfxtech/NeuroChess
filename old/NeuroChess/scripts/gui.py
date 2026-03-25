import pygame
from datetime import datetime

class Button:
    COLORS = {
        'button_face': (200, 162, 113),
        'button_text': (0, 0, 0),
        'border_light': (255, 255, 255),
        'border_dark': (139, 69, 19)
    }
    
    def __init__(self, x, y, text, action, font=None, min_width=90, padding=20, height=35):
        self.text = text
        self.action = action
        self.pressed = False
        self.font = font if font else pygame.font.Font(None, 24)
        
        # Рассчитываем ширину кнопки
        text_width = self.font.size(text)[0]
        self.width = max(min_width, text_width + padding)
        self.height = height
        self.rect = pygame.Rect(x, y, self.width, self.height)

    @staticmethod
    def calculate_width(text, font, min_width, padding):
        text_width = font.size(text)[0]
        return max(min_width, text_width + padding)

    def draw(self, surface):
        # Определяем цвет фона
        fill_color = self.COLORS['button_face']
        if self.pressed:
            fill_color = tuple(max(c-20, 0) for c in fill_color)
        
        # Рисуем фон
        pygame.draw.rect(surface, fill_color, self.rect)
        
        # Определяем цвета границ
        light_color = self.COLORS['border_light'] if not self.pressed else self.COLORS['border_dark']
        dark_color = self.COLORS['border_dark'] if not self.pressed else self.COLORS['border_light']
        
        # Рисуем границы
        border_width = 2
        # Верхняя и левая границы
        pygame.draw.line(surface, light_color, 
                        (self.rect.left, self.rect.top), 
                        (self.rect.right-1, self.rect.top), border_width)
        pygame.draw.line(surface, light_color,
                        (self.rect.left, self.rect.top),
                        (self.rect.left, self.rect.bottom-1), border_width)
        # Нижняя и правая границы
        pygame.draw.line(surface, dark_color,
                        (self.rect.left, self.rect.bottom-1),
                        (self.rect.right, self.rect.bottom-1), border_width)
        pygame.draw.line(surface, dark_color,
                        (self.rect.right-1, self.rect.top),
                        (self.rect.right-1, self.rect.bottom), border_width)
        
        # Рендерим текст
        text_surf = self.font.render(self.text, True, self.COLORS['button_text'])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event, local_mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(local_mouse_pos):
                self.pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.rect.collidepoint(local_mouse_pos):
                self.pressed = False
                return self.action
            self.pressed = False
        return False

class ModalWindow:
    COLORS = {
        'background': (200, 162, 113),
        'title_bar': (139, 69, 19),
        'text': (0, 0, 0),
        'border_light': (255, 255, 255),
        'border_dark': (139, 69, 19)
    }
    
    def __init__(self, surface, title, message, buttons=None, width=400, height=200, auto_close_time=None):
        self.surface = surface
        self.title = title
        self.message = message
        self.width = width
        self.height = height
        self.buttons = []
        self.result = None
        self.start_time = datetime.now()
        self.auto_close_time = auto_close_time
        self.active_button = None
        
        # Центрируем окно
        self.x = (self.surface.get_width() - self.width) // 2
        self.y = (self.surface.get_height() - self.height) // 2
        self.window_surface = pygame.Surface((self.width, self.height))
        
        if buttons:
            button_font = pygame.font.Font(None, 24)
            button_spacing = 15
            button_min_width = 90
            button_padding = 20

            # Рассчитываем ширину кнопок
            button_widths = [
                Button.calculate_width(text, button_font, button_min_width, button_padding)
                for text in buttons.keys()
            ]
            
            total_button_width = sum(button_widths) + button_spacing * (len(buttons) - 1)
            start_x = self.width - total_button_width - 15
            button_y = self.height - 55

            # Создаем кнопки
            x = start_x
            for (text, action), width in zip(buttons.items(), button_widths):
                self.buttons.append(Button(
                    x=x, y=button_y,
                    text=text, action=action,
                    font=button_font,
                    min_width=button_min_width,
                    padding=button_padding,
                    height=35
                ))
                x += width + button_spacing

    def draw(self, time_reset=False):
        self.window_surface.fill(self.COLORS['background'])
        
        # Рисуем границы окна
        border_width = 3
        pygame.draw.rect(self.window_surface, self.COLORS['border_dark'], 
                        (0, 0, self.width, self.height), border_width)
        pygame.draw.line(self.window_surface, self.COLORS['border_light'],
                        (0, 0), (self.width-1, 0), border_width)
        pygame.draw.line(self.window_surface, self.COLORS['border_light'],
                        (0, 0), (0, self.height-1), border_width)
        
        # Рисуем заголовок
        title_bar_height = 40
        pygame.draw.rect(self.window_surface, self.COLORS['title_bar'],
                        (border_width, border_width, 
                         self.width - border_width*2, title_bar_height))
        
        title_font = pygame.font.Font(None, 28)
        text_font = pygame.font.Font(None, 24)
        
        # Заголовок
        text_surf = title_font.render(self.title, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.width//2, title_bar_height//2 + 5))
        self.window_surface.blit(text_surf, text_rect)
        
        # Текст сообщения
        message_lines = self._wrap_text(self.message, text_font, self.width - 50)
        text_height = len(message_lines) * 30
        start_y = title_bar_height + (self.height - title_bar_height - text_height) // 2
        
        for i, line in enumerate(message_lines):
            text_surf = text_font.render(line, True, self.COLORS['text'])
            text_rect = text_surf.get_rect(center=(self.width//2, start_y + i*30))
            self.window_surface.blit(text_surf, text_rect)
        
        # Рисуем кнопки
        for button in self.buttons:
            button.draw(self.window_surface)

        if time_reset:
            self.start_time = datetime.now()

        self.surface.blit(self.window_surface, (self.x, self.y))
        pygame.display.flip()
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_mouse_pos = (event.pos[0] - self.x, event.pos[1] - self.y)
            for button in self.buttons:
                if button.handle_event(event, local_mouse_pos):
                    self.active_button = button
                    return False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_button:
                local_mouse_pos = (event.pos[0] - self.x, event.pos[1] - self.y)
                result = self.active_button.handle_event(event, local_mouse_pos)
                if result:
                    self.result = result
                    self.active_button = None
                    return True
                self.active_button = None
        return False

    def should_close(self):
        if self.auto_close_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            return elapsed >= self.auto_close_time
        return False

    def _wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = font.render(word, True, self.COLORS['text'])
            word_width = word_surface.get_width()
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width + font.size(' ')[0]
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
                
        lines.append(' '.join(current_line))
        return lines

class Toolbar:
    COLORS = {
        'background': (200, 162, 113),
        'border_dark': (139, 69, 19)
    }
    
    def __init__(self, surface, height, position='bottom', buttons_dict=None, btn_width=None, align=None):
        self.surface = surface
        self.height = height
        self.position = position
        self.buttons_dict = buttons_dict or {}
        self.btn_width = btn_width
        self.align = align
        self.buttons = []
        self.result = None
        self.active_button = None
        
        self.rect = pygame.Rect(0, 0, surface.get_width(), height)
        if position == 'bottom':
            self.rect.y = surface.get_height() - height
        else:
            self.rect.y = 0
            
        self._create_buttons()
        
    def _create_buttons(self):
        padding = 10
        spacing = 5
        button_height = self.height - 20
        
        num_buttons = len(self.buttons_dict)
        if num_buttons == 0:
            return
            
        if self.btn_width is not None:
            available_width = self.rect.width - 2*padding
            total_required = self.btn_width*num_buttons + spacing*(num_buttons-1)
            
            if self.align == 'right':
                start_x = available_width - total_required + padding
            else: # left or default
                start_x = padding
        else:
            available_width = self.rect.width - 2*padding
            total_spacing = (num_buttons-1)*spacing
            self.btn_width = (available_width - total_spacing) / num_buttons
            start_x = padding

        y_pos = (self.height - button_height)//2 + self.rect.y
        
        current_x = start_x + self.rect.x
        for text, action in self.buttons_dict.items():
            btn = Button(
                x=current_x,
                y=y_pos,
                text=text,
                action=action,
                min_width=self.btn_width,
                padding=0,
                height=button_height
            )
            self.buttons.append(btn)
            current_x += self.btn_width + spacing
            
    def draw(self):
        pygame.draw.rect(self.surface, self.COLORS['background'], self.rect)
        pygame.draw.line(self.surface, self.COLORS['border_dark'],
                        (self.rect.left, self.rect.bottom-1),
                        (self.rect.right, self.rect.bottom-1), 2)
        
        for btn in self.buttons:
            btn.draw(self.surface)

        pygame.display.flip()
            
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_mouse_pos = (event.pos[0], event.pos[1])
            for button in self.buttons:
                if button.handle_event(event, local_mouse_pos):
                    self.active_button = button
                    return False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_button:
                local_mouse_pos = (event.pos[0], event.pos[1])
                result = self.active_button.handle_event(event, local_mouse_pos)
                if result:
                    self.result = result
                    self.active_button = None
                    return True
                self.active_button = None
        return False
import pygame

TILE_SIZE = 80
BOARD_SIZE = TILE_SIZE * 8
SCREEN_SIZE = (BOARD_SIZE, BOARD_SIZE + TILE_SIZE*1.5)
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
    ],
    
    'button_face': (200, 162, 113),
    'button_text': (0, 0, 0),
    'border_light': (255, 255, 255),
    'border_dark': (139, 69, 19),

    
    'text': (40, 40, 40),
    'status_ongoing': (0, 150, 0),

    'background': (200, 162, 113),
    'title_bar': (139, 69, 19),
    'text': (0, 0, 0),
    'border_light': (255, 255, 255),
    'border_dark': (139, 69, 19)
}

EVENTS = [
    pygame.QUIT
]
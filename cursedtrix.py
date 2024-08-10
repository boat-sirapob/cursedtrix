import curses
from curses import wrapper
from dataclasses import dataclass
import random
from string import digits, ascii_letters, punctuation

MS_PER_SECOND = 1000
MATRIX_MIN_LENGTH = 3
MATRIX_MAX_LENGTH = 20
MATRIX_DENSITY = 1/30
MATRIX_CHARS = digits + ascii_letters + punctuation

BACKGROUND_COLOR = 16
# FOREGROUND_COLOR = 34 # lighter green
FOREGROUND_COLOR = curses.COLOR_GREEN
HIGHLIGHT_COLOR = curses.COLOR_WHITE
MAIN_COLOR_PAIR = 1
HIGHLIGHT_COLOR_PAIR = 2

@dataclass
class Vector2:
    x: int
    y: int

class Cell:
    def __init__(self, pos: Vector2, char: str = "", ttl: int = 0):
        self.pos: Vector2 = pos
        self.char: str = char
        self.ttl: int = ttl
        self.highlight: bool = False
        
        if self.char == 0:
            self.randomize_char()
    
    def randomize_char(self):
        self.char = random.choice(MATRIX_CHARS)

    def randomize_ttl(self):
        self.ttl = random.randint(MATRIX_MIN_LENGTH, MATRIX_MAX_LENGTH)

class MatrixState:
    def __init__(self, stdscr: curses.window):
        self.stdscr = stdscr
        self.height, self.width = self.stdscr.getmaxyx()
        
        self.matrix_cells: list[list[Cell]] = []
        
        self.clear()

    def clear(self):
        self.matrix_cells = [
            [Cell(pos = Vector2(x, y)) for x in range(self.width)] for y in range(self.height)
        ]

    def resize(self):
        target_y, target_x = self.stdscr.getmaxyx()
        
        copy_cells = [[cell for cell in row] for row in self.matrix_cells]
        
        self.matrix_cells = [
            [
                copy_cells[y][x]
                    if y < self.height and x < self.width
                    else Cell(pos = Vector2(x, y))
                    for x in range(target_x)
            ]
            for y in range(target_y)
        ]
        
        self.width, self.height = target_x, target_y
        
    def update(self):
        max_yx = get_max_yx(self.stdscr)
        if self.width != max_yx.x or self.height != max_yx.y:
            self.resize()

        for y in range(self.height-2, -1, -1):
            for x in range(self.width):
                cell = self.matrix_cells[y][x]
                next_cell = self.matrix_cells[y+1][x]

                if next_cell.ttl < cell.ttl:
                    next_cell.randomize_char()
                    next_cell.highlight = True
                else:
                    next_cell.highlight = False
                next_cell.ttl = cell.ttl

                cell.ttl = max(cell.ttl - 1, 0)

        rand_xs = random.sample(range(0, self.width-1), int(MATRIX_DENSITY * self.width))
        
        for rand_x in rand_xs:
            cell = self.matrix_cells[0][rand_x]
            if cell.ttl == 0 and self.matrix_cells[1][rand_x].ttl == 0:
                cell.randomize_char()
                cell.randomize_ttl()

class Matrix:
    def __init__(self, stdscr: curses.window, speed: int = 30):
        self.stdscr = stdscr
        self.state: MatrixState = MatrixState(stdscr)
        self.speed: int = speed
        
        self.frame_num: int = 0

    def display(self):
        for y in range(self.state.height):
            for x in range(self.state.width):                
                cell = self.state.matrix_cells[y][x]

                try:
                    color_pair = curses.color_pair(HIGHLIGHT_COLOR_PAIR if cell.highlight else MAIN_COLOR_PAIR)
                    self.stdscr.addch(y, x, cell.char if cell.ttl != 0 else " ", color_pair)
                except curses.error:
                    pass
        
        self.frame_num += 1
        
        self.stdscr.refresh()

    def run(self):
        running = True
        while running:
            self.stdscr.erase()
            self.state.update()
            self.display()
            
            curses.napms(MS_PER_SECOND // self.speed)

def get_max_yx(stdscr: curses.window) -> Vector2:
    y, x = stdscr.getmaxyx()
    
    return Vector2(x, y)

def main(stdscr: curses.window):
    curses.curs_set(0)
    
    curses.init_pair(MAIN_COLOR_PAIR, FOREGROUND_COLOR, BACKGROUND_COLOR)
    curses.init_pair(HIGHLIGHT_COLOR_PAIR, HIGHLIGHT_COLOR, BACKGROUND_COLOR)    
    
    matrix = Matrix(stdscr)
    matrix.run()

if __name__ == "__main__":
    wrapper(main)

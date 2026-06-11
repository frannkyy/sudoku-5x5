__version__ = "1.1.0"

import json
import random
from copy import deepcopy
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label


SIDE = 5
MAX_LEVEL = 100
SPLASH_SECONDS = 2.5


def shuffled(values):
    values = list(values)
    random.shuffle(values)
    return values


def generate_solution():
    """Create a complete valid 5x5 Latin-Sudoku solution using numbers 1..5.

    A 5x5 grid cannot be split into classic equal Sudoku boxes, so this version
    uses the 5x5 mobile-mini rule: each row and each column contains 1..5 once.
    """
    rows = shuffled(range(SIDE))
    cols = shuffled(range(SIDE))
    numbers = shuffled(range(1, SIDE + 1))
    return [[numbers[(row + col) % SIDE] for col in cols] for row in rows]


def candidates(board, row, col):
    """Return legal values for an empty cell."""
    if board[row][col] != 0:
        return []

    used = set(board[row])
    used.update(board[r][col] for r in range(SIDE))
    return [n for n in range(1, SIDE + 1) if n not in used]


def count_solutions(board, limit=2):
    """Count puzzle solutions up to limit. Used to keep generated puzzles unique."""
    best_cell = None
    best_candidates = None

    for row in range(SIDE):
        for col in range(SIDE):
            if board[row][col] == 0:
                cell_candidates = candidates(board, row, col)
                if not cell_candidates:
                    return 0
                if best_candidates is None or len(cell_candidates) < len(best_candidates):
                    best_cell = (row, col)
                    best_candidates = cell_candidates
                    if len(best_candidates) == 1:
                        break
        if best_candidates is not None and len(best_candidates) == 1:
            break

    if best_cell is None:
        return 1

    row, col = best_cell
    random.shuffle(best_candidates)
    total = 0

    for number in best_candidates:
        board[row][col] = number
        total += count_solutions(board, limit)
        board[row][col] = 0
        if total >= limit:
            return total

    return total


def clues_for_level(level):
    """Map level 1..100 to a clue target. Higher level means fewer clues."""
    level = max(1, min(MAX_LEVEL, int(level)))
    easiest = 18
    hardest = 8
    return round(easiest - ((level - 1) * (easiest - hardest) / (MAX_LEVEL - 1)))


def generate_puzzle(level):
    """Generate a 5x5 puzzle with a unique solution."""
    target_clues = clues_for_level(level)
    best_puzzle = None
    best_solution = None
    best_clue_count = SIDE * SIDE

    for _ in range(25):
        solution = generate_solution()
        puzzle = deepcopy(solution)
        positions = [(r, c) for r in range(SIDE) for c in range(SIDE)]
        random.shuffle(positions)
        clue_count = SIDE * SIDE

        for row, col in positions:
            if clue_count <= target_clues:
                break

            old_value = puzzle[row][col]
            if old_value == 0:
                continue

            puzzle[row][col] = 0
            test_board = deepcopy(puzzle)
            if count_solutions(test_board, limit=2) == 1:
                clue_count -= 1
            else:
                puzzle[row][col] = old_value

        if clue_count < best_clue_count:
            best_puzzle = deepcopy(puzzle)
            best_solution = deepcopy(solution)
            best_clue_count = clue_count

        if clue_count <= target_clues:
            return puzzle, solution

    return best_puzzle, best_solution


class SudokuCell(Button):
    def __init__(self, row, col, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.background_normal = ""
        self.font_size = "22sp"
        self.bold = True


class SudokuApp(App):
    title = "Sudoku 1-5: 100 Levels"

    def build(self):
        Window.clearcolor = (0.06, 0.07, 0.09, 1)
        self.storage_path = Path(self.user_data_dir) / "sudoku_5x5_save.json"
        self.level = 1
        self.unlocked_level = 1
        self.mistakes = 0
        self.hints = 0
        self.selected = None
        self.puzzle = None
        self.solution = None
        self.current = None
        self.fixed = None
        self.cells = {}

        self.app_root = BoxLayout(orientation="vertical")
        self.show_splash()
        Clock.schedule_once(lambda _dt: self.show_game(), SPLASH_SECONDS)
        return self.app_root

    def splash_image_path(self):
        base = Path(__file__).resolve().parent / "assets"
        for filename in ("splash.gif", "presplash.png", "splash.png"):
            candidate = base / filename
            if candidate.exists():
                return str(candidate)
        return ""

    def show_splash(self):
        self.app_root.clear_widgets()
        splash = FloatLayout()
        splash.add_widget(
            Image(
                source=self.splash_image_path(),
                fit_mode="fill",
                anim_delay=0.09,
                anim_loop=0,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
            )
        )
        self.app_root.add_widget(splash)

    def show_game(self):
        self.app_root.clear_widgets()
        root = self.build_game_ui()
        self.app_root.add_widget(root)
        self.load_or_create_state()
        self.refresh()

    def build_game_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))

        self.header = Label(
            text="",
            size_hint_y=None,
            height=dp(34),
            font_size="19sp",
            bold=True,
            color=(1, 1, 1, 1),
        )
        root.add_widget(self.header)

        self.message = Label(
            text="Tap a cell, then choose a number.",
            size_hint_y=None,
            height=dp(32),
            font_size="14sp",
            color=(0.78, 0.84, 0.95, 1),
        )
        root.add_widget(self.message)

        board_shell = BoxLayout(padding=dp(4), size_hint_y=0.70)
        self.grid = GridLayout(cols=SIDE, rows=SIDE, spacing=dp(2))
        board_shell.add_widget(self.grid)
        root.add_widget(board_shell)

        self.create_board()

        number_pad = GridLayout(cols=SIDE, rows=1, spacing=dp(4), size_hint_y=None, height=dp(54))
        for number in range(1, SIDE + 1):
            btn = Button(
                text=str(number),
                font_size="20sp",
                bold=True,
                background_normal="",
                background_color=(0.18, 0.28, 0.48, 1),
                color=(1, 1, 1, 1),
            )
            btn.bind(on_press=lambda _btn, n=number: self.place_number(n))
            number_pad.add_widget(btn)
        root.add_widget(number_pad)

        controls = GridLayout(cols=5, rows=1, spacing=dp(5), size_hint_y=None, height=dp(48))
        control_buttons = [
            ("Clear", self.clear_cell),
            ("Hint", self.give_hint),
            ("Check", self.check_board),
            ("New", self.new_current_level),
            ("Next", self.next_unlocked_level),
        ]
        for text, action in control_buttons:
            btn = Button(
                text=text,
                font_size="14sp",
                background_normal="",
                background_color=(0.16, 0.17, 0.20, 1),
                color=(1, 1, 1, 1),
            )
            btn.bind(on_press=lambda _btn, fn=action: fn())
            controls.add_widget(btn)
        root.add_widget(controls)

        nav = GridLayout(cols=2, rows=1, spacing=dp(5), size_hint_y=None, height=dp(44))
        prev_btn = Button(
            text="Previous Level",
            font_size="14sp",
            background_normal="",
            background_color=(0.12, 0.12, 0.15, 1),
            color=(1, 1, 1, 1),
        )
        prev_btn.bind(on_press=lambda _btn: self.previous_level())
        nav.add_widget(prev_btn)

        restart_btn = Button(
            text="Restart Level",
            font_size="14sp",
            background_normal="",
            background_color=(0.12, 0.12, 0.15, 1),
            color=(1, 1, 1, 1),
        )
        restart_btn.bind(on_press=lambda _btn: self.restart_level())
        nav.add_widget(restart_btn)
        root.add_widget(nav)

        return root

    def create_board(self):
        self.grid.clear_widgets()
        self.cells.clear()

        for row in range(SIDE):
            for col in range(SIDE):
                cell = SudokuCell(row, col)
                cell.bind(on_press=lambda btn: self.select_cell(btn.row, btn.col))
                self.cells[(row, col)] = cell
                self.grid.add_widget(cell)

    def valid_number_grid(self, grid):
        if not isinstance(grid, list) or len(grid) != SIDE:
            return False
        for row in grid:
            if not isinstance(row, list) or len(row) != SIDE:
                return False
            for value in row:
                if not isinstance(value, int) or value < 0 or value > SIDE:
                    return False
        return True

    def valid_fixed_grid(self, grid):
        if not isinstance(grid, list) or len(grid) != SIDE:
            return False
        for row in grid:
            if not isinstance(row, list) or len(row) != SIDE:
                return False
            for value in row:
                if not isinstance(value, bool):
                    return False
        return True

    def state_is_valid_5x5(self):
        return (
            self.valid_number_grid(self.puzzle)
            and self.valid_number_grid(self.solution)
            and self.valid_number_grid(self.current)
            and self.valid_fixed_grid(self.fixed)
        )

    def load_or_create_state(self):
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self.level = max(1, min(MAX_LEVEL, int(data.get("level", 1))))
                self.unlocked_level = max(1, min(MAX_LEVEL, int(data.get("unlocked_level", self.level))))
                self.mistakes = int(data.get("mistakes", 0))
                self.hints = int(data.get("hints", 0))
                self.puzzle = data.get("puzzle")
                self.solution = data.get("solution")
                self.current = data.get("current")
                self.fixed = data.get("fixed")

            if not self.state_is_valid_5x5():
                self.level = max(1, min(MAX_LEVEL, int(self.level)))
                self.unlocked_level = max(1, min(MAX_LEVEL, int(self.unlocked_level)))
                self.start_level(self.level, generate_new=True)
        except Exception:
            self.level = 1
            self.unlocked_level = 1
            self.start_level(1, generate_new=True)

    def save_state(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "level": self.level,
            "unlocked_level": self.unlocked_level,
            "mistakes": self.mistakes,
            "hints": self.hints,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "current": self.current,
            "fixed": self.fixed,
        }
        self.storage_path.write_text(json.dumps(data), encoding="utf-8")

    def start_level(self, level, generate_new=True):
        self.level = max(1, min(MAX_LEVEL, int(level)))
        self.selected = None
        self.mistakes = 0
        self.hints = 0

        if generate_new:
            self.puzzle, self.solution = generate_puzzle(self.level)
            self.current = deepcopy(self.puzzle)
            self.fixed = [[self.puzzle[r][c] != 0 for c in range(SIDE)] for r in range(SIDE)]

        self.save_state()
        if hasattr(self, "message"):
            self.message.text = f"Level {self.level} ready. Fill each row and column with 1-{SIDE}."
        if hasattr(self, "header") and hasattr(self, "message") and hasattr(self, "grid") and self.cells:
            self.refresh()

    def select_cell(self, row, col):
        self.selected = (row, col)
        value = self.current[row][col]
        if value:
            self.message.text = f"Selected {value}."
        else:
            self.message.text = "Selected an empty cell."
        self.refresh()

    def place_number(self, number):
        if self.selected is None:
            self.message.text = "Pick a cell first."
            return

        row, col = self.selected
        if self.fixed[row][col]:
            self.message.text = "That clue is locked. Pick an empty cell."
            return

        self.current[row][col] = number
        if number == self.solution[row][col]:
            self.message.text = "Nice move."
        else:
            self.mistakes += 1
            self.message.text = f"That number is not correct. Mistakes: {self.mistakes}"

        self.save_state()
        self.refresh()
        if self.is_solved():
            self.level_completed()

    def clear_cell(self):
        if self.selected is None:
            self.message.text = "Pick a cell first."
            return

        row, col = self.selected
        if self.fixed[row][col]:
            self.message.text = "You cannot clear a starting clue."
            return

        self.current[row][col] = 0
        self.message.text = "Cell cleared."
        self.save_state()
        self.refresh()

    def give_hint(self):
        if self.selected is None:
            empty_cells = [(r, c) for r in range(SIDE) for c in range(SIDE) if self.current[r][c] == 0]
            if not empty_cells:
                self.message.text = "No empty cells left."
                return
            self.selected = random.choice(empty_cells)

        row, col = self.selected
        if self.fixed[row][col]:
            self.message.text = "Select an empty cell for a hint."
            return

        self.current[row][col] = self.solution[row][col]
        self.hints += 1
        self.message.text = f"Hint used. Hints: {self.hints}"
        self.save_state()
        self.refresh()
        if self.is_solved():
            self.level_completed()

    def check_board(self):
        for row in range(SIDE):
            for col in range(SIDE):
                if self.current[row][col] == 0:
                    self.message.text = "The board is not complete yet."
                    return
                if self.current[row][col] != self.solution[row][col]:
                    self.message.text = "Some cells are wrong. Red cells show mistakes."
                    self.refresh()
                    return
        self.level_completed()

    def is_solved(self):
        return all(self.current[r][c] == self.solution[r][c] for r in range(SIDE) for c in range(SIDE))

    def level_completed(self):
        if self.level >= self.unlocked_level and self.unlocked_level < MAX_LEVEL:
            self.unlocked_level = self.level + 1

        self.save_state()
        if self.level < MAX_LEVEL:
            self.message.text = f"Solved! Level {self.level + 1} unlocked."
            Clock.schedule_once(lambda _dt: self.start_level(self.level + 1, generate_new=True), 1.2)
        else:
            self.message.text = "Amazing! You beat all 100 levels."
        self.refresh()

    def new_current_level(self):
        self.message.text = "Generating a fresh puzzle..."
        Clock.schedule_once(lambda _dt: self.start_level(self.level, generate_new=True), 0.1)

    def restart_level(self):
        self.current = deepcopy(self.puzzle)
        self.mistakes = 0
        self.hints = 0
        self.selected = None
        self.message.text = "Level restarted."
        self.save_state()
        self.refresh()

    def previous_level(self):
        if self.level <= 1:
            self.message.text = "You are already on Level 1."
            return
        self.start_level(self.level - 1, generate_new=True)

    def next_unlocked_level(self):
        if self.level >= MAX_LEVEL:
            self.message.text = "Level 100 is the final level."
            return
        if self.level + 1 > self.unlocked_level:
            self.message.text = "Solve this level to unlock the next one."
            return
        self.start_level(self.level + 1, generate_new=True)

    def refresh(self):
        if self.current is None or self.puzzle is None or self.solution is None or self.fixed is None:
            return

        filled = sum(1 for r in range(SIDE) for c in range(SIDE) if self.current[r][c] != 0)
        clue_count = sum(1 for r in range(SIDE) for c in range(SIDE) if self.puzzle[r][c] != 0)
        self.header.text = (
            f"Level {self.level}/{MAX_LEVEL}  |  Unlocked {self.unlocked_level}/{MAX_LEVEL}  |  "
            f"Clues {clue_count}  |  Mistakes {self.mistakes}"
        )

        selected_value = None
        if self.selected:
            selected_value = self.current[self.selected[0]][self.selected[1]]

        for row in range(SIDE):
            for col in range(SIDE):
                cell = self.cells[(row, col)]
                value = self.current[row][col]
                cell.text = "" if value == 0 else str(value)

                is_selected = self.selected == (row, col)
                in_same_area = False
                if self.selected:
                    sr, sc = self.selected
                    in_same_area = row == sr or col == sc

                is_same_number = selected_value and value == selected_value
                wrong = value != 0 and value != self.solution[row][col]

                if wrong:
                    bg = (0.62, 0.18, 0.18, 1)
                    text_color = (1, 1, 1, 1)
                elif is_selected:
                    bg = (0.94, 0.70, 0.26, 1)
                    text_color = (0.05, 0.05, 0.05, 1)
                elif is_same_number:
                    bg = (0.25, 0.38, 0.62, 1)
                    text_color = (1, 1, 1, 1)
                elif in_same_area:
                    bg = (0.18, 0.23, 0.32, 1)
                    text_color = (0.92, 0.95, 1, 1)
                elif self.fixed[row][col]:
                    bg = (0.13, 0.14, 0.17, 1)
                    text_color = (0.98, 0.98, 1, 1)
                else:
                    bg = (0.09, 0.10, 0.13, 1)
                    text_color = (0.56, 0.72, 1, 1)

                cell.background_color = bg
                cell.color = text_color
                cell.bold = bool(self.fixed[row][col])

        if filled == SIDE * SIDE and not self.is_solved():
            self.message.text = "Board full. Press Check to find mistakes."


if __name__ == "__main__":
    SudokuApp().run()

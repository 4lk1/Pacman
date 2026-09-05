"""Application layer: the pygame event loop and screen management.

The application owns the window, the input handling and the transitions
between screens (main menu, game view, pause menu, cheat menu, name
entry).  It delegates gameplay to :class:`PacmanGame` and drawing to
:class:`Renderer` and the UI helpers.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

import pygame

from .config import GameConfig
from .game import (PacmanGame, STATE_GAME_OVER, STATE_VICTORY)
from .highscores import HighscoreTable, MAX_NAME_LENGTH
from .maze_loader import DOWN, LEFT, RIGHT, UP
from .renderer import Renderer, Viewport
from .ui import (FontCache, Menu, draw_cheat_menu, draw_highscores,
                 draw_instructions, draw_name_entry, draw_pause_menu)

#: pygame key -> movement direction.
_KEY_DIRECTIONS: Dict[int, Tuple[int, int]] = {
    pygame.K_UP: UP,
    pygame.K_w: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_s: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_a: LEFT,
    pygame.K_RIGHT: RIGHT,
    pygame.K_d: RIGHT,
}

#: Name entry accepts alphanumeric characters and spaces only.
_NAME_CHAR = re.compile(r"[A-Za-z0-9 ]")

MENU_WINDOW = (800, 620)
MAIN_MENU_ITEMS = ["Start Game", "View Highscores", "Instructions", "Exit"]
PAUSE_MENU_ITEMS = ["Resume", "Return to Main Menu"]


class PacmanApp:
    """The top-level application running the pygame loop."""

    def __init__(self, config: GameConfig) -> None:
        """Initialize pygame and the application state.

        Args:
            config: Validated game configuration.
        """
        pygame.init()
        self.config = config
        self.highscores = HighscoreTable.load(config.highscore_filename)
        self.clock = pygame.time.Clock()
        self.fonts = FontCache()
        self.window = pygame.display.set_mode(MENU_WINDOW)
        pygame.display.set_caption("Pac-Man")

        self.running = True
        self.state = "menu"
        self.game: Optional[PacmanGame] = None
        self.renderer: Optional[Renderer] = None
        self.viewport: Optional[Viewport] = None

        self.menu = Menu(MAIN_MENU_ITEMS, "PAC-MAN", "Ghosts! More ghosts!")
        self.pause_menu = Menu(PAUSE_MENU_ITEMS, "PAUSED")

        self._held: Dict[Tuple[int, int], bool] = {
            UP: False, DOWN: False, LEFT: False, RIGHT: False,
        }
        self._last_dir: Optional[Tuple[int, int]] = None
        self._name = ""
        self._name_cursor = True
        self._end_kind = STATE_GAME_OVER
        self._time = 0.0
        self._toast: Optional[Tuple[str, float]] = None

    def run(self) -> None:
        """Run the main loop until the window is closed."""
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self._time += dt
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        """Process all pending pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event.key)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_move(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(event.pos)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Route a key press according to the current screen.

        Args:
            event: The KEYDOWN event.
        """
        key = event.key
        if self.state == "menu":
            self._menu_key(key)
        elif self.state == "highscores":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_b):
                self.state = "menu"
        elif self.state == "instructions":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_b):
                self.state = "menu"
        elif self.state == "playing":
            self._playing_key(key)
        elif self.state == "paused":
            self._paused_key(key)
        elif self.state == "cheat":
            self._cheat_key(key)
        elif self.state == "name_entry":
            self._name_key(key, getattr(event, "unicode", ""))

    def _menu_key(self, key: int) -> None:
        """Handle keys on the main menu.

        Args:
            key: The pressed pygame key.
        """
        if key in (pygame.K_UP, pygame.K_w):
            self.menu.move(-1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu.move(1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate_menu_item(self.menu.selection)

    def _playing_key(self, key: int) -> None:
        """Handle keys while playing.

        Args:
            key: The pressed pygame key.
        """
        if key in _KEY_DIRECTIONS:
            self._held[_KEY_DIRECTIONS[key]] = True
            self._last_dir = _KEY_DIRECTIONS[key]
        elif key in (pygame.K_p, pygame.K_ESCAPE):
            self.state = "paused"
        elif key == pygame.K_c:
            self.state = "cheat"

    def _paused_key(self, key: int) -> None:
        """Handle keys on the pause menu.

        Args:
            key: The pressed pygame key.
        """
        if key in (pygame.K_ESCAPE, pygame.K_p):
            self.state = "playing"
        elif key in (pygame.K_UP, pygame.K_w):
            self.pause_menu.move(-1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.pause_menu.move(1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.pause_menu.selection == 0:
                self.state = "playing"
            else:
                self._back_to_menu()

    def _cheat_key(self, key: int) -> None:
        """Handle keys on the cheat menu.

        Args:
            key: The pressed pygame key.
        """
        if key in (pygame.K_ESCAPE, pygame.K_c):
            self.state = "playing"
            return
        if self.game is None:
            return
        if key == pygame.K_1:
            self.game.cheats.invincible = not self.game.cheats.invincible
        elif key == pygame.K_2:
            current_level = self.game.level
            self.game.skip_level()
            if self.game.level is not current_level:
                self._resize_to_level()
        elif key == pygame.K_3:
            self.game.cheats.ghost_freeze = not self.game.cheats.ghost_freeze
        elif key == pygame.K_4:
            self.game.add_life()
        elif key == pygame.K_5:
            self.game.cheats.speed = not self.game.cheats.speed
        self._check_game_end()

    def _name_key(self, key: int, unicode_text: str) -> None:
        """Handle keys on the name entry screen.

        Args:
            key: The pressed pygame key.
            unicode_text: Character produced by the key.
        """
        if key == pygame.K_ESCAPE:
            self._back_to_menu()
        elif key == pygame.K_RETURN:
            self._save_name()
        elif key == pygame.K_BACKSPACE:
            self._name = self._name[:-1]
        elif unicode_text and len(self._name) < MAX_NAME_LENGTH:
            for char in unicode_text:
                if len(self._name) < MAX_NAME_LENGTH and _NAME_CHAR.fullmatch(
                        char):
                    self._name += char

    def _handle_keyup(self, key: int) -> None:
        """Release a held movement direction.

        Args:
            key: The released pygame key.
        """
        if key in _KEY_DIRECTIONS:
            direction = _KEY_DIRECTIONS[key]
            self._held[direction] = False
            if self._last_dir == direction:
                self._last_dir = next(
                    (d for d, held in self._held.items() if held), None
                )

    def _handle_mouse_move(self, position: Tuple[int, int]) -> None:
        """Highlight menu items under the mouse.

        Args:
            position: Mouse position.
        """
        if self.state == "menu":
            index = self.menu.hit(position)
            if index is not None:
                self.menu.selection = index
        elif self.state == "paused":
            index = self.pause_menu.hit(position)
            if index is not None:
                self.pause_menu.selection = index

    def _handle_mouse_click(self, position: Tuple[int, int]) -> None:
        """Activate the menu item clicked by the mouse.

        Args:
            position: Mouse position.
        """
        if self.state == "menu":
            index = self.menu.hit(position)
            if index is not None:
                self._activate_menu_item(index)
        elif self.state == "paused":
            index = self.pause_menu.hit(position)
            if index is not None:
                if index == 0:
                    self.state = "playing"
                else:
                    self._back_to_menu()

    def _activate_menu_item(self, index: int) -> None:
        """Run the action of a main menu item.

        Args:
            index: Index of the selected item.
        """
        label = self.menu.items[index]
        if label == "Start Game":
            self._start_game()
        elif label == "View Highscores":
            self.state = "highscores"
        elif label == "Instructions":
            self.state = "instructions"
        elif label == "Exit":
            self.running = False

    def _start_game(self) -> None:
        """Create a new game session and enter the game view."""
        self.game = PacmanGame(self.config)
        self._resize_to_level()
        self._last_dir = None
        for direction in self._held:
            self._held[direction] = False
        self.state = "playing"

    def _resize_to_level(self) -> None:
        """Resize the window and rebuild the renderer for the level."""
        if self.game is None or self.game.level is None:
            return
        self.viewport = Viewport(self.game.level.maze)
        self.window = pygame.display.set_mode(
            (self.viewport.window_width, self.viewport.window_height)
        )
        self.renderer = Renderer(self.viewport, self.fonts)

    def _back_to_menu(self) -> None:
        """Discard the current game and return to the main menu."""
        self.game = None
        self.renderer = None
        self.viewport = None
        self.window = pygame.display.set_mode(MENU_WINDOW)
        self.state = "menu"

    def _save_name(self) -> None:
        """Save the typed name and return to the main menu."""
        if self.game is not None and self._name.strip():
            self.highscores.add(self._name, self.game.score)
            self.highscores.save(self.config.highscore_filename)
        self._name = ""
        self._back_to_menu()

    def _check_game_end(self) -> None:
        """Move to the name entry screen when the game just ended."""
        if self.game is None:
            return
        if self.game.state == STATE_VICTORY:
            self._end_kind = STATE_VICTORY
            self.state = "name_entry"
            self._name = ""
        elif self.game.state == STATE_GAME_OVER:
            self._end_kind = STATE_GAME_OVER
            self.state = "name_entry"
            self._name = ""

    def _update(self, dt: float) -> None:
        """Advance the game and manage transient messages.

        Args:
            dt: Time step in seconds.
        """
        if self._toast is not None:
            remaining = self._toast[1] - dt
            if remaining > 0:
                self._toast = (self._toast[0], remaining)
            else:
                self._toast = None
        if self.state != "playing" or self.game is None:
            return
        current_level = self.game.level
        events = self.game.update(dt, self._last_dir)
        if self.game is not None and self.game.level is not current_level:
            self._resize_to_level()
        for event in events:
            if event.kind == "timeout":
                self._set_toast("Time's up! Restarting level...")
            elif event.kind == "life_lost":
                self._set_toast("Life lost!")
        self._check_game_end()

    def _set_toast(self, message: str) -> None:
        """Show a transient message on the game view.

        Args:
            message: Message text.
        """
        self._toast = (message, 2.5)

    def _draw(self) -> None:
        """Draw the current screen."""
        if self.state == "menu":
            self.menu.draw(self.window, self.fonts)
        elif self.state == "highscores":
            draw_highscores(self.window, self.fonts, self.highscores.top())
        elif self.state == "instructions":
            draw_instructions(self.window, self.fonts)
        elif self.state == "name_entry":
            if self.game is None:
                self.state = "menu"
                return
            title = ("YOU WIN!" if self._end_kind == STATE_VICTORY
                     else "GAME OVER")
            subtitle = f"Final score: {self.game.score}"
            cursor_visible = int(self._time * 2.5) % 2 == 0
            draw_name_entry(self.window, self.fonts, title, subtitle,
                            self._name, cursor_visible)
        elif self.state in ("playing", "paused", "cheat"):
            if self.renderer is None or self.game is None:
                return
            self.renderer.draw_game(self.window, self.game, self._time,
                                    self._toast)
            if self.state == "paused":
                draw_pause_menu(self.window, self.fonts, self.pause_menu)
            elif self.state == "cheat":
                draw_cheat_menu(self.window, self.fonts, self.game.cheats)
        pygame.display.flip()

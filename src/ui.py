"""Pygame user interface: menus and screens.

This module provides the main menu, the highscore and instructions
screens, the pause and cheat overlays, and the name entry form used
when a game ends.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pygame

from .entities import CheatState
from .highscores import ScoreEntry

#: Basic UI palette.
COLOR_BG = (0, 0, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_ACCENT = (255, 255, 0)
COLOR_MUTED = (160, 160, 160)
COLOR_SELECTED = (255, 255, 0)
COLOR_CHEAT = (255, 80, 80)
COLOR_PANEL = (20, 20, 40)


class FontCache:
    """Memoizes pygame fonts so they are created only once."""

    def __init__(self) -> None:
        """Initialize the empty cache."""
        self._fonts: Dict[Tuple[int, bool], pygame.font.Font] = {}

    def get(self, size: int, bold: bool = False) -> pygame.font.Font:
        """Return a cached font of the requested size.

        Args:
            size: Font size in pixels.
            bold: Whether to use the bold variant.

        Returns:
            A pygame font object.
        """
        key = (size, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, size)
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]


class Menu:
    """A vertical list menu with keyboard and mouse support."""

    def __init__(self, items: List[str], title: str,
                 subtitle: str = "") -> None:
        """Initialize the menu.

        Args:
            items: Menu item labels.
            title: Menu title.
            subtitle: Optional subtitle shown under the title.
        """
        self.items = items
        self.title = title
        self.subtitle = subtitle
        self.selection = 0
        self._rects: List[pygame.Rect] = []

    def move(self, delta: int) -> None:
        """Move the selection by *delta* items.

        Args:
            delta: Number of items to move (negative goes up).
        """
        count = len(self.items)
        if count == 0:
            return
        self.selection = (self.selection + delta) % count

    def hit(self, position: Tuple[int, int]) -> Optional[int]:
        """Return the menu item index under *position*, if any.

        Args:
            position: Mouse position.

        Returns:
            Index of the hovered item, or None.
        """
        for index, rect in enumerate(self._rects):
            if rect.collidepoint(position):
                return index
        return None

    def draw(self, surface: pygame.Surface, fonts: FontCache) -> None:
        """Draw the menu centered on the surface.

        Args:
            surface: Target surface.
            fonts: Shared font cache.
        """
        surface.fill(COLOR_BG)
        title_font = fonts.get(56, bold=True)
        title = title_font.render(self.title, True, COLOR_ACCENT)
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2,
                             40))
        if self.subtitle:
            sub_font = fonts.get(22)
            sub = sub_font.render(self.subtitle, True, COLOR_MUTED)
            surface.blit(sub, (surface.get_width() // 2 - sub.get_width() // 2,
                               105))
        button_w = 320
        button_h = 46
        gap = 14
        total = len(self.items) * (button_h + gap) - gap
        start_y = max(170, (surface.get_height() - total) // 2 + 40)
        center_x = surface.get_width() // 2
        self._rects = []
        for index, label in enumerate(self.items):
            rect = pygame.Rect(center_x - button_w // 2,
                               start_y + index * (button_h + gap),
                               button_w, button_h)
            self._rects.append(rect)
            selected = index == self.selection
            color = COLOR_SELECTED if selected else COLOR_PANEL
            pygame.draw.rect(surface, color, rect, border_radius=8)
            pygame.draw.rect(surface, COLOR_MUTED, rect, width=2,
                             border_radius=8)
            font = fonts.get(24, bold=selected)
            text = font.render(label, True,
                               COLOR_TEXT if selected else COLOR_MUTED)
            surface.blit(text, (rect.centerx - text.get_width() // 2,
                                rect.centery - text.get_height() // 2))
        hint = fonts.get(16).render(
            "Arrows / WASD + Enter, or mouse", True, COLOR_MUTED
        )
        surface.blit(hint, (surface.get_width() // 2 - hint.get_width() // 2,
                            surface.get_height() - 30))


def draw_highscores(surface: pygame.Surface, fonts: FontCache,
                    entries: List[ScoreEntry]) -> None:
    """Draw the highscore table screen.

    Args:
        surface: Target surface.
        fonts: Shared font cache.
        entries: Top 10 entries, highest score first.
    """
    surface.fill(COLOR_BG)
    title = fonts.get(44, bold=True).render("HIGHSCORES", True, COLOR_ACCENT)
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2,
                         40))
    if not entries:
        empty = fonts.get(24).render("No highscores yet. Play a game!",
                                     True, COLOR_MUTED)
        surface.blit(empty, (surface.get_width() // 2 - empty.get_width() // 2,
                             200))
    else:
        start_y = 140
        for index, entry in enumerate(entries[:10]):
            row = f"{index + 1:>2}.  {entry.name:<10}  {entry.score:>6}"
            color = COLOR_ACCENT if index == 0 else COLOR_TEXT
            text = fonts.get(24).render(row, True, color)
            surface.blit(text, (surface.get_width() // 2 - 140, start_y
                                + index * 40))
    hint = fonts.get(18).render("Press Esc to go back", True, COLOR_MUTED)
    surface.blit(hint, (surface.get_width() // 2 - hint.get_width() // 2,
                        surface.get_height() - 40))


#: Instructions text, one line per entry.
INSTRUCTIONS_LINES: List[str] = [
    "CONTROLS",
    "  Move: Arrow keys or WASD",
    "  Pause: P or Esc (opens the pause menu)",
    "  Cheat menu: C",
    "",
    "RULES",
    "  Eat all the pacgums to complete the level",
    "  Super-pacgums (the big blinking dots) make the ghosts",
    "  edible for a short time - eat them for bonus points!",
    "  Touching a normal ghost costs one life",
    "  Finish the level before the timer runs out",
    "  Complete all levels to win the game",
]


def draw_instructions(surface: pygame.Surface, fonts: FontCache) -> None:
    """Draw the instructions screen.

    Args:
        surface: Target surface.
        fonts: Shared font cache.
    """
    surface.fill(COLOR_BG)
    title = fonts.get(44, bold=True).render("INSTRUCTIONS", True,
                                            COLOR_ACCENT)
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2,
                         40))
    start_y = 130
    for index, line in enumerate(INSTRUCTIONS_LINES):
        color = COLOR_ACCENT if line and not line.startswith("  ") else (
            COLOR_MUTED if line == "" else COLOR_TEXT
        )
        text = fonts.get(20).render(line, True, color)
        surface.blit(text, (surface.get_width() // 2 - 260,
                            start_y + index * 34))
    hint = fonts.get(18).render("Press Esc to go back", True, COLOR_MUTED)
    surface.blit(hint, (surface.get_width() // 2 - hint.get_width() // 2,
                        surface.get_height() - 40))


def draw_pause_menu(surface: pygame.Surface, fonts: FontCache,
                    menu: Menu) -> None:
    """Draw the pause overlay with its menu.

    Args:
        surface: Target surface.
        fonts: Shared font cache.
        menu: The pause menu (Resume / Return to Main Menu).
    """
    _draw_overlay(surface)
    menu.draw(surface, fonts)


def draw_cheat_menu(surface: pygame.Surface, fonts: FontCache,
                    cheats: CheatState) -> None:
    """Draw the cheat mode overlay.

    Args:
        surface: Target surface.
        fonts: Shared font cache.
        cheats: Current cheat settings.
    """
    _draw_overlay(surface)
    title = fonts.get(40, bold=True).render("CHEAT MODE", True, COLOR_CHEAT)
    surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2,
                         90))
    rows = [
        ("1  Invincibility", cheats.invincible),
        ("2  Skip level", None),
        ("3  Ghost freeze", cheats.ghost_freeze),
        ("4  Extra life", None),
        ("5  Speed up", cheats.speed),
    ]
    for index, (label, state) in enumerate(rows):
        y = 170 + index * 44
        if state is True:
            rendered = fonts.get(24).render(f"{label}  [ON]", True,
                                            COLOR_ACCENT)
        elif state is False:
            rendered = fonts.get(24).render(f"{label}  [OFF]", True,
                                            COLOR_TEXT)
        else:
            rendered = fonts.get(24).render(label, True, COLOR_TEXT)
        surface.blit(rendered, (surface.get_width() // 2
                                - rendered.get_width() // 2, y))
    hint = fonts.get(16).render(
        "Press 1-5 to toggle, Esc to close", True, COLOR_MUTED
    )
    surface.blit(hint, (surface.get_width() // 2 - hint.get_width() // 2,
                        surface.get_height() - 60))


def draw_name_entry(surface: pygame.Surface, fonts: FontCache,
                    title: str, subtitle: str, name: str,
                    cursor_visible: bool) -> None:
    """Draw the name entry screen used after a game ends.

    Args:
        surface: Target surface.
        fonts: Shared font cache.
        title: Screen title (GAME OVER / YOU WIN!).
        subtitle: Final score text.
        name: Name typed so far.
        cursor_visible: Whether the cursor is currently shown.
    """
    surface.fill(COLOR_BG)
    title_text = fonts.get(52, bold=True).render(title, True, COLOR_ACCENT)
    surface.blit(title_text, (surface.get_width() // 2
                              - title_text.get_width() // 2, 80))
    sub_text = fonts.get(26).render(subtitle, True, COLOR_TEXT)
    surface.blit(sub_text, (surface.get_width() // 2
                            - sub_text.get_width() // 2, 160))
    prompt = fonts.get(22).render(
        "Enter your name to save your highscore (max 10 chars):",
        True, COLOR_MUTED,
    )
    surface.blit(prompt, (surface.get_width() // 2 - prompt.get_width() // 2,
                          240))
    box = pygame.Rect(surface.get_width() // 2 - 180, 280, 360, 46)
    pygame.draw.rect(surface, COLOR_PANEL, box, border_radius=6)
    pygame.draw.rect(surface, COLOR_MUTED, box, width=2, border_radius=6)
    name_font = fonts.get(26)
    name_text = name_font.render(name, True, COLOR_TEXT)
    name_x = box.centerx - name_text.get_width() // 2
    name_y = box.centery - name_text.get_height() // 2
    surface.blit(name_text, (name_x, name_y))
    if cursor_visible:
        cursor_text = name_font.render("_", True, COLOR_TEXT)
        surface.blit(cursor_text, (name_x + name_text.get_width() + 2, name_y))
    hint = fonts.get(18).render(
        "Enter: save   Esc: skip", True, COLOR_MUTED
    )
    surface.blit(hint, (surface.get_width() // 2 - hint.get_width() // 2,
                        surface.get_height() - 60))


def _draw_overlay(surface: pygame.Surface) -> None:
    """Dim the whole surface with a translucent black layer.

    Args:
        surface: Target surface.
    """
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))

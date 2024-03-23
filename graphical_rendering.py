from __future__ import annotations
from typing import List, Tuple, Callable

import numpy as np
import pygame

from constants import *


def colorize(tile: np.ndarray, palettes: List[str], palette_index: int) -> np.ndarray:
    """
    Colorizes a tile using a palette.
    """
    height, width = tile.shape
    arr = np.zeros((3, height, width))
    for i in range(height):
        for j in range(width):
            color_index = int(palettes[palette_index][tile[i][j]], 16)
            arr[:, i, j] = PALETTE_MAP[color_index]
    return arr


class TileBase(pygame.sprite.Sprite):
    """
    Base class for all tiles.
    """
    def __init__(self, app: App, x: int, y: int, width: int, height: int) -> None:
        super().__init__()
        self.app = app
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.arr = np.zeros((3, height, width), dtype=int)
        self.app.ui_renderer.all_sprites.append(self)

    def check_click(self, pos: Tuple[int]) -> None:
        """
        Checks if the tile was clicked.
        """
        pass

    def check_mouseover(self, pos: Tuple[int]) -> None:
        """
        Checks if the mouse is over the tile.
        """
        pass

    def update_pos(self, x: int, y: int) -> None:
        """
        Updates the position of the tile.
        """
        self.x = x
        self.y = y

    def update_arr(self) -> None:
        """
        Updates the array of the tile.
        """
        pass

    def update_image(self) -> None:
        """
        Updates the image of the tile.
        """
        self.image = pygame.transform.scale(
            pygame.surfarray.make_surface(self.arr.T),
            (self.width * SCALE, self.height * SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self, *args, **kwargs) -> None:
        """
        Updates the tile.
        """
        super().update()
        self.update_arr()
        self.update_image()

    def draw(self) -> None:
        """
        Draws the tile.
        """
        self.app.screen.blit(self.image, self.rect)


class ColorTile(TileBase):
    """
    A tile that represents a color square in the overall palette.
    """
    def __init__(self, app: App, x: int, y: int, index: int) -> None:
        super().__init__(app, x, y, 4, 4)
        self.app.ui_renderer.tile_sprites.append(self)
        self.index = index
        self.arr = np.array(PALETTE_MAP[index]).reshape((3, 1, 1))
        self.update_image()

    def check_click(self, pos: Tuple[int]) -> None:
        if self.rect.collidepoint(pos):
            self.app.palettes[self.app.selected_palette][self.app.palette_index] = hex(self.index)
            self.app.color_scales[self.app.selected_palette].arr = colorize(np.array([[0,1,2,3]]), self.app.palettes, self.app.selected_palette)

    def check_mouseover(self, pos: Tuple[int]) -> None:
        if self.rect.collidepoint(pos) and self.app.mode == 'metatiles':
            if self.app.selection.size != 4:
                self.app.selection.update_size(4)
            x = (pos[0] - self.rect.x) // (4 * SCALE)
            y = (pos[1] - self.rect.y) // (4 * SCALE)
            self.app.selection.rect.x = self.rect.x + (x * 4 * SCALE)
            self.app.selection.rect.y = self.rect.y + (y * 4 * SCALE)


class Tiles(TileBase):
    """
    A class that represents the table of tiles.
    """
    def __init__(self, app: App, x: int, y: int) -> None:
        super().__init__(app, x, y, TILE_SIZE, TILE_SIZE)
        self.app.ui_renderer.tile_sprites.append(self)
        self.raw_tiles = self.app.table_a
        self.update_image()

    def check_click(self, pos: Tuple[int]) -> None:
        if self.app.mode in ['tiles', 'metatiles']:
            if self.rect.collidepoint(pos):
                x = (pos[0] - self.rect.x) // SCALE
                y = (pos[1] - self.rect.y) // SCALE
                if self.app.mode == 'tiles':
                    self.raw_tiles[y, x] = self.app.palette_index
                elif self.app.mode == 'metatiles':
                    x = x // 8
                    y = y // 8
                    tile_index = y * 16 + x
                    self.app.selected_tile = tile_index
                self.update_arr()

    def check_mouseover(self, pos: Tuple[int]) -> None:
        if self.app.mode in ['tiles', 'metatiles']:
            if self.rect.collidepoint(pos):
                if self.app.mode == 'metatiles' and self.app.selection.size != 8:
                    self.app.selection.update_size(8)
                x = (pos[0] - self.rect.x) // (8 * SCALE)
                y = (pos[1] - self.rect.y) // (8 * SCALE)
                self.app.selection.rect.x = self.rect.x + (x * 8 * SCALE)
                self.app.selection.rect.y = self.rect.y + (y * 8 * SCALE)

    def update_arr(self) -> None:
        self.arr = colorize(self.raw_tiles, self.app.palettes, self.app.selected_palette)


class MetaTile(TileBase):
    """
    A class that represents a metatile.
    """
    def __init__(self, app: App, x: int, y: int, index: int) -> None:
        super().__init__(app, x, y, METATILE_SIZE, METATILE_SIZE)
        self.tiles = app.metatiles[index]
        self.palette = app.metatile_palettes[index]
        self.index = index
        self.arr = np.zeros((3, METATILE_SIZE, METATILE_SIZE), dtype=int)
        self.update_image()

    def check_click(self, pos: Tuple[int]) -> None:
        if self.app.mode == 'metatiles':
            if self.rect.collidepoint(pos):
                x = (pos[0] - self.rect.x) // (SCALE * 8)
                y = (pos[1] - self.rect.y) // (SCALE * 8)
                metatile_index = y * 2 + x
                self.tiles[metatile_index] = self.app.selected_tile
                self.palette = self.app.selected_palette
                self.app.metatile_palettes[self.index] = self.app.selected_palette
        if self.app.mode == 'metametatiles':
            if self.rect.collidepoint(pos):
                self.app.selected_metatile = self.index

    def check_mouseover(self, pos: Tuple[int]) -> None:
        if self.rect.collidepoint(pos) and self.app.mode in ['metatiles', 'metametatiles']:
            selection_size = 16 if self.app.mode == 'metametatiles' else 8
            if self.app.selection.size != selection_size:
                self.app.selection.update_size(selection_size)
            x = (pos[0] - self.rect.x) // (SCALE * selection_size)
            y = (pos[1] - self.rect.y) // (SCALE * selection_size)
            self.app.selection.rect.x = self.rect.x + (x * selection_size * SCALE)
            self.app.selection.rect.y = self.rect.y + (y * selection_size * SCALE)

    def update_arr(self) -> None:
        self.palette = self.app.metatile_palettes[self.index]
        for i in range(4):
            tile = self.tiles[i]
            table_y = tile // 16
            table_x = tile % 16
            arr_x = i % 2 * 8
            arr_y = i // 2 * 8
            colorized = colorize(self.app.table_a[table_y*8:table_y*8+8, table_x*8:table_x*8+8], self.app.palettes, self.palette)
            self.arr[:, arr_y:arr_y+8, arr_x:arr_x+8] = colorized


class MetaMetaTile(TileBase):
    """
    A class that represents a metametatile.
    """
    def __init__(self, app: App, x: int, y: int, index: int) -> None:
        super().__init__(app, x, y, METAMETATILE_SIZE // 2, METAMETATILE_SIZE // 2)
        self.metatiles = app.metametatiles[index]
        self.index = index
        self.arr = np.zeros((3, METAMETATILE_SIZE, METAMETATILE_SIZE), dtype=int)
        self.update_image()

    def check_click(self, pos: Tuple[int]) -> None:
        if self.rect.collidepoint(pos):
            if self.app.mode == 'metametatiles':
                x = (pos[0] - self.rect.x) // (SCALE * 8)
                y = (pos[1] - self.rect.y) // (SCALE * 8)
                metatile_index = y * 2 + x
                self.metatiles[metatile_index] = self.app.selected_metatile
                self.app.metametatiles[self.index] = self.metatiles
                self.update_image()
            elif self.app.mode == 'rooms':
                self.app.selected_metametatile = self.index

    def check_mouseover(self, pos: Tuple[int]) -> None:
        if self.rect.collidepoint(pos) and self.app.mode in ['metametatiles', 'rooms']:
            selection_size = 16 if self.app.mode == 'rooms' else 8
            if self.app.selection.size != selection_size:
                self.app.selection.update_size(selection_size)
            x = (pos[0] - self.rect.x) // (SCALE * selection_size)
            y = (pos[1] - self.rect.y) // (SCALE * selection_size)
            self.app.selection.rect.x = self.rect.x + (x * selection_size * SCALE)
            self.app.selection.rect.y = self.rect.y + (y * selection_size * SCALE)

    def update_arr(self) -> None:
        for i in range(4):
            metatile = self.app.ui_renderer.metatile_sprites[self.metatiles[i]]
            arr_x = i % 2 * 16
            arr_y = i // 2 * 16
            self.arr[:, arr_y:arr_y+16, arr_x:arr_x+16] = metatile.arr


class Room(TileBase):
    """
    A class that represents a room.
    """
    def __init__(self, app: App, x: int, y: int, index: int) -> None:
        super().__init__(app, x, y, ROOM_WIDTH // 2, ROOM_HEIGHT // 2)
        self.metametatiles = app.rooms[index]
        self.index = index
        self.arr = np.zeros((3, ROOM_HEIGHT, ROOM_WIDTH), dtype=int)
        self.update_image()

    def check_click(self, pos: Tuple[int]) -> None:
        if self.app.mode == 'rooms' and self.app.active_room == self.index and self.rect.collidepoint(pos):
            x = (pos[0] - self.rect.x) // (SCALE * 16)
            y = (pos[1] - self.rect.y) // (SCALE * 16)
            self.metametatiles[y][x] = self.app.selected_metametatile
            self.update_image()

    def check_mouseover(self, pos: Tuple[int]) -> None:
        if self.app.mode == 'rooms' and self.rect.collidepoint(pos):
            if self.app.selection.size != 16:
                self.app.selection.update_size(16)
            x = (pos[0] - self.rect.x) // (SCALE * 16)
            y = (pos[1] - self.rect.y) // (SCALE * 16)
            self.app.selection.rect.x = self.rect.x + (x * 16 * SCALE)
            self.app.selection.rect.y = self.rect.y + (y * 16 * SCALE)

    def update_arr(self) -> None:
        for i in range(6):
            for j in range(8):
                metatile = self.app.ui_renderer.metametatile_sprites[self.metametatiles[i][j]]
                arr_x = j * 32
                arr_y = i * 32
                self.arr[:, arr_y:arr_y+32, arr_x:arr_x+32] = metatile.arr


class ColorScale(TileBase):
    """
    A class that represents a color scale (game palette).
    """
    def __init__(self, app: App, x: int, y: int, palette_index: int) -> None:
        super().__init__(app, x, y, COLOR_SCALE_WIDTH, COLOR_SCALE_HEIGHT)
        self.app.ui_renderer.tile_sprites.append(self)
        self.palette_index = palette_index
        self.arr = colorize(np.array([[0,1,2,3]]), self.app.palettes, self.palette_index)
        self.update_image()

    def check_click(self, pos: Tuple[int]) -> None:
        if self.rect.collidepoint(pos):
            x = (pos[0] - self.rect.x) // (SCALE * 4)
            self.app.selected_palette = self.palette_index
            self.app.palette_index = x
            self.app.selected_color_x = self.rect.x + (x * 4 * SCALE) - 1
            self.app.selected_color_y = self.rect.y - 1

    def update_arr(self) -> None:
        self.arr = colorize(np.array([[0,1,2,3]]), self.app.palettes, self.palette_index)

    def check_mouseover(self, pos: Tuple[int]) -> None:
        if self.rect.collidepoint(pos) and self.app.mode == 'metatiles':
            if self.app.selection.size != 4:
                self.app.selection.update_size(4)
            x = (pos[0] - self.rect.x) // (SCALE * 4)
            y = (pos[1] - self.rect.y) // (SCALE * 4)
            self.app.selection.rect.x = self.rect.x + (x * 4 * SCALE)
            self.app.selection.rect.y = self.rect.y + (y * 4 * SCALE)


class Selection(pygame.sprite.Sprite):
    """
    A class that represents a selection rectangle.
    """
    def __init__(self, app: App, x: int, y: int, size: int) -> None:
        self.app = app
        self.update_size(size)
        self.rect.x = x
        self.rect.y = y

    def update_size(self, size: int) -> None:
        """
        Updates the size of the selection rectangle.
        """
        self.size = size
        self.image = pygame.Surface((size * SCALE, size * SCALE), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 64))
        self.rect = self.image.get_rect()


class Button(pygame.sprite.Sprite):
    """
    A class that represents a button.
    """
    def __init__(self, app: App, x: int, y: int, width: int, height: int, text: str, on_click: Callable = lambda: None) -> None:
        super().__init__()
        self.app = app
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = self.app.font.render(text, True, (255, 255, 255))
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill((24, 24, 24))
        self.rect = self.background.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        self.on_click = on_click
        self.app.ui_renderer.all_sprites.append(self)

    def draw(self) -> None:
        """
        Draws the button.
        """
        self.app.screen.blit(self.background, self.rect)
        self.app.screen.blit(self.text, (self.x + self.width // 2 - self.text.get_width() // 2, self.y + self.height // 2 - self.text.get_height() // 2))

    def check_mouseover(self, pos: Tuple[int]) -> None:
        """
        Checks if the mouse is over the button.
        """
        if self.rect.collidepoint(pos):
            self.background.fill((64, 64, 64))
        else:
            self.background.fill((24, 24, 24))

    def check_click(self, pos: Tuple[int]) -> None:
        """
        Checks if the button was clicked.
        """
        if self.rect.collidepoint(pos):
            self.on_click()

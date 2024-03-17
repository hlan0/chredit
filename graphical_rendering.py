import numpy as np
import pygame


PALETTE_MAP = [
    (124,124,124), (0,0,252), (0,0,188), (68,40,188), (148,0,132), (168,0,32), (96,0,0), (136,20,0),
    (80,48,0), (0,120,0), (0,104,0), (0,88,0), (0,64,88), (0,0,0), (0,0,0), (0,0,0),
    (188,188,188), (0,120,248), (0,88,248), (104,68,252), (216,0,204), (228,0,88), (152,50,0), (228,92,16),
    (172,124,0), (0,184,0), (0,168,0), (0,168,68), (0,136,136), (0,0,0), (0,0,0), (0,0,0),
    (248,248,248), (60,188,252), (104,136,252), (152,120,248), (248,120,248), (248,88,152), (255,141,108), (252,160,68),
    (248,184,0), (184,248,24), (88,216,84), (88,248,152), (0,232,216), (120,120,120), (0,0,0), (0,0,0),
    (252,252,252), (164,228,252), (184,184,248), (216,184,248), (248,184,248), (248,164,192), (244,210,198), (252,224,168), (248,216,120),
    (216,248,120), (184,248,184), (184,248,216), (0,252,252), (248,216,248), (0,0,0), (0,0,0)
]


def colorize(tile, palettes, palette_index):
    height, width = tile.shape
    arr = np.zeros((3, height, width))
    for i in range(height):
        for j in range(width):
            color_index = int(palettes[palette_index][tile[i][j]], 16)
            arr[:, i, j] = PALETTE_MAP[color_index]
    return arr


class TileBase(pygame.sprite.Sprite):
    def __init__(self, app, x, y, width, height):
        super().__init__()
        self.app = app
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.arr = np.zeros((3, height, width), dtype=int)

    def check_click(self, pos):
        pass

    def check_mouseover(self, pos):
        pass

    def update_image(self):
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(self.arr.T), (self.width * self.app.SCALE, self.height * self.app.SCALE))

    def update(self, *args, **kwargs):
        super().update()
        self.update_image()


class Tiles(TileBase):
    def __init__(self, app, x, y):
        super().__init__(app, x, y, 128, 128)
        self.app = app
        self.app.tile_sprites.add(self)
        self.raw_tiles = self.app.table_a
        self.update_image()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.app.mode == 'tiles':
            if self.rect.collidepoint(pos):
                x = pos[0] - self.rect.x
                y = pos[1] - self.rect.y
                self.raw_tiles[y//self.app.SCALE, x//self.app.SCALE] = self.app.palette_index
                self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.raw_tiles, self.app.palettes, self.app.selected_palette).T), (128 * self.app.SCALE, 128 * self.app.SCALE))
        elif self.app.mode == 'metatiles':
            if self.rect.collidepoint(pos):
                # for now it's 32 because we're scaling by 4
                x = (pos[0] - self.rect.x) // (self.app.SCALE * 8)
                y = (pos[1] - self.rect.y) // (self.app.SCALE * 8)
                tile_index = y * 16 + x
                self.app.selected_tile = tile_index

    def check_mouseover(self, pos):
        if self.app.mode == 'tiles' or self.app.mode == 'metatiles':
            if self.rect.collidepoint(pos):
                if self.app.mode == 'metatiles' and self.app.selection.size != 8:
                    self.app.selection.update_size(8)
                x = pos[0] - self.rect.x
                y = pos[1] - self.rect.y
                self.app.selection.rect.x = self.rect.x + (x // (8 * self.app.SCALE)) * (8 * self.app.SCALE)
                self.app.selection.rect.y = self.rect.y + (y // (8 * self.app.SCALE)) * (8 * self.app.SCALE)

    def update_image(self):
        self.arr = colorize(self.raw_tiles, self.app.palettes, self.app.selected_palette)
        super().update_image()


class MetaTile(TileBase):
    def __init__(self, app, x, y, index):
        super().__init__(app, x, y, 16, 16)
        self.app.metatile_sprite_group.add(self)
        self.tiles = app.metatiles[index]
        self.palette = app.metatile_palettes[index]
        self.index = index
        self.arr = np.zeros((3, 16, 16), dtype=int)
        self.update_image()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.app.mode == 'metatiles':
            if self.rect.collidepoint(pos):
                # for now it's 32 because we're scaling by 4
                x = (pos[0] - self.rect.x) // (self.app.SCALE * 8)
                y = (pos[1] - self.rect.y) // (self.app.SCALE * 8)
                metatile_index = y * 2 + x
                self.tiles[metatile_index] = self.app.selected_tile
                self.palette = self.app.selected_palette
                self.app.metatile_palettes[self.index] = self.app.selected_palette
        if self.app.mode == 'metametatiles':
            if self.rect.collidepoint(pos):
                self.app.selected_metatile = self.index

    def check_mouseover(self, pos):
        if self.rect.collidepoint(pos):
            selection_size = 16 if self.app.mode == 'metametatiles' else 8
            if self.app.selection.size != selection_size:
                self.app.selection.update_size(selection_size)
            x = (pos[0] - self.rect.x) // (self.app.SCALE * selection_size)
            y = (pos[1] - self.rect.y) // (self.app.SCALE * selection_size)
            self.app.selection.rect.x = self.rect.x + (x * selection_size * self.app.SCALE)
            self.app.selection.rect.y = self.rect.y + (y * selection_size * self.app.SCALE)

    def update_image(self):
        self.palette = self.app.metatile_palettes[self.index]
        for i in range(4):
            tile = self.tiles[i]
            table_y = tile // 16
            table_x = tile % 16
            arr_x = i % 2 * 8
            arr_y = i // 2 * 8
            colorized = colorize(self.app.table_a[table_y*8:table_y*8+8, table_x*8:table_x*8+8], self.app.palettes, self.palette)
            self.arr[:, arr_y:arr_y+8, arr_x:arr_x+8] = colorized
        super().update_image()


class MetaMetaTile(TileBase):
    def __init__(self, app, x, y, index):
        super().__init__(app, x, y, 16, 16)
        self.app.metametatile_sprite_group.add(self)
        self.metatiles = app.metametatiles[index]
        self.index = index
        self.arr = np.zeros((3, 32, 32), dtype=int)
        self.update_image()
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            if self.app.mode == 'metametatiles':
                x = (pos[0] - self.rect.x) // (self.app.SCALE * 8)
                y = (pos[1] - self.rect.y) // (self.app.SCALE * 8)
                metatile_index = y * 2 + x
                self.metatiles[metatile_index] = self.app.selected_metatile
                self.app.metametatiles[self.index] = self.metatiles
                self.update_image()
            elif self.app.mode == 'rooms':
                self.app.selected_metametatile = self.index

    def check_mouseover(self, pos):
        if self.rect.collidepoint(pos):
            selection_size = 16 if self.app.mode == 'rooms' else 8
            if self.app.selection.size != selection_size:
                self.app.selection.update_size(selection_size)
            x = (pos[0] - self.rect.x) // (self.app.SCALE * selection_size)
            y = (pos[1] - self.rect.y) // (self.app.SCALE * selection_size)
            self.app.selection.rect.x = self.rect.x + (x * selection_size * self.app.SCALE)
            self.app.selection.rect.y = self.rect.y + (y * selection_size * self.app.SCALE)

    def update_image(self):
        for i in range(4):
            metatile = self.app.metatile_sprites[self.metatiles[i]]
            arr_x = i % 2 * 16
            arr_y = i // 2 * 16
            self.arr[:, arr_y:arr_y+16, arr_x:arr_x+16] = metatile.arr
        super().update_image()


class Room(TileBase):
    def __init__(self, app, x, y, index):
        super().__init__(app, x, y, 128, 96)
        self.app.room_sprite_group.add(self)
        self.metametatiles = app.rooms[index]
        self.index = index
        self.arr = np.zeros((3, 192, 256), dtype=int)
        self.update_image()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.app.mode == 'rooms' and self.app.active_room == self.index and self.rect.collidepoint(pos):
            x = (pos[0] - self.rect.x) // (self.app.SCALE * 16)
            y = (pos[1] - self.rect.y) // (self.app.SCALE * 16)
            self.metametatiles[y][x] = self.app.selected_metametatile
            self.update_image()

    def check_mouseover(self, pos):
        if self.app.mode == 'rooms' and self.rect.collidepoint(pos):
            if self.app.selection.size != 16:
                self.app.selection.update_size(16)
            x = (pos[0] - self.rect.x) // (self.app.SCALE * 16)
            y = (pos[1] - self.rect.y) // (self.app.SCALE * 16)
            self.app.selection.rect.x = self.rect.x + (x * 16 * self.app.SCALE)
            self.app.selection.rect.y = self.rect.y + (y * 16 * self.app.SCALE)

    def update_image(self):
        for i in range(6):
            for j in range(8):
                metatile = self.app.metametatile_sprites[self.metametatiles[i][j]]
                arr_x = j * 32
                arr_y = i * 32
                self.arr[:, arr_y:arr_y+32, arr_x:arr_x+32] = metatile.arr
        super().update_image()


class ColorScale(TileBase):
    def __init__(self, app, x, y, palette):
        super().__init__(app, x, y, 16, 4)
        self.app.tile_sprites.add(self)
        self.palette = palette
        self.arr = colorize(np.array([[0,1,2,3]]), self.app.palettes, self.palette)
        self.update_image()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            x = (pos[0] - self.rect.x) // (self.app.SCALE * 4)
            self.app.selected_palette = self.palette
            self.app.palette_index = x


class Selection(pygame.sprite.Sprite):
    def __init__(self, app, x, y, size):
        self.app = app
        self.update_size(size)
        self.rect.x = x
        self.rect.y = y

    def update_size(self, size):
        self.size = size
        self.image = pygame.Surface((size * self.app.SCALE, size * self.app.SCALE), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 64))
        self.rect = self.image.get_rect()


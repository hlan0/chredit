import numpy as np
import pygame


def colorize(tile, palettes, palette_index):
    height, width = tile.shape
    arr = np.zeros((3, height, width))
    for i in range(height):
        for j in range(width):
            color_index = int(palettes[palette_index][tile[i][j]], 16)
            arr[0][i][j] = palette_map[color_index][0]
            arr[1][i][j] = palette_map[color_index][1]
            arr[2][i][j] = palette_map[color_index][2]
    return arr

palette_map = [
    (124,124,124), (0,0,252), (0,0,188), (68,40,188), (148,0,132), (168,0,32), (96,0,0), (136,20,0),
    (80,48,0), (0,120,0), (0,104,0), (0,88,0), (0,64,88), (0,0,0), (0,0,0), (0,0,0),
    (188,188,188), (0,120,248), (0,88,248), (104,68,252), (216,0,204), (228,0,88), (152,50,0), (228,92,16),
    (172,124,0), (0,184,0), (0,168,0), (0,168,68), (0,136,136), (0,0,0), (0,0,0), (0,0,0),
    (248,248,248), (60,188,252), (104,136,252), (152,120,248), (248,120,248), (248,88,152), (255,141,108), (252,160,68),
    (248,184,0), (184,248,24), (88,216,84), (88,248,152), (0,232,216), (120,120,120), (0,0,0), (0,0,0),
    (252,252,252), (164,228,252), (184,184,248), (216,184,248), (248,184,248), (248,164,192), (244,210,198), (252,224,168), (248,216,120),
    (216,248,120), (184,248,184), (184,248,216), (0,252,252), (248,216,248), (0,0,0), (0,0,0)
]


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


class Room(pygame.sprite.Sprite):
    def __init__(self, app, x, y, index):
        self.groups = app.room_sprite_group
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.metametatiles = app.rooms[index]
        self.index = index
        self.arr = np.zeros((3, 192, 256), dtype=int)
        self.image = None
        self.update_tiles()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update_tiles(self):
        for i in range(6):
            for j in range(8):
                metatile = self.app.metametatile_sprites[self.metametatiles[i][j]]
                arr_x = j * 32
                arr_y = i * 32
                self.arr[:, arr_y:arr_y+32, arr_x:arr_x+32] = metatile.arr
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(self.arr.T), (128 * self.app.SCALE, 96 * self.app.SCALE))

    def check_click(self, pos):
        if self.app.mode == 'rooms' and self.app.active_room == self.index and self.rect.collidepoint(pos):
            x = (pos[0] - self.rect.x) // (self.app.SCALE * 16)
            y = (pos[1] - self.rect.y) // (self.app.SCALE * 16)
            self.metametatiles[y][x] = self.app.selected_metametatile
            self.update_tiles()

    def update(self):
        self.update_tiles()

    def check_mouseover(self, pos):
        if self.app.mode == 'rooms' and self.rect.collidepoint(pos):
            if self.app.selection.size != 16:
                self.app.selection.update_size(16)
            x = (pos[0] - self.rect.x) // (self.app.SCALE * 16)
            y = (pos[1] - self.rect.y) // (self.app.SCALE * 16)
            self.app.selection.rect.x = self.rect.x + (x * 16 * self.app.SCALE)
            self.app.selection.rect.y = self.rect.y + (y * 16 * self.app.SCALE)


class MetaMetaTile(pygame.sprite.Sprite):
    def __init__(self, app, x, y, index):
        self.groups = app.metametatile_sprite_group
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.metatiles = app.metametatiles[index]

        self.index = index

        self.arr = np.zeros((3, 32, 32), dtype=int)
        self.image = None
        self.update_tiles()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update_tiles(self):
        for i in range(4):
            metatile = self.app.metatile_sprites[self.metatiles[i]]
            arr_x = i % 2 * 16
            arr_y = i // 2 * 16
            self.arr[:, arr_y:arr_y+16, arr_x:arr_x+16] = colorize(metatile.arr, self.app.palettes, metatile.palette)
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(self.arr.T), (16 * self.app.SCALE, 16 * self.app.SCALE))

    def update(self):
        self.update_tiles()

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            if self.app.mode == 'metametatiles':
                x = (pos[0] - self.rect.x) // (self.app.SCALE * 8)
                y = (pos[1] - self.rect.y) // (self.app.SCALE * 8)
                metatile_index = y * 2 + x
                self.metatiles[metatile_index] = self.app.selected_metatile
                self.app.metametatiles[self.index] = self.metatiles
                self.update_tiles()
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


class MetaTile(pygame.sprite.Sprite):
    def __init__(self, app, x, y, index):
        self.groups = app.metatile_sprite_group
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.tiles = app.metatiles[index]
        self.palette = app.metatile_palettes[index]

        self.index = index

        self.arr = np.zeros((16, 16), dtype=int)
        self.image = None
        self.update_tiles()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update_tiles(self):
        for i in range(4):
            tile = self.tiles[i]
            table_y = tile // 16
            table_x = tile % 16
            arr_x = i % 2 * 8
            arr_y = i // 2 * 8
            self.arr[arr_y:arr_y+8, arr_x:arr_x+8] = self.app.table_a[table_y*8:table_y*8+8, table_x*8:table_x*8+8]
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.arr, self.app.palettes, self.palette).T), (16 * self.app.SCALE, 16 * self.app.SCALE))

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

    def update(self):
        self.update_tiles()


class Tiles(pygame.sprite.Sprite):
    def __init__(self, app, x, y):
        self.groups = app.tile_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.tile = self.app.table_a
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.tile, self.app.palettes, self.app.selected_palette).T), (128 * self.app.SCALE, 128 * self.app.SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.app.mode == 'tiles':
            if self.rect.collidepoint(pos):
                x = pos[0] - self.rect.x
                y = pos[1] - self.rect.y
                self.tile[y//self.app.SCALE, x//self.app.SCALE] = self.app.palette_index
                self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.tile, self.app.palettes, self.app.selected_palette).T), (128 * self.app.SCALE, 128 * self.app.SCALE))
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

    def update(self):
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.tile, self.app.palettes, self.app.selected_palette).T), (128 * self.app.SCALE, 128 * self.app.SCALE))


class ColorScale(pygame.sprite.Sprite):
    def __init__(self, app, x, y, palette):
        self.groups = app.tile_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.palette = palette
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(np.array([[0,1,2,3]]), self.app.palettes, self.palette).T), (16 * self.app.SCALE,4 * self.app.SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            x = (pos[0] - self.rect.x) // (self.app.SCALE * 4)
            self.app.selected_palette = self.palette
            self.app.palette_index = x

    def check_mouseover(self, pos):
        pass

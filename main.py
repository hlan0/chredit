import numpy as np
import matplotlib.pyplot as plt
import pygame

from pygame.locals import HWSURFACE, DOUBLEBUF, RESIZABLE


def read_file(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()

    bytes = ''
    for byte in raw_data:
        bytes += bin(byte)[2:].zfill(8)
    bytes = list(bytes)
    

    patterns = []
    for i in range(0, len(bytes), 128):
        map1 = []
        for j in range(0, 64, 8):
            row = bytes[i+j:i+j+8]
            map1.append(row)

        map2 = []
        for j in range(64, 128, 8):
            row = bytes[i+j:i+j+8]
            map2.append(row)

        map3 = np.char.add(map1, map2)
        color_map = {'00': 0, '10': 1, '01': 2, '11': 3}
        map3 = np.vectorize(color_map.get)(map3)

        patterns.append(map3)

    table_a = patterns[:256]
    table_a_display = np.zeros((128, 128), dtype=int)

    table_b = patterns[256:]
    table_b_display = np.zeros((128, 128), dtype=int)
    
    cur_idx = 0

    for i in range(0, 128, 8):
        for j in range(0, 128, 8):
            table_a_display[i:i+8, j:j+8] = table_a[cur_idx]
            table_b_display[i:i+8, j:j+8] = table_b[cur_idx]
            cur_idx += 1

    return table_a_display, table_b_display


def to_binary(x):
    bin_data = []

    for i in range(0, 128, 8):
        for j in range(0, 128, 8):
            block = x[i:i+8, j:j+8]
            bin_data.append(block)

    inverse_color_map = {0: '00', 1: '10', 2: '01', 3: '11'}
    bin_data = np.vectorize(inverse_color_map.get)(bin_data)

    map1 = np.vectorize(lambda x: x[:1])(bin_data)
    map2 = np.vectorize(lambda x: x[1:])(bin_data)

    res = ''
    for i in range(256):
        res += ''.join(map1[i].flatten()) + ''.join(map2[i].flatten())

    return res

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


SCALE = 4


class Selection(pygame.sprite.Sprite):
    def __init__(self, app, x, y, size):
        self.app = app
        self.size = size
        self.image = pygame.Surface((size * SCALE, size * SCALE), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 64))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class App:
    def __init__(self, file_path=None):
        self.table_a, self.table_b = read_file(file_path)

        pygame.init()
        self.screen = pygame.display.set_mode((800, 800), HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.tile_sprites = pygame.sprite.Group()
        self.metatile_sprite_group = pygame.sprite.Group()
        self.metametatile_sprite_group = pygame.sprite.Group()
        self.running = False

        self.palettes = [
            ["0x0f", "0x13", "0x23", "0x30"],
            ["0x0f", "0x16", "0x26", "0x37"],
            ["0x0f", "0x0c", "0x1c", "0x2c"],
            ["0x0f", "0x29", "0x38", "0x30"]
        ]

        self.selected_palette = 0
        self.palette_index = 0

        self.metatiles = [[0, 0, 0, 0] for i in range(48)]
        self.metatile_palettes = [0] * 48
        self.metatile_sprites = []
        for i in range(48):
            x = (128 * SCALE) + (i % 6 * 16 * SCALE)
            y = i // 6 * 16 * SCALE
            self.metatile_sprites.append(MetaTile(self, x, y, i))

        self.metametatiles = [[0, 0, 0, 0] for i in range(48)]
        self.metametatile_sprites = []
        for i in range(48):
            x = (128 * SCALE) + (i % 6 * 16 * SCALE)
            y = i // 6 * 16 * SCALE
            self.metametatile_sprites.append(MetaMetaTile(self, x, y, i))

        self.selected_tile = 0
        self.selection = Selection(self, 0, 0, 8)
        self.show_selection = False

        self.metatile_selection = Selection(self, 0, 0, 16)

        self.mode = 'tiles'

    def save(self):
        a = to_binary(self.table_a) + to_binary(self.table_b)
        binary_data = bytes(int(a, 2).to_bytes((len(a) + 7) // 8, byteorder='big'))
        with open("a.chr", "wb") as f:
            f.write(binary_data)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # replace with UI
                if event.key == pygame.K_s:
                    self.save()
                if event.key == pygame.K_1:
                    self.mode = 'tiles'
                if event.key == pygame.K_2:
                    self.mode = 'metatiles'
                    for sprite in self.metatile_sprites:
                        for i in range(48):
                            x = (128 * SCALE) + (i % 6 * 16 * SCALE)
                            y = i // 6 * 16 * SCALE
                            self.metatile_sprites[i].rect.x = x
                            self.metatile_sprites[i].rect.y = y

                if event.key == pygame.K_3:
                    self.mode = 'metametatiles'
                    for sprite in self.metatile_sprites:
                        for i in range(48):
                            x = (0 * SCALE) + (i % 6 * 16 * SCALE)
                            y = i // 6 * 16 * SCALE
                            self.metatile_sprites[i].rect.x = x
                            self.metatile_sprites[i].rect.y = y

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for sprite in self.tile_sprites.sprites() + self.metatile_sprite_group.sprites():
                        sprite.check_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                x, y = event.pos[0] // (8 * SCALE), event.pos[1] // (8 * SCALE)
                self.selection.rect.x = x * (8 * SCALE)
                self.selection.rect.y = y * (8 * SCALE)
                if event.buttons[0]:
                    for sprite in self.tile_sprites.sprites() + self.metatile_sprite_group.sprites():
                        sprite.check_click(event.pos)

    def run(self):
        self.running = True
        while self.running:
            self.screen.fill((0, 0, 0))
            self.events()
            if self.mode == 'tiles' or self.mode == 'metatiles':
                self.tile_sprites.update()
                self.tile_sprites.draw(self.screen)
            if self.mode == 'metatiles' or self.mode == 'metametatiles':
                self.metatile_sprite_group.update()
                self.metatile_sprite_group.draw(self.screen)
                self.screen.blit(self.selection.image, self.selection.rect)
            """
            for i in range(8):
                for j in range(8):
                    pygame.draw.rect(self.screen, (64,64,64), (i*16*SCALE,j*16*SCALE,16*SCALE,16*SCALE), 1)
            """
            pygame.display.flip()


class MetaMetaTile(pygame.sprite.Sprite):
    def __init__(self, app, x, y, index):
        self.groups = app.metametatile_sprite_group
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.metatiles = app.metametatiles[index]

        self.index = index

        self.arr = np.zeros((32, 32), dtype=int)
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
            self.arr[arr_y:arr_y+16, arr_x:arr_x+16] = metatile.arr
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.arr, self.app.palettes, 0).T), (32 * SCALE, 32 * SCALE))

    def check_click(self, pos):
        pass


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

    def check_click(self, pos):
        if self.app.mode == 'metatiles':
            if self.rect.collidepoint(pos):
                # for now it's 32 because we're scaling by 4
                x = (pos[0] - self.rect.x) // (SCALE * 8)
                y = (pos[1] - self.rect.y) // (SCALE * 8)
                metatile_index = y * 2 + x
                self.tiles[metatile_index] = self.app.selected_tile
                self.palette = self.app.selected_palette
                self.app.metatile_palettes[self.index] = self.app.selected_palette

    def update_tiles(self):
        for i in range(4):
            tile = self.tiles[i]
            table_y = tile // 16
            table_x = tile % 16
            arr_x = i % 2 * 8
            arr_y = i // 2 * 8
            self.arr[arr_y:arr_y+8, arr_x:arr_x+8] = self.app.table_a[table_y*8:table_y*8+8, table_x*8:table_x*8+8]
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.arr, self.app.palettes, self.palette).T), (16 * SCALE, 16 * SCALE))

    def update(self):
        self.update_tiles()


class Tiles(pygame.sprite.Sprite):
    def __init__(self, app, x, y):
        self.groups = app.tile_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.tile = self.app.table_a
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.tile, self.app.palettes, self.app.selected_palette).T), (128 * SCALE, 128 * SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.app.mode == 'tiles':
            if self.rect.collidepoint(pos):
                x = pos[0] - self.rect.x
                y = pos[1] - self.rect.y
                self.tile[y//SCALE, x//SCALE] = self.app.palette_index
                self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.tile, self.app.palettes, self.app.selected_palette).T), (128 * SCALE, 128 * SCALE))
        elif self.app.mode == 'metatiles':
            if self.rect.collidepoint(pos):
                # for now it's 32 because we're scaling by 4
                x = (pos[0] - self.rect.x) // (SCALE * 8)
                y = (pos[1] - self.rect.y) // (SCALE * 8)
                tile_index = y * 16 + x
                self.app.selected_tile = tile_index

    def update(self):
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(self.tile, self.app.palettes, self.app.selected_palette).T), (128 * SCALE, 128 * SCALE))


class ColorScale(pygame.sprite.Sprite):
    def __init__(self, app, x, y, palette):
        self.groups = app.tile_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.app = app
        self.palette = palette
        self.image = pygame.transform.scale(pygame.surfarray.make_surface(colorize(np.array([[0,1,2,3]]), self.app.palettes, self.palette).T), (16 * SCALE,4 * SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            x = (pos[0] - self.rect.x) // (SCALE * 4)
            self.app.selected_palette = self.palette
            self.app.palette_index = x


if __name__ == '__main__':
    """
    table_a, table_b = read_file('sprites.chr')
    with open("a.txt", "r") as f:
        x = f.read().splitlines()
    x = [i.split() for i in x]
    x = np.array(x, dtype=int)
    attempt = to_binary(x)
    """


    app = App('sprites.chr')
    tiles = Tiles(app, 0, 0)
    color_scale_0 = ColorScale(app, 0, 128 * SCALE, 0)
    color_scale_1 = ColorScale(app, 0, 128 * SCALE + 4 * SCALE, 1)
    color_scale_2 = ColorScale(app, 0, 128 * SCALE + 8 * SCALE, 2)
    color_scale_3 = ColorScale(app, 0, 128 * SCALE + 12 * SCALE, 3)

    app.run()


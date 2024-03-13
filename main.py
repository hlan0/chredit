import json
import os
import numpy as np
import matplotlib.pyplot as plt
import pygame
import tkinter as tk

from tkinter import filedialog
from pygame.locals import HWSURFACE, DOUBLEBUF, RESIZABLE

from graphical_rendering import Selection, Room, MetaTile, MetaMetaTile, ColorScale, Tiles


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


class App:
    def __init__(self, file_path=None):
        if file_path is not None:
            self.table_a, self.table_b = read_file(file_path)
        else:
            self.table_a = np.zeros((128, 128), dtype=int)
            self.table_b = np.zeros((128, 128), dtype=int)

        root = tk.Tk()
        root.withdraw()

        self.SCALE = 2

        pygame.init()
        self.screen = pygame.display.set_mode((800, 800), HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.tile_sprites = pygame.sprite.Group()
        self.metatile_sprite_group = pygame.sprite.Group()
        self.metametatile_sprite_group = pygame.sprite.Group()
        self.room_sprite_group = pygame.sprite.Group()
        self.running = False

        self.palettes = [
            ["0x0f", "0x13", "0x23", "0x30"],
            ["0x0f", "0x16", "0x26", "0x37"],
            ["0x0f", "0x0c", "0x1c", "0x2c"],
            ["0x0f", "0x29", "0x38", "0x30"]
        ]

        self.selected_palette = 0
        self.palette_index = 0

        self.initialize_data()

        self.selected_tile = 0
        self.selected_metatile = 0
        self.selected_metametatile = 0
        self.active_room = 0
        self.selection = Selection(self, 0, 0, 8)
        self.show_selection = False

        self.mode = 'tiles'

    def initialize_data(self):
        self.tiles = Tiles(self, 0, 0)

        self.metatiles = [[1, 2, 17, 18] for i in range(48)]
        self.metatile_palettes = [0] * 48
        self.metatile_sprites = []
        for i in range(48):
            x = (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = i // 6 * 16 * self.SCALE
            self.metatile_sprites.append(MetaTile(self, x, y, i))

        self.metametatiles = [[0, 1, 2, 3] for i in range(48)]
        self.metametatile_sprites = []
        for i in range(48):
            x = (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = i // 6 * 16 * self.SCALE
            self.metametatile_sprites.append(MetaMetaTile(self, x, y, i))

        self.rooms = [np.zeros((6, 8), dtype=int) for i in range(48)]
        self.room_sprites = []
        for i in range(48):
            x = 128 * self.SCALE
            y = 0
            self.room_sprites.append(Room(self, x, y, i))

    def export(self):
        serialized = {
            'table_a': self.table_a.tolist(),
            'table_b': self.table_b.tolist(),
            'metatiles': self.metatiles,
            'metatile_palettes': self.metatile_palettes,
            'metametatiles': self.metametatiles,
            'rooms': [room.tolist() for room in self.rooms]
        }
        try:
            file_path = filedialog.asksaveasfilename(initialdir=".")
            with open(file_path, 'w') as file:
                json.dump(serialized, file)
        except:
            pass

    def import_data(self):
        try:
            file_path = filedialog.askopenfilename(initialdir=".")
            with open(file_path, 'r') as file:
                serialized = json.load(file)
            self.table_a = np.array(serialized['table_a'])
            self.table_b = np.array(serialized['table_b'])
            self.metatiles = serialized['metatiles']
            self.metatile_palettes = serialized['metatile_palettes']
            self.metametatiles = serialized['metametatiles']
            self.rooms = [np.array(room) for room in serialized['rooms']]

            self.tiles.tile = self.table_a
            for mt in self.metatile_sprites:
                mt.tiles = self.metatiles[mt.index]
            for mmt in self.metametatile_sprites:
                mmt.metatiles = self.metametatiles[mmt.index]
            for room in self.room_sprites:
                room.metametatiles = self.rooms[room.index]
        except:
            pass

    def save(self):
        a = to_binary(self.table_a) + to_binary(self.table_b)
        binary_data = bytes(int(a, 2).to_bytes((len(a) + 7) // 8, byteorder='big'))
        with open("a.chr", "wb") as f:
            f.write(binary_data)

    def write_to_file(self, destination_folder):
        with open(os.path.join(destination_folder, "metatiles.h"), "w") as file:
            file.write('const unsigned char metatiles[] = {\n')
            for i in range(48):
                file.write('\t')
                for j in range(4):
                    file.write(f'{self.metatiles[i][j]}, ')
                file.write(f'{self.metatile_palettes[i]}, ')
                file.write('\n')
            file.write('};\n\n')

        with open(os.path.join(destination_folder, "metametatiles.h"), "w") as file:
            file.write('const unsigned char metametatiles[] = {\n')
            for i in range(48):
                file.write('\t')
                for j in range(4):
                    file.write(f'{self.metametatiles[i][j]}, ')
                file.write('\n')
            file.write('};\n\n')

        with open(os.path.join(destination_folder, "rooms.h"), "w") as file:
            for i in range(48):
                file.write(f'const unsigned char room_{i}[] = ')
                file.write('{\n')
                for j in range(6):
                    file.write('\t')
                    for k in range(8):
                        file.write(f'{self.rooms[i][j][k]}, ')
                    file.write('\n')
                file.write('};\n\n')

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # replace with UI
                if event.key == pygame.K_o:
                    try:
                        file_path = filedialog.askopenfilename(initialdir=".")
                        self.table_a, self.table_b = read_file(file_path)
                        self.tiles.tile = self.table_a
                    except:
                        pass
                if event.key == pygame.K_RIGHT and self.mode == 'rooms':
                    self.active_room = (self.active_room + 1) % 48
                if event.key == pygame.K_LEFT and self.mode == 'rooms':
                    self.active_room = (self.active_room - 1) % 48

                if event.key == pygame.K_e:
                    self.export()
                if event.key == pygame.K_i:
                    self.import_data()
                   
                if event.key == pygame.K_s:
                    self.save()
                if event.key == pygame.K_1:
                    self.mode = 'tiles'
                if event.key == pygame.K_2:
                    self.mode = 'metatiles'
                    for sprite in self.metatile_sprites:
                        for i in range(48):
                            x = (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
                            y = i // 6 * 16 * self.SCALE
                            self.metatile_sprites[i].rect.x = x
                            self.metatile_sprites[i].rect.y = y

                if event.key == pygame.K_3:
                    self.mode = 'metametatiles'
                    for sprite in self.metatile_sprites:
                        for i in range(48):
                            x = (0 * self.SCALE) + (i % 6 * 16 * self.SCALE)
                            y = i // 6 * 16 * self.SCALE
                            self.metatile_sprites[i].rect.x = x
                            self.metatile_sprites[i].rect.y = y
                    for sprite in self.metametatile_sprites:
                        for i in range(48):
                            x = (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
                            y = i // 6 * 16 * self.SCALE
                            self.metametatile_sprites[i].rect.x = x
                            self.metametatile_sprites[i].rect.y = y

                if event.key == pygame.K_4:
                    self.mode = 'rooms'
                    for sprite in self.metametatile_sprites:
                        for i in range(48):
                            x = (0 * self.SCALE) + (i % 6 * 16 * self.SCALE)
                            y = i // 6 * 16 * self.SCALE
                            self.metametatile_sprites[i].rect.x = x
                            self.metametatile_sprites[i].rect.y = y

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for sprite in self.tile_sprites.sprites() + self.metatile_sprite_group.sprites() + self.metametatile_sprite_group.sprites() + self.room_sprite_group.sprites():
                        sprite.check_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                #x, y = event.pos[0] // (8 * self.SCALE), event.pos[1] // (8 * SCALE)
                #self.selection.rect.x = x * (8 * SCALE)
                #self.selection.rect.y = y * (8 * SCALE)
                for sprite in self.tile_sprites.sprites() + self.metatile_sprite_group.sprites() + self.metametatile_sprite_group.sprites() + self.room_sprite_group.sprites():
                    sprite.check_mouseover(event.pos)
                    if event.buttons[0]:
                        sprite.check_click(event.pos)

    def run(self):
        self.running = True
        while self.running:
            self.screen.fill((0, 0, 0))
            self.events()
            if self.mode == 'tiles' or self.mode == 'metatiles':
                self.tile_sprites.update()
                self.tile_sprites.draw(self.screen)
            if self.mode == 'metametatiles' or self.mode == 'rooms':
                self.metametatile_sprite_group.update()
                self.metametatile_sprite_group.draw(self.screen)
            if self.mode == 'metatiles' or self.mode == 'metametatiles':
                self.metatile_sprite_group.update()
                self.metatile_sprite_group.draw(self.screen)

            if self.mode == 'rooms':
                self.room_sprite_group.update()
                self.screen.blit(self.room_sprites[self.active_room].image, self.room_sprites[self.active_room].rect)

            if self.mode != 'tiles':
                self.screen.blit(self.selection.image, self.selection.rect)
            """
            for i in range(8):
                for j in range(8):
                    pygame.draw.rect(self.screen, (64,64,64), (i*16*SCALE,j*16*SCALE,16*SCALE,16*SCALE), 1)
            """
            pygame.display.flip()




if __name__ == '__main__':
    """
    table_a, table_b = read_file('sprites.chr')
    with open("a.txt", "r") as f:
        x = f.read().splitlines()
    x = [i.split() for i in x]
    x = np.array(x, dtype=int)
    attempt = to_binary(x)
    """


    app = App()
    color_scale_0 = ColorScale(app, 0, 128 * app.SCALE, 0)
    color_scale_1 = ColorScale(app, 0, 128 * app.SCALE + 4 * app.SCALE, 1)
    color_scale_2 = ColorScale(app, 0, 128 * app.SCALE + 8 * app.SCALE, 2)
    color_scale_3 = ColorScale(app, 0, 128 * app.SCALE + 12 * app.SCALE, 3)

    app.run()

import json
import os
import numpy as np
import pygame
import tkinter as tk

from tkinter import filedialog
from pygame.locals import HWSURFACE, DOUBLEBUF, RESIZABLE

from graphical_rendering import Selection, Room, MetaTile, MetaMetaTile, ColorScale, Tiles, ColorTile, PALETTE_MAP, Button


def read_file(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()

    byte_str = ''
    for byte in raw_data:
        byte_str += bin(byte)[2:].zfill(8)
    byte_list = list(byte_str)

    patterns = []
    for i in range(0, len(byte_list), 128):
        map1 = []
        for j in range(0, 64, 8):
            row = byte_list[i+j:i+j+8]
            map1.append(row)

        map2 = []
        for j in range(64, 128, 8):
            row = byte_list[i+j:i+j+8]
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


class App:
    def __init__(self, file_path=None):
        if file_path is not None:
            self.table_a, self.table_b = read_file(file_path)
        else:
            self.table_a = np.zeros((128, 128), dtype=int)
            self.table_b = np.zeros((128, 128), dtype=int)

        self.SCALE = 4

        pygame.init()

        self.screen = pygame.display.set_mode((800, 800), HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.tile_sprites = pygame.sprite.Group()
        self.metatile_sprite_group = pygame.sprite.Group()
        self.metametatile_sprite_group = pygame.sprite.Group()
        self.room_sprite_group = pygame.sprite.Group()
        self.running = False

        self.palettes = [
            ["0x0f", "0x01", "0x11", "0x21"],
            ["0x0f", "0x05", "0x15", "0x25"],
            ["0x0f", "0x08", "0x18", "0x28"],
            ["0x0f", "0x0a", "0x1a", "0x2a"]
        ]

        self.selected_palette = 0
        self.palette_index = 0

        self.selected_tile = 0
        self.selected_metatile = 0
        self.selected_metametatile = 0
        self.active_room = 0
        self.selection = Selection(self, 8, 8, 8)
        self.show_selection = False
        self.selected_color_x = 0
        self.selected_color_y = 0

        self.mode = 'metatiles'

        self.font = pygame.font.Font(None, 8 * self.SCALE)

        self.initialize_data()

        self.text_left = self.font.render("Tiles", True, (255, 255, 255))
        self.text_right = self.font.render("Metatiles", True, (255, 255, 255))
        self.palette_text = self.font.render("Palettes", True, (255, 255, 255))

    def initialize_data(self):
        self.tiles = Tiles(self, 8, 32 * self.SCALE)

        self.metatiles = [[0, 0, 0, 0] for i in range(48)]
        self.metatile_palettes = [0] * 48
        self.metatile_sprites = []
        for i in range(48):
            x = 16 + (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = (32 * self.SCALE) + i // 6 * 16 * self.SCALE
            self.metatile_sprites.append(MetaTile(self, x, y, i))

        self.metametatiles = [[0, 0, 0, 0] for i in range(48)]
        self.metametatile_sprites = []
        for i in range(48):
            x = 16 + (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = 8 + i // 6 * 16 * self.SCALE
            self.metametatile_sprites.append(MetaMetaTile(self, x, y, i))

        self.rooms = [np.zeros((6, 8), dtype=int) for i in range(48)]
        self.room_sprites = []
        for i in range(48):
            x = 16 + 128 * self.SCALE
            y = 32 * self.SCALE
            self.room_sprites.append(Room(self, x, y, i))

        self.color_scales = []
        for i in range(4):
            x = 8
            y = (128 * self.SCALE) + (40 * self.SCALE) + 8 + i * 4 * self.SCALE
            if self.selected_color_x == 0 and self.selected_color_y == 0:
                self.selected_color_x = x - 1
                self.selected_color_y = y - 1
            self.color_scales.append(ColorScale(self, x, y, i))
        
        for i in range(len(PALETTE_MAP)):
            x = 8 + (64 * self.SCALE) + (i % 16) * 4 * self.SCALE
            y = (128 * self.SCALE) + (40 * self.SCALE) + 8 + (i // 16) * 4 * self.SCALE
            a = ColorTile(self, x, y, i)
        
        self.buttons = [
            Button(self, 8, 8, 24 * self.SCALE, 8 * self.SCALE, "CHR", self.open_chr_file),
            Button(self, 24 * self.SCALE + 16, 8, 24 * self.SCALE, 8 * self.SCALE, "Load", self.import_data),
            Button(self, 48 * self.SCALE + 24, 8, 24 * self.SCALE, 8 * self.SCALE, "Save", self.export),
            Button(self, 72 * self.SCALE + 32, 8, 24 * self.SCALE, 8 * self.SCALE, "Export", self.write_to_file),

            Button(self, 96 * self.SCALE + 40, 8, 32 * self.SCALE, 8 * self.SCALE, "Metatiles", self.switch_mode_metatiles),
            Button(self, 128 * self.SCALE + 48, 8, 56 * self.SCALE, 8 * self.SCALE, "Metametatiles", self.switch_mode_metametatiles),
            Button(self, 184 * self.SCALE + 56, 8, 24 * self.SCALE, 8 * self.SCALE, "Rooms", self.switch_mode_rooms),
            Button(self, 208 * self.SCALE + 64, 8, 16 * self.SCALE, 8 * self.SCALE, "X", self.quit)
        ]

        self.room_buttons = [
            Button(self, 16 + 128 * self.SCALE, (32 * self.SCALE) + 8 + 96 * self.SCALE, 8 * self.SCALE, 8 * self.SCALE, "<", self.decrease_room),
            Button(self, 32 + (8 * self.SCALE) + 128 * self.SCALE, (32 * self.SCALE) + 8 + 96 * self.SCALE, 8 * self.SCALE, 8 * self.SCALE, ">", self.increase_room)
        ]
    
    def increase_room(self):
        if self.mode == 'rooms':
            self.active_room = (self.active_room + 1) % 48
            self.text_right = self.font.render(f"Room {self.active_room}", True, (255, 255, 255))
    
    def decrease_room(self):
        if self.mode == 'rooms':
            self.active_room = (self.active_room - 1) % 48
            self.text_right = self.font.render(f"Room {self.active_room}", True, (255, 255, 255))
    
    def export(self):
        serialized = {
            'palettes': self.palettes,
            'table_a': self.table_a.tolist(),
            'table_b': self.table_b.tolist(),
            'metatiles': self.metatiles,
            'metatile_palettes': self.metatile_palettes,
            'metametatiles': self.metametatiles,
            'rooms': [room.tolist() for room in self.rooms]
        }
        try:
            file_path = filedialog.asksaveasfilename(initialdir=".", filetypes=[("JSON Files", "*.json")])
            with open(file_path, 'w') as file:
                json.dump(serialized, file)
        except:
            pass

    def import_data(self):
        try:
            file_path = filedialog.askopenfilename(initialdir=".", filetypes=[("JSON Files", "*.json")])

            with open(file_path, 'r') as file:
                serialized = json.load(file)
            self.table_a = np.array(serialized['table_a'])
            self.table_b = np.array(serialized['table_b'])
            self.metatiles = serialized['metatiles']
            self.metatile_palettes = serialized['metatile_palettes']
            self.metametatiles = serialized['metametatiles']
            self.rooms = [np.array(room) for room in serialized['rooms']]
            self.palettes = serialized['palettes']

            self.tiles.raw_tiles = self.table_a
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

    def write_to_file(self):
        destination_folder = filedialog.askdirectory(initialdir=".")
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

        with open(os.path.join(destination_folder, "palettes.h"), "w") as file:
            file.write('const unsigned char palettes[] = {\n')
            for i in range(4):
                file.write('\t')
                for j in range(4):
                    file.write(f'{self.palettes[i][j]}, ')
                file.write('\n')
            file.write('};\n\n')
    
    def open_chr_file(self):
        try:
            file_path = filedialog.askopenfilename(initialdir=".")
            self.table_a, self.table_b = read_file(file_path)
            self.tiles.raw_tiles = self.table_a
        except:
            pass

    def switch_mode_tiles(self):
        self.mode = 'tiles'
    
    def switch_mode_metatiles(self):
        self.mode = 'metatiles'
        for i in range(48):
            x = 16 + (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = (32 * self.SCALE) + i // 6 * 16 * self.SCALE
            self.metatile_sprites[i].update_pos(x, y)
        self.text_left = self.font.render("Tiles", True, (255, 255, 255))
        self.text_right = self.font.render("Metatiles", True, (255, 255, 255))

    def switch_mode_metametatiles(self):
        self.mode = 'metametatiles'
        for i in range(48):
            x = 8 + (0 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = (32 * self.SCALE) + i // 6 * 16 * self.SCALE
            self.metatile_sprites[i].update_pos(x, y)
        for i in range(48):
            x = 16 + (128 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = (32 * self.SCALE) + i // 6 * 16 * self.SCALE
            self.metametatile_sprites[i].update_pos(x, y)
        self.text_left = self.font.render("Metatiles", True, (255, 255, 255))
        self.text_right = self.font.render("Metametatiles", True, (255, 255, 255))
    
    def switch_mode_rooms(self):
        self.mode = 'rooms'
        for i in range(48):
            x = 8 + (0 * self.SCALE) + (i % 6 * 16 * self.SCALE)
            y = (32 * self.SCALE) + i // 6 * 16 * self.SCALE
            self.metametatile_sprites[i].update_pos(x, y)
        self.text_left = self.font.render("Metametatiles", True, (255, 255, 255))
        self.text_right = self.font.render(f"Room {self.active_room}", True, (255, 255, 255))
    
    def quit(self):
        self.running = False

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for sprite in self.tile_sprites.sprites() + self.metatile_sprite_group.sprites() + self.metametatile_sprite_group.sprites() + self.room_sprite_group.sprites() + self.buttons + self.room_buttons:
                        sprite.check_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                for sprite in self.tile_sprites.sprites() + self.metatile_sprite_group.sprites() + self.metametatile_sprite_group.sprites() + self.room_sprite_group.sprites() + self.buttons + self.room_buttons:
                    sprite.check_mouseover(event.pos)
                    if event.buttons[0]:
                        sprite.check_click(event.pos)

    def run(self):
        self.running = True
        while self.running:
            self.screen.fill((12, 12, 12))
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
            
            for button in self.buttons:
                button.draw()
            
            if self.mode == 'rooms':
                for button in self.room_buttons:
                    button.draw()
            
            self.screen.blit(self.text_left, (8, 24 * self.SCALE))
            self.screen.blit(self.text_right, (16 + 128 * self.SCALE, 24 * self.SCALE))

            if self.mode == 'metatiles':
                self.screen.blit(self.palette_text, (8, (32 * self.SCALE) + (128 * self.SCALE) + 8))
                pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(self.selected_color_x,self.selected_color_y,4 * self.SCALE + 2,4*self.SCALE + 2), self.SCALE // 2)
            
            pygame.display.flip()


if __name__ == '__main__':
    app = App()
    app.run()

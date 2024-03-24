import json
import os
import numpy as np
import pygame
import tkinter as tk

from tkinter import filedialog
from pygame.locals import HWSURFACE, DOUBLEBUF, RESIZABLE

from entities import Selection, Room, MetaTile, MetaMetaTile, ColorScale, Tiles, ColorTile, Button
from file_io import FileIO
from ui_renderer import UIRenderer
from constants import *


class App:
    """
    Main application class. Handles the main loop and event handling.
    """
    def __init__(self) -> None:
        self.table_a = np.zeros((128, 128), dtype=int)
        self.table_b = np.zeros((128, 128), dtype=int)
        self.file_io = FileIO()
        self.ui_renderer = UIRenderer(self)

        root = tk.Tk()
        root.withdraw()

        pygame.init()

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), HWSURFACE | DOUBLEBUF | RESIZABLE)
        self.running = False

        self.palettes = [
            ['0x0f', '0x01', '0x11', '0x21'],
            ['0x0f', '0x05', '0x15', '0x25'],
            ['0x0f', '0x08', '0x18', '0x28'],
            ['0x0f', '0x0a', '0x1a', '0x2a']
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

        self.font = pygame.font.Font(None, 8 * SCALE)

        self.text_left = self.font.render('Tiles', True, WHITE)
        self.text_right = self.font.render('Metatiles', True, WHITE)
        self.palette_text = self.font.render('Palettes', True, WHITE)

        self.metatiles = [[0, 0, 0, 0] for i in range(48)]
        self.metatile_palettes = [0] * 48
        self.metametatiles = [[0, 0, 0, 0] for i in range(48)]
        self.rooms = [np.zeros((6, 8), dtype=int) for i in range(48)]

        self.initialize_panels()
        self.initialize_buttons()
        self.initialize_colors()

    def initialize_buttons(self) -> None:
        """
        Initializes the buttons in the UI.
        """
        button_height = 8
        button_x = MARGIN_LEFT

        button_labels = ['CHR', 'Load', 'Save', 'Export',
                         'Metatiles', 'Metametatiles', 'Rooms', 'Exit']
        button_functions = [self.open_chr_file, self.import_data, self.export, self.write_to_file,
                            self.switch_mode_metatiles, self.switch_mode_metametatiles,
                            self.switch_mode_rooms, self.quit]

        for i, label in enumerate(button_labels):
            button_width = 24 if len(label) <= 6 else 48
            self.ui_renderer.menu_buttons.append(Button(
                self, button_x, MARGIN_TOP, button_width * SCALE, button_height * SCALE, label,
                button_functions[i]))
            button_x += button_width * SCALE + SPACING

        self.ui_renderer.arrow_buttons = [
            Button(self, 16 + 128 * SCALE, (32 * SCALE) + 8 + 96 * SCALE,
                   8 * SCALE, 8 * SCALE, '<', self.decrease_room),
            Button(self, 32 + (8 * SCALE) + 128 * SCALE, (32 * SCALE) +
                   8 + 96 * SCALE, 8 * SCALE, 8 * SCALE, '>', self.increase_room)
        ]

    def initialize_panels(self) -> None:
        """
        Initializes the panels in the UI.
        """
        self.tiles = Tiles(self, MARGIN_LEFT, PANEL_Y)

        tile_size = 16 * SCALE

        for i in range(48):
            offset_x = i % 6 * tile_size
            offset_y = i // 6 * tile_size
            x = RIGHT_PANEL_X + offset_x
            y = PANEL_Y + offset_y
            self.ui_renderer.metatile_sprites.append(MetaTile(self, x, y, i))

        for i in range(48):
            offset_x = i % 6 * tile_size
            offset_y = i // 6 * tile_size
            x = RIGHT_PANEL_X + offset_x
            y = PANEL_Y + offset_y
            self.ui_renderer.metametatile_sprites.append(
                MetaMetaTile(self, x, y, i))

        for i in range(48):
            x = RIGHT_PANEL_X
            y = PANEL_Y
            self.ui_renderer.room_sprites.append(Room(self, x, y, i))

    def initialize_colors(self) -> None:
        """
        Initializes the color scales and color tiles in the UI.
        """
        color_tile_size = 4 * SCALE

        self.color_scales = []
        for i in range(4):
            x = MARGIN_LEFT
            offset_y = i * color_tile_size
            y = BOTTOM_PANEL_Y + 8 * SCALE + offset_y
            if self.selected_color_x == 0 and self.selected_color_y == 0:
                self.selected_color_x = x - 1
                self.selected_color_y = y - 1
            self.color_scales.append(ColorScale(self, x, y, i))

        self.all_colors = []
        for i in range(len(PALETTE_MAP)):
            offset_x = i % 16 * color_tile_size
            offset_y = i // 16 * color_tile_size
            x = MARGIN_LEFT + 64 * SCALE + offset_x
            y = BOTTOM_PANEL_Y + 8 * SCALE + offset_y
            self.all_colors.append(ColorTile(self, x, y, i))

    def increase_room(self) -> None:
        """
        Increases the active room index.
        """
        if self.mode == 'rooms':
            self.active_room = (self.active_room + 1) % 48
            self.text_right = self.font.render(
                f'Room {self.active_room}', True, WHITE)

    def decrease_room(self) -> None:
        """
        Decreases the active room index.
        """
        if self.mode == 'rooms':
            self.active_room = (self.active_room - 1) % 48
            self.text_right = self.font.render(
                f'Room {self.active_room}', True, WHITE)

    def export(self) -> None:
        """
        Exports the data to a JSON file.
        """
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
            file_path = filedialog.asksaveasfilename(
                initialdir='.', filetypes=[('JSON Files', '*.json')])
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(serialized, file)
        except FileNotFoundError:
            print('Could not save file: File not found')
        except json.JSONDecodeError:
            print('Could not save file: JSON decode error')

    def import_data(self):
        """
        Imports data from a JSON file.
        """
        try:
            file_path = filedialog.askopenfilename(
                initialdir='.', filetypes=[('JSON Files', '*.json')])

            with open(file_path, 'r', encoding='utf-8') as file:
                serialized = json.load(file)
            self.table_a = np.array(serialized['table_a'])
            self.table_b = np.array(serialized['table_b'])
            self.metatiles = serialized['metatiles']
            self.metatile_palettes = serialized['metatile_palettes']
            self.metametatiles = serialized['metametatiles']
            self.rooms = [np.array(room) for room in serialized['rooms']]
            self.palettes = serialized['palettes']

            self.tiles.raw_tiles = self.table_a
            for metatile in self.ui_renderer.metatile_sprites:
                metatile.tiles = self.metatiles[metatile.index]
            for metametatile in self.ui_renderer.metametatile_sprites:
                metametatile.metatiles = self.metametatiles[metametatile.index]
            for room in self.ui_renderer.room_sprites:
                room.metametatiles = self.rooms[room.index]
        except FileNotFoundError:
            print('Could not load file: File not found')
        except json.JSONDecodeError:
            print('Could not load file: JSON decode error')

    def write_to_file(self) -> None:
        """
        Exports data to C header files.
        """
        destination_folder = filedialog.askdirectory(initialdir='.')
        try:
            with open(os.path.join(destination_folder, 'metatiles.h'), 'w', encoding='utf-8') as file:
                file.write('const unsigned char metatiles[] = {\n')
                for i in range(48):
                    file.write('\t')
                    for j in range(4):
                        file.write(f'{self.metatiles[i][j]}, ')
                    file.write(f'{self.metatile_palettes[i]}, ')
                    file.write('\n')
                file.write('};\n\n')

            with open(os.path.join(destination_folder, 'metametatiles.h'), 'w', encoding='utf-8') as file:
                file.write('const unsigned char metametatiles[] = {\n')
                for i in range(48):
                    file.write('\t')
                    for j in range(4):
                        file.write(f'{self.metametatiles[i][j]}, ')
                    file.write('\n')
                file.write('};\n\n')

            with open(os.path.join(destination_folder, 'rooms.h'), 'w', encoding='utf-8') as file:
                for i in range(48):
                    file.write(f'const unsigned char room_{i}[] = ')
                    file.write('{\n')
                    for j in range(6):
                        file.write('\t')
                        for k in range(8):
                            file.write(f'{self.rooms[i][j][k]}, ')
                        file.write('\n')
                    file.write('};\n\n')

            with open(os.path.join(destination_folder, 'palettes.h'), 'w', encoding='utf-8') as file:
                file.write('const unsigned char palettes[] = {\n')
                for i in range(4):
                    file.write('\t')
                    for j in range(4):
                        file.write(f'{self.palettes[i][j]}, ')
                    file.write('\n')
                file.write('};\n\n')
        except FileNotFoundError:
            print('Could not save files: File not found')
        except NotADirectoryError:
            print('Could not save files: Not a directory')
        except IOError:
            print('Could not save files: IO Error')

    def open_chr_file(self) -> None:
        """
        Opens a CHR file and reads the data.
        """
        try:
            file_path = filedialog.askopenfilename(
                initialdir=".", filetypes=[('CHR Files', '*.chr')])
            self.table_a, self.table_b = self.file_io.read_file(file_path)
            self.tiles.raw_tiles = self.table_a
        except FileNotFoundError:
            print('Could not open file: File not found')

    def switch_mode_tiles(self) -> None:
        """
        Switches the mode to tiles.
        """
        self.mode = 'tiles'

    def switch_mode_metatiles(self) -> None:
        """
        Switches the mode to metatiles.
        """
        self.mode = 'metatiles'
        for i in range(48):
            x = 16 + (128 * SCALE) + (i % 6 * 16 * SCALE)
            y = PANEL_Y + i // 6 * 16 * SCALE
            self.ui_renderer.metatile_sprites[i].update_pos(x, y)
        self.text_left = self.font.render('Tiles', True, WHITE)
        self.text_right = self.font.render('Metatiles', True, WHITE)

    def switch_mode_metametatiles(self) -> None:
        """
        Switches the mode to metametatiles.
        """
        self.mode = 'metametatiles'
        for i in range(48):
            x = 8 + (0 * SCALE) + (i % 6 * 16 * SCALE)
            y = PANEL_Y + i // 6 * 16 * SCALE
            self.ui_renderer.metatile_sprites[i].update_pos(x, y)
        for i in range(48):
            x = 16 + (128 * SCALE) + (i % 6 * 16 * SCALE)
            y = PANEL_Y + i // 6 * 16 * SCALE
            self.ui_renderer.metametatile_sprites[i].update_pos(x, y)
        self.text_left = self.font.render('Metatiles', True, WHITE)
        self.text_right = self.font.render('Metametatiles', True, WHITE)

    def switch_mode_rooms(self) -> None:
        """
        Switches the mode to rooms.
        """
        self.mode = 'rooms'
        for i in range(48):
            x = 8 + (0 * SCALE) + (i % 6 * 16 * SCALE)
            y = PANEL_Y + i // 6 * 16 * SCALE
            self.ui_renderer.metametatile_sprites[i].update_pos(x, y)
        self.text_left = self.font.render('Metametatiles', True, WHITE)
        self.text_right = self.font.render(
            f'Room {self.active_room}', True, WHITE)

    def quit(self) -> None:
        """
        Quits the application.
        """
        self.running = False

    def events(self) -> None:
        """
        Handles events in the main loop.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for sprite in self.ui_renderer.all_sprites:
                        sprite.check_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                for sprite in self.ui_renderer.all_sprites:
                    sprite.check_mouseover(event.pos)
                    if event.buttons[0]:
                        sprite.check_click(event.pos)

    def run(self) -> None:
        """
        Main loop of the application.
        """
        self.running = True
        while self.running:
            self.screen.fill((12, 12, 12))
            self.events()

            self.ui_renderer.render_ui()

            self.screen.blit(self.text_left, (MARGIN_LEFT, MENU_HEIGHT))
            self.screen.blit(self.text_right, (RIGHT_PANEL_X, MENU_HEIGHT))

            if self.mode == 'metatiles':
                self.screen.blit(self.palette_text,
                                 (MARGIN_LEFT, BOTTOM_PANEL_Y))
                pygame.draw.rect(self.screen, WHITE, pygame.Rect(
                    self.selected_color_x, self.selected_color_y, 4 * SCALE + 2, 4*SCALE + 2), SCALE // 2)

            pygame.display.flip()


if __name__ == '__main__':
    app = App()
    app.run()

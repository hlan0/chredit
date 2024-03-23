from __future__ import annotations

import pygame


class UIRenderer:
    """
    UIRenderer class is responsible for rendering the UI elements of the application.
    """
    def __init__(self, app: App) -> None:
        self.app = app
        self.tile_sprites = []
        self.room_sprites = []
        self.menu_buttons = []
        self.arrow_buttons = []
        self.metatile_sprites = []
        self.metametatile_sprites = []
        self.all_sprites = []

    def render_ui(self) -> None:
        """
        Renders the UI elements of the application.
        """
        if self.app.mode in ['tiles', 'metatiles']:
            for sprite in self.tile_sprites:
                sprite.update()
                sprite.draw()

        if self.app.mode in ['metametatiles', 'rooms']:
            for sprite in self.metametatile_sprites:
                sprite.update()
                sprite.draw()

        if self.app.mode in ['metatiles', 'metametatiles']:
            for sprite in self.metatile_sprites:
                sprite.update()
                sprite.draw()

        if self.app.mode == 'rooms':
            self.room_sprites[self.app.active_room].update()
            self.room_sprites[self.app.active_room].draw()

        if self.app.mode != 'tiles':
            self.app.screen.blit(self.app.selection.image, self.app.selection.rect)

        for button in self.menu_buttons:
            button.draw()

        if self.app.mode == 'rooms':
            for button in self.arrow_buttons:
                button.draw()

import json
import os

import pygame
from appdirs import user_data_dir
from pygame.event import Event, post

import scenes.equip
import scenes.title
from button import ButtonComponent, render_all_buttons
from game_events import PAUSE_QUIT_TO_MENU, PAUSE_SAVE_AND_QUIT
from scene import Scene, SceneManager
from utils import APP_AUTHOR, APP_NAME, find_data_file


class CrashResultsScene(Scene):
    def __init__(self):
        self.regular_font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 42
        )
        self.huge_font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 80
        )

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        player_entity = world.find_entity("player")

        # Create a sprite for the header
        self.pause = pygame.sprite.Sprite()
        self.pause.image = self.huge_font.render("You Crashed!", 1, (200, 200, 200))
        self.pause.rect = self.pause.image.get_rect(
            centerx=background.get_width() // 2, centery=background.get_height() // 4
        )

        self.pause_help = pygame.sprite.Sprite()
        self.pause_help.image = self.regular_font.render(
            "Try hitting clouds, birds, or airplanes to get money for upgrades!",
            1,
            (200, 200, 200),
        )
        self.pause_help.rect = self.pause_help.image.get_rect(
            centerx=background.get_width() // 2, centery=background.get_height() // 2
        )

        self.pause_currency = pygame.sprite.Sprite()
        self.pause_currency.image = self.regular_font.render(
            f"Current money for upgrades: ${ player_entity.player.currency }",
            1,
            (200, 200, 200),
        )
        self.pause_currency.rect = self.pause_currency.image.get_rect(
            centerx=background.get_width() // 2,
            centery=background.get_height() // 2 + 100,
        )

        # menu setup
        men = [
            ("Quit", lambda: post(Event(PAUSE_QUIT_TO_MENU))),
            ("Save + Continue", lambda: post(Event(PAUSE_SAVE_AND_QUIT))),
        ]

        for idx, m in enumerate(men):
            offset = -((len(men) * 480) // 2) + 240

            rect = pygame.Rect(0, 0, 190, 49)
            rect.centerx = background.get_width() // 2 + (offset + (idx * 480))
            rect.centery = background.get_height() - 100

            button = world.gen_entity()
            button.attach(
                ButtonComponent(
                    rect,
                    m[0].upper(),
                    m[1],
                )
            )

        # Put all the sprites we want to render into a sprite group for easy adds and removes
        self.pause_screen = pygame.sprite.Group()
        self.pause_screen.add(self.pause)
        self.pause_screen.add(self.pause_help)
        self.pause_screen.add(self.pause_currency)

    def update(self, events, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        context["paused"] = True

        exiting = False

        for event in events:
            if event.type == PAUSE_QUIT_TO_MENU:
                context["paused"] = False
                exiting = True
            elif event.type == PAUSE_SAVE_AND_QUIT:
                self._save(settings["save_file"], world)
                context["paused"] = False
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "stop",
                        "sound": "background_music",
                    }
                )

                self.teardown(world)
                return SceneManager.replace(scenes.equip.EquipScene())

        if exiting:
            world.inject_event(
                {
                    "type": "sound",
                    "action": "stop",
                    "sound": "background_music",
                }
            )
            return SceneManager.new_root(scenes.title.TitleScene())

        world.process_all_systems(events)

    def render(self, world):
        context = world.find_component("context")

        screen = context["screen"]

        # Blit the text to the screen over top of the background surface
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, overlay.get_rect())

        # Render the static pause screen elements
        self.pause_screen.draw(screen)

        # Display the buttons
        render_all_buttons(screen, world)

    def _save(self, save_file, world):
        if not os.path.exists(user_data_dir(APP_NAME, APP_AUTHOR)):
            os.makedirs(user_data_dir(APP_NAME, APP_AUTHOR))
        f = open(os.path.join(user_data_dir(APP_NAME, APP_AUTHOR), save_file), "w")
        player_entity = world.find_entity("player")
        out = {
            "currency": player_entity.player.currency,
            "hasCloudSleeves": player_entity.player.hasCloudSleeves,
            "hasWings": player_entity.player.hasWings,
            "hasJetBoots": player_entity.player.hasJetBoots,
            "extraFuel": player_entity.player.extraFuel,
        }
        f.write(json.dumps(out))
        f.close()

    def render_previous(self):
        return True

    def teardown(self, world):
        buttons = world.filter("button")

        world.remove_entities(buttons)

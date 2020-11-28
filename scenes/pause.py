import json
import os

import pygame
from appdirs import user_data_dir
from pygame.event import Event, post

import scenes.title
from button import ButtonComponent, render_all_buttons
from game_events import PAUSE_CONTINUE, PAUSE_QUIT_TO_MENU, PAUSE_SAVE_AND_QUIT
from scene import Scene, SceneManager
from utils import APP_AUTHOR, APP_NAME


class PauseScene(Scene):
    def __init__(self):
        self.regular_font = pygame.font.Font(None, 42)

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        # Create a sprite for the header
        self.pause = pygame.sprite.Sprite()
        self.pause.image = self.regular_font.render("Paused", 1, (200, 200, 200))
        self.pause.rect = self.pause.image.get_rect(
            centerx=background.get_width() // 2, centery=background.get_height() // 4
        )

        options = [
            ("Continue", lambda: post(Event(PAUSE_CONTINUE))),
            ("Save & Quit", lambda: post(Event(PAUSE_SAVE_AND_QUIT))),
            ("Quit to Menu", lambda: post(Event(PAUSE_QUIT_TO_MENU))),
        ]
        for idx, menu_item in enumerate(options):
            offset = 0

            rect = pygame.Rect(0, 0, 200, 60)
            rect.centerx = background.get_width() // 2
            rect.centery = background.get_height() // 2 + (offset + (idx * 70))

            button = world.gen_entity()
            button.attach(
                ButtonComponent(
                    pygame.Color("green"),
                    pygame.Color("red"),
                    rect,
                    menu_item[0].upper(),
                    pygame.Color("black"),
                    menu_item[1],
                )
            )

        # Put all the sprites we want to render into a sprite group for easy adds and removes
        self.pause_screen = pygame.sprite.Group()
        self.pause_screen.add(self.pause)

    def update(self, events, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        context["paused"] = True

        exiting = False

        for event in events:
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                context["paused"] = False
                return SceneManager.pop()
            elif event.type == PAUSE_CONTINUE:
                context["paused"] = False
                return SceneManager.pop()
            elif event.type == PAUSE_SAVE_AND_QUIT:
                self._save(settings["save_file"], world)
                context["paused"] = False
                exiting = True
            elif event.type == PAUSE_QUIT_TO_MENU:
                context["paused"] = False
                exiting = True

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
        }
        f.write(json.dumps(out))
        f.close()

    def render_previous(self):
        return True

    def teardown(self, world):
        buttons = world.filter("button")

        world.remove_entities(buttons)

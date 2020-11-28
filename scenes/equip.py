import json
import os

import pygame
from appdirs import user_data_dir
from pygame.event import Event, post

import scenes.title
from button import ButtonComponent, render_all_buttons
from game_events import EQUIP_QUIT, EQUIP_SAVE_AND_START
from scene import Scene, SceneManager
from scenes.game import GameScene
from utils import APP_AUTHOR, APP_NAME, find_data_file


class EquipScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(None, 36)

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        # menu setup
        men = []
        men.append(("Quit", lambda: post(Event(EQUIP_QUIT))))
        men.append(("Save + Start", lambda: post(Event(EQUIP_SAVE_AND_START))))

        for idx, m in enumerate(men):
            offset = -((len(men) * 70) // 2) + 100

            rect = pygame.Rect(0, 0, 200, 60)
            rect.centerx = background.get_width() // 2
            rect.centery = background.get_height() // 2 + (offset + (idx * 70))

            button = world.gen_entity()
            button.attach(
                ButtonComponent(
                    pygame.Color("green"),
                    pygame.Color("red"),
                    rect,
                    m[0].upper(),
                    pygame.Color("black"),
                    m[1],
                )
            )

    def update(self, events, world):
        settings = world.find_component("settings")

        for event in events:
            if event.type == EQUIP_QUIT:
                return SceneManager.new_root(scenes.title.TitleScene())
            if event.type == EQUIP_SAVE_AND_START:
                self._save(settings["save_file"], world)
                return SceneManager.new_root(GameScene())

        world.process_all_systems(events)

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]

        player_entity = world.find_entity("player")

        # Draw a nice background
        screen.blit(pygame.image.load(find_data_file("resources/bg_sky.png")), (0, 0))
        screen.blit(pygame.image.load(find_data_file("resources/bg_sky.png")), (0, 500))

        # text
        text = self.font.render(
            f"Currency: {player_entity.player.currency}", True, (245, 245, 245)
        )
        screen.blit(text, (50, 50))

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
        return False

    def teardown(self, world):
        buttons = world.filter("button")

        world.remove_entities(buttons)

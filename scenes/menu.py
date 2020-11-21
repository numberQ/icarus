from os import path

import pygame
from appdirs import user_data_dir
from pygame.event import Event, post

from button import ButtonComponent, render_all_buttons
from game_events import CONTINUE, NEW_GAME, QUIT
from scene import Scene, SceneManager
from scenes.game import GameScene
from utils import APP_AUTHOR, APP_NAME


class MenuScene(Scene):
    def __init__(self):
        pass

    def setup(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        background = context["background"]

        # menu setup
        men = []
        men.append(("New Game", lambda: post(Event(NEW_GAME))))
        if path.exists(
            path.join(user_data_dir(APP_NAME, APP_AUTHOR), settings["save_file"])
        ):
            men.append(("Continue", lambda: post(Event(CONTINUE))))
        men.append(("Quit", lambda: post(Event(QUIT))))

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
        for event in events:
            if event.type == NEW_GAME:
                return SceneManager.new_root(GameScene())
            if event.type == CONTINUE:
                # we have no data to save right now, so just start a fresh game if we have a save file
                return SceneManager.new_root(GameScene())
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return SceneManager.pop()

        world.process_all_systems(events)

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]

        # Display the buttons
        render_all_buttons(screen, world)

    def render_previous(self):
        return True

    def teardown(self, world):
        buttons = world.filter("button")

        world.remove_entities(buttons)

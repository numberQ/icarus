from os import path

import pygame
from appdirs import user_data_dir
from pygame.event import Event, post

from button import ButtonComponent, render_all_buttons
from game_events import CONTINUE, CONTROLS, CREDITS, LOAD, NEW_GAME, QUIT, SCENE_REFOCUS
from scene import Scene, SceneManager
from scenes.controls import ControlsScene
from scenes.credits import CreditsScene
from scenes.game import GameScene
from utils import APP_AUTHOR, APP_NAME


class MenuScene(Scene):
    def __init__(self):
        pass

    def setup(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        background = context["background"]

        # Create our player entity here, and we can extend it once we pick an option
        # player_entity = world.gen_entity()
        # player_entity.attach(PlayerComponent())

        # menu setup
        men = []
        men.append(("New Game", lambda: post(Event(NEW_GAME))))
        if path.exists(
            path.join(user_data_dir(APP_NAME, APP_AUTHOR), settings["save_file"])
        ):
            men.append(("Continue", lambda: post(Event(CONTINUE))))
        men.append(("Controls", lambda: post(Event(CONTROLS))))
        men.append(("Credits", lambda: post(Event(CREDITS))))
        men.append(("Quit", lambda: post(Event(QUIT))))

        for idx, m in enumerate(men):
            offset = -((len(men) * 60) // 2) + 140

            rect = pygame.Rect(0, 0, 200, 60)
            rect.centerx = background.get_width() // 2
            rect.centery = background.get_height() // 2 + (offset + (idx * 60))

            button = world.gen_entity()
            button.attach(
                ButtonComponent(
                    rect,
                    m[0].upper(),
                    m[1],
                )
            )

    def update(self, events, world):
        for event in events:
            if event.type == SCENE_REFOCUS:
                self._transition_back_to(events, world)
            if event.type == NEW_GAME:
                self.teardown(world)
                return SceneManager.new_root(GameScene())
            if event.type == CONTINUE:
                self.teardown(world)
                post(Event(LOAD))
                return SceneManager.new_root(GameScene())
            if event.type == CONTROLS:
                self._transition_away_from(events, world)
                return SceneManager.push(ControlsScene())
            if event.type == CREDITS:
                self._transition_away_from(events, world)
                return SceneManager.push(CreditsScene())
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return SceneManager.pop()

        world.process_all_systems(events)

    # This helps us hide things we want when we push a new scene
    def _transition_away_from(self, events, world):
        buttons = world.filter("button")

        for button in buttons:
            btn = button["button"]
            btn["rect"].centery += 5000

    # This helps us get everything back in the right spot when we transition back to our scene
    def _transition_back_to(self, events, world):
        buttons = world.filter("button")

        for button in buttons:
            btn = button["button"]
            btn["rect"].centery -= 5000

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

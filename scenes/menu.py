from os import path

import pygame

from button import Button
from game_events import CONTINUE, NEW_GAME, QUIT
from scene import Scene, SceneManager
from scenes.game import GameScene


class MenuScene(Scene):
    def __init__(self):
        self.menu = pygame.sprite.Group()

    def setup(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        background = context["background"]

        # menu setup
        men = []
        men.append("New Game")
        if path.exists(settings["save_file"]):
            men.append("Continue")
        men.append("Quit")

        for idx, m in enumerate(men):
            offset = -((len(men) * 70) // 2) + 100

            rect = pygame.Rect(0, 0, 200, 60)
            rect.centerx = background.get_width() // 2
            rect.centery = background.get_height() // 2 + (offset + (idx * 70))

            btn = Button(
                pygame.Color("green"),
                pygame.Color("red"),
                rect,
                self._handle_click,
                m,
                pygame.Color("black"),
            )
            self.menu.add(btn)

    def update(self, events, world):
        # Update menu buttons
        self.menu.update(events)

        for event in events:
            if event.type == NEW_GAME:
                return SceneManager.new_root(GameScene())
            if event.type == CONTINUE:
                # we have no data to save right now, so just start a fresh game if we have a save file
                return SceneManager.new_root(GameScene())
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return SceneManager.pop()

        # I dunno what i'm doing lol
        world.process_all_systems()

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]

        self.menu.draw(screen)

    def render_previous(self):
        return True

    def _handle_click(self, btn):
        action = btn.text.lower()

        if action == "new game":
            pygame.event.post(pygame.event.Event(NEW_GAME))
            return
        elif action == "continue":
            pygame.event.post(pygame.event.Event(CONTINUE))
            return
        elif action == "quit":
            pygame.event.post(pygame.event.Event(QUIT))
            return
        else:
            raise Exception(f"Unknown button with text {action} clicked")

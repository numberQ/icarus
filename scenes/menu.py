import pygame

from button import Button
import game_events
from scene import Scene, SceneManager
from scenes.game import GameScene


class MenuScene(Scene):
    def __init__(self):
        self.menu = pygame.sprite.Group()

    def setup(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        screen = context["screen"]
        background = context["background"]

        # menu setup
        men = ["New Game", "Continue", "Options", "Quit"]

        for idx, m in enumerate(men):
            offset = -((len(men) * 70) // 2) + 100

            rect = pygame.Rect(0, 0, 200, 60)
            rect.centerx = background.get_width() // 2
            rect.centery = background.get_height() // 2 + (offset + (idx * 70))

            btn = Button(
                pygame.Color("green"),
                pygame.Color("red"),
                rect,
                self.menu_action,
                m.upper(),
                pygame.Color("black"),
            )
            self.menu.add(btn)

    def update(self, events, world):
        # Update menu buttons
        self.menu.update(events)

        for event in events:
            if event.type == game_events.NEW_GAME:
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

    def menu_action(self, btn):
        # if the user picked new game
        action = btn.text.lower()

        if action == "new game":
            pygame.event.post(pygame.event.Event(game_events.NEW_GAME))
            return

        if action == "continue":
            pygame.event.post(pygame.event.Event(game_events.CONTINUE))
            return

        if action == "options":
            pygame.event.post(pygame.event.Event(game_events.OPTIONS))
            return

        if action == "quit":
            pygame.event.post(pygame.event.Event(game_events.QUIT))
            return

        # if we get here with an empty action somehow, just do nothing
        return

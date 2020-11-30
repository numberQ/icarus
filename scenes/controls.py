import pygame
from pygame.event import Event, post

from button import ButtonComponent, render_all_buttons
from game_events import BACK
from scene import Scene, SceneManager
from utils import find_data_file


class ControlsScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 36
        )
        self.icarus_offset = 0
        self.icarus_offset_increment = 1

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        rect = pygame.Rect(0, 0, 190, 49)
        rect.centerx = background.get_width() // 2
        rect.centery = background.get_height() // 2 + 100

        button = world.gen_entity()
        button.attach(
            ButtonComponent(
                rect,
                "Back".upper(),
                lambda: post(Event(BACK)),
            )
        )

    def update(self, events, world):
        for event in events:
            if event.type == BACK:
                return SceneManager.pop()

        world.process_all_systems(events)

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]

        surf = pygame.Surface((screen.get_width() // 2 - 30, 170))
        screen.blit(surf, (screen.get_width() // 4 + 15, screen.get_height() // 2 - 30))

        text = self.font.render(
            "Press right and left to rotate while flying.", True, (245, 245, 245)
        )
        screen.blit(text, (screen.get_width() // 4 + 25, screen.get_height() // 2 - 20))

        text = self.font.render(
            "Press space to boost with the jet booster.", True, (245, 245, 245)
        )
        screen.blit(text, (screen.get_width() // 4 + 25, screen.get_height() // 2 + 20))

        # Display the buttons
        render_all_buttons(screen, world)

    def render_previous(self):
        return True

    def teardown(self, world):
        buttons = world.filter("button")

        for button in buttons:
            btn = button["button"]
            if btn["text"] == "BACK":
                world.remove_entity(button)

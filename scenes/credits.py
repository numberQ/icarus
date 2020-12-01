import pygame
from pygame.event import Event, post

from button import ButtonComponent, render_all_buttons
from game_events import BACK
from scene import Scene, SceneManager
from utils import find_data_file


class CreditsScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 36
        )
        self.atari_font = pygame.font.Font(
            find_data_file("resources/atari-font/AtariFontFullVersion-ZJ23.ttf"), 20
        )
        self.arcade_font = pygame.font.Font(
            find_data_file("resources/arcade-classic-font/ArcadeClassic-ov2x.ttf"), 26
        )
        self.icarus_offset = 0
        self.icarus_offset_increment = 1

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        rect = pygame.Rect(0, 0, 190, 49)
        rect.centerx = background.get_width() // 2
        rect.centery = background.get_height() - 100

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

        surf = pygame.Surface((screen.get_width() // 2 + 40, 630))
        screen.blit(surf, (screen.get_width() // 4 - 20, 280))

        text = self.font.render("Programmed By:", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 300))
        text = self.font.render("Austin Decker", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 340))
        text = self.font.render("Dan Muckerman", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 375))
        text = self.font.render("Chris Yealy", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 410))

        text = self.font.render("Sprites By:", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 2 + 60, 300))
        text = self.font.render("Austin Forry", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 2 + 60, 340))

        prod = pygame.sprite.Sprite()
        prod.image = self.font.render(
            "A Technical Incompetence Production", 1, (240, 240, 240)
        )
        prod.rect = prod.image.get_rect(centerx=screen.get_width() // 2, centery=470)
        screen.blit(prod.image, prod.rect)

        text = self.font.render("Sound fx and buttons:", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 570))
        text = self.font.render("kenney.nl", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 610))

        text = self.font.render("Music:", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 2 + 60, 570))
        text = self.font.render("freepd.com", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 2 + 60, 610))

        text = self.font.render("Fonts Used:", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 660))
        text = self.atari_font.render(
            "Atari Font by Genshichi Yasui", True, (245, 245, 245)
        )
        screen.blit(text, (screen.get_width() // 4, 700))
        text = self.arcade_font.render(
            "Arcade Classic Font by Koen Hachmang", True, (245, 245, 245)
        )
        screen.blit(text, (screen.get_width() // 4, 725))
        text = self.font.render("DpComic Font by codeman38", True, (245, 245, 245))
        screen.blit(text, (screen.get_width() // 4, 748))

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

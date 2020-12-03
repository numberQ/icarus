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

        self.scroll_offset = 0

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        rect = pygame.Rect(0, 0, 190, 49)
        rect.centerx = background.get_width() // 2
        rect.centery = background.get_height() - 50

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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4 and self.scroll_offset < 0:
                    self.scroll_offset += 5
                if event.button == 5 and self.scroll_offset > -180:
                    self.scroll_offset -= 5

        world.process_all_systems(events)

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]

        surf = pygame.Surface(
            (screen.get_width() // 2 + 40, screen.get_height() - 280 - 100)
        )

        text = self.font.render("Programmed By:", True, (245, 245, 245))
        surf.blit(text, (20, 20 + self.scroll_offset))
        text = self.font.render("Austin Decker", True, (245, 245, 245))
        surf.blit(text, (20, 60 + self.scroll_offset))
        text = self.font.render("Dan Muckerman", True, (245, 245, 245))
        surf.blit(text, (20, 95 + self.scroll_offset))
        text = self.font.render("Chris Yealy", True, (245, 245, 245))
        surf.blit(text, (20, 130 + self.scroll_offset))

        text = self.font.render("Sprites By:", True, (245, 245, 245))
        surf.blit(text, (surf.get_width() // 2 + 60, 20 + self.scroll_offset))
        text = self.font.render("Austin Forry", True, (245, 245, 245))
        surf.blit(text, (surf.get_width() // 2 + 60, 60 + self.scroll_offset))

        prod = pygame.sprite.Sprite()
        prod.image = self.font.render(
            "A Technical Incompetence Production", True, (240, 240, 240)
        )
        prod.rect = prod.image.get_rect(
            centerx=surf.get_width() // 2, centery=190 + self.scroll_offset
        )
        surf.blit(prod.image, prod.rect)

        text = self.font.render("Sound fx and buttons:", True, (245, 245, 245))
        surf.blit(text, (20, 290 + self.scroll_offset))
        text = self.font.render("kenney.nl", True, (245, 245, 245))
        surf.blit(text, (20, 330 + self.scroll_offset))

        text = self.font.render("Music:", True, (245, 245, 245))
        surf.blit(text, (surf.get_width() // 2 + 60, 290 + self.scroll_offset))
        text = self.font.render("freepd.com", True, (245, 245, 245))
        surf.blit(text, (surf.get_width() // 2 + 60, 330 + self.scroll_offset))

        text = self.font.render("Fonts Used:", True, (245, 245, 245))
        surf.blit(text, (20, 380 + self.scroll_offset))
        text = self.atari_font.render(
            "Atari Font by Genshichi Yasui", True, (245, 245, 245)
        )
        surf.blit(text, (20, 420 + self.scroll_offset))
        text = self.arcade_font.render(
            "Arcade Classic Font by Koen Hachmang", True, (245, 245, 245)
        )
        surf.blit(text, (20, 445 + self.scroll_offset))
        text = self.font.render("DpComic Font by codeman38", True, (245, 245, 245))
        surf.blit(text, (20, 468 + self.scroll_offset))

        # Arrows to indicate scrolling is available
        if self.scroll_offset < 0:
            up_triangle = (
                (surf.get_width() - 35, 30),  # bottom left
                (surf.get_width() - 15, 30),  # bottom right
                (surf.get_width() - 25, 15),  # top
            )
            pygame.draw.polygon(surf, (245, 245, 245), up_triangle)
        if self.scroll_offset > -180:
            down_triangle = (
                (surf.get_width() - 35, surf.get_height() - 30),  # top left
                (surf.get_width() - 15, surf.get_height() - 30),  # top right
                (surf.get_width() - 25, surf.get_height() - 15),  # bottom
            )
            pygame.draw.polygon(surf, (245, 245, 245), down_triangle)

        screen.blit(surf, (screen.get_width() // 4 - 20, 280))

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

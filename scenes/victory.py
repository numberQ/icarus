import math

import pygame
from pygame.event import Event, post

import scenes.title
from button import ButtonComponent, render_all_buttons
from game_events import PAUSE_QUIT_TO_MENU
from scene import Scene, SceneManager
from utils import find_data_file


class VictoryScene(Scene):
    def __init__(self):
        self.victory_font = pygame.font.Font(
            find_data_file("resources/atari-font/AtariFontFullVersion-ZJ23.ttf"), 100
        )
        self.regular_font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 30
        )
        self.victory_screen = pygame.sprite.Group()

        self.angle = 270

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        # Create a sprite for the title
        victory_text = pygame.sprite.Sprite()
        victory_text.image = self.victory_font.render("VICTORY", True, (240, 240, 240))
        victory_text.rect = victory_text.image.get_rect(
            centerx=background.get_width() // 2, centery=110
        )

        self.victory_screen.add(victory_text)

        sub_text = pygame.sprite.Sprite()
        sub_text.image = self.regular_font.render(
            "Never regret thy fall, O Icarus of the fearless flight",
            True,
            (185, 185, 185),
        )
        sub_text.rect = sub_text.image.get_rect(
            centerx=background.get_width() // 2, centery=190
        )

        self.victory_screen.add(sub_text)

        # menu setup
        men = [
            ("Quit", lambda: post(Event(PAUSE_QUIT_TO_MENU))),
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

    def update(self, events, world):
        world.process_all_systems(events)

        for event in events:

            if event.type == PAUSE_QUIT_TO_MENU:
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "stop",
                        "sound": "background_music",
                    }
                )
                return SceneManager.new_root(scenes.title.TitleScene())

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]

        # Draw a nice background
        screen.blit(pygame.image.load(find_data_file("resources/bg_space.png")), (0, 0))
        screen.blit(
            pygame.image.load(find_data_file("resources/bg_space.png")), (0, 500)
        )

        # Moon's hot
        moon_sprite = pygame.sprite.Sprite()
        moon_sprite.image = pygame.image.load(
            find_data_file("resources/object_moon.png")
        )
        moon_sprite.rect = moon_sprite.image.get_rect()
        moon_sprite.rect.centerx = screen.get_width() / 2
        moon_sprite.rect.centery = screen.get_height() / 2 + 30
        screen.blit(moon_sprite.image, moon_sprite.rect)

        # Sub text backing box
        pygame.draw.rect(
            screen,
            (10, 10, 10),
            [
                screen.get_width() // 2 - 300,
                190 - 15 - 10,  # text y position - half font height - buffer
                600,
                50,
            ],
        )

        # Text
        self.victory_screen.draw(screen)

        # Icarus himself
        radius = 145
        radians = math.radians(self.angle)
        icarus_sprite = pygame.sprite.Sprite()
        icarus_sprite.image = pygame.image.load(
            find_data_file("resources/icarus_body.png")
        )
        rotated_image = pygame.transform.rotate(
            icarus_sprite.image, self.angle * -1 - 90
        )
        icarus_sprite.rect = rotated_image.get_rect()
        icarus_sprite.rect.centerx = (
            moon_sprite.rect.centerx + math.cos(radians) * radius
        )
        icarus_sprite.rect.centery = (
            moon_sprite.rect.centery + math.sin(radians) * radius
        )
        screen.blit(rotated_image, icarus_sprite.rect)

        # Rotate Icarus
        self.angle += 1
        self.angle %= 360

        # Display the buttons
        render_all_buttons(screen, world)

    def teardown(self, world):
        buttons = world.filter("button")

        world.remove_entities(buttons)

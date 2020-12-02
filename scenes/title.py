import pygame

from game_events import SCENE_REFOCUS
from scene import Scene, SceneManager
from scenes.menu import MenuScene
from utils import find_data_file


class TitleScene(Scene):
    def __init__(self):
        self.title_font = pygame.font.Font(
            find_data_file("resources/atari-font/AtariFontFullVersion-ZJ23.ttf"), 180
        )
        self.subtitle_font = pygame.font.Font(
            find_data_file("resources/arcade-classic-font/ArcadeClassic-ov2x.ttf"), 52
        )
        self.regular_font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 36
        )
        self.icarus_offset = 0
        self.icarus_offset_increment = 1

    def setup(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        background = context["background"]

        # Create a sprite for the title
        self.title = pygame.sprite.Sprite()
        self.title.image = self.title_font.render(settings["title"], 1, (240, 240, 240))
        self.title.rect = self.title.image.get_rect(
            centerx=background.get_width() // 2, centery=150
        )

        # Create a sprite for the title
        self.subtitle = pygame.sprite.Sprite()
        self.subtitle.image = self.subtitle_font.render(
            settings["subtitle"], 1, (240, 240, 240)
        )
        self.subtitle.rect = self.subtitle.image.get_rect(
            centerx=background.get_width() // 2, centery=250
        )

        # Create a sprite for the Press any key prompt
        self.push_anything = pygame.sprite.Sprite()
        self.push_anything.image = self.regular_font.render(
            "Press any key", 1, (240, 240, 240)
        )
        self.push_anything.rect = self.push_anything.image.get_rect(
            centerx=background.get_width() // 2,
            centery=background.get_height() // 2,
        )

        # Put all the sprites we want to render into a sprite group for easy adds and removes
        self.title_screen = pygame.sprite.Group()
        self.title_screen.add(self.title, self.subtitle, self.push_anything)

    def update(self, events, world):

        # Start music loop
        world.inject_event(
            {
                "type": "sound",
                "action": "start",
                "sound": "title_music",
            }
        )

        # Run all the systems registered in the world
        world.process_all_systems(events)

        # If a key press is detected, push the next scene
        for event in events:
            if event.type == SCENE_REFOCUS:
                self._transition_back_to(events, world)
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self._transition_away_from(events, world)
                return SceneManager.push(MenuScene())

    # This helps us hide things we want when we push a new scene
    def _transition_away_from(self, events, world):
        self.title_screen.remove(self.push_anything)

    # This helps us get everything back in the right spot when we transition back to our scene
    def _transition_back_to(self, events, world):
        self.title_screen.add(self.push_anything)

    def render(self, world):
        context = world.find_component("context")

        screen = context["screen"]

        # Draw a nice background
        screen.blit(
            pygame.image.load(find_data_file("resources/bg_sky-space.png")), (0, 0)
        )
        screen.blit(
            pygame.image.load(find_data_file("resources/bg_cityscape.png")), (0, 500)
        )

        # Icarus himself
        sprite = pygame.sprite.Sprite()
        sprite.image = pygame.image.load(find_data_file("resources/icarus_body.png"))
        sprite.rect = sprite.image.get_rect()
        sprite.rect.centerx = 180
        sprite.rect.centery = screen.get_height() // 2 + 190 + (self.icarus_offset // 3)
        screen.blit(sprite.image, sprite.rect)

        # Moon's hot
        sprite = pygame.sprite.Sprite()
        sprite.image = pygame.image.load(find_data_file("resources/object_moon.png"))
        sprite.rect = sprite.image.get_rect()
        sprite.rect.centerx = screen.get_width()
        sprite.rect.centery = 20
        screen.blit(sprite.image, sprite.rect)

        # Blit the text to the screen over top of the background surface
        self.title_screen.draw(screen)

        self.icarus_offset = self.icarus_offset + self.icarus_offset_increment

        if abs(self.icarus_offset) > 10:
            self.icarus_offset_increment = self.icarus_offset_increment * -1

    def render_previous(self):
        return False

import pygame

from game_events import SCENE_REFOCUS
from scene import Scene, SceneManager
from scenes.menu import MenuScene


class TitleScene(Scene):
    def __init__(self):
        self.title_font = pygame.font.Font(None, 52)
        self.regular_font = pygame.font.Font(None, 36)

    def setup(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        background = context["background"]

        # Create a sprite for the title
        self.title = pygame.sprite.Sprite()
        self.title.image = self.title_font.render(settings["title"], 1, (10, 10, 10))
        self.title.rect = self.title.image.get_rect(
            centerx=background.get_width() // 2, centery=50
        )

        # Create a sprite for the Press any key prompt
        self.push_anything = pygame.sprite.Sprite()
        self.push_anything.image = self.regular_font.render(
            "Press any key", 1, (10, 10, 10)
        )
        self.push_anything.rect = self.push_anything.image.get_rect(
            centerx=background.get_width() // 2,
            centery=background.get_height() // 3 * 2,
        )

        # Put all the sprites we want to render into a sprite group for easy adds and removes
        self.title_screen = pygame.sprite.Group()
        self.title_screen.add(self.title, self.push_anything)

    def update(self, events, world):
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
        background = context["background"]

        # Blit the text to the screen over top of the background surface
        screen.blit(background, (0, 0))
        self.title_screen.draw(screen)

    def render_previous(self):
        return False

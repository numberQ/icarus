import pygame

from scene import Scene, SceneManager
from scenes.menu import MenuScene
import game_events


class TitleScene(Scene):
    def __init__(self):
        self.title = pygame.font.Font(None, 52)
        self.font = pygame.font.Font(None, 36)

    def setup(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        background = context["background"]

        self.text = self.title.render(settings["title"], 1, (10, 10, 10))
        self.text_pos = self.text.get_rect(centerx=background.get_width() // 2, centery=50)
        self.push_anything = self.font.render("Press any key", 1, (10, 10, 10))
        self.push_anything_pos = self.push_anything.get_rect(centerx=background.get_width() // 2, centery=background.get_height()//3 * 2)

    def update(self, events, world):
        # If a key press is detected, push the next scene
        for event in events:
            if event.type == game_events.SCENE_REFOCUS:
                self._transition_back_to(events, world)
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self._transition_away_from(events, world)
                return SceneManager.push(MenuScene())
    
    # This helps us hide things we want when we push a new scene
    def _transition_away_from(self, events, world):
        self.push_anything_pos.y=-100  # Simple hiding technique
    
    # This helps us get everything back in the right spot when we transition back to our scene
    def _transition_back_to(self, events, world):
        context = world.find_component("context")
        background = context["background"]
        self.push_anything_pos.centery = background.get_height()//3 * 2

    def render(self, world):
        context = world.find_component("context")

        screen = context["screen"]
        background = context["background"]

        # Blit the text to the screen over top of the background surface
        screen.blit(background, (0, 0))
        screen.blit(self.text, self.text_pos)
        screen.blit(self.push_anything, self.push_anything_pos)

    def render_previous(self):
        return False

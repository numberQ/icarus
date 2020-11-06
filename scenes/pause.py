import pygame

from scene import Scene


class PauseScene(Scene):
    def __init__(self):
        self.regular_font = pygame.font.Font(None, 36)

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        # Create a sprite for the header
        self.pause = pygame.sprite.Sprite()
        self.pause.image = self.regular_font.render("Paused", 1, (200, 200, 200))
        self.pause.rect = self.pause.image.get_rect(
            centerx=background.get_width() // 2, centery=background.get_height() // 4
        )

        # Put all the sprites we want to render into a sprite group for easy adds and removes
        self.pause_screen = pygame.sprite.Group()
        self.pause_screen.add(self.pause)

    def update(self, events, world):
        # If a key press is detected, push the next scene
        pass

    # This helps us hide things we want when we push a new scene
    def _transition_away_from(self, events, world):
        pass

    # This helps us get everything back in the right spot when we transition back to our scene
    def _transition_back_to(self, events, world):
        pass

    def render(self, world):
        context = world.find_component("context")

        screen = context["screen"]

        # Blit the text to the screen over top of the background surface
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, overlay.get_rect())

        self.pause_screen.draw(screen)

    def render_previous(self):
        return True

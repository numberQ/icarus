from scene import Scene
import pygame

class GameScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(None, 36)

    def setup(self, world):
        pass

    def update(self, events, world):
        world.process_all_systems()

    def render(self, world):
        context = world.find_only('context')
        screen = context['screen']
        background = context['background']

        # text setup
        text = self.font.render("NEW GAME", 1, (10, 10, 10))
        text_pos = text.get_rect(centerx=background.get_width() // 2, centery=background.get_height() // 2)
        
        screen.blit(background, (0, 0))
        screen.blit(text,text_pos)

        
    def render_previous(self):
        return False
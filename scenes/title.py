from scene import Scene, SceneManager
from scenes.menu import MenuScene
import pygame

class TitleScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
    
    def setup(self, world):
        context = world.find_only('context')
        settings = world.find_only('settings')
        background = context['background']
        
        self.text = self.font.render(settings['title'], 1, (10, 10, 10))
        self.text_pos = self.text.get_rect(centerx=background.get_width() // 2)
    
    def update(self, events, world):
        # If a key press is detected, push the next scene
        for event in events:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return SceneManager.replace(MenuScene())

        # Always just do nothing unless a 
        return SceneManager.nothing()

    def render(self, world):
        context = world.find_only('context')

        screen = context['screen']
        background = context['background']

        # Blit the text to the screen over top of the background surface
        screen.blit(background, (0, 0))
        screen.blit(self.text, self.text_pos)
        

    def render_previous(self):
        return False

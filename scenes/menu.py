from scene import Scene, SceneManager, SceneSwitch
from scenes.game import GameScene
from button import Button
from events import *

import pygame
import sys
    

class MenuScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.menu = pygame.sprite.Group()

    def setup(self, world):
        context = world.find_only('context')
        settings = world.find_only('settings')
        screen = context['screen']
        background = context['background']

        #bg
        screen.blit(background, (0, 0))

        #title
        self.text = self.font.render(settings['title'], 1, (10, 10, 10))
        self.text_pos = self.text.get_rect(centerx=background.get_width() // 2)
        screen.blit(self.text, self.text_pos)

        # menu setup
        men = ['New Game', 'Continue', 'Options', 'Quit']

        for idx, m in enumerate(men):
            offset = -((len(men) * 70) // 2) + 100

            rect = pygame.Rect(0, 0, 200, 60);
            rect.centerx = background.get_width() // 2
            rect.centery = background.get_height() // 2 + (offset + (idx * 70))

            btn = Button(pygame.Color('green'), 
                   pygame.Color('red'), 
                   rect, 
                   self.menu_action,
                   m.upper(),
                   pygame.Color('black'))
            self.menu.add(btn)

    def update(self, events, world):
        # Update menu buttons
        self.menu.update(events)

        for event in events:
            if event.type == NEW_GAME:
                return SceneManager.replace(GameScene())

        # I dunno what i'm doing lol
        world.process_all_systems()

    def render(self, world):
        context = world.find_only('context')
        screen = context['screen']

        self.menu.draw(screen)

        
    def render_previous(self):
        return False

    
    def menu_action(self, btn):
        # if the user picked new game
        action = btn.text.lower()

        if action == 'new game':
            pygame.event.post(pygame.event.Event(NEW_GAME))
            return

        if action == 'continue':
            pygame.event.post(pygame.event.Event(CONTINUE))
            return

        if action == 'options':
            pygame.event.post(pygame.event.Event(OPTIONS))
            return

        if action == 'quit':
            pygame.event.post(pygame.event.Event(QUIT))
            return

        # if we get here with an empty action somehow, just do nothing
        return
import pygame

import scenes.title
from button import Button
from game_events import PAUSE_CONTINUE, PAUSE_QUIT_TO_MENU, PAUSE_SAVE_AND_QUIT
from scene import Scene, SceneManager


class PauseScene(Scene):
    def __init__(self):
        self.regular_font = pygame.font.Font(None, 42)

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]

        # Create a sprite for the header
        self.pause = pygame.sprite.Sprite()
        self.pause.image = self.regular_font.render("Paused", 1, (200, 200, 200))
        self.pause.rect = self.pause.image.get_rect(
            centerx=background.get_width() // 2, centery=background.get_height() // 4
        )

        self.menu = pygame.sprite.Group()
        options = ["Continue", "Save & Quit", "Quit to Menu"]
        for idx, menu_item in enumerate(options):
            offset = 0

            rect = pygame.Rect(0, 0, 200, 60)
            rect.centerx = background.get_width() // 2
            rect.centery = background.get_height() // 2 + (offset + (idx * 70))

            btn = Button(
                pygame.Color("green"),
                pygame.Color("red"),
                rect,
                self._handle_click,
                menu_item,
                pygame.Color("black"),
            )
            self.menu.add(btn)

        # Put all the sprites we want to render into a sprite group for easy adds and removes
        self.pause_screen = pygame.sprite.Group()
        self.pause_screen.add(self.pause)

    def update(self, events, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        context["paused"] = True

        # Update the button graphics
        self.menu.update(events)

        for event in events:
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                return SceneManager.pop()
            elif event.type == PAUSE_CONTINUE:
                return SceneManager.pop()
            elif event.type == PAUSE_SAVE_AND_QUIT:
                self._save(settings["save_file"])
                return SceneManager.new_root(scenes.title.TitleScene())
            elif event.type == PAUSE_QUIT_TO_MENU:
                return SceneManager.new_root(scenes.title.TitleScene())

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
        self.menu.draw(screen)

    def _handle_click(self, btn):
        action = btn.text.lower()

        if action == "continue":
            pygame.event.post(pygame.event.Event(PAUSE_CONTINUE))
            return
        elif action == "save & quit":
            pygame.event.post(pygame.event.Event(PAUSE_SAVE_AND_QUIT))
            return
        elif action == "quit to menu":
            pygame.event.post(pygame.event.Event(PAUSE_QUIT_TO_MENU))
            return
        else:
            raise Exception(f"Unknown button with text {action} clicked")

    def _save(self, save_file):
        f = open(save_file, "w")
        f.write("{'title': 'Now the file has more content!'}")
        f.close()

    def render_previous(self):
        return True

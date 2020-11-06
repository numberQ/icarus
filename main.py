# Hide the pygame support prompt
import os

import pygame

from common_components import ContextComponent
from ecs import WORLD, Component
from scene import SceneManager
from scenes.title import TitleScene

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"



class ContextComponent(Component):
    def __init__(self, screen, clock, background):
        metadata = {
            "screen": screen,
            "clock": clock,
            "background": background,
            "running": True,
        }
        Component.__init__(self, "context", metadata)


def main():
    # Initialize pygame before we do anything else
    pygame.init()

    # Load game metadata and store it in an entity
    settings = Component.load_from_json("settings")
    WORLD.gen_entity().attach(settings)

    # Set up the pygame window
    screen = pygame.display.set_mode((settings["height"], settings["width"]))
    pygame.display.set_caption(settings["title"])

    # Store our dynamic resources that are created at runtime in the game world
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((200, 200, 200))

    context = ContextComponent(screen, pygame.time.Clock(), background)
    game = WORLD.gen_entity()
    game.attach(context)

    # Create a new Title screen object
    title_screen = TitleScene()

    # Initialize a SceneManager with our title screen
    manager = SceneManager(title_screen, WORLD)

    # BIG GAME LOOP
    while game["context"]["running"]:
        game["context"]["clock"].tick(60)

        # Process game wide events, most likely only QUIT
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game["context"]["running"] = False

        # Update the current scene
        switch_event = manager.update(events, WORLD)

        # Render the current scene
        manager.render(WORLD)
        pygame.display.update()  # Double buffers whatever was on the screen object to the actual display

        # Finally switch scenes in the scene manager
        manager.switch(switch_event, WORLD)


if __name__ == "__main__":
    main()

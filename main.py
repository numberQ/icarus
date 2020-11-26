import pygame

from button import ButtonSystem
from common_components import ContextComponent
from ecs import WORLD, Component
from scene import SceneManager
from scenes.title import TitleScene
from sound import AudioSystem
from utils import find_data_file


def main():
    # Initialize pygame before we do anything else
    pygame.init()

    programIcon = pygame.image.load(find_data_file("resources/icarus_icon.png"))
    pygame.display.set_icon(programIcon)

    # Initialize global systems in the game world
    if pygame.mixer.get_init() is not None:
        WORLD.register_system(AudioSystem())
    WORLD.register_system(ButtonSystem())

    # Load game metadata and store it in an entity
    settings = Component.load_from_json("settings")
    WORLD.gen_entity().attach(settings)

    # Set up the pygame window
    screen = pygame.display.set_mode((settings["height"], settings["width"]), vsync=1)
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
        pygame.display.flip()  # Double buffers whatever was on the screen object to the actual display

        # Finally switch scenes in the scene manager
        manager.switch(switch_event, WORLD)


if __name__ == "__main__":
    main()

import pprint

from ecs import *
from scene import SceneManager
from scene_title import TitleScene


# e = Entity()

# player_name = input('Enter player name: ')
# c = PlayerComponent(player_name)

# e.attach(c)

# print("\ncreated entity: ")
# pprint.pprint(e)
# print("\ndict: ")
# pprint.pprint(e.__dict__)

# print("\nplayer component: ")
# pprint.pprint(e.player)
# print("\ndict: ")
# pprint.pprint(e.player.__dict__)

# print("\nplayer name: " + e.player.name)

# print("\nfile load test: ")

# e.attach(Component.load_from_json('test'))
# pprint.pprint(e.test.__dict__)

import pygame

def main():
    # Create a new game world, represented here by a dict
    world = {
        "resources": {
            "height": 640,
            "width": 480,
            "title": "Icarus: From Boyz II Men", # I'm sorry I forgot the subtitle
        },
        "context": {
        }
    }

    pygame.init()

    ### Optionally, overwrite the default resource settings by reading from a file here ###

    screen = pygame.display.set_mode((world['resources']['height'], world['resources']['width']))
    pygame.display.set_caption(world['resources']['title'])

    # Dynamic resources created at runtime
    world['context']['clock'] = pygame.time.Clock()
    world['context']['screen'] = screen
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((200,200,200))
    world['context']['background'] = background
    world['context']['running'] = True  # easy toggle to stop the game

    # Create a new Title screen object
    title_screen = TitleScene()

    # Initialize a SceneManager with our title screen
    manager = SceneManager(title_screen, world)

    # BIG GAME LOOP
    while world['context']['running']:
        world['context']['clock'].tick(60)

        # Process game wide events, most likely only QUIT
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                world['context']['running'] = False

        # Update the current scene
        switch_event = manager.update(events, world)

        # Render the current scene
        manager.render(world)
        pygame.display.update()

        # Finally switch scenes in the scene manager
        manager.switch(switch_event, world)



if __name__ == "__main__":
    # import sys
    # from os import path
    # sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
    main()


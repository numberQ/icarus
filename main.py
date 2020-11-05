import pprint

from ecs import *


e = Entity()

player_name = input('Enter player name: ')
c = PlayerComponent(player_name)

e.attach(c)

print("\ncreated entity: ")
pprint.pprint(e)
print("\ndict: ")
pprint.pprint(e.__dict__)

print("\nplayer component: ")
pprint.pprint(e.player)
print("\ndict: ")
pprint.pprint(e.player.__dict__)

print("\nplayer name: " + e.player.name)

print("\nfile load test: ")

e.attach(Component.load_from_json('test'))
pprint.pprint(e.test.__dict__)

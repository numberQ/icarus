import json
import uuid
from typing import Dict


class World:
    eindex = {}  # Index mapping entity IDs to entity objects
    cindex = {}  # Index mapping component names to entity objects
    systems = []  # List of all systems
    subscriptions = {}  # Map of which systems are subscribed to which events
    events_to_send = (
        []
    )  # List to buffer all events in before they are dispatched to systems

    # This function generates a new entity within this world. The entity is tracked inside this worlds mappings
    def gen_entity(self):
        id = str(uuid.uuid4())
        entity = Entity(id)
        self.eindex[id] = entity
        return entity

    # Query method which returns a list of all entities which have a given component. Useful for building systems
    def filter(self, component):
        entities = self.cindex.get(component)
        return entities if entities is not None else []

    # Query method for when you only have one entity with a given component. It returns the component from that single entity
    # Useful for things like global game settings so you can say:
    #     WORLD.find_only('settings')
    # instead of:
    #     WORLD.filter('settings')[0]['settings']
    def find_only(self, component):
        filtered = self.filter(component)
        return filtered[0][component] if filtered is not [] else None

    # Query method that returns an entity given a particular id. This is useful for cross referencing entities. For example,
    # entity A could store entity B's ID in a component. This would then allow you to look up entity B while analyzing entity A.
    # Useful for parent-child relationships too
    def get(self, eid):
        return self.eindex.get(eid)

    # Registers a system with the world. This allows events to be dispatched to it, as well as run through the helper method
    def register_system(self, system):
        self.systems.append(system)

    # Unregisters a system with the world so it will stop being run
    def unregister_system(self, system):
        self.systems.remove(system)

    # Calling this method injects an event into the world. In the implementation, all events are buffered until the systems are processed. This makes it so
    # all systems see the same events every frame, instead of System B adding an event before System C runs. In the old arch, System A (which ran before system B)
    # wouldn't see that event until the next frame where as System C would process that event on the current frame.
    def inject_event(self, event):
        self.events_to_send.append(event)

    # Internal helper function to dispatch the buffered events to the proper system. It's called right before the systems are processed.
    def _dispatch_events(self):
        for event in self.events_to_send:
            event_type = event["type"]
            for subscriber in self.subscriptions[event_type]:
                subscriber.events.append(event)
        self.events_to_send = []

    # Convenience method to run all currently registered systems
    def process_all_systems(self):
        self._dispatch_events()
        for system in self.systems:
            system.process(WORLD)


class Component:
    def __init__(self, metatype: str, metadata: Dict):
        self.metatype = metatype
        self.__dict__.update(metadata)

    # Method that allows indexing an entity like a dictionary. Makes IDE experience better since static analyzers can't see fields created at runtime
    def __getitem__(self, key):
        return self.__dict__[key]

    # Method that allows assigning an entity like a dictionary. Makes IDE experience better since static analyzers can't see fields created at runtime
    def __setitem__(self, key, value):
        self.__dict__[key] = value

    # Helper method which allows Components to be formated, which is useful for debugging what's actually in a component
    def __repr__(self):
        return str(self.__dict__)

    @classmethod
    def load_from_json(cls, filename) -> "Component":
        """
        Allows loading a Component from a JSON file.
        MUST contain a string "metatype" field, and an object "metadata" field.

        Example:
        {
            "metatype": "player",
            "metadata": {
                "name": "Craigory",
                "ac": 1000,
                ...
            }
        }

        :param filename: name of the JSON file, without the .json
        :return: a new Component instance using the usual construtor
        """
        with open(filename + ".json", "r") as f:
            loaded_json = json.load(f)
            metatype = loaded_json["metatype"]
            metadata = loaded_json["metadata"]
            return Component(metatype, metadata)


# Create a singleton state for the world. This bundles up all the class local methods and datums into one
# singleton instead of many small singletons spread across several classes
WORLD = World()


# The Entity class defines a single entity in our system composed
# of multiple components. At its heart, an Entity object is simply
# an empty bucket associated with a unique ID.
#
# This class provides exactly one relevant function: a way to
# attach a component dictionary to the entity. This function
# simply takes the dictionary loaded using the Component()
# function above, instantiates a new class on-the-fly, and
# sets a class attribute. Here is an example of how to attach
# our 'meta' object from above to an entity:
#
#     >>> e = WORLD.gen_entity()
#     >>> print(e)
#     {'id': '5afec678-4c4e-44a9-be74-8764f62b61fd', 'components': []}
#     >>>
#     >>> e.attach(Component('meta'))
#     >>> print(e)
#     {'components': ['meta'],
#      'id': '5afec678-4c4e-44a9-be74-8764f62b61fd',
#      'meta': <ecs.Component object at 0x108a1e400>}
#     >>> e.meta.name = 'Player'
#
# The attach() function also takes a namespace argument for
# renaming longer component names when creating the attribute:
#
#     >> e = WORLD.gen_entity()
#     >> e.attach(Component('meta'), namespace='m')
#     >> e.m.name = 'Player'
#
# We also do some housekeeping: the 'components' object variable
# keeps track of all components attached to this entity:
#
#     >>> e = WORLD.gen_entity()
#     >>> e.attach(Component('meta')
#     >>> e.components
#     ['meta']
#
# Note that namespacing maintains the original class name inside
# the components array:
#
#     >>> e = WORLD.gen_entity()
#     >>> e.attach(Component('meta'), namespace='m')
#     >>> e.components
#     ['meta']
#
# Finally, we also track two reverse mappings: (i) to go from a
# given entity ID to an entity object, and (ii) to go from a
# component type to a list of entity objects. Both these are
# implemented as class methods so no instantiated object is needed
# to retrieve them.
#
# The first is useful in many cases where you want to reference a
# particular entity and use it in a system. For example, an attack
# component can simply store the ID of the entity being attacked.
# The damage-calculation system simply looks up the entity using
# this reverse index.
#
#     target = WORLD.get('47d78b7e-8c5c-417b-8f46-be0de7c0b62d')
#
# The second index is used in implementing systems that deal with
# all entities having a particular component attached. For example,
# a MovementSystem can easily grab all entities containing a
# movement component:
#
#     entities = WORLD.filter('movement')
#
class Entity(object):
    def __init__(self, id):
        self.id = str(uuid.uuid4())
        self.components = []

    def attach(self, component: Component, namespace: str = None):
        # Append component name to list of components
        self.components.append(component.metatype)
        # Create a raw 'Component' object based on the JSON schema
        key = namespace if namespace else component.metatype
        self.__dict__[key] = component
        # Add to component index
        if component.metatype not in WORLD.cindex:
            WORLD.cindex[component.metatype] = []
        WORLD.cindex[component.metatype].append(self)

    # Method that allows indexing an entity like a dictionary. Makes IDE experience better since static analyzers can't see fields created at runtime
    def __getitem__(self, key):
        return self.__dict__[key]

    # Helper method which allows Entities to be formated, which is useful for debugging what's actually in an entity
    def __repr__(self):
        return str(self.__dict__)


# The final class that completes our ECS implementation is the System
# class for defining systems that update the world.
#
# The class is designed as a simple pub-sub system where each system
# decides which game events it wants to be notified of. This is done
# using the `subscribe()` method, which takes an event type (string)
# as a parameter.
#
# Each System object contains its own list of pending events and
# a class method, inject_event(), allows for injecting game events into the
# entire set of systems. This function it basically looks up all
# subscribers of that given event and simply appends the event into
# each of their event lists. Note that at this point, the event has
# not yet been handled, but simply registered as pending by appending
# into each subscriber's events list.
#
# The reason the inject_event() function is a class method and not an object
# level method is so that external parts of the game, such as the
# input system, can freely inject events into systems.
#
# Finally, the process() function can be overridden by subclasses to
# define their own custom game loop logic. The `pending()` function
# can be used here to retrieve (and clear) all pending events in the
# system, and the Entity.filter() function can be called to get a
# filtered list of entities relevant to this system. Here is a very
# simple example of how to implement a system:
#
#     class MovementSystem(System):
#         def __init__(self):
#             super().__init__()
#             self.subscribe('move')
#
#         def process(self, world):
#             # Get list of pending events and clear current event queue
#             events = self.pending()
#             # Filter entities by type. Fast because we use component_index.
#             entities = world.filter('movement')
#
#             # Do something here that modifies state or generates events
#
#             # Inject any new events at the end
#             world.inject_event({'type': 'move', 'data': randstr(10)})
#
# Note that above, the process() function first gets all pending events,
# runs some processing code, and finally, if needed, emits a new set of
# events that get picked up in the next round by other systems.
#
# Note that there is also no restriction on which entities you access in
# the process() function inside a System object. Above, I show an example
# of picking entities having a single component ('movement'), but you can
# instead easily choose to pick out different sets, apply any kind of
# set operators, etc. before arriving at the entities you need and
# continuing with the loop.
#
# Here's a made-up example that illustrates how to do this using Python's
# built-in set operations:
#
#     def process(self, world):
#         ent_with_move = set(Entity.filter('movement'))
#         ent_with_pos = set(Entity.filter('position'))
#         ent_with_ai = set(Entity.filter('ai'))
#         entities = list((ent_with_move& ent_with_pos) | ent_with_ai)
#
#         # Rest of the loop goes here and uses 'entities'
#
class System(object):
    def __init__(self):
        self.events = []

    def subscribe(self, event_type):
        if event_type not in WORLD.subscriptions:
            WORLD.subscriptions[event_type] = []
        WORLD.subscriptions[event_type].append(self)

    def pending(self):
        # Get pending events and clear queue
        ret = self.events
        self.events = []
        return ret

    def process(self, world):
        pass

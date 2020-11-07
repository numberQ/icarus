from enum import Enum

import pygame

import game_events


# All scenes should implement this class's interface
class Scene:
    # This method get called once when the scene is first added to the game. This allows the Scene to do one time setup using resources stored in the world
    def setup(self, world):
        pass

    # Runs scene physics/logic/collision detection
    def update(self, events, world):
        pass

    # Returns a scene switch event (see the helper functions in SceneManager to generate them)
    # This method should the scene
    def render(self, world):
        pass

    # This method returns either True or False to allow the game to determine whether previous scenes should be rendered
    # This can be useful for like pause guis and the like
    def render_previous(self):
        return False

    # This method can be useful for cleaning up all the entities and systems your scene created from the game world
    def teardown(self, world):
        pass


# Simple enum for switching between scenes
class SceneSwitch(Enum):
    Nothing = 0
    Pop = 1
    Push = 2
    Replace = 3
    New_Root = 4


# Class which acts like a stack of scenes, allowing switching and overlaying between them
class SceneManager:
    scenes = []

    # Initialize the scene manager with an initial scene using the given world
    def __init__(self, scene, world):
        scene.setup(world)
        self.scenes.append(scene)

    # Method to get the current scene
    def _current(self):
        assert len(self.scenes) > 0
        return self.scenes[-1]

    # Handles a scene switch event and adds it to our stack of scenes
    def switch(self, scene_switch, world):
        if scene_switch["type"] == SceneSwitch.Nothing:
            pass
        elif scene_switch["type"] == SceneSwitch.Pop:
            self.scenes.pop().teardown(world)
            pygame.event.post(pygame.event.Event(game_events.SCENE_REFOCUS))
        elif scene_switch["type"] == SceneSwitch.Push:
            scene = scene_switch["scene"]
            scene.setup(world)
            self.scenes.append(scene)
        elif scene_switch["type"] == SceneSwitch.Replace:
            scene = scene_switch["scene"]
            scene.setup(world)
            self.scenes.pop().teardown(world)
            self.scenes.append(scene)
        elif scene_switch["type"] == SceneSwitch.New_Root:
            scene = scene_switch["scene"]
            scene.setup(world)
            # Remove all scenes in reverse
            for _ in range(len(self.scenes)):
                self.scenes.pop().teardown(world)
            self.scenes.append(scene)

    # Helper calls update for the current scene
    def update(self, events, world):
        # Just in case the update function didn't return any state transition, default to do nothing
        return self._current().update(events, world) or self.nothing()

    # Calls render on all appropriate scenes
    def render(self, world):
        self._render_all_scenes(self.scenes, world)

    # Pravate helper to render all appropriate scenes starting from the bottom up (uses recursion to bottom up traverse)
    def _render_all_scenes(self, scenes, world):
        assert len(scenes) > 0
        last = scenes[-1]
        rest = scenes[:-1]
        if last.render_previous() is True:
            self._render_all_scenes(rest, world)
        last.render(world)

    # Helper methods to generate a sceenswitch event for you instead of having to create one inline
    @staticmethod
    def nothing():
        return {"type": SceneSwitch.Nothing}

    @staticmethod
    def pop():
        return {"type": SceneSwitch.Pop}

    @staticmethod
    def push(scene):
        return {"type": SceneSwitch.Push, "scene": scene}

    @staticmethod
    def replace(scene):
        return {"type": SceneSwitch.Replace, "scene": scene}

    @staticmethod
    def new_root(scene):
        return {"type": SceneSwitch.New_Root, "scene": scene}

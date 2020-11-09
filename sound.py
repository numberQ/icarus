import json

import pygame

from ecs import System


class AudioSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("sound")

        with open("resources/audio.json", "r") as f:
            self.audio_table = json.load(f)

        self.audio_files = {}
        for (key, value) in self.audio_table.items():
            self.audio_files[key] = pygame.mixer.Sound(value)

        self.started_sounds = []
        self.previously_paused = False
        self.reduced_volume = 0.7

    def process(self, events, world):
        world_events = self.pending()

        context = world.find_component("context")
        currently_paused = context["paused"]

        # If the game has been paused, quiet all background sounds
        if not self.previously_paused and currently_paused:
            for sound in self.started_sounds:
                vol = sound.get_volume() - self.reduced_volume
                sound.set_volume(vol)

        # If the game has been unpaused, bring all sounds back to their
        # regular volume
        if self.previously_paused and not currently_paused:
            for sound in self.started_sounds:
                vol = sound.get_volume() + self.reduced_volume
                sound.set_volume(vol)

        # Store the current pause state
        self.previously_paused = currently_paused

        for event in world_events:
            if event["action"] == "start":
                sound = self.audio_files[event["sound"]]
                if sound.get_num_channels() == 0:
                    self.started_sounds.append(sound)
                    sound.play(loops=-1)
            if event["action"] == "stop":
                sound = self.audio_files[event["sound"]]
                sound.stop()
            if event["action"] == "play":
                sound = self.audio_files[event["sound"]]
                if sound.get_num_channels() == 0:
                    sound.play()

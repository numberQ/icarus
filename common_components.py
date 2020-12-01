from ecs import Component


class ContextComponent(Component):
    def __init__(self, screen, clock, background):
        metadata = {
            "screen": screen,
            "clock": clock,
            "background": background,
            "running": True,
            "paused": False,
        }
        Component.__init__(self, "context", metadata)


class SpriteComponent(Component):
    def __init__(self, sprite):
        metadata = {"sprite": sprite}
        Component.__init__(self, "sprite", metadata)


class MovementComponent(Component):
    def __init__(self, xvel=0, yvel=0, xaccel=0, yaccel=0):
        metadata = {"xvel": xvel, "yvel": yvel, "xaccel": xaccel, "yaccel": yaccel}
        Component.__init__(self, "movement", metadata)


class PlayerComponent(Component):
    """
    For the player entity. Reacts to user inputs.
    """

    def __init__(self):
        metadata = {
            "has_jumped": False,
            "jumping": False,
            "currency": 0,
            "hasCloudSleeves": 0,
            "hasWings": 0,
            "hasJetBoots": 0,
            "extraFuel": 0,
            "maxBoosts": 0,
            "numBoosts": 0,
        }
        Component.__init__(self, "player", metadata)

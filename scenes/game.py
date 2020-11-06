import math

import pygame
from ecs import Component, System
from pygame.sprite import Sprite
from scene import Scene


class GraphicComponent(Component):
    """
    For visible entities that have a sprite.
    """

    def __init__(self, sprite):
        metadata = {"sprite": sprite}
        Component.__init__(self, "graphic", metadata)


class PositionComponent(Component):
    """
    For entities that exist somewhere on the coordinate grid
    (i.e., anything physically in the game world).
    """

    def __init__(self, x, y):
        metadata = {"x": x, "y": y}
        Component.__init__(self, "position", metadata)


class VelocityComponent(Component):
    """
    For entities with some kind of physics-based movement.
    """

    def __init__(self, speed, angle):
        metadata = {"speed": speed, "angle": angle}
        Component.__init__(self, "velocity", metadata)


class RotationComponent(Component):
    """
    For entities that rotate. Affects both graphics and physics.
    Maybe makes more sense as a RotationalVelocityComponent or something, that adds its speed to VelocityComponent's angle?
    """

    def __init__(self, angle):
        metadata = {"angle": angle}
        Component.__init__(self, "rotation", metadata)


class PlayerComponent(Component):
    """
    For the player entity. Reacts to user inputs.
    """

    def __init__(self):
        Component.__init__(self, "player", {})


class GlidingComponent(Component):
    """
    For any entity that requires gliding physics. Allows the GlidingSystem to find it.
    """

    def __init__(self):
        Component.__init__(self, "gliding", {})


class GlidingSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("move")
        self.angle_magnitude = 0.03

    def process(self, world):
        # We don't actually need the movement events, but this clears the queue for the next frame
        self.pending()

        gliders = world.filter("gliding")

        # All gliders should have velocity, position, and rotation components
        for glider in gliders:

            # Copy rotational angle into velocity angle
            # This feels off - I think rotation should actually be rotational velocity
            angle = glider.rotation.angle
            glider.velocity.angle = angle

            # sin and cos math requires radians, so let's convert
            angle_radians = math.radians(angle)

            # Simulate gliding forces by having angle from the ground influence velocity
            speed = glider.velocity.speed
            speed += math.sin(angle_radians) * self.angle_magnitude

            # Some basic velocity calculations
            glider.position.x += math.cos(angle_radians) * speed
            glider.position.y += math.sin(angle_radians) * speed

            # Now that we've manipulated the velocity's speed, give it back to velocity
            glider.velocity.speed = speed


class PlayerSprite(Sprite):
    def __init__(self, image_path):
        Sprite.__init__(self)

        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()


class GameScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(None, 36)

    def setup(self, world):

        # Player entity setup
        player_entity = world.gen_entity()
        player_entity.attach(
            GraphicComponent(PlayerSprite("resources/icarus_himself.png"))
        )
        player_entity.attach(PositionComponent(100, 100))
        player_entity.attach(VelocityComponent(1, 0))
        player_entity.attach(RotationComponent(0))
        player_entity.attach(PlayerComponent())
        player_entity.attach(GlidingComponent())

        # System registration
        world.register_system(GlidingSystem())

    def update(self, events, world):
        world.inject_event({"type": "move"})
        world.process_all_systems()

        # There will only ever be one player entity, unless scope drastically changes
        player_entity = world.filter("player")[0]

        keys = pygame.key.get_pressed()

        # The player only has direct control over their angle from the ground.
        # Our rudimentary physics takes care of the rest.
        # Also, clamp the angle from straight up to straight down. Otherwise things get out of control.
        # Must improve physics engine before allowing full 360 degree rotation.
        if keys[pygame.K_RIGHT]:
            angle = player_entity.rotation.angle + 1
            player_entity.rotation.angle = min(angle, 90)
        if keys[pygame.K_LEFT]:
            angle = player_entity.rotation.angle - 1
            player_entity.rotation.angle = max(angle, -90)

    def render(self, world):
        context = world.find_only("context")
        screen = context["screen"]
        background = context["background"]

        graphical_entities = world.filter("graphic")
        player_entity = world.filter("player")[0]

        screen.blit(background, (0, 0))

        for entity in graphical_entities:
            # We're assuming all graphical entities also have a position and rotation.
            # Is there a better way to do this? Will there ever be a graphical entity WITHOUT a position/rotation?
            image = entity.graphic.sprite.image
            rotated_image = pygame.transform.rotate(image, entity.rotation.angle * -1)
            screen.blit(rotated_image, (entity.position.x, entity.position.y))

        # text
        text = self.font.render(
            f"angle: {player_entity.velocity.angle}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 500))

        text = self.font.render(
            f"speed: {player_entity.velocity.speed}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 550))

    def render_previous(self):
        return False

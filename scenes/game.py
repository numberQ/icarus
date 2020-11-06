import math

import pygame
from pygame.sprite import Sprite

from ecs import Component, System
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


class PhysicsComponent(Component):
    """
    For entities with some kind of physics-based movement.
    """

    def __init__(self):
        metadata = {"velocity": 0, "angle": 0, "acceleration": 0}
        Component.__init__(self, "physics", metadata)


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


class GravityComponent(Component):
    """
    For entities that should be affected by gravity.
    """

    def __init__(self):
        Component.__init__(self, "gravity", {})


class ForceSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("physics_force")

    def process(self, world):

        events = self.pending()
        physics_entities = set(world.filter("physics"))

        for event in events:
            magnitude = event["magnitude"]
            angle = event["angle"]

            if magnitude == 0:
                continue

            for entity in physics_entities:
                if entity.physics.velocity == 0:
                    entity.physics.angle = angle
                theta = math.radians(angle - entity.physics.angle)
                current_accel = entity.physics.acceleration

                new_accel = math.sqrt(
                    pow(magnitude, 2)
                    + pow(current_accel, 2)
                    + 2 * magnitude * current_accel * math.cos(theta)
                ) * math.copysign(1, magnitude)
                new_angle = math.degrees(theta / 2)

                entity.physics.acceleration = new_accel
                entity.physics.angle += new_angle
                entity.physics.velocity += entity.physics.acceleration


class MovementSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("move")

    def process(self, world):

        # Clear event queue
        self.pending()

        physics_entities = set(world.filter("physics"))

        for entity in physics_entities:
            radians = math.radians(entity.physics.angle)
            speed = entity.physics.velocity

            xx = entity.position.x + math.cos(radians) * speed
            yy = entity.position.y + math.sin(radians) * speed

            xx %= 1200
            yy %= 800

            entity.position.x = xx
            entity.position.y = yy

            # Reset acceleration so we can calculate it fresh next frame
            # THIS IS CURRENTLY HAPPENING IN THE SCENE RENDER - NEED TO FIGURE OUT A BETTER WAY
            # entity.physics.acceleration = 0


class GlidingSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("glide")
        self.angle_magnitude = 0.1

    def process(self, world):

        # Clear event queue
        self.pending()

        gliders = world.filter("gliding")

        # All gliders should have physics and rotation components
        for glider in gliders:

            # Trig math requires radians, so let's convert
            angle = glider.rotation.angle
            radians = math.radians(angle)
            magnitude = math.sin(radians) * self.angle_magnitude

            world.inject_event(
                {"type": "physics_force", "magnitude": magnitude, "angle": angle}
            )


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
        player_entity.attach(PhysicsComponent())
        player_entity.attach(RotationComponent(0))
        player_entity.attach(PlayerComponent())
        player_entity.attach(GlidingComponent())
        player_entity.attach(GravityComponent())

        # System registration
        world.register_system(ForceSystem())
        world.register_system(MovementSystem())
        world.register_system(GlidingSystem())

    def update(self, events, world):

        # Gravity comes first
        world.inject_event({"type": "physics_force", "magnitude": 0, "angle": 90})

        # Then gliding, which translates rotation into acceleration
        world.inject_event({"type": "glide"})

        # Finally, we add movement after any events that could affect acceleration
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
            f"image angle: {player_entity.rotation.angle}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 300))

        text = self.font.render(
            f"vel angle: {player_entity.physics.angle}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 325))

        text = self.font.render(
            f"vel magnitude: {player_entity.physics.velocity}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 350))

        text = self.font.render(
            f"acc: {player_entity.physics.acceleration}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 375))

        # This is bad - only putting it here so we can display acceleration for debug purposes
        # Let's figure out a better way to do this
        player_entity.physics.acceleration = 0

    def render_previous(self):
        return False

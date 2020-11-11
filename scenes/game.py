import math

import pygame
from pygame.sprite import Sprite

from ecs import Component, System
from scene import Scene, SceneManager
from scenes.pause import PauseScene


class GraphicComponent(Component):
    """
    For visible entities that have a sprite.
    """

    def __init__(self, sprite: pygame.sprite.Sprite):
        metadata = {"sprite": sprite}
        Component.__init__(self, "graphic", metadata)


class PositionComponent(Component):
    """
    For entities that exist somewhere on the coordinate grid
    (i.e., anything physically in the game world).
    """

    def __init__(self, x: int, y: int):
        metadata = {"x": x, "y": y}
        Component.__init__(self, "position", metadata)


class PhysicsComponent(Component):
    """
    For entities with some kind of physics-based movement.
    """

    def __init__(self, mass: float):
        metadata = {
            "velocity_magnitude": 0,
            "velocity_angle": 0,
            "force_magnitude": 0,
            "force_angle": 0,
            "mass": mass,
        }
        Component.__init__(self, "physics", metadata)


class RotationComponent(Component):
    """
    For entities that rotate. Affects both graphics and physics.
    Maybe makes more sense as a RotationalVelocityComponent or something, that adds its speed to VelocityComponent's angle?
    """

    def __init__(self, angle: float):
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
    """
    Accumulates forces acting on physics entities.
    """

    def __init__(self):
        super().__init__()
        self.subscribe("physics_force")

    def process(self, world):

        events = self.pending()
        physics_entities = set(world.filter("physics"))

        for event in events:
            added_magnitude = event["magnitude"]
            angle = event["angle"]

            if added_magnitude == 0:
                continue

            for entity in physics_entities:

                if entity.physics.force_magnitude == 0:
                    entity.physics.force_magnitude = added_magnitude
                    entity.physics.force_angle = angle
                    continue

                current_magnitude = entity.physics.force_magnitude
                theta = math.radians(angle - entity.physics.force_angle)

                resultant_magnitude = math.sqrt(
                    pow(current_magnitude, 2)
                    + pow(added_magnitude, 2)
                    + 2 * current_magnitude * added_magnitude * math.cos(theta)
                )

                # When all forces are in perfect equilibrium, resultant magnitude will be 0.
                # Because we can't divide by 0, handle that edge case without the Law of Sines.
                if resultant_magnitude == 0:
                    resultant_theta = 0
                else:
                    resultant_theta = math.degrees(
                        math.asin(
                            added_magnitude * math.sin(theta) / resultant_magnitude
                        )
                    )

                entity.physics.force_magnitude = resultant_magnitude
                entity.physics.force_angle += resultant_theta


class MovementSystem(System):
    """
    Converts forces that have been accumulated throughout the frame into acceleration,
    then applies that acceleration to physics entites as velocity.
    """

    def __init__(self):
        super().__init__()
        self.subscribe("move")

    def process(self, world):

        # Clear event queue
        self.pending()

        physics_entities = set(world.filter("physics"))

        for entity in physics_entities:

            if entity.physics.velocity_magnitude == 0:
                entity.physics.velocity_magnitude = (
                    entity.physics.force_magnitude / entity.physics.mass
                )
                entity.physics.velocity_angle = entity.physics.force_angle
            else:
                acceleration = entity.physics.force_magnitude / entity.physics.mass
                velocity = entity.physics.velocity_magnitude
                theta = math.radians(
                    entity.physics.force_angle - entity.physics.velocity_angle
                )

                resultant_magnitude = math.sqrt(
                    pow(velocity, 2)
                    + pow(acceleration, 2)
                    + 2 * velocity * acceleration * math.cos(theta)
                )
                resultant_theta = math.degrees(
                    math.asin(acceleration * math.sin(theta) / resultant_magnitude)
                )

                entity.physics.velocity_magnitude = resultant_magnitude
                entity.physics.velocity_angle += resultant_theta

            # Drag equation
            cross_sectional_area = 0.75 * math.cos(math.radians(entity.rotation.angle))
            drag_magnitude = (
                0.5  # Drag magnitude is always divided by 2
                * 0.5  # Drag coefficient
                * 1.22  # Air resistance
                * cross_sectional_area
                * pow(entity.physics.velocity_magnitude, 2)
                / entity.physics.mass
            )

            # Drag force always acts in the opposite direction of velocity,
            # so we can simply modify magnitude without worrying about angle.
            entity.physics.velocity_magnitude -= drag_magnitude
            speed = entity.physics.velocity_magnitude

            radians = math.radians(entity.physics.velocity_angle)

            xx = entity.position.x + math.cos(radians) * speed
            yy = entity.position.y + math.sin(radians) * speed

            xx %= world.find_component("settings").height
            yy %= world.find_component("settings").width

            entity.position.x = xx
            entity.position.y = yy


class GlidingSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("glide")
        self.angle_multiplier = 10

    def process(self, world):

        # Clear event queue
        self.pending()

        gliders = world.filter("gliding")

        # All gliders should have physics and rotation components
        for glider in gliders:

            # Trig math requires radians, so let's convert
            angle = glider.rotation.angle
            radians = math.radians(angle)
            magnitude = math.sin(radians) * self.angle_multiplier

            world.inject_event(
                {"type": "physics_force", "magnitude": magnitude, "angle": angle}
            )


class PhysicsFrameResetSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("physics_frame_reset")

    def process(self, world):

        # Clear event queue
        self.pending()

        physics_entities = set(world.filter("physics"))

        for entity in physics_entities:
            entity.physics.force_magnitude = 0
            entity.physics.force_angle = 0


class PlayerSprite(Sprite):
    def __init__(self, image_path):
        Sprite.__init__(self)

        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()


class GameScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.systems = []

    def setup(self, world):

        # Player entity setup
        player_entity = world.gen_entity()
        player_entity.attach(
            GraphicComponent(PlayerSprite("resources/icarus_himself.png"))
        )
        player_entity.attach(PositionComponent(100, 100))
        average_adult_mass_kg = 62
        player_entity.attach(PhysicsComponent(average_adult_mass_kg))
        player_entity.attach(RotationComponent(0))
        player_entity.attach(PlayerComponent())
        player_entity.attach(GlidingComponent())
        player_entity.attach(GravityComponent())

        # System registration
        self.systems = [
            PhysicsFrameResetSystem(),
            ForceSystem(),
            MovementSystem(),
            # GlidingSystem(),
        ]
        for sys in self.systems:
            world.register_system(sys)

    def update(self, events, world):

        # At the start of every frame, before any other physics calculations can happen, per-frame values need reset
        world.inject_event({"type": "physics_frame_reset"})

        # Gravity comes first
        world.inject_event({"type": "physics_force", "magnitude": 9.8, "angle": 90})

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

        for event in events:
            # Use keyup here as a simple way to only trigger once and not repeatedly
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                return SceneManager.push(PauseScene())

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]
        background = context["background"]

        graphical_entities = world.filter("graphic")
        player_entity = world.find_entity("player")

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
            f"vel angle: {player_entity.physics.velocity_angle}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 325))

        text = self.font.render(
            f"vel magnitude: {player_entity.physics.velocity_magnitude}",
            True,
            (10, 10, 10),
        )
        screen.blit(text, (10, 350))

        text = self.font.render(
            f"force angle: {player_entity.physics.force_angle}", True, (10, 10, 10)
        )
        screen.blit(text, (10, 375))

        text = self.font.render(
            f"force magnitude: {player_entity.physics.force_magnitude}",
            True,
            (10, 10, 10),
        )
        screen.blit(text, (10, 400))

    def render_previous(self):
        return False

    def teardown(self, world):
        player = world.find_entity("player")
        world.remove_entity(player)

        for sys in self.systems:
            world.unregister_system(sys)

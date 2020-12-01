import json
import math
from os import path
import random

import pygame
from appdirs import user_data_dir
from pygame.sprite import Sprite

from common_components import PlayerComponent
from ecs import Component, System
from game_events import LOAD, SCENE_REFOCUS
from scene import Scene, SceneManager
from scenes.crash_results import CrashResultsScene
from scenes.pause import PauseScene
from utils import APP_AUTHOR, APP_NAME, find_data_file


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


class PhysicsFrameResetSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("physics_frame_reset")

    def process(self, events, world):
        if world.find_component("context")["paused"]:
            return

        # If we haven't been asked to reset, don't reset
        events = self.pending()
        if not events:
            return

        # get entities that need reset
        physics_entities = set(world.filter("physics"))

        for entity in physics_entities:

            # For now, this is the only thing that needs reset.
            # In in the future, we might also reset forces acting on the entity.
            entity.physics.acceleration = 0


class ForceSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("physics_force")

    def process(self, events, world):
        if world.find_component("context")["paused"]:
            return

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

    def process(self, events, world):
        if world.find_component("context")["paused"]:
            return

        # If we haven't been asked to move, don't move
        events = self.pending()
        if not events:
            return

        context = world.find_component("context")
        screen = context["screen"]

        physics_entities = set(world.filter("physics"))

        for entity in physics_entities:

            in_space = calculate_altitude(entity, screen) < -2200

            min_cross_section = 0.1
            max_cross_section = 0.75
            cross_sectional_area = min_cross_section + (
                max_cross_section - min_cross_section
            ) * math.sin(math.radians(entity.rotation.angle - entity.physics.angle))

            # Drag coefficient helps determine the force of drag, and varies by material
            drag_coeff = 0.9
            if entity.player is not None and entity.player.hasCloudSleeves:
                drag_coeff = 0.3

            # The higher you are, the less resistance the atmosphere provides
            air_density = 1.22
            if in_space:
                air_density = 0.9

            # Aerodynamic drag equation
            drag_magnitude = (
                0.5  # Drag magnitude is always divided by 2
                * drag_coeff
                * air_density
                * cross_sectional_area
                * pow(entity.physics.velocity, 2)
                / 62  # Entity weight
            ) * math.copysign(1, entity.physics.velocity)

            radians = math.radians(entity.physics.angle)

            drag_magnitude *= abs(math.sin(radians))
            entity.physics.velocity -= drag_magnitude
            speed = entity.physics.velocity

            xx = entity.position.x + math.cos(radians) * speed
            yy = entity.position.y + math.sin(radians) * speed

            # very simplistic gravity
            gravity = 8
            if entity.player is not None and entity.player.hasCloudSleeves:
                gravity = 4

            if in_space:
                gravity = 1
            yy += gravity

            entity.position.x = xx
            entity.position.y = yy


class GlidingSystem(System):
    def __init__(self):
        super().__init__()
        self.subscribe("glide")
        self.angle_magnitude = 0.5

    def process(self, events, world):
        if world.find_component("context")["paused"]:
            return

        # If we haven't been asked to glide, don't glide
        events = self.pending()
        if not events:
            return

        gliders = world.filter("gliding")

        # All gliders should have physics and rotation components
        for glider in gliders:

            angle = glider.rotation.angle
            radians = math.radians(angle)
            magnitude = math.sin(radians) * self.angle_magnitude

            # Since the angle can only every be -90 to 90 (i.e., the right half of the unit plane),
            # negative magnitude means a force pushing towards the left half of the unit plane.
            # That doesn't feel very good in the game, though - so let's cut the player a break
            # and make forward velocity stronger than backwards velocity.
            if magnitude < 0:
                magnitude /= 4

            world.inject_event(
                {"type": "physics_force", "magnitude": magnitude, "angle": angle}
            )


class BackgroundComponent(Component):
    def __init__(self, image_path, y):
        metadata = {
            "image": pygame.image.load(find_data_file(image_path)),
            "x": 0,
            "y": y,
        }
        Component.__init__(self, "background", metadata)

class CollectableComponent(Component):
    def __init__(self, worth):
        metadata = {
            "worth": worth,
        }
        Component.__init__(self, "collectable", metadata)

class PlayerSprite(Sprite):
    def __init__(self, image_path):
        Sprite.__init__(self)

        self.image = pygame.image.load(find_data_file(image_path))
        self.rect = self.image.get_rect()


class CameraComponent(Component):
    def __init__(self, target_entity_id):
        metadata = {
            "target_entity_id": target_entity_id,
            "x": 0,
            "y": 0,
        }
        Component.__init__(self, "camera", metadata)


class CollectableSystem(System):
    def __init__(self):
        self.offscreen_slots = []
        super().__init__()

        screen_info = pygame.display.Info()
        self.x_slot_size = 150
        self.y_slot_size = 75

        # Special case where we immediately need collectables on screen for the player to collect
        num_x_slots = screen_info.current_w // self.x_slot_size
        num_y_slots = screen_info.current_h // self.y_slot_size

        self.screen_slots = []
        for x_slot in range(num_x_slots):
            for y_slot in range(num_y_slots):
                self.screen_slots.append((x_slot, y_slot))

        # Slots to spawn new collectables off screen
        num_x_slots = 300 // self.x_slot_size
        num_y_slots = (screen_info.current_h + 200) // self.y_slot_size

        self.offscreen_slots = []
        for x_slot in range(num_x_slots):
            for y_slot in range(num_y_slots):
                self.offscreen_slots.append((x_slot, y_slot))


    def process(self, events, world):
        screen = world.find_component("context")["screen"]
        camera = world.find_component("camera")
        player = world.get(camera["target_entity_id"])

        collectables = world.filter("collectable")

        # Update player's sprite rect so we can use pygame's collision detection
        player.graphic.sprite.rect = player.graphic.sprite.image.get_rect(x=player.position.x, y=player.position.y)

        to_remove = []
        
        for collectable in collectables:
            collision = pygame.sprite.collide_rect(player.graphic.sprite, collectable.graphic.sprite)
            if collision:
                player.player.currency += collectable.collectable.worth
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "play",
                        "sound": "collect",
                    }
                )
                to_remove.append(collectable)

        # Remove old collectables that have been scrolled past
        for collectable in collectables:
            if collectable.position.x < camera.x - 200:
                to_remove.append(collectable)

        # Create new collectables
        current_collectables = len(collectables) - len(to_remove)
        total_collectables = 10
        need_collectables = total_collectables - current_collectables
        
        collectable_spawners = [create_cloud, create_bird, create_plane]

        # Divide the screen up into a grid of unused "slots" where we can place 
        if current_collectables == 0:
            all_slots = self.screen_slots
        else:
            all_slots = self.offscreen_slots

        chosen_slots = random.sample(all_slots, k=need_collectables)

        for i in range(need_collectables):
            spawner = random.choices(collectable_spawners, weights=(60, 30, 10), k=1)[0]
            
            x_slot, y_slot = chosen_slots[i]

            # Special case where we immediately need collectables on screen for the player to collect
            if (current_collectables == 0):
                x = camera.x + (x_slot * self.x_slot_size)
                y = camera.y + (y_slot * self.y_slot_size)
            else:
                # Spawn these new collectables off screen
                x = camera.x + screen.get_width() + (x_slot * self.x_slot_size)
                y = camera.y - 100 + (y_slot * self.y_slot_size)
            spawner(world.gen_entity(), (x, y))
        
        # Remove all the collectables that are due for cleanup
        world.remove_entities(to_remove)
                

class CameraSystem(System):
    def __init__(self):
        super().__init__()

    def process(self, events, world):
        screen = world.find_component("context")["screen"]
        camera = world.find_component("camera")
        player = world.get(camera["target_entity_id"])

        x_max_off = screen.get_width() * 0.40
        x_min_off = screen.get_width() * 0.15

        y_top_off = screen.get_height() * 0.40
        y_bottom_off = screen.get_height() * 0.55

        # Keep the player with in the above bounds of the screen
        if camera.x <= player.position.x - x_max_off:
            camera.x = player.position.x - x_max_off
        if camera.x >= player.position.x - x_min_off:
            camera.x = player.position.x - x_min_off

        if camera.y >= player.position.y - y_top_off:
            camera.y = player.position.y - y_top_off
        if camera.y <= player.position.y - y_bottom_off:
            camera.y = player.position.y - y_bottom_off

        if camera.x < 0:
            camera.x = 0
        if camera.y > 0:
            camera.y = 0
        if camera.y < -2540:
            camera.y = -2540


def calculate_altitude(player, screen):
    sprite_height = player.graphic.sprite.image.get_height()
    return player.position.y - screen.get_height() + sprite_height


def load(world):
    settings = world.find_component("settings")
    if path.exists(
        path.join(user_data_dir(APP_NAME, APP_AUTHOR), settings["save_file"])
    ):
        with open(
            path.join(user_data_dir(APP_NAME, APP_AUTHOR), settings["save_file"]),
            "r",
        ) as f:
            loaded_json = json.load(f)
            player_entity = world.find_entity("player")
            player_entity.player.currency = loaded_json["currency"]
            player_entity.player.hasCloudSleeves = loaded_json["hasCloudSleeves"]
            player_entity.player.hasWings = loaded_json["hasWings"]
            player_entity.player.hasJetBoots = loaded_json["hasJetBoots"]
            player_entity.player.extraFuel = loaded_json["extraFuel"]

            if player_entity.player.hasJetBoots:
                player_entity.player.maxBoosts = 1 + player_entity.player.extraFuel
                player_entity.player.numBoosts = player_entity.player.maxBoosts


def create_cloud(entity, position):
    entity.attach(CollectableComponent(100))
    entity.attach(PositionComponent(position[0], position[1]))
    entity.attach(RotationComponent(0))
    sprite = pygame.sprite.Sprite()
    sprite.image = pygame.image.load(find_data_file("resources/object_cloud.png"))
    sprite.rect = sprite.image.get_rect(x=position[0], y=position[1])
    entity.attach(GraphicComponent(sprite))


def create_bird(entity, position):
    entity.attach(CollectableComponent(200))
    entity.attach(PositionComponent(position[0], position[1]))
    entity.attach(RotationComponent(0))
    sprite = pygame.sprite.Sprite()
    sprite.image = pygame.image.load(find_data_file("resources/object_bird.png"))
    sprite.rect = sprite.image.get_rect(x=position[0], y=position[1])
    entity.attach(GraphicComponent(sprite))


def create_plane(entity, position):
    entity.attach(CollectableComponent(300))
    entity.attach(PositionComponent(position[0], position[1]))
    entity.attach(RotationComponent(0))
    sprite = pygame.sprite.Sprite()
    sprite.image = pygame.image.load(find_data_file("resources/object_plane.png"))
    sprite.rect = sprite.image.get_rect(x=position[0], y=position[1])
    entity.attach(GraphicComponent(sprite))


class GameScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 36
        )

    def setup(self, world):
        context = world.find_component("context")
        screen = context["screen"]

        # Create a sprite for the title
        self.help_message = pygame.sprite.Sprite()
        self.help_message.image = self.font.render(
            "Press space to start flying", 1, (240, 240, 240)
        )
        self.help_message.rect = self.help_message.image.get_rect(
            centerx=screen.get_width() // 2, centery=screen.get_height() // 2
        )

        # Player entity setup
        player_entity = world.gen_entity()
        player_entity.attach(
            GraphicComponent(PlayerSprite("resources/icarus_body.png"))
        )
        player_entity.attach(PositionComponent(100, 100))
        player_entity.attach(PhysicsComponent())
        player_entity.attach(RotationComponent(-20))
        player_entity.attach(PlayerComponent())
        player_entity.attach(GlidingComponent())
        player_entity.attach(GravityComponent())

        # Scrolling background - layers defined by the y coord
        world.gen_entity().attach(BackgroundComponent("resources/bg_space.png", -2540))
        world.gen_entity().attach(BackgroundComponent("resources/bg_space.png", -2040))
        world.gen_entity().attach(
            BackgroundComponent("resources/bg_sky-space.png", -1540)
        )
        world.gen_entity().attach(BackgroundComponent("resources/bg_sky.png", -1040))
        world.gen_entity().attach(BackgroundComponent("resources/bg_sky.png", -540))
        world.gen_entity().attach(BackgroundComponent("resources/bg_sky.png", -40))
        world.gen_entity().attach(
            BackgroundComponent("resources/bg_cityscape.png", 460)
        )

        # Create the camera
        camera_entity = world.gen_entity()
        camera_entity.attach(CameraComponent(player_entity.id))

        # System registration
        self.systems = [
            PhysicsFrameResetSystem(),
            ForceSystem(),
            MovementSystem(),
            GlidingSystem(),
            CameraSystem(),
            CollectableSystem(),
        ]
        for sys in self.systems:
            world.register_system(sys)

    def update(self, events, world):

        for event in events:
            if event.type == SCENE_REFOCUS:
                self.teardown(world)
                self.setup(world)

        # Loading should happen only AFTER refocusing, if both events have fired this frame
        for event in events:
            if event.type == LOAD:
                load(world)

        context = world.find_component("context")
        screen = context["screen"]

        # There will only ever be one player entity, unless scope drastically changes
        player_entity = world.filter("player")[0]

        # No physics until the player has jumped
        if player_entity.player.has_jumped:

            # First, clear out per-frame physics values
            world.inject_event({"type": "physics_frame_reset"})

            # TODO: Simulate gravity as a force, instead of just doing it in the movement system
            # world.inject_event({"type": "physics_force", "magnitude": 0, "angle": 90})

            # Then gliding, which translates rotation into acceleration
            world.inject_event({"type": "glide"})

            # Finally, we add movement after any events that could affect acceleration
            world.inject_event({"type": "move"})

            if calculate_altitude(player_entity, screen) > 0:
                for sys in self.systems:
                    world.unregister_system(sys)
                return SceneManager.push(CrashResultsScene())

        world.process_all_systems(events)

        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()

        # Before doing anything else, the player must jump off the cliff
        if not player_entity.player.has_jumped:

            if keys[pygame.K_SPACE] and not player_entity.player.jumping:

                # Tell everyone we've jumped
                player_entity.player.has_jumped = True
                player_entity.player.jumping = True

                # The jump itself
                world.inject_event(
                    {"type": "physics_force", "magnitude": 20, "angle": -20}
                )

                # Start background music
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "start",
                        "sound": "background_music",
                    }
                )

        # We don't want to rotate before jumping. TODO: or do we?
        else:

            if player_entity.player.jumping:
                player_entity.rotation.angle += 0.5
                if player_entity.rotation.angle > 0:
                    player_entity.player.jumping = False

            rotation_speed = 1
            # If you have the wings upgrade, you can use shift to go back to slower rotation
            if player_entity.player.hasWings and not mods & pygame.KMOD_SHIFT:
                rotation_speed = 2

            # The player only has direct control over their angle from the ground.
            # Our rudimentary physics takes care of the rest.
            # Also, clamp the angle from straight up to straight down.
            if keys[pygame.K_RIGHT]:
                player_entity.player.jumping = False
                angle = player_entity.rotation.angle + rotation_speed
                player_entity.rotation.angle = min(angle, 90)
            if keys[pygame.K_LEFT]:
                player_entity.player.jumping = False
                angle = player_entity.rotation.angle - rotation_speed
                player_entity.rotation.angle = max(angle, -90)

            for event in events:
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_SPACE
                    and player_entity.player.has_jumped
                    and player_entity.player.hasJetBoots
                    and player_entity.player.numBoosts > 0
                ):
                    player_entity.player.jumping = False
                    player_entity.player.numBoosts -= 1
                    world.inject_event(
                        {
                            "type": "physics_force",
                            "magnitude": 15,
                            "angle": player_entity.rotation.angle,
                        }
                    )

        for event in events:
            # Use keyup here as a simple way to only trigger once and not repeatedly
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                return SceneManager.push(PauseScene())

            # This is just for debug purposes
            # if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            #     player_entity.player.currency += 1000

    def render(self, world):
        context = world.find_component("context")
        screen = context["screen"]
        background = context["background"]

        graphical_entities = world.filter("graphic")
        player_entity = world.find_entity("player")
        camera = world.find_component("camera")

        # City background
        backgrounds = world.filter("background")
        for background in backgrounds:
            background = background.background
            x = background.x - camera.x
            if x < -500:
                # TODO: does an offset help?
                background.x = camera.x  # - (x + 500)
            if x > 0:
                # TODO: does an offset help?
                background.x = camera.x - 500  # + x
            y = background.y - camera.y
            screen.blit(background.image, (x, y))

        for entity in graphical_entities:
            # We're assuming all graphical entities also have a position and rotation.
            # TODO: Is there a better way to do this? Will there ever be a graphical entity WITHOUT a position/rotation?
            image = entity.graphic.sprite.image
            rotated_image = pygame.transform.rotate(image, entity.rotation.angle * -1)
            adjusted_x = entity.position.x - camera.x
            adjusted_y = entity.position.y - camera.y
            screen.blit(rotated_image, (adjusted_x, adjusted_y))

        # # text
        # text = self.font.render(
        #     f"image angle: {player_entity.rotation.angle}", True, (10, 10, 10)
        # )
        # screen.blit(text, (10, 300))
        #
        # text = self.font.render(
        #     f"vel angle: {player_entity.physics.angle}", True, (10, 10, 10)
        # )
        # screen.blit(text, (10, 325))
        #
        # text = self.font.render(
        #     f"vel magnitude: {player_entity.physics.velocity}", True, (10, 10, 10)
        # )
        # screen.blit(text, (10, 350))
        #
        # text = self.font.render(
        #     f"acc: {player_entity.physics.acceleration}", True, (10, 10, 10)
        # )
        # screen.blit(text, (10, 375))
        #
        # text = self.font.render(f"x: {player_entity.position.x}", True, (10, 10, 10))
        # screen.blit(text, (10, 400))
        #
        # text = self.font.render(f"y: {player_entity.position.y}", True, (10, 10, 10))
        # screen.blit(text, (10, 425))
        #
        # altitude = calculate_altitude(player_entity, screen)
        # text = self.font.render(f"altitude: {altitude}", True, (10, 10, 10))
        # screen.blit(text, (10, 450))

        text = self.font.render(
            f"${player_entity.player.currency}", True, (245, 245, 245)
        )
        screen.blit(text, (50, 50))

        if player_entity.player.maxBoosts > 0:
            text = self.font.render("Boosts: ", True, (245, 245, 245))
            screen.blit(text, (50, 85))

            for i in range(player_entity.player.numBoosts):
                pygame.draw.circle(screen, (220, 40, 10), (160 + i * 25, 102), 10)
            for i in range(
                player_entity.player.numBoosts, player_entity.player.maxBoosts
            ):
                pygame.draw.circle(screen, (128, 128, 128), (160 + i * 25, 102), 10, 3)

        if not player_entity.player.has_jumped:
            screen.blit(self.help_message.image, self.help_message.rect)

    def render_previous(self):
        return False

    def teardown(self, world):
        player = world.find_entity("player")
        camera = world.find_entity("camera")

        if player is not None:
            world.remove_entities([player, camera])
        else:
            world.remove_entities([camera])

        for sys in self.systems:
            world.unregister_system(sys)

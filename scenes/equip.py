import json
import os

import pygame
from appdirs import user_data_dir
from pygame.event import Event, post

import scenes.title
from button import ButtonComponent, render_all_buttons
from game_events import (
    EQUIP_BUY_CLOUD_SLEEVES,
    EQUIP_BUY_JET_BOOTS,
    EQUIP_BUY_MORE_FUEL,
    EQUIP_BUY_WINGS,
    EQUIP_QUIT,
    EQUIP_SAVE_AND_START,
    LOAD,
)
from scene import Scene, SceneManager
from utils import APP_AUTHOR, APP_NAME, find_data_file


class EquipScene(Scene):
    def __init__(self):
        self.font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 36
        )
        self.big_font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 58
        )
        self.small_font = pygame.font.Font(
            find_data_file("resources/dpcomic-font/DpcomicRegular-p3jD.ttf"), 28
        )
        self.icarus_offset = 0
        self.icarus_offset_increment = 1

        self.extra_fuel_cost = 0

    def setup(self, world):
        context = world.find_component("context")
        background = context["background"]
        settings = world.find_component("settings")

        player_entity = world.find_entity("player")
        player_entity.player.has_jumped = False

        self.extra_fuel_cost = (
            settings["extraFuelCost"]
            + settings["extraFuelCost"] * player_entity.player.extraFuel // 2
        )

        # menu setup
        men = []
        men.append(("Quit", lambda: post(Event(EQUIP_QUIT))))
        men.append(("Save + Start", lambda: post(Event(EQUIP_SAVE_AND_START))))

        for idx, m in enumerate(men):
            offset = -((len(men) * 480) // 2) + 240

            rect = pygame.Rect(0, 0, 190, 49)
            rect.centerx = background.get_width() // 2 + (offset + (idx * 480))
            rect.centery = background.get_height() - 100

            button = world.gen_entity()
            button.attach(
                ButtonComponent(
                    rect,
                    m[0].upper(),
                    m[1],
                )
            )

        rect = pygame.Rect(120, 560, 49, 49)
        jet_boots_button = world.gen_entity()
        jet_boots_button.attach(
            ButtonComponent(
                rect,
                "Buy" if player_entity.player.hasJetBoots == 0 else "",
                lambda: post(Event(EQUIP_BUY_JET_BOOTS)),
                is_small=True,
                is_disabled=(
                    player_entity.player.currency < settings["jetBootsCost"]
                    or player_entity.player.hasJetBoots == 1
                ),
                image="resources/checkmark.png"
                if player_entity.player.hasJetBoots == 1
                else None,
            )
        )

        rect = pygame.Rect(120, 660, 49, 49)
        more_fuel_button = world.gen_entity()
        more_fuel_button.attach(
            ButtonComponent(
                rect,
                "Buy" if player_entity.player.extraFuel < 9 else "",
                lambda: post(Event(EQUIP_BUY_MORE_FUEL)),
                is_small=True,
                is_disabled=(
                    (
                        player_entity.player.currency < self.extra_fuel_cost
                        and player_entity.player.hasJetBoots == 1
                    )
                    or player_entity.player.hasJetBoots == 0
                    or player_entity.player.extraFuel == 9
                ),
                image="resources/locked.png"
                if player_entity.player.hasJetBoots == 0
                else "resources/checkmark.png"
                if player_entity.player.extraFuel == 9
                else None,
            )
        )

        rect = pygame.Rect(640, 560, 49, 49)
        cloud_sleeves_button = world.gen_entity()
        cloud_sleeves_button.attach(
            ButtonComponent(
                rect,
                "Buy" if player_entity.player.hasCloudSleeves == 0 else "",
                lambda: post(Event(EQUIP_BUY_CLOUD_SLEEVES)),
                is_small=True,
                is_disabled=(
                    player_entity.player.currency < settings["cloudSleevesCost"]
                    or player_entity.player.hasCloudSleeves == 1
                ),
                image="resources/checkmark.png"
                if player_entity.player.hasCloudSleeves == 1
                else None,
            )
        )

        rect = pygame.Rect(640, 660, 49, 49)
        wings_button = world.gen_entity()
        wings_button.attach(
            ButtonComponent(
                rect,
                text="Buy"
                if player_entity.player.hasCloudSleeves == 1
                and player_entity.player.hasWings == 0
                else "",
                callback=lambda: post(Event(EQUIP_BUY_WINGS)),
                is_small=True,
                is_disabled=(
                    (
                        player_entity.player.currency < settings["wingsCost"]
                        and player_entity.player.hasCloudSleeves == 1
                    )
                    or player_entity.player.hasCloudSleeves == 0
                    or player_entity.player.hasWings == 1
                ),
                image="resources/locked.png"
                if player_entity.player.hasCloudSleeves == 0
                else "resources/checkmark.png"
                if player_entity.player.hasWings == 1
                else None,
            )
        )

    def update(self, events, world):
        settings = world.find_component("settings")

        for event in events:
            if event.type == EQUIP_QUIT:
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "stop",
                        "sound": "shop_music",
                    }
                )
                return SceneManager.new_root(scenes.title.TitleScene())
            if event.type == EQUIP_BUY_CLOUD_SLEEVES:
                self._shop(settings["cloudSleevesCost"], "cloud_sleeves", world)
                self.teardown(world)
                self.setup(world)
            if event.type == EQUIP_BUY_WINGS:
                self._shop(settings["wingsCost"], "wings", world)
                self.teardown(world)
                self.setup(world)
            if event.type == EQUIP_BUY_JET_BOOTS:
                self._shop(settings["jetBootsCost"], "jet_boots", world)
                self.teardown(world)
                self.setup(world)
            if event.type == EQUIP_BUY_MORE_FUEL:
                self._shop(self.extra_fuel_cost, "extra_fuel", world)
                self.teardown(world)
                self.setup(world)
            if event.type == EQUIP_SAVE_AND_START:
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "stop",
                        "sound": "shop_music",
                    }
                )
                self._save(settings["save_file"], world)
                self.teardown(world)
                post(Event(LOAD))
                return SceneManager.pop()

        world.process_all_systems(events)

        # start music
        world.inject_event(
            {
                "type": "sound",
                "action": "start",
                "sound": "shop_music",
            }
        )

    def render(self, world):
        context = world.find_component("context")
        settings = world.find_component("settings")
        screen = context["screen"]

        player_entity = world.find_entity("player")

        # Draw a nice background
        screen.blit(pygame.image.load(find_data_file("resources/bg_sky.png")), (0, 0))
        screen.blit(pygame.image.load(find_data_file("resources/bg_sky.png")), (0, 500))

        # text
        text = self.font.render(
            f"Money for upgrades: ${player_entity.player.currency}",
            True,
            (245, 245, 245),
        )
        screen.blit(text, (50, 50))

        text = self.big_font.render("Legs:", True, (245, 245, 245))
        screen.blit(text, (120, 480))
        pygame.draw.line(screen, (245, 245, 245), (120, 531), (223, 531), width=8)

        text = self.font.render("Jet Booster", True, (245, 245, 245))
        screen.blit(text, (180, 550))
        if player_entity.player.hasJetBoots == 1:
            text = self.font.render("Owned", True, (245, 245, 245))
        else:
            text_color = (
                (120, 250, 40)
                if player_entity.player.currency >= settings["jetBootsCost"]
                else (170, 200, 200)
            )
            text = self.font.render(
                f"Cost: ${settings['jetBootsCost']}", True, text_color
            )
        screen.blit(text, (180, 582))
        text = self.small_font.render(
            "Press space to give yourself a boost!", True, (230, 200, 85)
        )
        screen.blit(text, (120, 614))

        text = self.font.render("More Fuel", True, (245, 245, 245))
        screen.blit(text, (180, 650))
        if player_entity.player.extraFuel == 9:
            text = self.font.render("Maxed Out", True, (245, 245, 245))
        else:
            text_color = (
                (120, 250, 40)
                if player_entity.player.currency >= self.extra_fuel_cost
                else (170, 200, 200)
            )
            text = self.font.render(f"Cost: ${self.extra_fuel_cost}", True, text_color)
        screen.blit(text, (180, 682))
        # TODO
        text = self.small_font.render(
            "More fuel means more boosting!", True, (230, 200, 85)
        )
        screen.blit(text, (120, 714))
        if player_entity.player.hasJetBoots > 0:
            text = self.small_font.render(
                f"Total boosts: {player_entity.player.extraFuel + 1}{'! Wow!' if player_entity.player.extraFuel == 9 else ''}",
                True,
                (220, 40, 10),
            )
            screen.blit(text, (120, 744))

        text = self.big_font.render("Arms:", True, (245, 245, 245))
        screen.blit(text, (640, 480))
        pygame.draw.line(screen, (245, 245, 245), (640, 531), (763, 531), width=8)

        text = self.font.render("Cloud Sleeves", True, (245, 245, 245))
        screen.blit(text, (700, 550))
        if player_entity.player.hasCloudSleeves == 1:
            text = self.font.render("Owned", True, (245, 245, 245))
        else:
            text_color = (
                (120, 250, 40)
                if player_entity.player.currency >= settings["cloudSleevesCost"]
                else (170, 200, 200)
            )
            text = self.font.render(
                f"Cost: ${settings['cloudSleevesCost']}", True, text_color
            )
        screen.blit(text, (700, 582))
        text = self.small_font.render(
            "Don't let gravity get you down!", True, (230, 200, 85)
        )
        screen.blit(text, (640, 614))

        text = self.font.render("Bird Wings", True, (245, 245, 245))
        screen.blit(text, (700, 650))
        if player_entity.player.hasWings == 1:
            text = self.font.render("Owned", True, (245, 245, 245))
        else:
            text_color = (
                (120, 250, 40)
                if player_entity.player.currency >= settings["wingsCost"]
                else (170, 200, 200)
            )
            text = self.font.render(f"Cost: ${settings['wingsCost']}", True, text_color)
        screen.blit(text, (700, 682))
        text = self.small_font.render(
            "Make tighter turns! Y'know, like a bird. Just go with it.",
            True,
            (230, 200, 85),
        )
        screen.blit(text, (640, 714))
        text = self.small_font.render(
            "If you want to pretend you don't have wings, hold shift.",
            True,
            (230, 200, 85),
        )
        screen.blit(text, (640, 744))

        # Icarus himself
        sprite = pygame.sprite.Sprite()
        sprite.image = pygame.image.load(find_data_file("resources/icarus_body.png"))
        sprite.image = pygame.transform.scale(sprite.image, (288, 200))
        sprite.rect = sprite.image.get_rect()
        sprite.rect.centerx = screen.get_width() // 2
        sprite.rect.centery = screen.get_height() // 2 - 240 + self.icarus_offset
        screen.blit(sprite.image, sprite.rect)

        # Display the buttons
        render_all_buttons(screen, world)

        # Flip display to render lines
        pygame.display.flip()

        self.icarus_offset = self.icarus_offset + self.icarus_offset_increment

        if abs(self.icarus_offset) > 10:
            self.icarus_offset_increment = self.icarus_offset_increment * -1

    def _save(self, save_file, world):
        if not os.path.exists(user_data_dir(APP_NAME, APP_AUTHOR)):
            os.makedirs(user_data_dir(APP_NAME, APP_AUTHOR))
        f = open(os.path.join(user_data_dir(APP_NAME, APP_AUTHOR), save_file), "w")
        player_entity = world.find_entity("player")
        out = {
            "currency": player_entity.player.currency,
            "hasCloudSleeves": player_entity.player.hasCloudSleeves,
            "hasWings": player_entity.player.hasWings,
            "hasJetBoots": player_entity.player.hasJetBoots,
            "extraFuel": player_entity.player.extraFuel,
        }
        f.write(json.dumps(out))
        f.close()

    def _shop(self, cost, item, world):
        player_entity = world.find_entity("player")

        if player_entity.player.currency >= cost:
            player_entity.player.currency = player_entity.player.currency - cost

            if item == "cloud_sleeves":
                player_entity.player.hasCloudSleeves = 1
            if item == "wings":
                player_entity.player.hasWings = 1
            if item == "jet_boots":
                player_entity.player.hasJetBoots = 1
            if item == "extra_fuel":
                player_entity.player.extraFuel += 1

    def render_previous(self):
        return False

    def teardown(self, world):
        buttons = world.filter("button")

        world.remove_entities(buttons)

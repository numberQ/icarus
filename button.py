import pygame

from ecs import Component, System


# Helper function which creates the surfaces for buttons
def _create_image(image_path, text):
    font = pygame.font.Font(None, 30)
    # create a sprite from the given image path
    # and create the rect to blit the text onto
    # if this is for the pressed button, move the rect down to keep the text aligned
    sprite = pygame.sprite.Sprite()
    sprite.image = pygame.image.load(image_path)
    sprite.rect = sprite.image.get_rect()
    if "press" in image_path:
        sprite.rect.move_ip(0, 4)

    # render the text once here instead of every frame
    if text != "":
        text_surf = font.render(text, 1, pygame.Color("white"))
        # again, see how easy it is to center stuff using Rect's attributes like 'center'
        text_rect = text_surf.get_rect(center=sprite.rect.center)
        sprite.image.blit(text_surf, text_rect)
    return sprite.image


# Helper function to take all buttons from the world and render then to a surface
def render_all_buttons(surface, world):
    buttons = world.filter("button")
    for button in buttons:
        btn = button["button"]
        if btn["isMouseDown"]:
            surface.blit(btn["clicked"], btn["rect"])
        elif btn["active"]:
            surface.blit(btn["hover"], btn["rect"])
        else:
            surface.blit(btn["normal"], btn["rect"])


class ButtonComponent(Component):
    def __init__(self, color, color_hover, rect, text="", outline=None, callback=None):
        normal_image = _create_image("resources/btn_inactive.png", text)
        hover_image = _create_image("resources/btn_hover.png", text)
        clicked_image = _create_image("resources/btn_press.png", text)
        metadata = {
            "normal": normal_image,
            "hover": hover_image,
            "clicked": clicked_image,
            "rect": rect,
            "text": text,
            "active": False,
            "isMouseDown": False,
            "callback": callback,
        }
        Component.__init__(self, "button", metadata)


class ButtonSystem(System):
    def __init__(self):
        super().__init__()

    def process(self, events, world):
        # clear the event queue
        self.pending()

        mouseup = False
        mousedown = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP:
                mouseup = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                mousedown = True

        mouse_pos = pygame.mouse.get_pos()
        buttons = world.filter("button")

        for button in buttons:
            btn = button["button"]
            previously_active = btn["active"]
            currently_active = btn["rect"].collidepoint(mouse_pos)
            btn["active"] = currently_active

            # Play a sound if the button has been focused
            if not previously_active and currently_active:
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "play",
                        "sound": "rollover",
                    }
                )

            # If the mouse is clicked, highlight the button as clicked until mouseup
            if currently_active and mousedown:
                btn["isMouseDown"] = True

            if not currently_active:
                btn["isMouseDown"] = False

            # Test if the button is clicked, play a clicked sound,
            # Then run the callback if it exists
            if currently_active and btn["isMouseDown"] and mouseup:
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "play",
                        "sound": "click",
                    }
                )
                if btn["callback"]:
                    btn["callback"]()

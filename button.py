import pygame

from ecs import Component, System


# Helper function which creates the surfaces for buttons
def _create_image(color, outline, text, rect):
    font = pygame.font.Font(None, 36)
    # function to create the actual surface
    # see how we can make use of Rect's virtual attributes like 'size'
    img = pygame.Surface(rect.size)
    if outline:
        # here we can make good use of Rect's functions again
        # first, fill the Surface in the outline color
        # then fill a rectangular area in the actual color
        # 'inflate' is used to 'shrink' the rect
        img.fill(outline)
        img.fill(color, rect.inflate(-4, -4))
    else:
        img.fill(color)

    # render the text once here instead of every frame
    if text != "":
        text_surf = font.render(text, 1, pygame.Color("black"))
        # again, see how easy it is to center stuff using Rect's attributes like 'center'
        text_rect = text_surf.get_rect(center=rect.center)
        img.blit(text_surf, text_rect)
    return img


# Helper function to take all buttons from the world and render then to a surface
def render_all_buttons(surface, world):
    buttons = world.filter("button")
    for button in buttons:
        btn = button["button"]
        if btn["active"]:
            surface.blit(btn["hover"], btn["rect"])
        else:
            surface.blit(btn["normal"], btn["rect"])


class ButtonComponent(Component):
    def __init__(self, color, color_hover, rect, text="", outline=None, callback=None):
        tmp_rect = pygame.Rect(0, 0, *rect.size)
        normal_image = _create_image(color, outline, text, tmp_rect)
        hover_image = _create_image(color_hover, outline, text, tmp_rect)
        metadata = {
            "normal": normal_image,
            "hover": hover_image,
            "rect": rect,
            "text": text,
            "active": False,
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
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP:
                mouseup = True

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

            # Test if the button is clicked, play a clicked sound,
            # Then run the callback if it exists
            if currently_active and mouseup:
                world.inject_event(
                    {
                        "type": "sound",
                        "action": "play",
                        "sound": "click",
                    }
                )
                if btn["callback"]:
                    btn["callback"]()

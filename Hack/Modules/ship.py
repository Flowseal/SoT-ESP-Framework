"""
@Author https://github.com/DougTheDruid
@Source https://github.com/DougTheDruid/SoT-ESP-Framework
"""

import os
from pyglet.sprite import Sprite
from pyglet.shapes import Circle
from pyglet import image
from helpers import calculate_distance, object_to_screen, foreground_batch, background_batch
from mapping import ships
from Graphics.elements import LabelDefault
from Modules import DisplayObject
from Classes import Ship, Crew

CIRCLE_SIZE = 25
SLOOP_ICON = image.load(os.path.join(os.getcwd(), 'Graphics', 'Images', 'Sloop_icon.png'))
BRIGANTINE_ICON = image.load(os.path.join(os.getcwd(), 'Graphics', 'Images', 'Brigantine_icon.png'))
GALLEON_ICON = image.load(os.path.join(os.getcwd(), 'Graphics', 'Images', 'Galleon_icon.png'))


class ShipModule(DisplayObject):
    """
    Class to generate information for a ship object in memory
    """

    def __init__(self, actor_id, address, raw_name, my_coords):
        """
        Upon initialization of this class, we immediately initialize the
        DisplayObject parent class as well (to utilize common methods)

        We then set our class variables and perform all of our info collecting
        functions, like finding the actors base address and converting the
        "raw" name to a more readable name per our Mappings. We also create
        a circle and label and add it to our batch for display to the screen.

        All of this data represents a "Ship". If you want to add more, you will
        need to add another class variable under __init__ and in the update()
        function

        :param memory_reader: The SoT MemoryHelper Object we use to read memory
        :param address: The address in which the AActor begins
        :param my_coords: a dictionary of the local players coordinates
        :param raw_name: The raw actor name used to translate w/ mapping.py
        """
        # Initialize our super-class
        super().__init__()

        self.actor_id = actor_id
        self.address = address
        self.actor_root_comp_ptr = self._get_root_comp_address(address)
        self.my_coords = my_coords
        self.raw_name = raw_name

        # Generate our Ship's info
        self.name = ships.get(self.raw_name).get("Name")
        self.coords = self._coord_builder(self.actor_root_comp_ptr,
                                          self.coord_offset)
        self.distance = calculate_distance(self.coords, self.my_coords)

        self.screen_coords = object_to_screen(self.my_coords, self.coords)
        self.crew_guid = Ship.get_crew_guid(self.address)

        # All of our actual display information & rendering
        self.text_str = self._built_text_string()
        self.text_render = self._build_text_render()
        self.circle = self._build_circle_render()
        self.icon = self._build_icon_render()

        # Used to track if the display object needs to be removed
        self.to_delete = False
        

    def _build_icon_render(self) -> Sprite:
        """
        Creates an icon based on ship type
        """
        if "Galleon" in self.name:
            ship_type = GALLEON_ICON
        elif "Brig" in self.name:
            ship_type = BRIGANTINE_ICON
        else:
            ship_type = SLOOP_ICON

        if self.screen_coords:
            return Sprite(ship_type, self.screen_coords[0] - CIRCLE_SIZE, self.screen_coords[1] - CIRCLE_SIZE,
                          batch=foreground_batch)

        return Sprite(ship_type, 0, 0, batch=foreground_batch)

    def _build_circle_render(self) -> Circle:
        """
        Creates a circle located at the screen coordinates (if they exist).
        Uses the color specified in our globals w/ a size of 10px radius.
        Assigns the object to our batch & group
        """
        if self.screen_coords:
            return Circle(self.screen_coords[0] - CIRCLE_SIZE/2, self.screen_coords[1] - CIRCLE_SIZE/2,
                          CIRCLE_SIZE, color=(255, 255, 255), batch=background_batch)

        return Circle(0, 0, CIRCLE_SIZE, color=(255, 255, 255), batch=background_batch)

    def _built_text_string(self) -> str:
        """
        Generates a string used for rendering. Separate function in the event
        you need to add more data (Sunk %, hole count, etc)
        """
        return f"{self.name} - {self.distance}m"

    def _build_text_render(self) -> LabelDefault:
        """
        Function to build our actual label which is sent to Pyglet. Sets it to
        be located at the screen coordinated + our text_offsets from helpers.py

        Assigns the object to our batch & group

        :rtype: LabelDefault
        :return: What text we want displayed next to the ship
        """
        if self.screen_coords:
            return LabelDefault(self.text_str,
                         x=self.screen_coords[0] + CIRCLE_SIZE / 2 + 10,
                         y=self.screen_coords[1] + CIRCLE_SIZE / 2 - 30,
                         batch=foreground_batch)

        return LabelDefault(self.text_str, x=0, y=0, batch=foreground_batch)

    def update(self, my_coords: dict):
        """
        A generic method to update all the interesting data about a ship
        object, to be called when seeking to perform an update on the
        Actor without doing a full-scan of all actors in the game.

        1. Determine if the actor is what we expect it to be
        2. See if any data has changed
        3. Update the data if something has changed

        In theory if all data is the same, we could *not* update our Label's
        text, therefore saving resources. Not implemented, but a possibility
        """
        if self._get_actor_id(self.address) != self.actor_id:
            self.to_delete = True
            self.circle.delete()
            self.icon.delete()
            self.text_render.delete()
            return

        self.my_coords = my_coords
        self.coords = self._coord_builder(self.actor_root_comp_ptr,
                                          self.coord_offset)
        new_distance = calculate_distance(self.coords, self.my_coords)

        self.screen_coords = object_to_screen(self.my_coords, self.coords)

        if self.screen_coords:
            # Ships have two actors dependant on distance. This switches them
            # seamlessly at 1750m
            if "Near" in self.name and new_distance > 1750:
                self.text_render.visible = False
                self.circle.visible = False
                self.icon.visible = False
            elif "Near" not in self.name and new_distance < 1750:
                self.text_render.visible = False
                self.circle.visible = False
                self.icon.visible = False
            else:
                self.text_render.visible = True
                self.icon.visible = True
                self.circle.visible = True

            # Update the position of our circle and text
            self.circle.x = self.screen_coords[0] - CIRCLE_SIZE / 2
            self.circle.y = self.screen_coords[1] - CIRCLE_SIZE / 2
            self.icon.x = self.screen_coords[0] - CIRCLE_SIZE * 1.45
            self.icon.y = self.screen_coords[1] - CIRCLE_SIZE * 1.45
            self.text_render.x = self.screen_coords[0] + CIRCLE_SIZE / 2 + 10
            self.text_render.y = self.screen_coords[1] + CIRCLE_SIZE / 2 - 30
   
            # Update ship color if we know the crew
            if self.crew_guid in Crew.tracker:
                self.circle.color = Crew.tracker[self.crew_guid].color[:3]

            # Update our text to reflect out new distance
            self.distance = new_distance
            self.text_str = self._built_text_string()
            self.text_render.text = self.text_str

        else:
            # if it isn't on our screen, set it to invisible to save resources
            self.text_render.visible = False
            self.circle.visible = False
            self.icon.visible = False
    
    def _delete(self):
        self.text_render.delete()
        self.circle.delete()
        self.icon.delete()

"""A module for tracking useful in-game information."""

import config
import mss
import mss.windows
import time
import cv2
import threading
import numpy as np
import utils
from components import Point


# The distance between the top of the minimap and the top of the screen
MINIMAP_TOP_BORDER = 21

# The thickness of the other three borders of the minimap
MINIMAP_BOTTOM_BORDER = 8

# The bottom right corner of the minimap
MINIMAP_TEMPLATE = cv2.imread('assets/minimap_template.jpg', 0)

# The player's symbol on the minimap
PLAYER_TEMPLATE = cv2.imread('assets/player_template.png', 0)

# A rune's symbol on the minimap
RUNE_RANGES = (
    ((141, 148, 245), (146, 158, 255)),
)
rune_filtered = utils.filter_color(cv2.imread('assets/rune_template.png'), RUNE_RANGES)
RUNE_TEMPLATE = cv2.cvtColor(rune_filtered, cv2.COLOR_BGR2GRAY)

# The Elite Boss's warning sign
ELITE_TEMPLATE = cv2.imread('assets/elite_template.jpg', 0)


class Capture:
    """
    A class that tracks player position and various in-game events. It constantly updates
    the config module with information regarding these events. It also annotates and
    displays the minimap in a pop-up window.
    """

    def __init__(self):
        """Initializes this Capture object's main thread."""

        config.capture = self

        self.ready = False
        self.calibrated = False
        self.minimap = {}
        self.minimap_ratio = 1
        self.minimap_sample = None

        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """
        Starts this Capture's thread.
        :return:    None
        """

        print('\n[~] Started video capture.')
        self.thread.start()

    def _main(self):
        """Constantly monitors the player's position and in-game events."""

        mss.windows.CAPTUREBLT = 0
        with mss.mss() as sct:
            rune_counter = 0
            while True:
                frame = np.array(sct.grab(config.MONITOR))

                if not self.calibrated:
                    # Calibrate by finding the bottom right corner of the minimap
                    _, br = utils.single_match(frame[:round(frame.shape[0] / 4),
                                                     :round(frame.shape[1] / 3)],
                                               MINIMAP_TEMPLATE)
                    mm_tl = (MINIMAP_BOTTOM_BORDER, MINIMAP_TOP_BORDER)
                    mm_br = tuple(max(75, a - MINIMAP_BOTTOM_BORDER) for a in br)
                    self.minimap_ratio = (mm_br[0] - mm_tl[0]) / (mm_br[1] - mm_tl[1])
                    self.minimap_sample = frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]
                    self.calibrated = True

                height, width, _ = frame.shape

                # Check for unexpected black screen regardless of whether bot is enabled
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if config.enabled and not config.bot.alert_active \
                        and np.count_nonzero(gray < 15) / height / width > 0.95:
                    config.bot.alert_active = True
                    config.enabled = False

                # Check for elite warning
                elite_frame = frame[height//4:3*height//4, width//4:3*width//4]
                elite = utils.multi_match(elite_frame, ELITE_TEMPLATE, threshold=0.9)
                if config.enabled and not config.bot.alert_active and elite:
                    config.bot.alert_active = True
                    config.enabled = False

                # Crop the frame to only show the minimap
                minimap = frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]

                # Determine the player's position
                player = utils.multi_match(minimap, PLAYER_TEMPLATE, threshold=0.8)
                if player:
                    config.player_pos = utils.convert_to_relative(player[0], minimap)

                # Check for a rune
                if rune_counter == 0 and not config.bot.rune_active:
                    filtered = utils.filter_color(minimap, RUNE_RANGES)
                    matches = utils.multi_match(filtered, RUNE_TEMPLATE, threshold=0.9)
                    if matches and config.routine.sequence:
                        abs_rune_pos = (matches[0][0], matches[0][1])
                        config.bot.rune_pos = utils.convert_to_relative(abs_rune_pos, minimap)
                        distances = list(map(Capture._distance_to_rune, config.routine.sequence))
                        index = np.argmin(distances)
                        config.bot.rune_closest_pos = config.routine[index].location
                        config.bot.rune_active = True
                rune_counter = (rune_counter + 1) % 100

                # Package display information to be polled by GUI
                self.minimap = {
                    'minimap': minimap,
                    'rune_active': config.bot.rune_active,
                    'rune_pos': config.bot.rune_pos,
                    'path': config.path,
                    'player_pos': config.player_pos
                }

                if not self.ready:
                    self.ready = True
                time.sleep(0.001)

    @staticmethod
    def _count(frame, threshold):
        """
        Counts the number of pixels in FRAME that are less than or equal to THRESHOLD.
        Two pixels are compared by their corresponding tuple elements in order.
        :param frame:       The image in which to search.
        :param threshold:   The pixel value to compare to.
        :return:            The number of pixels in FRAME that are below THRESHOLD.
        """

        count = 0
        for row in frame:
            for col in row:
                pixel = frame[row][col]
                if len(pixel) == len(threshold):
                    valid = True
                    for i in range(len(pixel)):
                        valid = valid and frame[i] <= threshold[i]
                    if valid:
                        count += 1
        return count

    @staticmethod
    def _distance_to_rune(point):
        """
        Calculates the distance from POINT to the rune.
        :param point:   The position to check.
        :return:        The distance from POINT to the rune, infinity if it is not a Point object.
        """

        if isinstance(point, Point):
            return utils.distance(config.bot.rune_pos, point.location)
        return float('inf')

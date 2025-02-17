"""A collection of all commands that a Kanna can use to interact with the game."""

import config
import time
import math
import settings
import utils
from components import Command
from vkeys import press, key_down, key_up


def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Auto Maple.
    """

    num_presses = 2
    if direction == 'up' or direction == 'down':
        num_presses = 1
    d_y = target[1] - config.player_pos[1]
    if abs(d_y) > settings.move_tolerance * 1.5:
        if direction == 'down':
            press('space', 3)
        elif direction == 'up':
            press('space', 1)
    press('e', num_presses)


class Adjust(Command):
    """Fine-tunes player position using small movements."""

    def __init__(self, x, y, max_steps=5):
        super().__init__(locals())
        self.target = (float(x), float(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        counter = self.max_steps
        toggle = True
        error = utils.distance(config.player_pos, self.target)
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            if toggle:
                d_x = self.target[0] - config.player_pos[0]
                threshold = settings.adjust_tolerance / math.sqrt(2)
                if abs(d_x) > threshold:
                    walk_counter = 0
                    if d_x < 0:
                        key_down('left')
                        while config.enabled and d_x < -1 * threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('left')
                    else:
                        key_down('right')
                        while config.enabled and d_x > threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('right')
                    counter -= 1
            else:
                d_y = self.target[1] - config.player_pos[1]
                if abs(d_y) > settings.adjust_tolerance / math.sqrt(2):
                    if d_y < 0:
                        Teleport('up').main()
                    else:
                        key_down('down')
                        time.sleep(0.05)
                        press('space', 3, down_time=0.1)
                        key_up('down')
                        time.sleep(0.05)
                    counter -= 1
            error = utils.distance(config.player_pos, self.target)
            toggle = not toggle


class Buff(Command):
    """Uses each of Kanna's buffs once. Uses 'Haku Reborn' whenever it is available."""

    def __init__(self):
        super().__init__(locals())
        self.haku_time = 0
        self.buff_time = 0

    def main(self):
        buffs = ['f1', 'f2']
        now = time.time()
        if self.haku_time == 0 or now - self.haku_time > 490:
            press('f4', 2)
            press('f3', 2)
            self.haku_time = now
        if self.buff_time == 0 or now - self.buff_time > settings.buff_cooldown:
            for key in buffs:
                press(key, 3, up_time=0.3)
            self.buff_time = now


class Teleport(Command):
    """
    Teleports in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """

    def __init__(self, direction, jump='False'):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)
        self.jump = settings.validate_boolean(jump)

    def main(self):
        num_presses = 3
        time.sleep(0.05)
        if self.direction in ['up', 'down']:
            num_presses = 2
        if self.direction != 'up':
            key_down(self.direction)
            time.sleep(0.05)
        if self.jump:
            if self.direction == 'down':
                press('space', 3, down_time=0.1)
            else:
                press('space', 1)
        if self.direction == 'up':
            key_down(self.direction)
            time.sleep(0.05)
        press('e', num_presses)
        key_up(self.direction)
        if settings.record_layout:
            config.layout.add(*config.player_pos)


class Shikigami(Command):
    """Attacks using 'Shikigami Haunting' in a given direction."""

    def __init__(self, direction, attacks=2, repetitions=1):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)
        self.attacks = int(attacks)
        self.repetitions = int(repetitions)

    def main(self):
        time.sleep(0.05)
        key_down(self.direction)
        time.sleep(0.05)
        for _ in range(self.repetitions):
            press('r', self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class Tengu(Command):
    """Uses 'Tengu Strike' once."""

    def main(self):
        press('q', 1)


class Yaksha(Command):
    """
    Places 'Ghost Yaksha Boss' in a given direction, or towards the center of the map if
    no direction is specified.
    """

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction:
            press(self.direction, 1, down_time=0.1, up_time=0.05)
        else:
            if config.player_pos[0] > 0.5:
                press('left', 1, down_time=0.1, up_time=0.05)
            else:
                press('right', 1, down_time=0.1, up_time=0.05)
        press('2', 3)


class Vanquisher(Command):
    """Holds down 'Vanquisher's Charm' until this command is called again."""

    def main(self):
        key_up('f')
        time.sleep(0.075)
        key_down('f')
        time.sleep(0.15)


class Kishin(Command):
    """Uses 'Kishin Shoukan' once."""

    def main(self):
        press('ctrl', 4, down_time=0.1, up_time=0.15)


class NineTails(Command):
    """Uses 'Nine-Tailed Fury' once."""

    def main(self):
        press('3', 3)


class Exorcist(Command):
    """Uses 'Exorcist's Charm' once."""

    def __init__(self, jump='False'):
        super().__init__(locals())
        self.jump = settings.validate_boolean(jump)

    def main(self):
        if self.jump:
            press('space', 1, down_time=0.1, up_time=0.15)
        press('w', 2, up_time=0.05)


class Domain(Command):
    """Uses 'Spirit's Domain' once."""

    def main(self):
        press('z', 3)


class Legion(Command):
    """Uses 'Ghost Yaksha: Great Oni Lord's Legion' once."""

    def main(self):
        press('5', 2, down_time=0.1)


class BlossomBarrier(Command):
    """Places a 'Blossom Barrier' on the ground once."""

    def main(self):
        press('g', 2)


class Yukimusume(Command):
    """Uses 'Yuki-musume Shoukan' once."""

    def main(self):
        press('c', 2)


class Balance(Command):
    """Restores mana using 'Mana Balance' once."""

    def main(self):
        press('lshift', 2)


class Charm(Command):
    """Jumps up using 'Shikigami Charm'."""

    def main(self):
        press('d', 2)

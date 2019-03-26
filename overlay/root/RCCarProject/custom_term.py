#!/usr/bin/env python2

import curses
import time
import sys

# ------------------------------------- Message ID -----------------------------------------
DIRECTION = 0
COMMAND = 1

# -------------------------------------- Directions -----------------------------------------
FORWARD = "forward"
BACKWARD = "backward"
ROTATE_RIGHT = "rotate_right"
ROTATE_LEFT = "rotate_left"
TURN_RIGHT = "turn_right"
TURN_LEFT = "turn_left"

# -------------------------------------- Commands -------------------------------------------
SPEED_UP = "s+"
SPEED_DOWN = "s-"
TURN_RATE_UP = "t+"
TURN_RATE_DOWN = "t-"
EXIT_SESSION = "e"


# ------------------------------------ Custom terminal ----------------------------------------
class CustomTerm(object):

    def __init__(self):

        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(False)

        self.stdscr.keypad(True)
        self._speed = 0
        self._turn_rate = 0
        self._direction = None
        self._distance = 0

        self.stdscr.addstr(0, 0, "    ____  ______   _________    ____")
        self.stdscr.addstr(1, 0, "   / __ \\/ ____/  / ____/   |  / __ \\")
        self.stdscr.addstr(2, 0, "  / /_/ / /      / /   / /| | / /_/ /")
        self.stdscr.addstr(3, 0, " / _, _/ /___   / /___/ ___ |/ _, _/ ")
        self.stdscr.addstr(4, 0, "/_/ |_|\\____/   \\____/_/  |_/_/ |_| ")
        self.stdscr.addstr(5, 0, "                                         ")
        self.stdscr.addstr(6, 0, "-----------------------------------------")
        self.stdscr.addstr(7, 0, "Controls:")
        self.stdscr.addstr(8, 0, "q/w: increase/decrease turn rate.")
        self.stdscr.addstr(9, 0, "a/z: increase/decrease speed.")
        self.stdscr.addstr(10, 0, "f4: exit.")
        self.stdscr.addstr(11, 0, "-----------------------------------------")
        self.stdscr.addstr(12, 0, "Current direction: {}\n".format(self._direction))
        self.stdscr.addstr(13, 0, "Current speed: {}\n".format(self._speed))
        self.stdscr.addstr(14, 0, "Current turn rate: {}\n".format(self._turn_rate))
        self.stdscr.addstr(15, 0, "Distance to object: {}\n".format(self._turn_rate))
        self.stdscr.refresh()

    def end_session(self):

        self.stdscr.keypad(False)
        curses.curs_set(True)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def get_input(self):

        msg_id = None
        message = None

        # get user input
        start = time.time()
        keys = set()

        while time.time() - start < 0.3:
            keys.add(self.stdscr.getch())

        # # if exit key
        if curses.KEY_F4 in keys:

            msg_id = COMMAND
            message = EXIT_SESSION
            self._direction = None

        elif ord('a') in keys or ord('A') in keys:

            msg_id = COMMAND
            message = SPEED_UP

        elif ord('z') in keys or ord('Z') in keys:

            msg_id = COMMAND
            message = SPEED_DOWN

        elif ord('q') in keys or ord('Q') in keys:

            msg_id = COMMAND
            message = TURN_RATE_UP

        elif ord('w') in keys or ord('W') in keys:

            msg_id = COMMAND
            message = TURN_RATE_DOWN

        elif curses.KEY_UP in keys:

            msg_id = DIRECTION

            if curses.KEY_RIGHT in keys:

                message = TURN_RIGHT

            elif curses.KEY_LEFT in keys:

                message = TURN_LEFT

            else:

                message = FORWARD

        elif curses.KEY_DOWN in keys:

            msg_id = DIRECTION
            message = BACKWARD

        elif curses.KEY_RIGHT in keys:

            msg_id = DIRECTION

            if curses.KEY_UP in keys:

                message = TURN_RIGHT

            else:

                message = ROTATE_RIGHT

        elif curses.KEY_LEFT in keys:

            msg_id = DIRECTION

            if curses.KEY_UP in keys:

                message = TURN_LEFT

            else:

                message = ROTATE_LEFT

        else:

            pass

        return msg_id, message

    def update_data(self, direction=None, speed=None, turn_rate=None, object_range=None):

        if direction:
            self._direction = direction
            self.stdscr.addstr(12, 0, "Current direction: {}\n".format(self._direction))

        if speed:
            self._speed = speed
            self.stdscr.addstr(13, 0, "Current speed: {}\n".format(self._speed))

        if turn_rate:
            self._turn_rate = turn_rate
            self.stdscr.addstr(14, 0, "Current turn rate: {}\n".format(self._turn_rate))

        if object_range:
            self._distance = object_range
            self.stdscr.addstr(15, 0, "Distance to object: {}\n".format(self._distance))


        self.stdscr.refresh()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_session()


def main():
    ct = CustomTerm()

    while True:

        if ct.get_input() == curses.KEY_F4:
            break
        else:
            ct.update_data()

    ct.end_session()


if __name__ == '__main__':
    main()

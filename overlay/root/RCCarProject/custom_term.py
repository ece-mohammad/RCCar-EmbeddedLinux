#!/usr/bin/env python2

import curses
import time

# ------------------------------------- Message ID -----------------------------------------
DIRECTION = 0
COMMAND = 1

# -------------------------------------- Directions -----------------------------------------
FORWARD = "forward"
BACKWARD = "backward"
ROTATE_RIGHT = "rotate_right"
ROTATE_LEFT = "rotate_left"
FORWARD_RIGHT = "fwd_right"
FORWARD_LEFT = "fwd_left"
BACKWARD_RIGHT = "bwd_right"
BACKWARD_LEFT = "bwd_left"

# -------------------------------------- Commands -------------------------------------------
SPEED_UP = "speed+"
SPEED_DOWN = "speed-"
TURN_RATE_UP = "turn_rate+"
TURN_RATE_DOWN = "turn_rate-"
STOP_CAR = "stop"
EXIT_SESSION = "exit"


# ------------------------------------ Custom terminal ----------------------------------------
class CustomTerm(object):

    def __init__(self):

        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(False)
        curses.halfdelay(1)

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
        """
        End the custom terminal session
        :return: 0
        """
        self.stdscr.keypad(False)
        curses.curs_set(True)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

        return 0

    def get_input(self):
        """
        gets user input from the terminal
        :return: (message type, message)
        message type: Indicates the type of the pressed key (DIRECTION, COMMAND)
        message: indicates action associated with the pressed key
        """

        # get user input
        start = time.time()
        keys = set()

        # add keys to set
        while (time.time() - start) < 0.05:
            keys.add(self.stdscr.getch())

        # if exit key
        if curses.KEY_F4 in keys:

            msg_id = COMMAND
            message = EXIT_SESSION
            self._direction = None
            self._speed = 0
            self._turn_rate = 0
            self._distance = 0

        # if key is a
        elif ord('a') in keys or ord('A') in keys:

            msg_id = COMMAND
            message = SPEED_UP

        # if key is z
        elif ord('z') in keys or ord('Z') in keys:

            msg_id = COMMAND
            message = SPEED_DOWN

        # if key is w
        elif ord('w') in keys or ord('W') in keys:

            msg_id = COMMAND
            message = TURN_RATE_UP

        # if key is q
        elif ord('q') in keys or ord('Q') in keys:

            msg_id = COMMAND
            message = TURN_RATE_DOWN

        # if up + right
        elif curses.KEY_UP in keys and curses.KEY_RIGHT in keys:

            msg_id = DIRECTION
            message = FORWARD_RIGHT

        # if up + left
        elif curses.KEY_UP in keys and curses.KEY_LEFT in keys:

            msg_id = DIRECTION
            message = FORWARD_LEFT

        # if down + right
        elif curses.KEY_DOWN in keys and curses.KEY_RIGHT in keys:

            msg_id = DIRECTION
            message = BACKWARD_RIGHT

        # if down + left
        elif curses.KEY_DOWN in keys and curses.KEY_LEFT in keys:

            msg_id = DIRECTION
            message = BACKWARD_LEFT

        # if up
        elif curses.KEY_UP in keys:

            msg_id = DIRECTION
            message = FORWARD

        # if down
        elif curses.KEY_DOWN in keys:

            msg_id = DIRECTION
            message = BACKWARD

        # if right
        elif curses.KEY_RIGHT in keys:

            msg_id = DIRECTION
            message = ROTATE_RIGHT

        # if left
        elif curses.KEY_LEFT in keys:

            msg_id = DIRECTION
            message = ROTATE_LEFT
        
        # if no key is pressed
        elif -1 in keys:

            # stop the car
            msg_id = COMMAND
            message = STOP_CAR

        # otherwise
        else:

            pass

        return msg_id, message

    def update_data(self, direction=None, speed=None, turn_rate=None, object_range=None):
        """
        Updates session data
        :param direction: Current direction of the RC car
        :param speed: Current speed of the RC Car
        :param turn_rate: Current turn rate of RC Car
        :param object_range: Current distance to the object in front of the car
        :return: 0
        """
        if direction is not None:
            self._direction = direction
            self.stdscr.addstr(12, 0, "Current direction: {}\n".format(self._direction))

        if speed is not None:
            self._speed = speed
            self.stdscr.addstr(13, 0, "Current speed: {}\n".format(self._speed))

        if turn_rate is not None:
            self._turn_rate = turn_rate
            self.stdscr.addstr(14, 0, "Current turn rate: {}\n".format(self._turn_rate))

        if object_range is not None:
            self._distance = object_range
            self.stdscr.addstr(15, 0, "Distance to object: {}\n".format(self._distance))

        self.stdscr.refresh()

        return  0

    def display_message(self, msg):
        """
        Displays a message on the screen
        :param msg: message to be displayed
        :return: 0
        """
        self.stdscr.addstr(16, 0, " "*80)
        self.stdscr.addstr(16, 0, msg)
        return 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ends session when exiting current context
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return: 0
        """
        self.end_session()

        return 0


if __name__ == '__main__':

    ct = CustomTerm()

    while True:

        msg_type, msg_data = ct.get_input()

        if msg_type == COMMAND and msg_data == EXIT_SESSION:

            break

        else:

            ct.display_message("Message type: {}, data: {}".format(msg_type, msg_data))

    ct.end_session()


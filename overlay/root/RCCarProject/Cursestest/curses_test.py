#!/usr/bin/env python2

import curses
import time


class RCCarTerm(object):

    def __init__(self):

        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(False)

        self.stdscr.keypad(True)
        self._speed = 0
        self._turn_rate = 0
        self._direction = None

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
        self.stdscr.refresh()

    def end_session(self):

        self.stdscr.keypad(False)
        curses.curs_set(True)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def get_input(self):

        # get user input
        start = time.time()
        keys = set()

        while time.time() - start < 0.3:
            keys.add(self.stdscr.getch())

        return keys

        #
        #
        # # if exit key
        # if key == curses.KEY_F4:
        #
        #     # end session
        #     self.stdscr.addstr(0, 0, "Closing curses session...\n")
        #     self.stdscr.refresh()
        #     self.end_session()
        #     sys.exit(0)
        #
        # elif key == ord('a') or key == ord('A'):
        #
        #     self._speed += 1
        #     if self._speed > 100:
        #         self._speed = 100
        #
        #     self.stdscr.refresh()
        #
        # elif key == ord('z') or key == ord('Z'):
        #
        #     self._speed -= 1
        #     if self._speed < 0:
        #         self._speed = 0
        #
        # elif key == ord('q') or key == ord('Q'):
        #
        #     self._turn_rate += 1
        #     if self._turn_rate > 100:
        #         self._turn_rate = 100
        #
        # elif key == ord('w') or key == ord('W'):
        #
        #     self._turn_rate -= 1
        #     if self._turn_rate < 0:
        #         self._turn_rate = 0
        #
        # elif key == curses.KEY_UP:
        #
        #     self._direction = "Forward"
        #
        # elif key == curses.KEY_DOWN:
        #
        #     self._direction = "Backwards"
        #
        # elif key == curses.KEY_RIGHT:
        #
        #     self._direction = "Right"
        #
        # elif key == curses.KEY_LEFT:
        #
        #     self._direction = "Left"
        #
        # else:
        #
        #     pass

    # def update_display(self):
    #     self.stdscr.addstr(12, 0, "Current direction: {}\n".format(self._direction))
    #     self.stdscr.addstr(13, 0, "Current speed: {}\n".format(self._speed))
    #     self.stdscr.addstr(14, 0, "Current turn rate: {}\n".format(self._turn_rate))
    #     self.stdscr.refresh()
    #
    #     return key


def main():
    ct = RCCarTerm()

    while True:
        keys = ct.get_input()
        if curses.KEY_F4 in keys:
            break
        else:
            print("\r{}\r".format(keys))

    ct.end_session()


if __name__ == '__main__':
    main()

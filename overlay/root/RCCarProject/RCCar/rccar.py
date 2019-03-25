#!/usr/bin/env python2

import logging as log
from math import ceil

from MotorControl import motor_controller as motor
from Ultrasonic import ultrasonic

# ---------------- Logging/Debug configurations ---------------

VERBOSE = "verbose"
QUIET = "quiet"
WARNINGS = "warnings"
ERRORS = "errors"

FILE = "file"
STDOUT = "stdout"

# ---------------------------------- Error codes -------------------------------

SUCCESS = 0
ERR_INVALID_PIN_NUMBER = 1
ERR_INVALID_ARGUMENT = 2
ERR_INVALID_CONFIGURATION = 3
ERR_PWM_NOT_RUNNING = 4
ERR_ERROR = 5

# -------------------------------- States --------------------------------------

UNINITIALIZED = 0
READY = 1
RUNNING = 2
STOPPED = 3

# ----------------------------- Directions -------------------------------------

FORWARD = 0
BACKWARD = 1
ROTATE_RIGHT = 2
ROTATE_LEFT = 3
TURN_RIGHT = 4
TURN_LEFT = 5


# ------------------------------ RC Car Controller -----------------------------


class RCCar(object):

    def __init__(self, **kwargs):

        self._left_motor_pin_1 = kwargs.get("left_motor_pin_1", None)
        self._left_motor_pin_2 = kwargs.get("left_motor_pin_2", None)
        self._right_motor_pin_1 = kwargs.get("right_motor_pin_1", None)
        self._right_motor_pin_2 = kwargs.get("right_motor_pin_2", None)
        self._ultrasonic_trig_pin = kwargs.get("ultrasonic_trig_pin", None)
        self._ultrasonic_echo_pin = kwargs.get("ultrasonic_echo_pin", None)

        self._min_speed = kwargs.get("motor_min_speed", 30)
        self._turn_rate = kwargs.get("car_turn_rate", 50)
        self._rel_speed = 0
        self._state = STOPPED
        self._direction = None

        self._distance = 0
        self._ultrasonic_handler = None

        self.right_motor = motor.MotorControl(min_speed=kwargs.get("motor_min_speed", 30))
        self.left_motor = motor.MotorControl(min_speed=kwargs.get("motor_min_speed", 30))
        self.ultrasonic = ultrasonic.UltrasonicSensor(min_distance=5, max_distance=300)

    # initialize car components
    def initialize(self):

        err_code = SUCCESS
        left_motor = self.right_motor.init_motor(self._right_motor_pin_1, self._right_motor_pin_2)
        right_motor = self.left_motor.init_motor(self._left_motor_pin_1, self._left_motor_pin_2)
        ranger = self.ultrasonic.init_ultrasonic(trig_pin=self._ultrasonic_trig_pin, echo_pin=self._ultrasonic_echo_pin)

        if left_motor != motor.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Left motor failed to initialize!")

        elif right_motor != motor.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Right motor failed to initialize!")

        elif ranger != ultrasonic.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Ultrasonic failed to initialize!")

        else:

            self._state = READY
            log.debug("Car modules initialized successfully!")

        return err_code

    # de-initialize car modules
    def deinit(self):

        err_code = SUCCESS

        # TODO :: Deinit car modules
        if self._state != UNINITIALIZED:

            self.right_motor.deinit_motor()
            self.left_motor.deinit_motor()
            self.ultrasonic.de_init()

        else:

            err_code = ERR_ERROR

        return err_code

    # move the car in a given direction
    def move(self, direction):

        err_code = SUCCESS

        if self._state == UNINITIALIZED:

            log.error("Trying to move car before initialization!")
            err_code = ERR_ERROR

        else:

            if self._rel_speed:

                # calculate motor speed
                speed = int(30 + ceil(0.7 * self._rel_speed))

            else:

                speed = 0

            self._direction = direction

            if direction == FORWARD:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=speed)

            elif direction == BACKWARD:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=speed)

            elif direction == ROTATE_RIGHT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._min_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._min_speed)

            elif direction == ROTATE_LEFT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._min_speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._min_speed)

            elif direction == TURN_RIGHT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=int(speed * (self._turn_rate / 100.0)))
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=speed)

            elif direction == TURN_LEFT:

                self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=speed)
                self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=int(speed * (self._turn_rate / 100.0)))

            else:

                log.error("Failed to move car in direction: {}".format(direction))
                log.debug("Invalid direction: {}".format(direction))
                err_code = ERR_INVALID_ARGUMENT
                self._direction = None

        return err_code

    # change motor parameters
    def change_motor_params(self, speed=None, turn_rate=None):

        err_code = SUCCESS

        if speed:
            self._rel_speed = speed
            log.debug("Changed motor speed to: {}!".format(speed))

        if turn_rate:
            self._turn_rate = turn_rate
            log.debug("Changed turn rate to: {}!".format(speed))

        if self._state != STOPPED or self._state != UNINITIALIZED:
            self.move(self._direction)

        return err_code

    # get car's speed
    def get_speed(self):

        return self._rel_speed

    # gets distance ahead of the car
    def get_distance(self):

        self._direction = self.ultrasonic.get_distance()
        return self._distance

    # --------------------------- configure logging ----------------------------
    @classmethod
    def log_config(cls, stream, **kwargs):
        verbosity = kwargs.get("verbosity", QUIET)
        filename = kwargs.get("filename", ".gpiolog")

        # logger for debugging
        if verbosity == VERBOSE:

            dlevel = log.DEBUG

        elif verbosity == QUIET:

            dlevel = log.INFO

        elif verbosity == WARNINGS:

            dlevel = log.WARNING

        elif verbosity == ERRORS:

            dlevel = log.ERROR

        else:

            dlevel = log.INFO

        if stream == FILE:

            log.basicConfig(filename=filename, filemode='w', format="[RC_CAR]::%(levelname)s::%(asctime)s::%(message)s",
                            datefmt="%d/%m/%Y %I:%M:%S", level=dlevel)

        else:

            log.basicConfig(format="[RC_CAR]::%(levelname)s::%(asctime)s::%(message)s", datefmt="%d/%m/%Y %I:%M:%S",
                            level=dlevel)


if __name__ == '__main__':

    import time

    # HearBeat Pin
    HEART_BEAT_PIN = 5

    # Right Motor Pins
    RIGHT_MOTOR_PIN_1 = 12
    RIGHT_MOTOR_PIN_2 = 16

    # Left Motor Pin
    LEFT_MOTOR_PIN_1 = 20
    LEFT_MOTOR_PIN_2 = 21

    # Motor min duty cycle
    MOTOR_MIN_SPEED = 30

    # Ultrasonic Pins
    US_TRGI_PIN = 26
    US_ECHO_PIN = 19

    RCCar.log_config(STDOUT, verbosity=VERBOSE)

    rc = RCCar(
            left_motor_pin_1=LEFT_MOTOR_PIN_1,
            left_motor_pin_2=LEFT_MOTOR_PIN_2,
            right_motor_pin_1=RIGHT_MOTOR_PIN_1,
            right_motor_pin_2=RIGHT_MOTOR_PIN_2,
            ultrasonic_trig_pin=US_TRGI_PIN,
            ultrasonic_echo_pin=US_ECHO_PIN
    )

    rc.initialize()

    rc.change_motor_params(speed=1)

    count = 0

    while (count < 1):

        count += 1
        time.sleep(1)

        if (count < 10):

            rc.move(FORWARD)

        else:

            rc.move(BACKWARD)

        print("speed: {}, distance: {}".format(rc.get_speed(), rc.get_distance()))

    rc.deinit()

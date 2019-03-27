#!/usr/bin/env python2

import logging as log
from math import ceil

import motor_controller as motor
import ultrasonic

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

# TODO :: Find integration problem!!
# TODO :: 1 - Ultrasonic reads 0
# TODO :: 2 - Motors are not working properly

class RCCar(object):

    def __init__(self, **kwargs):

        self.right_motor = None
        self.left_motor = None
        self.ultrasonic = None

        self._left_motor_pin_1 = kwargs.get("lm_pin_1", None)
        self._left_motor_pin_2 = kwargs.get("lm_pin_2", None)
        self._right_motor_pin_1 = kwargs.get("rm_pin_1", None)
        self._right_motor_pin_2 = kwargs.get("rm_pin_2", None)

        self._ultrasonic_trig_pin = kwargs.get("us_trig_pin", None)
        self._ultrasonic_echo_pin = kwargs.get("us_echo_pin", None)
        self._ultrasonic_min_distance = kwargs.get("us_min_distance", None)
        self._ultrasonic_max_distance = kwargs.get("us_max_distance", None)

        self._motor_min_speed = kwargs.get("motor_min_speed", 0)

        self._car_turn_rate = kwargs.get("car_turn_rate", 0)
        self._car_speed = 0
        self._car_direction = None

        self._distance_to_object = 0

        self._state = UNINITIALIZED

    # initialize car components
    def initialize(self):

        err_code = SUCCESS

        # create instances of car modules 9left motor, right motor, ultrasonic)
        self.right_motor = motor.MotorControl(self._motor_min_speed)
        self.left_motor = motor.MotorControl(self._motor_min_speed)
        self.ultrasonic = ultrasonic.UltrasonicSensor(self._ultrasonic_min_distance, self._ultrasonic_max_distance)

        # initialize car modules
        left_motor = self.right_motor.init_motor(self._right_motor_pin_1, self._right_motor_pin_2)
        right_motor = self.left_motor.init_motor(self._left_motor_pin_1, self._left_motor_pin_2)
        ranger = self.ultrasonic.init_ultrasonic(trig_pin=self._ultrasonic_trig_pin, echo_pin=self._ultrasonic_echo_pin)

        # if initializing left motor was successful
        if left_motor != motor.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Left motor failed to initialize!")

        # if initializing right motor was successful
        elif right_motor != motor.SUCCESS:

            err_code = ERR_ERROR
            log.critical("Right motor failed to initialize!")

        # if initializing ultrasonic was successful
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

        # check if car is initialized
        if self._state != UNINITIALIZED:

            # deinit car modules
            self.right_motor.deinit_motor()
            self.left_motor.deinit_motor()
            self.ultrasonic.deinit_ultrasonic()

            # reset car attributes
            self.right_motor = None
            self.left_motor = None
            self.ultrasonic = None

            self._left_motor_pin_1 = None
            self._left_motor_pin_2 = None
            self._right_motor_pin_1 = None
            self._right_motor_pin_2 = None

            self._ultrasonic_trig_pin = None
            self._ultrasonic_echo_pin = None
            self._ultrasonic_min_distance = None
            self._ultrasonic_max_distance = None

            self._motor_min_speed = 0
            self._car_turn_rate = 0
            self._car_speed = 0
            self._car_direction = None

            self._distance_to_object = 0

            self._state = UNINITIALIZED

        else:

            err_code = ERR_ERROR
            log.error("Failed to deinit car modules! Car modules are already uninitialized!")

        return err_code

    # move the car in a given direction
    def move(self, direction, speed):

        err_code = SUCCESS

        # check if car is initialized
        if self._state == UNINITIALIZED:

            log.error("Trying to move car before initialization!")
            err_code = ERR_ERROR

        else:

            if speed >= 0:

                self._car_speed = speed

            else:

                self._car_speed = 0
                log.error("Car speed {} can't be a negative number!".format(speed))

            # if car speed is > 0
            if self._car_speed:

                # calculate motor speed
                motors_pwm = int(self._motor_min_speed + ceil(0.7 * self._car_speed))

                self._state = RUNNING
                self._car_direction = direction

                # if direction is forward
                if direction == FORWARD:

                    # rotate both motors in the same direction (clockwise direction)
                    self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=motors_pwm)
                    self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=motors_pwm)
                    log.debug("Moving car in forward direction!")

                elif direction == BACKWARD:

                    self.right_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=motors_pwm)
                    self.left_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=motors_pwm)
                    self._state = RUNNING
                    log.debug("Moving car in backwards direction!")

                elif direction == ROTATE_RIGHT:

                    self.right_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._motor_min_speed)
                    self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._motor_min_speed)
                    self._state = RUNNING
                    log.debug("Rotating car to the right!")

                elif direction == ROTATE_LEFT:

                    self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=self._motor_min_speed)
                    self.left_motor.rotate_motor(direction=motor.ROTATE_CCW, speed=self._motor_min_speed)
                    self._state = RUNNING
                    log.debug("Rotating car to the left!")

                elif direction == TURN_RIGHT:

                    self.right_motor.rotate_motor(direction=motor.ROTATE_CW,
                                                  speed=(motors_pwm - int(motors_pwm * self._car_turn_rate / 100)))
                    self.left_motor.rotate_motor(direction=motor.ROTATE_CW, speed=motors_pwm)
                    self._state = RUNNING
                    log.debug("Turning car to the right!")

                elif direction == TURN_LEFT:

                    self.right_motor.rotate_motor(direction=motor.ROTATE_CW, speed=motors_pwm)
                    self.left_motor.rotate_motor(direction=motor.ROTATE_CW,
                                                 speed=(motors_pwm - int(motors_pwm * self._car_turn_rate / 100)))
                    self._state = RUNNING
                    log.debug("Turning car to the left!")

                else:

                    log.error("Failed to move car in direction: {}".format(direction))
                    log.debug("Invalid direction: {}".format(direction))
                    err_code = ERR_INVALID_ARGUMENT

            else:

                self.right_motor.update_speed(0)
                self.left_motor.update_speed(0)
                self._state = STOPPED

        return err_code

    # change motor parameters
    def change_car_params(self, speed=None, turn_rate=None):

        err_code = SUCCESS

        if speed:
            self._car_speed = speed
            log.debug("Changed motor speed to: {}!".format(speed))

        if turn_rate:
            self._car_turn_rate = turn_rate
            log.debug("Changed turn rate to: {}!".format(speed))

        if (self._state != STOPPED and self._state != UNINITIALIZED) and self._car_direction:
            self.move(self._car_direction)

        return err_code

    # get car's speed
    def get_speed(self):

        return self._car_speed

    # gets distance ahead of the car
    def get_distance(self):

        self._distance_to_object = self.ultrasonic.get_distance()

        return self._distance_to_object

    # --------------------------- configure logging ----------------------------
    @classmethod
    def log_config(cls, stream, **kwargs):

        verbosity = kwargs.get("verbosity", QUIET)
        filename = kwargs.get("filename", ".rccar_log")

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

    RCCar.log_config(STDOUT, verbosity=QUIET)

    rc = RCCar(
            left_motor_pin_1=LEFT_MOTOR_PIN_1,
            left_motor_pin_2=LEFT_MOTOR_PIN_2,
            right_motor_pin_1=RIGHT_MOTOR_PIN_1,
            right_motor_pin_2=RIGHT_MOTOR_PIN_2,
            ultrasonic_trig_pin=US_TRGI_PIN,
            ultrasonic_echo_pin=US_ECHO_PIN
    )

    rc.initialize()

    rc.change_car_params(speed=1, turn_rate=1)

    count = 0
    max_count = 20

    while count < max_count:

        count += 1
        time.sleep(1)

        if (count < max_count / 2):

            rc.move(FORWARD)

        else:

            rc.move(BACKWARD)

        print("speed: {}, distance: {}".format(rc.get_speed(), rc.get_distance()))

    rc.deinit()
